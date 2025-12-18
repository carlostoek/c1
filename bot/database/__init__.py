"""
Database module - Models, engine y sesiones.
"""
from bot.database.base import Base
from bot.database.models import (
    BotConfig,
    InvitationToken,
    VIPSubscriber,
    FreeChannelRequest,
    ActionConfig,
    LevelConfig,
    BadgeConfig,
    RewardConfig,
    MissionConfig,
)
from bot.database.engine import (
    init_db,
    close_db,
    get_session,
    get_engine,
    get_session_factory
)

__all__ = [
    # Models
    "Base",
    "BotConfig",
    "InvitationToken",
    "VIPSubscriber",
    "FreeChannelRequest",

    # Gamification Config Models
    "ActionConfig",
    "LevelConfig",
    "BadgeConfig",
    "RewardConfig",
    "MissionConfig",

    # Engine & Sessions
    "init_db",
    "close_db",
    "get_session",
    "get_engine",
    "get_session_factory",
]
