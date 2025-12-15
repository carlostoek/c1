"""
Tests for Event Bus System - B1 Feature.

Validación del sistema de eventos pub/sub completamente desacoplado.
"""
import asyncio

import pytest

from bot.events import (
    Event,
    EventBus,
    UserJoinedVIPEvent,
    TokenGeneratedEvent,
    UserRequestedFreeChannelEvent,
    UserJoinedFreeChannelEvent,
    UserVIPExpiredEvent,
    subscribe,
)


@pytest.fixture
def event_bus_instance():
    """Obtiene instancia de EventBus y la limpia para cada test."""
    # Reset antes de cada test
    EventBus.reset_instance()
    bus = EventBus.get_instance()
    yield bus
    # Limpiar después de cada test
    bus.clear_subscribers()
    EventBus.reset_instance()


@pytest.mark.asyncio
async def test_event_bus_singleton(event_bus_instance):
    """
    Test: EventBus es singleton.

    Verificar que obtenemos la misma instancia siempre.
    """
    bus1 = EventBus.get_instance()
    bus2 = EventBus.get_instance()

    assert bus1 is bus2
    print("✅ EventBus es singleton correctamente")


@pytest.mark.asyncio
async def test_event_bus_publish_subscribe(event_bus_instance):
    """
    Test: Publicar y suscribirse a eventos.

    1. Suscribir un handler a UserJoinedVIPEvent
    2. Publicar un evento
    3. Verificar que el handler recibió el evento
    """
    bus = event_bus_instance
    received_events = []

    # Suscribir handler
    @bus.subscribe(UserJoinedVIPEvent)
    async def on_vip_join(event):
        received_events.append(event)

    # Publicar evento
    event = UserJoinedVIPEvent(
        user_id=123,
        plan_name="Mensual",
        duration_days=30,
        token_id=1
    )
    bus.publish(event)

    # Esperar procesamiento asíncrono
    await asyncio.sleep(0.1)

    # Verificaciones
    assert len(received_events) == 1
    assert received_events[0].user_id == 123
    assert received_events[0].plan_name == "Mensual"
    assert received_events[0].duration_days == 30
    assert received_events[0].token_id == 1

    print("✅ Pub/Sub funciona correctamente")


@pytest.mark.asyncio
async def test_multiple_subscribers_same_event(event_bus_instance):
    """
    Test: Múltiples suscriptores reciben el mismo evento.

    1. Suscribir 3 handlers al mismo tipo de evento
    2. Publicar un evento
    3. Verificar que todos los handlers lo recibieron
    """
    bus = event_bus_instance
    results = {"handler1": [], "handler2": [], "handler3": []}

    @bus.subscribe(TokenGeneratedEvent)
    async def handler1(event):
        results["handler1"].append(event)

    @bus.subscribe(TokenGeneratedEvent)
    async def handler2(event):
        results["handler2"].append(event)

    @bus.subscribe(TokenGeneratedEvent)
    async def handler3(event):
        results["handler3"].append(event)

    # Publicar evento
    event = TokenGeneratedEvent(
        admin_id=999,
        token_id=5,
        token_string="ABC123",
        duration_hours=24
    )
    bus.publish(event)

    # Esperar procesamiento
    await asyncio.sleep(0.1)

    # Verificar que todos recibieron
    assert len(results["handler1"]) == 1
    assert len(results["handler2"]) == 1
    assert len(results["handler3"]) == 1
    assert results["handler1"][0].token_string == "ABC123"

    print("✅ Múltiples suscriptores funcionan correctamente")


@pytest.mark.asyncio
async def test_event_types_separation(event_bus_instance):
    """
    Test: Eventos de tipos diferentes no se interfieren.

    1. Suscribir a UserJoinedVIPEvent
    2. Publicar TokenGeneratedEvent
    3. Verificar que NO se recibió nada (eventos separados)
    4. Publicar UserJoinedVIPEvent
    5. Verificar que SÍ se recibió
    """
    bus = event_bus_instance
    vip_events = []
    token_events = []

    @bus.subscribe(UserJoinedVIPEvent)
    async def on_vip(event):
        vip_events.append(event)

    @bus.subscribe(TokenGeneratedEvent)
    async def on_token(event):
        token_events.append(event)

    # Publicar TokenGeneratedEvent
    bus.publish(TokenGeneratedEvent(admin_id=1, token_id=1))
    await asyncio.sleep(0.05)

    # No debe recibirse en vip_events
    assert len(vip_events) == 0
    assert len(token_events) == 1

    # Publicar UserJoinedVIPEvent
    bus.publish(UserJoinedVIPEvent(user_id=100))
    await asyncio.sleep(0.05)

    # Ahora debe recibirse en vip_events
    assert len(vip_events) == 1
    assert len(token_events) == 1

    print("✅ Separación de tipos de eventos funciona correctamente")


@pytest.mark.asyncio
async def test_subscribe_all_decorator(event_bus_instance):
    """
    Test: @subscribe_all recibe todos los eventos.

    1. Suscribir a todos los eventos
    2. Publicar eventos de diferentes tipos
    3. Verificar que se recibieron todos
    """
    bus = event_bus_instance
    all_events = []

    @bus.subscribe_all
    async def global_listener(event):
        all_events.append(event)

    # Publicar diferentes eventos
    bus.publish(UserJoinedVIPEvent(user_id=1))
    bus.publish(TokenGeneratedEvent(admin_id=2))
    bus.publish(UserRequestedFreeChannelEvent(user_id=3))

    await asyncio.sleep(0.1)

    # Verificar que recibió todos
    assert len(all_events) == 3
    assert isinstance(all_events[0], UserJoinedVIPEvent)
    assert isinstance(all_events[1], TokenGeneratedEvent)
    assert isinstance(all_events[2], UserRequestedFreeChannelEvent)

    print("✅ subscribe_all funciona correctamente")


@pytest.mark.asyncio
async def test_event_properties(event_bus_instance):
    """
    Test: Propiedades automáticas de eventos.

    Verificar que event_id y timestamp se generan automáticamente.
    """
    event = UserJoinedVIPEvent(user_id=123, plan_name="Pro")

    # Verificar event_id existe y es único
    assert event.event_id is not None
    assert len(event.event_id) > 0

    # Crear otro evento
    event2 = UserJoinedVIPEvent(user_id=456)
    assert event.event_id != event2.event_id

    # Verificar timestamp existe
    assert event.timestamp is not None

    # Verificar event_type
    assert event.event_type == "UserJoinedVIPEvent"
    assert event2.event_type == "UserJoinedVIPEvent"

    print("✅ Propiedades de eventos funcionan correctamente")


@pytest.mark.asyncio
async def test_error_handling_in_handler(event_bus_instance):
    """
    Test: Error en un handler no afecta a otros handlers.

    1. Suscribir handler que lanza excepción
    2. Suscribir handler normal
    3. Publicar evento
    4. Verificar que el handler normal recibió, y no hubo crash
    """
    bus = event_bus_instance
    received_events = []

    @bus.subscribe(UserJoinedVIPEvent)
    async def failing_handler(event):
        raise RuntimeError("Handler intencional fallido")

    @bus.subscribe(UserJoinedVIPEvent)
    async def normal_handler(event):
        received_events.append(event)

    # Publicar evento (no debe crashear)
    bus.publish(UserJoinedVIPEvent(user_id=100))
    await asyncio.sleep(0.1)

    # El handler normal debe haber recibido a pesar del error
    assert len(received_events) == 1
    assert received_events[0].user_id == 100

    print("✅ Error handling funciona correctamente (handlers aislados)")


@pytest.mark.asyncio
async def test_get_subscribers_count(event_bus_instance):
    """
    Test: Contar suscriptores.

    Verificar que get_subscribers_count() retorna el conteo correcto.
    """
    bus = event_bus_instance

    # Inicialmente sin suscriptores
    assert bus.get_subscribers_count() == 0

    # Suscribir a VIP
    @bus.subscribe(UserJoinedVIPEvent)
    async def h1(e):
        pass

    assert bus.get_subscribers_count(UserJoinedVIPEvent) == 1
    assert bus.get_subscribers_count() == 1

    # Suscribir otro a VIP
    @bus.subscribe(UserJoinedVIPEvent)
    async def h2(e):
        pass

    assert bus.get_subscribers_count(UserJoinedVIPEvent) == 2
    assert bus.get_subscribers_count() == 2

    # Suscribir a Token
    @bus.subscribe(TokenGeneratedEvent)
    async def h3(e):
        pass

    assert bus.get_subscribers_count(TokenGeneratedEvent) == 1
    assert bus.get_subscribers_count() == 3

    print("✅ Conteo de suscriptores funciona correctamente")


@pytest.mark.asyncio
async def test_clear_subscribers(event_bus_instance):
    """
    Test: Limpiar suscriptores.

    Verificar que clear_subscribers() funciona correctamente.
    """
    bus = event_bus_instance

    # Suscribir
    @bus.subscribe(UserJoinedVIPEvent)
    async def h1(e):
        pass

    @bus.subscribe(TokenGeneratedEvent)
    async def h2(e):
        pass

    assert bus.get_subscribers_count() == 2

    # Limpiar tipo específico
    bus.clear_subscribers(UserJoinedVIPEvent)
    assert bus.get_subscribers_count(UserJoinedVIPEvent) == 0
    assert bus.get_subscribers_count() == 1

    # Limpiar todos
    bus.clear_subscribers()
    assert bus.get_subscribers_count() == 0

    print("✅ Limpieza de suscriptores funciona correctamente")


@pytest.mark.asyncio
async def test_event_with_metadata(event_bus_instance):
    """
    Test: Eventos con metadata personalizada.

    Verificar que se pueden agregar campos extra en metadata.
    """
    bus = event_bus_instance
    received = []

    @bus.subscribe(UserVIPExpiredEvent)
    async def handler(event):
        received.append(event)

    # Crear evento con metadata
    event = UserVIPExpiredEvent(
        user_id=123,
        subscription_id=5,
        days_active=30,
        metadata={"reason": "Test", "notification_sent": True}
    )

    bus.publish(event)
    await asyncio.sleep(0.05)

    assert len(received) == 1
    assert received[0].metadata["reason"] == "Test"
    assert received[0].metadata["notification_sent"] is True

    print("✅ Metadata en eventos funciona correctamente")


@pytest.mark.asyncio
async def test_decorator_syntax(event_bus_instance):
    """
    Test: Sintaxis de decorador para subscribe.

    Verificar que @subscribe funciona como decorador con instancia.
    """
    bus = event_bus_instance
    received = []

    # Usar método subscribe como decorador
    @bus.subscribe(UserJoinedVIPEvent)
    async def on_vip_event(event):
        received.append(event)

    bus.publish(UserJoinedVIPEvent(user_id=777))
    await asyncio.sleep(0.05)

    assert len(received) == 1
    assert received[0].user_id == 777

    print("✅ Sintaxis de decorador funciona correctamente")


if __name__ == "__main__":
    # Ejecutar tests
    pytest.main([__file__, "-v"])
