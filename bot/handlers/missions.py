"""
Mission Handlers - Comandos y tracking de misiones.

Funcionalidad:
- /misiones: Ver misiones activas del usuario
- Tracking automático al ganar puntos/reacciones
- Reset automático de misiones temporales
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from bot.database import get_session
from bot.services.container import ServiceContainer
from bot.database.models import ObjectiveType

logger = logging.getLogger(__name__)
router = Router()


# ===== COMANDO /MISIONES =====

@router.message(Command("misiones"))
async def show_missions(message: Message):
    """
    Muestra misiones activas del usuario con progreso.

    Estructura:
    - Misiones por completar
    - Progreso y objetivo
    - Recompensa si existe
    """
    try:
        async with get_session() as session:
            container = ServiceContainer(session, message.bot)

            # Obtener misiones activas
            active_missions = await container.missions.get_active_missions(
                message.from_user.id
            )

            if not active_missions:
                await message.answer(
                    "🎯 <b>No hay misiones disponibles</b>\n\n"
                    "Vuelve más tarde para ver nuevas misiones.",
                    parse_mode="HTML"
                )
                return

            # Obtener progreso del usuario
            user_missions = await container.missions.get_user_missions(
                message.from_user.id,
                include_completed=False
            )

            # Mapear progreso
            progress_map = {um.mission_id: um for um in user_missions}

            # Construir mensaje
            text = "🎯 <b>Misiones Activas</b>\n\n"

            mission_count = 0

            for mission in active_missions:
                user_mission = progress_map.get(mission.id)

                # Skip misiones completadas
                if user_mission and user_mission.is_completed:
                    continue

                mission_count += 1

                # Info básica
                text += f"{mission.display_name}\n"
                text += f"📝 {mission.description}\n"

                # Iconos según objetivo
                obj_icons = {
                    "points": "💰",
                    "reactions": "❤️",
                    "level": "⭐",
                    "custom": "🎯"
                }
                obj_icon = obj_icons.get(mission.objective_type.value, "🎯")

                # Progreso
                if user_mission:
                    progress = user_mission.current_progress
                    objective = mission.objective_value
                    pct = user_mission.progress_percentage
                    text += f"{obj_icon} Progreso: {progress}/{objective} ({pct:.0f}%)\n"
                else:
                    text += f"{obj_icon} Objetivo: {mission.objective_value}\n"

                # Recompensa
                if mission.reward:
                    text += f"🎁 Recompensa: {mission.reward.display_name}\n"

                text += "\n"

            if mission_count == 0:
                await message.answer(
                    "✅ <b>¡Completaste todas las misiones!</b>\n\n"
                    "Vuelve más tarde para nuevas misiones.",
                    parse_mode="HTML"
                )
                return

            await message.answer(text, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error showing missions: {e}", exc_info=True)
        await message.answer(
            "❌ Error al cargar misiones. Intenta más tarde.",
            parse_mode="HTML"
        )


# ===== EVENT LISTENERS (tracking automático) =====

async def on_points_earned(user_id: int, amount: int, session):
    """
    Listener cuando usuario gana puntos.

    Se llama desde PointsService.award_points() después de otorgar puntos.

    Args:
        user_id: ID del usuario
        amount: Cantidad de puntos ganados
        session: Sesión de BD
    """
    try:
        container = ServiceContainer(session)

        # Actualizar misiones de puntos
        updated = await container.missions.update_progress(
            user_id=user_id,
            objective_type=ObjectiveType.POINTS,
            amount=amount
        )

        # Log de completadas
        for um in updated:
            if um.is_completed and um.completed_at:
                logger.info(
                    f"Mission completed! user={user_id}, "
                    f"mission={um.mission.name}"
                )

    except Exception as e:
        logger.error(f"Error in on_points_earned: {e}", exc_info=True)


async def on_reaction_made(user_id: int, session):
    """
    Listener cuando usuario hace reacción a un mensaje.

    Se llama desde ReactionHandler después de registrar la reacción.

    Args:
        user_id: ID del usuario
        session: Sesión de BD
    """
    try:
        container = ServiceContainer(session)

        await container.missions.update_progress(
            user_id=user_id,
            objective_type=ObjectiveType.REACTIONS,
            amount=1
        )

    except Exception as e:
        logger.error(f"Error in on_reaction_made: {e}", exc_info=True)


async def on_level_up(user_id: int, new_level: int, session):
    """
    Listener cuando usuario sube de nivel.

    Se llama desde LevelsService.apply_level_up() después de aplicar level-up.

    Args:
        user_id: ID del usuario
        new_level: Nuevo nivel
        session: Sesión de BD
    """
    try:
        container = ServiceContainer(session)

        # Actualizar misiones de nivel
        # Incrementar el nivel como si fuera un "logro"
        await container.missions.update_progress(
            user_id=user_id,
            objective_type=ObjectiveType.LEVEL,
            amount=1
        )

    except Exception as e:
        logger.error(f"Error in on_level_up: {e}", exc_info=True)


# ===== CRON JOB =====

async def reset_missions_cron():
    """
    Job para resetear misiones expiradas (daily/weekly).

    Ejecutar periódicamente vía APScheduler:
    - IntervalTrigger(hours=1) - Cada hora
    - O CronTrigger(hour=0, minute=0) - Medianoche

    Sin argumentos, se conecta a la BD automáticamente.
    """
    try:
        async with get_session() as session:
            container = ServiceContainer(session)
            count = await container.missions.reset_expired_missions()
            logger.info(f"Cron: Reset {count} expired missions")

    except Exception as e:
        logger.error(f"Error in cron reset_missions: {e}", exc_info=True)


# ===== INTEGRACIÓN EN OTROS SERVICIOS =====

"""
CÓMO INTEGRAR EN OTROS SERVICIOS:

1. En PointsService.award_points():

   async def award_points(self, user_id, amount, reason=None, apply_multipliers=True):
       # ... código existente ...

       # Trigger missions update
       from bot.handlers.missions import on_points_earned
       await on_points_earned(user_id, final_amount, self.session)

2. En ReactionHandler / reactions service:

   async def record_user_reaction(...):
       # ... código existente ...

       # Trigger missions update
       from bot.handlers.missions import on_reaction_made
       await on_reaction_made(user_id, session)

3. En LevelsService.apply_level_up():

   async def apply_level_up(self, user_id, new_level):
       # ... código existente ...

       # Trigger missions update
       from bot.handlers.missions import on_level_up
       await on_level_up(user_id, new_level, self.session)

4. En main.py (APScheduler setup):

   from bot.handlers.missions import reset_missions_cron
   from apscheduler.schedulers.asyncio import AsyncIOScheduler
   from apscheduler.triggers.cron import CronTrigger

   scheduler = AsyncIOScheduler()

   # Resetear misiones a medianoche UTC
   scheduler.add_job(
       reset_missions_cron,
       CronTrigger(hour=0, minute=0, timezone="UTC"),
       id="reset_missions",
       name="Reset expired missions"
   )

   scheduler.start()

5. En handlers/__init__.py:

   from bot.handlers.missions import router as missions_router

   def register_all_handlers(dispatcher: Dispatcher) -> None:
       dispatcher.include_router(missions_router)
"""
