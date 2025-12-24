"""
Background job: Streak expiration checker.

Resetea rachas que han expirado por inactividad.
"""

from datetime import datetime, timedelta, UTC
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging

from bot.gamification.database.models import UserStreak, GamificationConfig

logger = logging.getLogger(__name__)


async def check_expired_streaks(session: AsyncSession, bot: Bot):
    """
    Resetea rachas expiradas.

    Flujo:
    1. Obtener GamificationConfig para streak_reset_hours
    2. Calcular threshold: now - timedelta(hours=streak_reset_hours)
    3. SELECT UserStreak WHERE last_reaction_date < threshold
    4. Para cada racha expirada:
       - current_streak = 0
       - Opcional: notificar usuario
    5. Log estadísticas

    Args:
        session: AsyncSession de SQLAlchemy
        bot: Instancia del Bot de aiogram
    """

    # Obtener configuración
    config = await session.get(GamificationConfig, 1)
    if not config:
        logger.error("GamificationConfig not found")
        return

    reset_hours = config.streak_reset_hours
    threshold = datetime.now(UTC) - timedelta(hours=reset_hours)

    # Buscar rachas expiradas
    stmt = select(UserStreak).where(
        UserStreak.last_reaction_date < threshold,
        UserStreak.current_streak > 0
    )
    result = await session.execute(stmt)
    expired_streaks = result.scalars().all()

    reset_count = 0

    for streak in expired_streaks:
        old_streak = streak.current_streak

        # Resetear
        streak.current_streak = 0
        reset_count += 1

        logger.info(
            f"Streak expired: User {streak.user_id} "
            f"(was {old_streak} days, last reaction {streak.last_reaction_date})"
        )

        # Notificar (opcional)
        if config.notifications_enabled:
            await notify_streak_lost(bot, streak.user_id, old_streak)

    await session.commit()

    logger.info(
        f"Streak expiration check completed: "
        f"{len(expired_streaks)} streaks checked, {reset_count} reset"
    )


async def notify_streak_lost(bot: Bot, user_id: int, streak_days: int):
    """
    Notifica pérdida de racha.

    Envía mensaje privado al usuario informando que perdió su racha
    y lo motiva a empezar una nueva.

    Args:
        bot: Instancia del Bot de aiogram
        user_id: ID del usuario de Telegram
        streak_days: Número de días de racha perdidos
    """
    try:
        message = (
            f"🔥 <b>Racha Perdida</b>\n\n"
            f"Tu racha de {streak_days} días expiró por inactividad.\n\n"
            f"¡Reacciona hoy para empezar una nueva racha!"
        )

        await bot.send_message(user_id, message, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Failed to notify user {user_id}: {e}")


def setup_streak_expiration_scheduler(
    scheduler: AsyncIOScheduler,
    session_maker,
    bot: Bot
):
    """
    Configura job en scheduler.

    El job se ejecuta cada 1 hora para verificar rachas expiradas.

    Args:
        scheduler: AsyncIOScheduler de APScheduler
        session_maker: Factory de sesiones async de SQLAlchemy
        bot: Instancia del Bot de aiogram
    """

    async def job():
        async with session_maker() as session:
            await check_expired_streaks(session, bot)

    scheduler.add_job(
        job,
        trigger='interval',
        hours=1,
        id='streak_expiration_checker',
        replace_existing=True
    )

    logger.info("Streak expiration checker scheduled (every 1 hour)")
