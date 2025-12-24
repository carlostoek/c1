"""Background jobs para gamificación."""

from bot.gamification.background.auto_progression_checker import (
    setup_auto_progression_scheduler,
    check_all_users_progression,
    notify_level_up
)
from bot.gamification.background.streak_expiration_checker import (
    setup_streak_expiration_scheduler,
    check_expired_streaks,
    notify_streak_lost
)

__all__ = [
    "setup_auto_progression_scheduler",
    "check_all_users_progression",
    "notify_level_up",
    "setup_streak_expiration_scheduler",
    "check_expired_streaks",
    "notify_streak_lost"
]
