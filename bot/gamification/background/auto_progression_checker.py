"""
Background job: Auto-progression checker.

Verifies periodically users who should level up
but haven't done so due to lack of interaction.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import logging
import json

from bot.gamification.database.models import UserGamification
from bot.gamification.services.level import LevelService

logger = logging.getLogger(__name__)


async def check_all_users_progression(session: AsyncSession, bot: Bot):
    """Verifies pending level-ups for all users."""
    level_service = LevelService(session)
    
    # Get all users
    stmt = select(UserGamification)
    result = await session.execute(stmt)
    all_users = result.scalars().all()
    
    processed = 0
    level_ups = 0
    
    # Process in batch
    BATCH_SIZE = 100
    for i in range(0, len(all_users), BATCH_SIZE):
        batch = all_users[i:i+BATCH_SIZE]
        
        for user_gamif in batch:
            try:
                changed, old_level, new_level = await level_service.check_and_apply_level_up(
                    user_gamif.user_id
                )
                
                if changed:
                    level_ups += 1
                    logger.info(
                        f"Auto level-up: User {user_gamif.user_id} "
                        f"{old_level.name} → {new_level.name}"
                    )
                    
                    # Notify
                    await notify_level_up(bot, user_gamif.user_id, old_level, new_level)
                
                processed += 1
            
            except Exception as e:
                logger.error(f"Error processing user {user_gamif.user_id}: {e}")
        
        # Commit batch
        await session.commit()
    
    logger.info(
        f"Auto-progression check completed: "
        f"{processed} users processed, {level_ups} level-ups applied"
    )


async def notify_level_up(bot: Bot, user_id: int, old_level, new_level):
    """Notify level-up to user."""
    try:
        # Parse benefits if available
        benefits_text = ""
        if new_level.benefits:
            try:
                benefits = json.loads(new_level.benefits)
                if isinstance(benefits, dict) and benefits:
                    benefits_items = []
                    for key, value in benefits.items():
                        benefits_items.append(f"• {key.title()}: {value}")
                    benefits_text = "\n" + "\n".join(benefits_items)
            except (json.JSONDecodeError, AttributeError):
                benefits_text = f"\nBeneficios: {new_level.benefits}"
        else:
            benefits_text = "\nBeneficios desbloqueados: Ninguno especificado"

        message = (
            f"🎉 <b>¡Subiste de nivel!</b>\n\n"
            f"Nivel anterior: {old_level.name}\n"
            f"<b>Nivel nuevo: {new_level.name}</b>\n\n"
            f"Besitos mínimos: {new_level.min_besitos}{benefits_text}"
        )

        await bot.send_message(user_id, message, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Failed to notify user {user_id}: {e}")


def setup_auto_progression_scheduler(
    scheduler: AsyncIOScheduler,
    session_maker,
    bot: Bot
):
    """Set up job in scheduler."""
    
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