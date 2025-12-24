"""Handlers de Telegram para gamificación."""

from bot.gamification.handlers.admin import main, mission_wizard, reward_wizard
from bot.gamification.handlers.user import profile, missions, rewards, leaderboard

# Exportar routers admin
gamification_admin_router = main.router
gamification_mission_wizard_router = mission_wizard.router
gamification_reward_wizard_router = reward_wizard.router

# Exportar routers user
gamification_user_profile_router = profile.router
gamification_user_missions_router = missions.router
gamification_user_rewards_router = rewards.router
gamification_user_leaderboard_router = leaderboard.router

__all__ = [
    "gamification_admin_router",
    "gamification_mission_wizard_router",
    "gamification_reward_wizard_router",
    "gamification_user_profile_router",
    "gamification_user_missions_router",
    "gamification_user_rewards_router",
    "gamification_user_leaderboard_router",
]
