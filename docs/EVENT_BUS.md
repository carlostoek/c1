# Event Bus (Pub/Sub) - Sistema de Eventos Desacoplado

## Descripción General

El Event Bus es un sistema centralizado de publicación/suscripción (pub/sub) que permite la comunicación desacoplada entre diferentes componentes del bot. Utiliza un patrón singleton para garantizar una única instancia global que maneja eventos de manera asíncrona y no bloqueante.

## Arquitectura

### Componentes Principales

- **EventBus**: Clase singleton que gestiona la publicación y suscripción de eventos
- **event_bus**: Instancia global conveniente para uso en cualquier parte del sistema
- **Event**: Clase base para todos los eventos del sistema
- **Event Types**: Definiciones específicas de eventos con atributos relevantes

### Patrones de Diseño

- **Singleton**: Garantiza una única instancia del EventBus
- **Pub/Sub**: Publicación y suscripción desacoplada de eventos
- **Async/Await**: Procesamiento no bloqueante de eventos

## Implementación

### EventBus Singleton

```python
from bot.events import event_bus

# Publicar un evento
event_bus.publish(UserJoinedVIPEvent(user_id=123, plan_name="Mensual"))

# Suscribirse como decorador
@event_bus.subscribe(UserJoinedVIPEvent)
async def on_user_joined_vip(event):
    print(f"Usuario {event.user_id} se unió al VIP!")

# Suscribirse directamente
def my_handler(event):
    pass

event_bus.subscribe(UserJoinedVIPEvent, my_handler)
```

### Tipos de Eventos Disponibles

#### Eventos de Usuario
- `UserStartedBotEvent`: Usuario ejecuta /start por primera vez
- `UserRoleChangedEvent`: El rol de un usuario cambia

#### Eventos VIP
- `UserJoinedVIPEvent`: Usuario activa suscripción VIP
- `UserVIPExpiredEvent`: Suscripción VIP expira
- `TokenGeneratedEvent`: Admin genera token VIP

#### Eventos Free Channel
- `UserRequestedFreeChannelEvent`: Usuario solicita acceso Free
- `UserJoinedFreeChannelEvent`: Usuario recibe acceso Free

#### Eventos de Interacción
- `MessageReactedEvent`: Usuario reacciona a mensaje
- `DailyLoginEvent`: Usuario reclama regalo diario
- `UserReferredEvent`: Usuario refiere a otro

#### Eventos de Gamificación
- `PointsAwardedEvent`: Puntos (Besitos) otorgados
- `BadgeUnlockedEvent`: Usuario desbloquea insignia
- `RankUpEvent`: Usuario sube de rango

#### Eventos de Broadcast
- `MessageBroadcastedEvent`: Mensaje enviado a canal

## Funcionalidades

### Suscripción a Eventos

```python
# Suscribirse a evento específico
@event_bus.subscribe(UserStartedBotEvent)
async def on_user_started(event):
    # Manejar evento de usuario nuevo
    pass

# Suscribirse a todos los eventos (global listener)
@event_bus.subscribe_all
async def log_all_events(event):
    print(f"Evento recibido: {event.event_type}")
```

### Publicación de Eventos

```python
# Publicar evento de forma no bloqueante
event_bus.publish(UserJoinedVIPEvent(
    user_id=123,
    plan_name="Mensual",
    duration_days=30
))
```

### Procesamiento Asincrónico

- Los eventos se procesan en segundo plano sin bloquear la ejecución
- Todos los handlers se ejecutan en paralelo de manera segura
- Manejo de errores individual para cada handler
- Logging automático de eventos y errores

## Ventajas del Sistema

1. **Desacoplamiento**: Componentes no necesitan conocerse directamente
2. **Extensibilidad**: Fácil agregar nuevos listeners sin modificar código existente
3. **Confiabilidad**: Manejo seguro de errores y logging detallado
4. **Asincronía**: Procesamiento no bloqueante de eventos
5. **Flexibilidad**: Soporte para listeners específicos y globales

## Casos de Uso

### Gamificación
- Otorgamiento automático de Besitos cuando un usuario reacciona
- Desbloqueo de badges y cambios de rango
- Recompensas por daily login y referidos

### Notificaciones
- Envío automático de notificaciones cuando ocurren eventos
- Agrupación de recompensas en batch notifications
- Templates dinámicos basados en eventos

### Estadísticas
- Actualización automática de métricas cuando ocurren eventos
- Seguimiento de actividades de usuarios

## Seguridad y Error Handling

- Ejecución segura de handlers con try/catch individual
- Logging detallado de errores sin detener el sistema
- Validación de tipos de eventos
- Protección contra fallos en cascada

## Integración con Otros Sistemas

### Con Gamificación
```python
# En listeners.py
@subscribe(MessageReactedEvent)
async def on_message_reacted(event: MessageReactedEvent):
    # Otorgar Besitos automáticamente
    async with get_session() as session:
        container = ServiceContainer(session, bot)
        await container.gamification.award_besitos(
            user_id=event.user_id,
            action="message_reacted"
        )
```

### Con Notificaciones
```python
# En listeners.py
@subscribe(BadgeUnlockedEvent)
async def on_badge_unlocked(event: BadgeUnlockedEvent):
    # Enviar notificación de badge desbloqueado
    async with get_session() as session:
        container = ServiceContainer(session, bot)
        batch = await container.notifications.create_reward_batch(
            user_id=event.user_id,
            action="¡Nueva insignia desbloqueada!"
        )
        batch.add_badge(f"🏆 {event.badge_name}", "¡Felicidades!")
        await container.notifications.send_reward_batch(batch)
```

## Testing

El sistema incluye soporte para testing con métodos de limpieza:

```python
# Limpiar suscriptores para tests
event_bus.clear_subscribers()
EventBus.reset_instance()
```

## Performance

- Uso de asyncio para procesamiento concurrente
- Locks para operaciones thread-safe
- Logging eficiente
- Gestión de memoria optimizada

## Ejemplo Completo

```python
from bot.events import event_bus, UserJoinedVIPEvent

# Definir un listener
@event_bus.subscribe(UserJoinedVIPEvent)
async def handle_vip_activation(event):
    print(f"Usuario {event.user_id} activó VIP: {event.plan_name}")
    
    # Otorgar recompensas
    async with get_session() as session:
        container = ServiceContainer(session, bot)
        
        # Otorgar Besitos
        amount, ranked_up, new_rank = await container.gamification.award_besitos(
            user_id=event.user_id,
            action="joined_vip"
        )
        
        # Enviar notificación
        batch = await container.notifications.create_reward_batch(
            user_id=event.user_id,
            action=f"¡Activaste tu suscripción VIP! ({event.plan_name})"
        )
        batch.add_besitos(amount, "Bono VIP")
        await container.notifications.send_reward_batch(batch)

# Publicar evento
event_bus.publish(UserJoinedVIPEvent(
    user_id=123456,
    plan_name="Mensual",
    duration_days=30
))
```