"""
Admin Narrative Handlers - Gestión de contenido narrativo.

Incluye:
- main.py: Menú principal de narrativa para admin
- stats.py: Estadísticas de uso de narrativa
"""

from aiogram import Router

from bot.middlewares import DatabaseMiddleware, AdminAuthMiddleware

# Router para handlers de narrativa de admin
narrative_admin_router = Router(name="admin_narrative")

# Aplicar middlewares en orden
narrative_admin_router.message.middleware(DatabaseMiddleware())
narrative_admin_router.callback_query.middleware(DatabaseMiddleware())
narrative_admin_router.message.middleware(AdminAuthMiddleware())
narrative_admin_router.callback_query.middleware(AdminAuthMiddleware())

# Importar handlers (esto registra los handlers en el router)
from bot.handlers.admin.narrative import main, stats  # noqa: E402, F401

__all__ = ["narrative_admin_router"]
