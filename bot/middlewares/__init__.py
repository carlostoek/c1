"""
Middlewares module - Procesamiento pre/post handlers.
"""
from bot.middlewares.admin_auth import AdminAuthMiddleware
from bot.middlewares.database import DatabaseMiddleware
from bot.middlewares.gamification import GamificationMiddleware

__all__ = [
    "AdminAuthMiddleware",
    "DatabaseMiddleware",
    "GamificationMiddleware",
]
