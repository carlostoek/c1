"""
Background tasks for user lifecycle management (ONDA D).
"""
import logging

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from bot.database import get_session
from bot.services.user_lifecycle import UserLifecycleService, LifecycleState
from bot.services.risk_score import RiskScoreService
from bot.services.reengagement import ReengagementService

logger = logging.getLogger(__name__)


async def update_user_lifecycle_states(bot: Bot):
    """
    Periodically evaluates and updates the lifecycle state for all users.
    Runs every hour.
    """
    logger.info("🔄 Running task: Update User Lifecycle States")
    try:
        async with get_session() as session:
            lifecycle_service = UserLifecycleService(session)
            updated_count = await lifecycle_service.evaluate_all_users_state()
            if updated_count > 0:
                logger.info(f"✅ User lifecycle states updated for {updated_count} users.")
            else:
                logger.debug("✓ No user lifecycle state transitions were needed.")
    except Exception as e:
        logger.error(f"❌ Error in update_user_lifecycle_states task: {e}", exc_info=True)


async def send_reengagement_messages(bot: Bot):
    """
    Sends re-engagement messages to users who are at risk or dormant.
    Runs every 6 hours.
    """
    logger.info("🔄 Running task: Send Re-engagement Messages")
    try:
        async with get_session() as session:
            # These services would ideally come from a container
            lifecycle_service = UserLifecycleService(session)
            reengagement_service = ReengagementService(session, lifecycle_service)
            
            at_risk_sent = await reengagement_service.send_reengagement_messages_for_state(LifecycleState.AT_RISK)
            dormant_sent = await reengagement_service.send_reengagement_messages_for_state(LifecycleState.DORMANT)

            total_sent = at_risk_sent + dormant_sent
            if total_sent > 0:
                logger.info(f"✅ Sent {total_sent} re-engagement messages.")
            else:
                logger.debug("✓ No re-engagement messages sent.")
    except Exception as e:
        logger.error(f"❌ Error in send_reengagement_messages task: {e}", exc_info=True)


async def calculate_risk_scores(bot: Bot):
    """
    Recalculates the churn risk score for all users.
    Runs daily at 4 AM UTC.
    """
    logger.info("🔄 Running task: Calculate All User Risk Scores")
    try:
        async with get_session() as session:
            risk_score_service = RiskScoreService(session)
            processed_count = await risk_score_service.update_all_risk_scores()
            logger.info(f"✅ Calculated risk scores for {processed_count} users.")
    except Exception as e:
        logger.error(f"❌ Error in calculate_risk_scores task: {e}", exc_info=True)


async def archive_lost_users(bot: Bot):
    """
    Archives data for users who have been in the 'LOST' state for a long time.
    Runs weekly on Sunday at 5 AM UTC.
    Placeholder for now.
    """
    logger.info("🔄 Running task: Archive Lost Users (Placeholder)")
    # TODO: Implement the logic to archive user data for GDPR compliance or data cleanup.
    # This might involve anonymizing data or moving it to a separate 'archive' table.
    logger.info("✅ Archive Lost Users task finished (no action taken).")


def add_lifecycle_tasks_to_scheduler(scheduler: AsyncIOScheduler, bot: Bot):
    """Adds all ONDA D lifecycle management tasks to the APScheduler."""

    # Task 1: Update user lifecycle states (every hour)
    scheduler.add_job(
        update_user_lifecycle_states,
        trigger=IntervalTrigger(hours=1),
        args=[bot],
        id="update_user_lifecycle_states",
        name="Update User Lifecycle States",
        replace_existing=True,
        max_instances=1,
    )
    logger.info("✅ Task scheduled: Update User Lifecycle States (every 1 hour)")

    # Task 2: Send re-engagement messages (every 6 hours)
    scheduler.add_job(
        send_reengagement_messages,
        trigger=IntervalTrigger(hours=6),
        args=[bot],
        id="send_reengagement_messages",
        name="Send Re-engagement Messages",
        replace_existing=True,
        max_instances=1,
    )
    logger.info("✅ Task scheduled: Send Re-engagement Messages (every 6 hours)")

    # Task 3: Calculate risk scores (daily at 4 AM UTC)
    scheduler.add_job(
        calculate_risk_scores,
        trigger=CronTrigger(hour=4, minute=0, timezone="UTC"),
        args=[bot],
        id="calculate_risk_scores",
        name="Calculate All User Risk Scores",
        replace_existing=True,
        max_instances=1,
    )
    logger.info("✅ Task scheduled: Calculate Risk Scores (daily at 4 AM UTC)")
    
    # Task 4: Archive lost users (weekly on Sunday at 5 AM UTC)
    scheduler.add_job(
        archive_lost_users,
        trigger=CronTrigger(day_of_week='sun', hour=5, minute=0, timezone="UTC"),
        args=[bot],
        id="archive_lost_users",
        name="Archive Lost Users",
        replace_existing=True,
        max_instances=1,
    )
    logger.info("✅ Task scheduled: Archive Lost Users (weekly on Sunday at 5 AM UTC)")
