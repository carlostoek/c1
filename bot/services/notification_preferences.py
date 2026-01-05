"""
Service for managing user notification preferences (ONDA D).

- Allows users to configure what notifications they receive.
- Manages quiet hours and timezones.
- Provides a centralized way to check if a notification should be sent.
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import NotificationPreferences

logger = logging.getLogger(__name__)


class NotificationPreferencesService:
    """Manages user-specific notification settings."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_preferences(self, user_id: int) -> NotificationPreferences:
        """
        Retrieves a user's notification preferences, creating them if they don't exist.
        """
        preferences = await self.session.get(NotificationPreferences, user_id)
        if not preferences:
            preferences = NotificationPreferences(user_id=user_id)
            self.session.add(preferences)
            await self.session.commit()
            logger.info(f"Created default notification preferences for user {user_id}.")
        return preferences

    async def update_preferences(self, user_id: int, new_settings: Dict[str, Any]) -> NotificationPreferences:
        """
        Updates a user's notification preferences from a dictionary.
        """
        preferences = await self.get_preferences(user_id)
        for key, value in new_settings.items():
            if hasattr(preferences, key):
                if key == "timezone":
                    try:
                        ZoneInfo(value)
                    except ZoneInfoNotFoundError:
                        logger.warning(f"User {user_id} tried to set invalid timezone: {value}")
                        continue # Skip invalid timezone
                setattr(preferences, key, value)
        
        await self.session.commit()
        logger.info(f"Updated notification preferences for user {user_id}.")
        return preferences

    async def get_quiet_hours(self, user_id: int) -> Optional[Tuple[int, int]]:
        """
        Gets the user's defined quiet hours (start, end).
        """
        preferences = await self.get_preferences(user_id)
        if preferences.quiet_hours_start is not None and preferences.quiet_hours_end is not None:
            return (preferences.quiet_hours_start, preferences.quiet_hours_end)
        return None

    async def is_in_quiet_hours(self, user_id: int) -> bool:
        """
        Checks if the current time is within the user's quiet hours.
        """
        preferences = await self.get_preferences(user_id)
        
        try:
            user_tz = ZoneInfo(preferences.timezone)
        except ZoneInfoNotFoundError:
            user_tz = ZoneInfo("UTC") # Fallback to UTC

        now_user_time = datetime.now(user_tz)
        current_hour = now_user_time.hour

        start = preferences.quiet_hours_start
        end = preferences.quiet_hours_end

        # Handle overnight quiet hours (e.g., 22:00 to 08:00)
        if start > end:
            return current_hour >= start or current_hour < end
        # Handle same-day quiet hours (e.g., 13:00 to 15:00)
        else:
            return start <= current_hour < end

    async def should_notify(self, user_id: int, notification_type: str) -> bool:
        """
        Checks if a user should receive a notification of a specific type.
        Considers both explicit preferences and quiet hours.
        
        `notification_type` should correspond to a boolean attribute on the
        `NotificationPreferences` model (e.g., 'content_notifications').
        """
        preferences = await self.get_preferences(user_id)

        # 1. Check if this specific notification type is enabled
        if not getattr(preferences, notification_type, False):
            logger.debug(f"Notification '{notification_type}' disabled for user {user_id}.")
            return False
            
        # 2. Check if user is in their quiet hours
        if await self.is_in_quiet_hours(user_id):
            logger.debug(f"User {user_id} is in quiet hours. Suppressing notification.")
            return False
            
        # TODO: 3. Check max_messages_per_day
        # This requires a separate tracking mechanism, perhaps in Redis or another table.
        # For now, we assume it's not implemented.

        return True
