"""
Gamification handlers module - Registro de handlers de gamificación.

Estructura:
- user/: Handlers de usuarios para gamificación
- admin/: Handlers de administración para gamificación
- reaction_hook: Hook para eventos de reacción
"""
import logging
from aiogram import Router

from bot.gamification.handlers.user import router as user_gamification_router
from bot.gamification.handlers.admin import router as admin_gamification_router
from bot.gamification.background.reaction_hook import router as reaction_router

logger = logging.getLogger(__name__)

# Router principal que incluye todos los routers de gamificación
gamification_router = Router()

# Incluir routers hijos
gamification_router.include_router(user_gamification_router)
gamification_router.include_router(admin_gamification_router)
gamification_router.include_router(reaction_router)

logger.info("✅ Routers de gamificación registrados")

__all__ = ["gamification_router", "user_gamification_router", "admin_gamification_router", "reaction_router"]