"""
Middlewares module - Procesamiento pre/post handlers.
"""
from bot.middlewares.admin_auth import AdminAuthMiddleware
from bot.middlewares.database import DatabaseMiddleware
from bot.middlewares.typing_indicator import TypingIndicatorMiddleware
from bot.middlewares.auto_reaction import AutoReactionMiddleware

__all__ = [
    "AdminAuthMiddleware",
    "DatabaseMiddleware",
    "TypingIndicatorMiddleware",
    "AutoReactionMiddleware",
]
