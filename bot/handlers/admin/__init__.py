"""
Admin handlers module.
"""
from bot.handlers.admin.main import admin_router
from bot.handlers.admin import vip, free

__all__ = ["admin_router", "vip", "free"]
