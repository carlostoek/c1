"""
Service for user re-engagement (ONDA D).

- Generates re-engagement messages based on user's lifecycle state.
- Manages when and how to send re-engagement communications.
- Handles user return bonuses.
- Adheres to "dignity rules" to avoid spamming.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import UserLifecycle, ReengagementLog
from bot.services.user_lifecycle import UserLifecycleService, LifecycleState
# from bot.services.lucien_voice import LucienVoiceService # ONDA B

logger = logging.getLogger(__name__)


class ReengagementService:
    """Manages the re-engagement process for inactive users."""

    def __init__(
        self,
        session: AsyncSession,
        lifecycle_service: UserLifecycleService,
        # lucien_service: LucienVoiceService, # ONDA B
    ):
        self.session = session
        self.lifecycle_service = lifecycle_service
        # self.lucien_service = lucien_service # ONDA B

    async def get_reengagement_message(self, user_id: int, state: LifecycleState) -> Optional[str]:
        """
        Gets a re-engagement message appropriate for the user's state.
        This will use LucienVoiceService in the future.
        """
        lifecycle = await self.lifecycle_service.get_user_lifecycle(user_id)
        if not lifecycle:
            return None

        # Placeholder messages, to be replaced by LucienVoiceService
        days_inactive = (datetime.utcnow() - lifecycle.last_activity).days
        messages = {
            LifecycleState.AT_RISK: f"He notado tu ausencia de {days_inactive} días. Diana preguntó por ti...",
            LifecycleState.DORMANT: f"Han pasado {days_inactive} días. Hay cosas que quiero mostrarte...",
            LifecycleState.LOST: "Este será mi último mensaje. Si decides volver, aquí estaré.",
        }
        
        # This logic will be more complex, considering message history
        return messages.get(state)

    async def should_send_message(self, user_id: int) -> bool:
        """
        Determines if a re-engagement message should be sent, respecting dignity rules.
        - Max 2-3 messages per inactive user.
        - Never more than 1 message per week.
        - Respects do_not_disturb flag.
        """
        lifecycle = await self.lifecycle_service.get_user_lifecycle(user_id)
        if not lifecycle or lifecycle.do_not_disturb:
            return False

        # Rule: Max 3 messages total
        if lifecycle.messages_sent_count >= 3:
            return False
            
        # Rule: Not more than 1 message per week
        if lifecycle.last_message_sent and (datetime.utcnow() - lifecycle.last_message_sent) < timedelta(days=7):
            return False
            
        return True

    async def record_message_sent(self, user_id: int, message_type: str) -> None:
        """
        Records that a re-engagement message has been sent to a user.
        """
        lifecycle = await self.lifecycle_service.get_user_lifecycle(user_id)
        if not lifecycle:
            return

        now = datetime.utcnow()
        lifecycle.messages_sent_count += 1
        lifecycle.last_message_sent = now

        log_entry = ReengagementLog(
            user_id=user_id,
            message_type=message_type,
            sent_at=now,
        )
        self.session.add(log_entry)
        await self.session.commit()
        logger.info(f"Recorded re-engagement message '{message_type}' for user {user_id}.")

    async def get_return_bonus(self, user_id: int) -> int:
        """
        Calculates a "welcome back" bonus in besitos for a returning user.
        The bonus could depend on the length of absence.
        """
        days_inactive = await self.lifecycle_service.calculate_days_inactive(user_id)
        
        if days_inactive > 30:  # LOST
            return 100 # Big bonus
        elif days_inactive > 7: # DORMANT
            return 50
        elif days_inactive > 3: # AT_RISK
            return 20
            
        return 0

    async def process_user_return(self, user_id: int) -> Dict:
        """
        Processes a user's return after a period of inactivity.
        - Calculates and returns a bonus.
        - Resets their lifecycle state.
        - Returns a welcome back message.
        """
        bonus = await self.get_return_bonus(user_id)
        
        # This will grant the besitos via GamificationService
        # For now, we just return the amount.
        
        # Reset lifecycle state
        lifecycle = await self.lifecycle_service.update_user_activity(user_id)
        
        # Placeholder message
        welcome_back_message = f"Has vuelto. Te estaba esperando. Como muestra de aprecio, he añadido {bonus} besitos a tu cuenta."

        return {
            "bonus_granted": bonus,
            "welcome_back_message": welcome_back_message,
            "new_state": lifecycle.current_state,
        }

    async def send_reengagement_messages_for_state(self, state: LifecycleState) -> int:
        """
        Finds users in a given state and sends them a re-engagement message if appropriate.
        """
        users_in_state = await self.lifecycle_service.get_users_by_state(state)
        sent_count = 0
        
        for user in users_in_state:
            if await self.should_send_message(user.user_id):
                message = await self.get_reengagement_message(user.user_id, state)
                if message:
                    # In a real scenario, this would use the bot to send the message
                    logger.info(f"WOULD SEND to {user.user_id}: {message}")
                    
                    await self.record_message_sent(user.user_id, f"{state.value}_auto")
                    sent_count += 1
        
        logger.info(f"Sent {sent_count} re-engagement messages for state {state.value}.")
        return sent_count
