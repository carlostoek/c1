# Notification System - Templates y RewardBatch

## Descripción General

El sistema de notificaciones proporciona una capa centralizada para enviar mensajes personalizados a los usuarios del bot. Incluye templates HTML predefinidos y un sistema de RewardBatch para agrupar múltiples recompensas en una sola notificación, evitando el spam de mensajes.

## Componentes del Sistema

### NotificationService
Servicio centralizado que maneja todo el envío de notificaciones con:
- Templates reutilizables
- Logging automático
- Consistencia visual
- Sistema de RewardBatch

### NotificationTemplates
Repositorio de templates HTML predefinidos con placeholders dinámicos para diferentes tipos de notificaciones.

### RewardBatch
Sistema para agrupar múltiples recompensas (Besitos, badges, ranks) en una sola notificación unificada.

### NotificationType
Enum que define todos los tipos posibles de notificaciones en el sistema.

## Tipos de Notificaciones

### Bienvenida y Onboarding
- `WELCOME`: Mensaje de bienvenida para nuevos usuarios

### Recompensas
- `REWARD`: Notificación general de recompensa
- `POINTS_EARNED`: Notificación de Besitos ganados
- `BADGE_UNLOCKED`: Notificación de badge desbloqueado
- `RANK_UP`: Notificación de cambio de rango

### VIP
- `VIP_ACTIVATED`: Activación de suscripción VIP
- `VIP_EXPIRING_SOON`: Aviso de expiración próxima
- `VIP_EXPIRED`: Notificación de expiración

### Daily Rewards
- `DAILY_LOGIN`: Regalo diario reclamado
- `STREAK_MILESTONE`: Nuevo récord de racha

### Referrals
- `REFERRAL_SUCCESS`: Referido exitoso

### Errores y Avisos
- `ERROR`: Mensajes de error
- `WARNING`: Mensajes de advertencia
- `INFO`: Mensajes informativos

## Templates Disponibles

### WELCOME_DEFAULT
```html
👋 <b>¡Bienvenido/a {first_name}!</b>

{role_emoji} Tu rol actual: <b>{role_name}</b>

Este bot te da acceso a canales exclusivos y recompensas por participar.

<b>💋 Sistema de Besitos:</b>
Gana Besitos (puntos) por:
• Ingresar al canal Free
• Reaccionar a mensajes
• Login diario
• Referir amigos

<b>Usa /help para más información.</b>
```

### BESITOS_EARNED
```html
💋 <b>¡Ganaste Besitos!</b>

<b>+{amount} Besitos</b>

Razón: {reason}

Total acumulado: {total_besitos} 💋
```

### BADGE_UNLOCKED
```html
🏆 <b>¡Nueva Insignia Desbloqueada!</b>

{badge_icon} <b>{badge_name}</b>

{badge_description}

<i>Insignias desbloqueadas: {total_badges}</i>
```

### RANK_UP
```html
⭐ <b>¡Subiste de Rango!</b>

{old_rank} → {new_rank}

Total de Besitos: {total_besitos} 💋

¡Sigue participando para seguir subiendo!
```

### DAILY_LOGIN
```html
🎁 <b>¡Regalo Diario Reclamado!</b>

<b>+{besitos} Besitos 💋</b>

Días consecutivos: {streak_days} 🔥

{streak_bonus}

¡Vuelve mañana para mantener tu racha!
```

## RewardBatch System

El sistema de RewardBatch permite agrupar múltiples recompensas en una sola notificación:

```python
from bot.notifications.batch import RewardBatch

# Crear un batch
batch = RewardBatch(user_id=123, action="Reaccionaste a un mensaje")

# Agregar diferentes tipos de recompensas
batch.add_besitos(50, "Reacción")
batch.add_badge("🔥 Hot Streak", "10 días consecutivos")
batch.add_rank_up("Novato", "Bronce")

# Enviar notificación unificada
await container.notifications.send_reward_batch(batch)
```

### Tipos de Recompensas en Batch
- **Besitos**: Puntos ganados con cantidad y razón
- **Badges**: Insignias desbloqueadas con nombre y descripción
- **Ranks**: Cambios de rango con antiguo y nuevo rango
- **Custom**: Recompensas personalizadas con icono y descripción

## Uso del Servicio de Notificaciones

### Enviar Notificación Simple
```python
await container.notifications.send(
    user_id=123,
    notification_type=NotificationType.POINTS_EARNED,
    context={
        "amount": 50,
        "reason": "Primera reacción",
        "total_besitos": 150
    }
)
```

### Enviar Notificación de Bienvenida
```python
await container.notifications.send_welcome(
    user_id=123,
    first_name="Juan",
    role_name="Free",
    role_emoji="🆓"
)
```

### Enviar Notificación de Besitos
```python
await container.notifications.send_besitos(
    user_id=123,
    amount=50,
    reason="Reacción a mensaje",
    total_besitos=150
)
```

### Enviar Batch de Recompensas
```python
batch = RewardBatch(user_id=123, action="¡Lograste algo importante!")

batch.add_besitos(50, "Reacción")
batch.add_badge("🏆 Reactor Pro", "50 reacciones totales")
batch.add_rank_up("Novato", "Bronce")

await container.notifications.send_reward_batch(batch)
```

## Templates Personalizados

El sistema soporta templates personalizados almacenados en base de datos:

```python
# Templates personalizados se almacenan en NotificationTemplate
# con tipo único y contenido HTML
```

### Prioridad de Templates
1. Templates personalizados de base de datos (si existen y están activos)
2. Templates por defecto del sistema

## Integración con Gamificación

El sistema de notificaciones está estrechamente integrado con la gamificación:

```python
# En listeners de gamificación
@subscribe(PointsAwardedEvent)
async def on_points_awarded(event: PointsAwardedEvent):
    batch = await container.notifications.create_reward_batch(
        user_id=event.user_id,
        action="¡Ganaste puntos!"
    )
    batch.add_besitos(event.points, event.reason)
    await container.notifications.send_reward_batch(batch)
```

## Formato HTML

Todos los templates usan formato HTML con:
- **Negritas**: `<b>texto</b>`
- **Íconos**: Emojis como 💋, 🏆, ⭐
- **Listas**: Usando bullets
- **Formato estructurado**: Para mejor legibilidad

## Variables de Contexto

Cada template define variables específicas que deben ser proporcionadas:

| Template | Variables Requeridas |
|----------|---------------------|
| WELCOME_DEFAULT | first_name, role_name, role_emoji |
| BESITOS_EARNED | amount, reason, total_besitos |
| BADGE_UNLOCKED | badge_icon, badge_name, badge_description, total_badges |
| RANK_UP | old_rank, new_rank, total_besitos |
| DAILY_LOGIN | besitos, streak_days, streak_bonus |

## Error Handling

- Validación de variables requeridas en templates
- Logging detallado de errores
- Fallback a templates por defecto si hay problemas
- Manejo seguro de format strings

## Performance

- Templates cacheados en memoria para mejor performance
- Procesamiento eficiente de variables
- Uso de format strings optimizados
- Logging asincrónico

## Ejemplos de Uso

### Enviar Notificación Compleja
```python
# Combinar múltiples recompensas
async def handle_daily_login(user_id):
    # Otorgar recompensas
    besitos, streak, is_record = await container.gamification.claim_daily_login(user_id)
    
    # Verificar badges
    new_badges = await container.gamification.check_and_unlock_badges(user_id)
    
    # Crear batch
    batch = await container.notifications.create_reward_batch(
        user_id=user_id,
        action="¡Reclamaste tu regalo diario!"
    )
    
    batch.add_besitos(besitos, f"Regalo diario (racha de {streak} días)")
    
    if is_record:
        batch.add_custom("🔥", "¡Nuevo récord de racha!", f"{streak} días consecutivos")
    
    for badge_id in new_badges:
        badge_def = container.gamification.config.get_badge_definition(badge_id)
        batch.add_badge(f"{badge_def.icon} {badge_def.name}", badge_def.description)
    
    await container.notifications.send_reward_batch(batch)
```

### Personalización de Templates
```python
# Templates pueden ser personalizados por administradores
# a través de la interfaz de administración
```

## Best Practices

- Usar RewardBatch para múltiples recompensas en lugar de notificaciones separadas
- Proporcionar siempre contexto completo para evitar errores de renderizado
- Utilizar emojis y formato HTML para mejor experiencia de usuario
- Implementar logging para seguimiento de notificaciones enviadas
- Validar que los templates tengan todas las variables requeridas