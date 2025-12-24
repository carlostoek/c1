"""Handlers de Telegram para gamificación."""

from bot.gamification.handlers.admin import main, mission_wizard, reward_wizard

# Exportar routers
gamification_admin_router = main.router
gamification_mission_wizard_router = mission_wizard.router
gamification_reward_wizard_router = reward_wizard.router

__all__ = [
    "gamification_admin_router",
    "gamification_mission_wizard_router",
    "gamification_reward_wizard_router",
]
