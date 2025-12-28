"""
Handlers de narrativa para usuarios.

Exporta los routers de interacción narrativa del usuario.
"""
from bot.narrative.handlers.user.story import story_router
from bot.narrative.handlers.user.journal import journal_router
from bot.narrative.handlers.user.challenge import challenge_router
from bot.middlewares import DatabaseMiddleware

# Aplicar middleware de database a todos los routers
for router in (story_router, journal_router, challenge_router):
    router.message.middleware(DatabaseMiddleware())
    router.callback_query.middleware(DatabaseMiddleware())

__all__ = ["story_router", "journal_router", "challenge_router"]
