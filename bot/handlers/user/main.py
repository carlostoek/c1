"""
User Router - Router principal para handlers de usuario.

Agrupa todos los handlers relacionados con interacciones de usuarios normales.
"""
from aiogram import Router
from bot.middlewares.database import DatabaseMiddleware

# Router principal para handlers de usuario
user_router = Router(name="user")

# Middlewares
# DatabaseMiddleware: Inyecta sesión de BD en data["session"]
user_router.message.middleware(DatabaseMiddleware())
user_router.callback_query.middleware(DatabaseMiddleware())

# NOTA: No usamos AdminAuthMiddleware aquí
# Los usuarios normales deben poder acceder a estos handlers

# Importar handlers para registrarlos en el router
# Esto es necesario para que los decorators @router.funcionen
from bot.handlers.user import (
    start,
    reactions,
    profile,
    shop
    # vip_flow,
    # free_flow
)

__all__ = ["user_router"]
