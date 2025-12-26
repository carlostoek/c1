"""
Admin handlers module.
"""
from bot.handlers.admin.main import admin_router
from bot.handlers.admin import vip, free, broadcast, management, stats, dashboard, pricing

__all__ = ["admin_router", "vip", "free", "broadcast", "management", "stats", "dashboard", "pricing"]
