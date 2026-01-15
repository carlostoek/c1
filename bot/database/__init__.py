"""
Database module - Models, engine y sesiones.
"""
from bot.database.base import Base
from bot.database.models import (
    BotConfig,
    User,
    SubscriptionPlan,
    InvitationToken,
    VIPSubscriber,
    FreeChannelRequest
)
from bot.database.gamification_models import (
    GamificationConfig,
    Publication,
    UserReaction,
    UserPoints,
    PointsTransaction,
    Badge,
    UserBadge,
    UserLevel,
    MediaSet,
    MediaSetItem,
    ShopItem,
    ShopPurchase,
    Mission,
    UserMissionProgress
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
    "User",
    "SubscriptionPlan",
    "InvitationToken",
    "VIPSubscriber",
    "FreeChannelRequest",

    # Gamification Models
    "GamificationConfig",
    "Publication",
    "UserReaction",
    "UserPoints",
    "PointsTransaction",
    "Badge",
    "UserBadge",
    "UserLevel",
    "MediaSet",
    "MediaSetItem",
    "ShopItem",
    "ShopPurchase",
    "Mission",
    "UserMissionProgress",

    # Engine & Sessions
    "init_db",
    "close_db",
    "get_session",
    "get_engine",
    "get_session_factory",
]
