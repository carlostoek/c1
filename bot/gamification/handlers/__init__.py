"""Handlers de Telegram para gamificación."""

from bot.gamification.handlers.admin import (
    main,
    mission_wizard,
    reward_wizard,
    wizard_level,
    config,
    level_config,
    transaction_history,
    mission_config,
    reward_config,
    reaction_config,
    daily_gift_config,
    unified_wizard,
    config_panel
)
from bot.gamification.handlers.user import (
    profile,
    missions,
    rewards,
    leaderboard,
    reactions,
    daily_gift
)

# Exportar routers admin
gamification_admin_router = main.router
gamification_mission_wizard_router = mission_wizard.router
gamification_reward_wizard_router = reward_wizard.router
gamification_level_wizard_router = wizard_level.router
gamification_config_router = config.router
gamification_level_config_router = level_config.router
gamification_transaction_history_router = transaction_history.router
gamification_mission_config_router = mission_config.router
gamification_reward_config_router = reward_config.router
gamification_reaction_config_router = reaction_config.router
gamification_daily_gift_config_router = daily_gift_config.router
gamification_unified_wizard_router = unified_wizard.router
gamification_config_panel_router = config_panel.router

# Exportar routers user
gamification_user_profile_router = profile.router
gamification_user_missions_router = missions.router
gamification_user_rewards_router = rewards.router
gamification_user_leaderboard_router = leaderboard.router
gamification_user_reactions_router = reactions.router
gamification_user_daily_gift_router = daily_gift.router

__all__ = [
    "gamification_admin_router",
    "gamification_mission_wizard_router",
    "gamification_reward_wizard_router",
    "gamification_level_wizard_router",
    "gamification_config_router",
    "gamification_level_config_router",
    "gamification_transaction_history_router",
    "gamification_mission_config_router",
    "gamification_reward_config_router",
    "gamification_reaction_config_router",
    "gamification_daily_gift_config_router",
    "gamification_unified_wizard_router",
    "gamification_config_panel_router",
    "gamification_user_profile_router",
    "gamification_user_missions_router",
    "gamification_user_rewards_router",
    "gamification_user_leaderboard_router",
    "gamification_user_reactions_router",
    "gamification_user_daily_gift_router",
]
