"""
Admin handlers module.
"""
from bot.handlers.admin.main import admin_router
from bot.handlers.admin import vip, free, broadcast, reactions, management, stats, dashboard, pricing, configuration

__all__ = ["admin_router", "vip", "free", "broadcast", "reactions", "management", "stats", "dashboard", "pricing", "configuration"]
