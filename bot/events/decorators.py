"""
Event Decorators - Decoradores de conveniencia para eventos.

Provee sintaxis más limpia para suscribirse a eventos.
"""
from typing import Callable, Type

from bot.events.base import Event
from bot.events.bus import event_bus


def subscribe(event_type: Type[Event]):
    """
    Decorador para suscribirse a un evento.

    Sintaxis limpia para registrar handlers.

    Args:
        event_type: Tipo de evento a escuchar

    Examples:
        >>> from bot.events.decorators import subscribe
        >>> from bot.events.types import UserJoinedVIPEvent
        >>>
        >>> @subscribe(UserJoinedVIPEvent)
        >>> async def handle_vip_join(event):
        ...     print(f"User {event.user_id} joined VIP!")
    """

    def decorator(func: Callable) -> Callable:
        event_bus.subscribe(event_type, func)
        return func

    return decorator


def subscribe_all(func: Callable) -> Callable:
    """
    Decorador para suscribirse a TODOS los eventos.

    Args:
        func: Handler que recibirá todos los eventos

    Examples:
        >>> @subscribe_all
        >>> async def log_all_events(event):
        ...     logger.info(f"Event: {event.event_type}")
    """
    event_bus.subscribe_all(func)
    return func
