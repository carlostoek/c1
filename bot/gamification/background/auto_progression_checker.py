"""
Background job: Auto-progression checker.

Verifica periódicamente usuarios que deben subir de nivel
pero no lo han hecho por falta de interacción.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

from bot.gamification.database.models import UserGamification
from bot.gamification.services.container import GamificationContainer

logger = logging.getLogger(__name__)


async def check_all_users_progression(session: AsyncSession, bot: Bot):
    """
    Verifica level-ups pendientes para todos los usuarios.

    Flujo:
    1. Obtener todos los UserGamification
    2. Para cada usuario:
       - Llamar level_service.check_and_apply_level_up()
       - Si hubo cambio, notificar al usuario
    3. Log de estadísticas (X usuarios procesados, Y level-ups)

    Batch processing: 100 usuarios por lote

    Args:
        session: AsyncSession de SQLAlchemy
        bot: Instancia del Bot de aiogram
    """
    # Crear container de gamificación
    gamification = GamificationContainer(session, bot)

    # Obtener todos los usuarios
    stmt = select(UserGamification)
    result = await session.execute(stmt)
    all_users = result.scalars().all()

    processed = 0
    level_ups = 0

    # Procesar en batch
    BATCH_SIZE = 100
    for i in range(0, len(all_users), BATCH_SIZE):
        batch = all_users[i:i+BATCH_SIZE]

        for user_gamif in batch:
            try:
                changed, old_level, new_level = await gamification.level.check_and_apply_level_up(
                    user_gamif.user_id
                )

                if changed:
                    level_ups += 1
                    logger.info(
                        f"Auto level-up: User {user_gamif.user_id} "
                        f"{old_level.name} → {new_level.name}"
                    )

                    # Notificar usando servicio de notificaciones
                    await gamification.notifications.notify_level_up(
                        user_gamif.user_id, old_level, new_level
                    )

                processed += 1

            except Exception as e:
                logger.error(f"Error processing user {user_gamif.user_id}: {e}")

        # Commit batch
        await session.commit()

    logger.info(
        f"Auto-progression check completed: "
        f"{processed} users processed, {level_ups} level-ups applied"
    )


def setup_auto_progression_scheduler(
    scheduler: AsyncIOScheduler,
    session_maker,
    bot: Bot
):
    """
    Configura job en scheduler.

    El job se ejecuta cada 6 horas para verificar usuarios
    que necesitan subir de nivel.

    Args:
        scheduler: AsyncIOScheduler de APScheduler
        session_maker: Factory de sesiones async de SQLAlchemy
        bot: Instancia del Bot de aiogram
    """

    async def job():
        async with session_maker() as session:
            await check_all_users_progression(session, bot)

    scheduler.add_job(
        job,
        trigger='interval',
        hours=6,
        id='auto_progression_checker',
        replace_existing=True
    )

    logger.info("Auto-progression checker scheduled (every 6 hours)")
