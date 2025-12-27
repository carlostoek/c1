"""
User Narrative Handlers - Navegación de la historia por usuarios.

Incluye:
- story.py: Navegación de fragmentos narrativos
- decisions.py: Procesamiento de decisiones del usuario
"""

from aiogram import Router

from bot.middlewares import DatabaseMiddleware

# Router para handlers de narrativa de usuario
narrative_router = Router(name="user_narrative")

# Aplicar middleware de database
narrative_router.message.middleware(DatabaseMiddleware())
narrative_router.callback_query.middleware(DatabaseMiddleware())

# Importar handlers (esto registra los handlers en el router)
from bot.handlers.user.narrative import story, decisions  # noqa: E402, F401

__all__ = ["narrative_router"]
