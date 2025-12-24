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

    processed = 0
    level_ups = 0

    # Procesar usuarios en streaming para evitar cargarlos todos en memoria
    stmt = select(UserGamification)
    result = await session.stream_scalars(stmt)

    # Procesar en batches
    batch = []
    async for user_gamif in result:
        batch.append(user_gamif)

        # Procesar batch cuando alcance el tamaño o terminar el iterador
        if len(batch) >= 100:
            for batch_user in batch:
                try:
                    changed, old_level, new_level = await gamification.level.check_and_apply_level_up(
                        batch_user.user_id
                    )

                    if changed:
                        level_ups += 1
                        logger.info(
                            f"Auto level-up: User {batch_user.user_id} "
                            f"{old_level.name} → {new_level.name}"
                        )

                        # Notificar usando servicio de notificaciones
                        await gamification.notifications.notify_level_up(
                            batch_user.user_id, old_level, new_level
                        )

                    processed += 1

                except Exception as e:
                    logger.error(f"Error processing user {batch_user.user_id}: {e}")

            # Commit batch
            await session.commit()
            batch = []  # Resetear batch

    # Procesar el último batch si hay usuarios restantes
    if batch:
        for batch_user in batch:
            try:
                changed, old_level, new_level = await gamification.level.check_and_apply_level_up(
                    batch_user.user_id
                )

                if changed:
                    level_ups += 1
                    logger.info(
                        f"Auto level-up: User {batch_user.user_id} "
                        f"{old_level.name} → {new_level.name}"
                    )

                    # Notificar usando servicio de notificaciones
                    await gamification.notifications.notify_level_up(
                        batch_user.user_id, old_level, new_level
                    )

                processed += 1

            except Exception as e:
                logger.error(f"Error processing user {batch_user.user_id}: {e}")

        # Commit último batch
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
