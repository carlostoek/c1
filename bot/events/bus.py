"""
Event Bus - Sistema central de eventos pub/sub.

Singleton que maneja la publicación y suscripción de eventos
de manera asíncrona y desacoplada.
"""
import asyncio
import logging
from collections import defaultdict
from typing import Callable, Dict, List, Type

from bot.events.base import Event

logger = logging.getLogger(__name__)


class EventBus:
    """
    Event Bus singleton - Sistema de publicación/suscripción de eventos.

    Permite que módulos publiquen eventos sin conocer a los suscriptores,
    y que módulos se suscriban a eventos sin modificar el código fuente.

    Attributes:
        _instance: Instancia singleton
        _subscribers: Dict de suscriptores por tipo de evento
        _global_subscribers: Listeners que reciben todos los eventos

    Examples:
        >>> bus = EventBus.get_instance()
        >>>
        >>> # Suscribirse a evento
        >>> @bus.subscribe(UserJoinedVIPEvent)
        >>> async def on_user_joined_vip(event):
        ...     print(f"User {event.user_id} joined VIP!")
        >>>
        >>> # Publicar evento
        >>> await bus.publish(UserJoinedVIPEvent(user_id=123, plan_name="Mensual"))
    """

    _instance: "EventBus" = None

    def __init__(self):
        """Inicializa el Event Bus."""
        if EventBus._instance is not None:
            raise RuntimeError("EventBus es singleton. Usa EventBus.get_instance()")

        # Suscriptores por tipo de evento
        self._subscribers: Dict[Type[Event], List[Callable]] = defaultdict(list)

        # Suscriptores globales (reciben todos los eventos)
        self._global_subscribers: List[Callable] = []

        # Lock para operaciones thread-safe
        self._lock = asyncio.Lock()

        logger.info("🚌 EventBus inicializado")

    @classmethod
    def get_instance(cls) -> "EventBus":
        """
        Obtiene la instancia singleton del EventBus.

        Returns:
            Instancia única de EventBus
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """Resetea la instancia (útil para testing)."""
        cls._instance = None

    def subscribe(self, event_type: Type[Event], handler: Callable = None):
        """
        Suscribe un handler a un tipo de evento.

        Puede usarse como decorador o llamarse directamente.

        Args:
            event_type: Tipo de evento a escuchar
            handler: Función async que maneja el evento (opcional si es decorador)

        Returns:
            Handler (para uso como decorador) o None

        Examples:
            >>> # Como decorador
            >>> @bus.subscribe(UserJoinedVIPEvent)
            >>> async def on_vip(event):
            ...     pass
            >>>
            >>> # Como llamada directa
            >>> bus.subscribe(UserJoinedVIPEvent, my_handler)
        """

        def decorator(func: Callable) -> Callable:
            self._subscribers[event_type].append(func)
            logger.debug(f"📝 Suscrito: {func.__name__} → {event_type.__name__}")
            return func

        # Si se llama como decorador (@subscribe)
        if handler is None:
            return decorator

        # Si se llama directamente (subscribe(event, handler))
        return decorator(handler)

    def subscribe_all(self, handler: Callable):
        """
        Suscribe un handler a TODOS los eventos (global listener).

        Args:
            handler: Función async que maneja eventos

        Examples:
            >>> @bus.subscribe_all
            >>> async def log_all_events(event):
            ...     print(f"Event: {event.event_type}")
        """
        self._global_subscribers.append(handler)
        logger.debug(f"📝 Suscrito global: {handler.__name__}")
        return handler

    async def publish(self, event: Event):
        """
        Publica un evento a todos los suscriptores.

        Args:
            event: Instancia del evento a publicar

        Examples:
            >>> await bus.publish(UserJoinedVIPEvent(
            ...     user_id=123,
            ...     plan_name="Mensual"
            ... ))
        """
        event_type = type(event)

        logger.info(
            f"📢 Evento publicado: {event.event_type} | "
            f"ID: {event.event_id} | User: {event.user_id}"
        )

        # Obtener suscriptores del tipo específico
        specific_subscribers = self._subscribers.get(event_type, [])

        # Combinar suscriptores específicos + globales
        all_subscribers = specific_subscribers + self._global_subscribers

        if not all_subscribers:
            logger.debug(f"⚠️ No hay suscriptores para {event.event_type}")
            return

        # Ejecutar todos los handlers en paralelo
        tasks = []
        for handler in all_subscribers:
            task = asyncio.create_task(self._safe_execute_handler(handler, event))
            tasks.append(task)

        # Esperar a que todos terminen
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log de errores
        errors = [r for r in results if isinstance(r, Exception)]
        if errors:
            logger.error(
                f"❌ {len(errors)} errores ejecutando handlers para {event.event_type}"
            )

    async def _safe_execute_handler(self, handler: Callable, event: Event):
        """
        Ejecuta un handler de manera segura (con try/catch).

        Args:
            handler: Handler a ejecutar
            event: Evento a pasar
        """
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)

            logger.debug(f"✅ Handler ejecutado: {handler.__name__}")

        except Exception as e:
            logger.error(
                f"❌ Error en handler {handler.__name__} "
                f"para evento {event.event_type}: {e}",
                exc_info=True,
            )

    def get_subscribers_count(self, event_type: Type[Event] = None) -> int:
        """
        Obtiene cantidad de suscriptores.

        Args:
            event_type: Tipo de evento (None = todos)

        Returns:
            Cantidad de suscriptores
        """
        if event_type is None:
            # Total de suscriptores
            total = sum(len(subs) for subs in self._subscribers.values())
            total += len(self._global_subscribers)
            return total
        else:
            return len(self._subscribers.get(event_type, []))

    def clear_subscribers(self, event_type: Type[Event] = None):
        """
        Limpia suscriptores (útil para testing).

        Args:
            event_type: Tipo a limpiar (None = todos)
        """
        if event_type is None:
            self._subscribers.clear()
            self._global_subscribers.clear()
            logger.debug("🧹 Todos los suscriptores limpiados")
        else:
            self._subscribers[event_type].clear()
            logger.debug(f"🧹 Suscriptores de {event_type.__name__} limpiados")


# Instancia global (alias conveniente)
event_bus = EventBus.get_instance()
