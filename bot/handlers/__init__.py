"""
Handlers module - Registro de todos los handlers del bot.

Estructura:
- admin/: Handlers de administración
- user/: Handlers de usuarios
"""
import logging
from aiogram import Dispatcher

from bot.handlers.admin import admin_router
from bot.handlers.admin.narrative import narrative_admin_router
from bot.handlers.user import user_router
from bot.handlers.user.free_join_request import free_join_router
from bot.handlers.user.narrative import narrative_router
from bot.narrative.handlers import story_router, journal_router, challenge_router
from bot.gamification.handlers import (
    gamification_admin_router,
    gamification_mission_wizard_router,
    gamification_reward_wizard_router,
    gamification_level_wizard_router,
    gamification_config_router,
    gamification_level_config_router,
    gamification_transaction_history_router,
    gamification_mission_config_router,
    gamification_reward_config_router,
    gamification_reaction_config_router,
    gamification_daily_gift_config_router,
    gamification_unified_wizard_router,
    gamification_config_panel_router,
    gamification_user_profile_router,
    gamification_user_missions_router,
    gamification_user_rewards_router,
    gamification_user_leaderboard_router,
    gamification_user_reactions_router,
    gamification_user_daily_gift_router,
)
from bot.shop.handlers import (
    shop_admin_router,
    shop_user_router,
    backpack_router,
)

logger = logging.getLogger(__name__)


def register_all_handlers(dispatcher: Dispatcher) -> None:
    """
    Registra todos los routers y handlers en el dispatcher.

    Args:
        dispatcher: Instancia del Dispatcher
    """
    logger.info("Registrando handlers...")

    # Registrar routers principales
    dispatcher.include_router(admin_router)
    dispatcher.include_router(narrative_admin_router)
    dispatcher.include_router(user_router)
    dispatcher.include_router(free_join_router)
    dispatcher.include_router(narrative_router)

    # Registrar routers de narrativa inmersiva
    dispatcher.include_router(story_router)
    dispatcher.include_router(journal_router)
    dispatcher.include_router(challenge_router)

    # Registrar routers de gamificación (admin)
    dispatcher.include_router(gamification_admin_router)
    dispatcher.include_router(gamification_mission_wizard_router)
    dispatcher.include_router(gamification_reward_wizard_router)
    dispatcher.include_router(gamification_level_wizard_router)
    dispatcher.include_router(gamification_config_router)
    dispatcher.include_router(gamification_level_config_router)
    dispatcher.include_router(gamification_transaction_history_router)
    dispatcher.include_router(gamification_mission_config_router)
    dispatcher.include_router(gamification_reward_config_router)
    dispatcher.include_router(gamification_reaction_config_router)
    dispatcher.include_router(gamification_daily_gift_config_router)
    dispatcher.include_router(gamification_unified_wizard_router)
    dispatcher.include_router(gamification_config_panel_router)

    # Registrar routers de gamificación (user)
    dispatcher.include_router(gamification_user_profile_router)
    dispatcher.include_router(gamification_user_missions_router)
    dispatcher.include_router(gamification_user_rewards_router)
    dispatcher.include_router(gamification_user_leaderboard_router)
    dispatcher.include_router(gamification_user_reactions_router)
    dispatcher.include_router(gamification_user_daily_gift_router)

    # Registrar routers de tienda
    dispatcher.include_router(shop_admin_router)
    dispatcher.include_router(shop_user_router)
    dispatcher.include_router(backpack_router)

    logger.info("Handlers registrados correctamente")


__all__ = ["register_all_handlers", "admin_router", "user_router"]
