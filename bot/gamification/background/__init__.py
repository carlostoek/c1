"""Background jobs para gamificación."""

from bot.gamification.background.auto_progression_checker import (
    setup_auto_progression_scheduler,
    check_all_users_progression
)
from bot.gamification.background.streak_expiration_checker import (
    setup_streak_expiration_scheduler,
    check_expired_streaks,
    notify_streak_lost
)
from bot.gamification.background.reaction_hook import (
    router as reaction_router,
    on_reaction_event,
    is_valid_reaction
)

__all__ = [
    "setup_auto_progression_scheduler",
    "check_all_users_progression",
    "setup_streak_expiration_scheduler",
    "check_expired_streaks",
    "notify_streak_lost",
    "reaction_router",
    "on_reaction_event",
    "is_valid_reaction"
]
