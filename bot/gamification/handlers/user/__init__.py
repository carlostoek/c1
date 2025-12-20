"""
Gamification User handlers module.
"""
from bot.gamification.handlers.user.profile import router as user_profile_router
from bot.gamification.handlers.user.missions import router as user_missions_router
from bot.gamification.handlers.user.rewards import router as user_rewards_router
from bot.gamification.handlers.user.leaderboard import router as user_leaderboard_router

# Include all sub-routers
user_profile_router.include_router(user_missions_router)
user_profile_router.include_router(user_rewards_router)
user_profile_router.include_router(user_leaderboard_router)

router = user_profile_router

__all__ = ["router"]