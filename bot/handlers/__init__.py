"""
Handlers module - Registro de todos los handlers del bot.

Estructura:
- admin/: Handlers de administración
- user/: Handlers de usuarios
"""
import logging
from aiogram import Dispatcher

from bot.handlers.admin import admin_router
from bot.handlers.user import user_router

logger = logging.getLogger(__name__)


def register_all_handlers(dispatcher: Dispatcher) -> None:
    """
    Registra todos los routers y handlers en el dispatcher.

    Args:
        dispatcher: Instancia del Dispatcher
    """
    logger.info("Registrando handlers...")

    # Registrar routers
    dispatcher.include_router(admin_router)
    dispatcher.include_router(user_router)

    logger.info("Handlers registrados correctamente")


__all__ = ["register_all_handlers", "admin_router", "user_router"]
