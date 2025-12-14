"""
Events Module - Sistema de eventos del bot.

Exports:
    - EventBus, event_bus (singleton)
    - Event (base class)
    - Event types (todos los eventos)
    - Decoradores (@subscribe, @subscribe_all)
"""

from bot.events.base import Event
from bot.events.bus import EventBus, event_bus
from bot.events.decorators import subscribe, subscribe_all

# Importar todos los event types para fácil acceso
from bot.events.types import (
    # Broadcast events
    MessageBroadcastedEvent,
    # Free channel events
    UserJoinedFreeChannelEvent,
    UserRequestedFreeChannelEvent,
    # Gamification events
    BadgeUnlockedEvent,
    PointsAwardedEvent,
    RankUpEvent,
    # Interaction events
    DailyLoginEvent,
    MessageReactedEvent,
    UserReferredEvent,
    # User events
    UserRoleChangedEvent,
    UserStartedBotEvent,
    # VIP events
    TokenGeneratedEvent,
    UserJoinedVIPEvent,
    UserVIPExpiredEvent,
)

__all__ = [
    # Core
    "EventBus",
    "event_bus",
    "Event",
    # Decorators
    "subscribe",
    "subscribe_all",
    # User events
    "UserStartedBotEvent",
    "UserRoleChangedEvent",
    # VIP events
    "UserJoinedVIPEvent",
    "UserVIPExpiredEvent",
    "TokenGeneratedEvent",
    # Free channel events
    "UserRequestedFreeChannelEvent",
    "UserJoinedFreeChannelEvent",
    # Interaction events
    "MessageReactedEvent",
    "DailyLoginEvent",
    "UserReferredEvent",
    # Gamification events
    "PointsAwardedEvent",
    "BadgeUnlockedEvent",
    "RankUpEvent",
    # Broadcast events
    "MessageBroadcastedEvent",
]
