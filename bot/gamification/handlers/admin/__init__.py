"""
Gamification Admin handlers module.
"""
from bot.gamification.handlers.admin.main import router as admin_main_router
from bot.gamification.handlers.admin.mission_wizard import router as admin_mission_wizard_router
from bot.gamification.handlers.admin.reward_wizard import router as admin_reward_wizard_router
from bot.gamification.handlers.admin.templates import router as admin_templates_router
from bot.gamification.handlers.admin.stats import router as admin_stats_router
from bot.gamification.handlers.admin.reaction_config import router as admin_reaction_config_router
from bot.gamification.handlers.admin.level_config import router as admin_level_config_router
from bot.gamification.handlers.admin.mission_config import router as admin_mission_config_router
from bot.gamification.handlers.admin.reward_config import router as admin_reward_config_router
from bot.gamification.handlers.admin.transaction_history import router as admin_transaction_history_router

# Include all sub-routers
admin_main_router.include_router(admin_mission_wizard_router)
admin_main_router.include_router(admin_reward_wizard_router)
admin_main_router.include_router(admin_templates_router)
admin_main_router.include_router(admin_stats_router)
admin_main_router.include_router(admin_reaction_config_router)
admin_main_router.include_router(admin_level_config_router)
admin_main_router.include_router(admin_mission_config_router)
admin_main_router.include_router(admin_reward_config_router)
admin_main_router.include_router(admin_transaction_history_router)

# Export main router as 'router' to match expected interface
router = admin_main_router

__all__ = ["router", "admin_main_router", "admin_mission_wizard_router", "admin_reward_wizard_router", "admin_templates_router", "admin_stats_router", "admin_reaction_config_router", "admin_level_config_router", "admin_mission_config_router", "admin_reward_config_router", "admin_transaction_history_router"]