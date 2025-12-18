# Gamification System - Besitos, Badges, Ranks, Daily Login, Reacciones y Commit

## Descripción General

El sistema de gamificación es un componente integral que motiva a los usuarios a interactuar con el bot mediante un sistema de puntos (Besitos), insignias (badges), rangos, login diario y reacciones. Utiliza el Event Bus para otorgar recompensas automáticamente cuando ocurren ciertas acciones.

## Componentes del Sistema

### GamificationService
Servicio principal que maneja:
- Otorgamiento de Besitos
- Verificación y desbloqueo de badges
- Actualización de rangos
- Sistema de login diario
- Rate limiting de reacciones

### ConfigurationService
Sistema de configuración centralizada con CRUD completo para:
- ActionConfig: Recompensas por acción
- BadgeConfig: Definiciones de badges
- LevelConfig: Rangos y requisitos
- RewardConfig: Recompensas configurables
- MissionConfig: Misiones y objetivos
- Sistema de cache con TTL configurable

### GamificationListeners
Event listeners que otorgan recompensas automáticamente cuando ocurren eventos específicos.

## Sistema de Besitos

### Descripción
Los "Besitos" son puntos que los usuarios ganan por interactuar con el bot. Representan el sistema de puntos principal de gamificación.

### Recompensas por Acción
- `user_started`: 10 Besitos (bienvenida)
- `joined_vip`: 100 Besitos (activación VIP)
- `joined_free_channel`: 25 Besitos (ingreso canal Free)
- `message_reacted`: 5 Besitos (reacción a mensaje)
- `first_reaction_of_day`: 10 Besitos (bonus primer reacción)
- `daily_login_base`: 20 Besitos (gift diario)
- `daily_login_streak_bonus`: 5 Besitos por día (racha)
- `referral_success`: 50 Besitos (referido)

### Otorgamiento de Besitos
```python
# Otorgar Besitos por acción específica
amount, ranked_up, new_rank = await container.gamification.award_besitos(
    user_id=123,
    action="message_reacted"
)

# Otorgar Besitos personalizados
amount, ranked_up, new_rank = await container.gamification.award_besitos(
    user_id=123,
    action="custom_action",
    custom_amount=100,
    custom_reason="Recompensa especial"
)
```

## Sistema de Rangos

### Definición de Rangos
- 🌱 **Novato**: 0-499 Besitos
- 🥉 **Bronce**: 500-1999 Besitos
- 🥈 **Plata**: 2000+ Besitos

### Cambio de Rango
- El sistema verifica automáticamente si un usuario sube de rango al ganar Besitos
- Se emite un evento `RankUpEvent` cuando ocurre un cambio
- Se envía notificación de cambio de rango

## Sistema de Badges

### Badges Disponibles
- ❤️ **Reactor**: 100 reacciones totales
- 🔥 **Hot Streak**: 7 días de login consecutivo
- 🌟 **Consistent**: 30 días de login consecutivo
- 💋 **Coleccionista**: 1000 Besitos acumulados
- 👑 **VIP**: Usuario con suscripción VIP activa

### Desbloqueo de Badges
- Los badges se verifican y desbloquean automáticamente al cumplir requisitos
- Se emite un evento `BadgeUnlockedEvent` cuando se desbloquea un badge
- Se envía notificación de badge desbloqueado

### Verificación de Badges
```python
# Verificar y desbloquear badges
new_badges = await container.gamification.check_and_unlock_badges(user_id=123)
```

## Sistema de Login Diario

### Daily Login
- Los usuarios pueden reclamar un regalo diario
- Otorga Besitos base + bonus por racha
- Mantiene racha de login consecutivos

### Funcionalidades
- **Racha de login**: Contador de días consecutivos de login
- **Bonus por racha**: Más Besitos por mantener la racha
- **Récord personal**: Seguimiento del récord de racha
- **Rate limiting**: No se puede reclamar más de una vez al día

### Uso del Sistema
```python
# Reclamar daily login
besitos_ganados, dias_racha, es_nuevo_record = await container.gamification.claim_daily_login(
    user_id=123
)
```

## Sistema de Reacciones

### Descripción
Los usuarios pueden reaccionar a mensajes usando botones inline, ganando Besitos por cada reacción.

### Rate Limiting
- **Límite diario**: Máximo 50 reacciones por día
- **Tiempo entre reacciones**: Mínimo 5 segundos entre reacciones
- **Verificación automática**: Sistema verifica si puede reaccionar antes de otorgar Besitos

### Tipos de Reacciones
- ❤️ Like
- 🔥 Fire
- 💋 Beso
- 👍 Thumbs up
- Y otros según configuración

### Registro de Reacciones
```python
# Verificar si puede reaccionar
puede_reaccionar = await container.gamification.can_react_to_message(user_id=123)

if puede_reaccionar:
    # Registrar la reacción
    await container.gamification.record_reaction(user_id=123)
```

## Sistema de Commit (Contribuciones)

### Descripción
El sistema de "commit" representa las contribuciones del usuario al sistema, reflejando su participación activa.

### Componentes
- **Total de reacciones**: Contador de todas las reacciones del usuario
- **Reacciones diarias**: Contador de reacciones en el día actual
- **Última reacción**: Timestamp de la última reacción
- **Contribución total**: Medida del nivel de participación del usuario

## Integración con Event Bus

### Eventos de Gamificación
- `PointsAwardedEvent`: Emitido cuando se otorgan Besitos
- `BadgeUnlockedEvent`: Emitido cuando se desbloquea un badge
- `RankUpEvent`: Emitido cuando un usuario sube de rango

### Listeners Automáticos
```python
# En gamification/listeners.py
@subscribe(UserStartedBotEvent)
async def on_user_started_bot(event: UserStartedBotEvent):
    # Otorga 10 Besitos de bienvenida
    pass

@subscribe(MessageReactedEvent)
async def on_message_reacted(event: MessageReactedEvent):
    # Otorga Besitos por reacción
    pass
```

## Base de Datos

### Modelos Relacionados
- `UserProgress`: Progreso individual de cada usuario
  - `total_besitos`: Total acumulado
  - `current_rank`: Rango actual
  - `total_reactions`: Total de reacciones
  - `reactions_today`: Reacciones hoy
  - `last_reaction_at`: Última reacción
  - `daily_streak_id`: Relación con streak diario

- `UserBadge`: Insignias desbloqueadas por usuarios
  - `user_id`: ID del usuario
  - `badge_id`: ID de la insignia
  - `unlocked_at`: Fecha de desbloqueo

- `DailyStreak`: Información de racha diaria
  - `current_streak`: Racha actual
  - `longest_streak`: Mejor racha
  - `last_login_date`: Último login
  - `total_logins`: Total de logins

- `BesitosTransaction`: Historial de transacciones
  - `user_id`: ID del usuario
  - `amount`: Cantidad de Besitos
  - `reason`: Razón de la transacción
  - `created_at`: Fecha de transacción

## Configuración del Sistema

### ConfigurationService Integration
El sistema de gamificación ahora utiliza el ConfigurationService para gestionar todas las configuraciones dinámicamente:

**ActionConfig (Recompensas por acción):**
```python
# Obtener puntos configurados para una acción
points = await container.configuration.get_points_for_action("message_reacted")

# Crear nueva acción con puntos
action = await container.configuration.create_action(
    action_key="custom_action",
    display_name="Acción Custom",
    points_amount=15,
    description="Reacción especial"
)
```

**BadgeConfig (Definiciones de badges):**
```python
# Crear nuevo badge
badge = await container.configuration.create_badge(
    badge_key="reactor",
    name="Reactor",
    icon="❤️",
    requirement_type="total_reactions",
    requirement_value=100,
    description="100 reacciones totales"
)

# Verificar badges disponibles para un usuario
badges = await container.configuration.get_badges_for_user_progress(
    total_reactions=150,
    total_points=2000,
    streak_days=7,
    is_vip=True
)
```

**LevelConfig (Rangos y requisitos):**
```python
# Crear nuevo nivel
level = await container.configuration.create_level(
    name="Diamante",
    min_points=5000,
    max_points=None,
    multiplier=1.5,
    icon="💎"
)

# Obtener nivel correspondiente a puntos
level = await container.configuration.get_level_for_points(3000)
```

**RewardConfig (Recompensas configurables):**
```python
# Crear recompensa
reward = await container.configuration.create_reward(
    name="Recompensa Especial",
    reward_type="both",  # points + badge
    points_amount=100,
    badge_id=1
)
```

**MissionConfig (Misiones y objetivos):**
```python
# Crear misión
mission = await container.configuration.create_mission(
    name="Reactor Activo",
    mission_type="cumulative",
    target_value=50,
    target_action="message_reacted",
    reward_id=1,
    description="Reacciona a 50 mensajes",
    is_repeatable=True,
    cooldown_hours=24
)
```

**Sistema de Cache:**
```python
# El ConfigurationService implementa cache con TTL para mejorar rendimiento
cache = get_config_cache()
stats = cache.get_stats()  # hits, misses, hit_ratio, etc.
```

## Uso del Servicio

### Obtener o Crear Progreso
```python
progress = await container.gamification.get_or_create_progress(user_id=123)
```

### Otorgar Besitos
```python
# Otorgar Besitos por acción específica (lee puntos desde ActionConfig)
amount, ranked_up, new_rank = await container.gamification.award_besitos(
    user_id=123,
    action="message_reacted"
)

# Otorgar Besitos personalizados
amount, ranked_up, new_rank = await container.gamification.award_besitos(
    user_id=123,
    action="custom_action",
    custom_amount=100,
    custom_reason="Recompensa especial"
)
```

### Verificar Badges
```python
new_badges = await container.gamification.check_and_unlock_badges(user_id=123)
```

### Reclamar Daily Login
```python
besitos, streak, is_record = await container.gamification.claim_daily_login(user_id=123)
```

### Verificar Puede Reaccionar
```python
puede = await container.gamification.can_react_to_message(user_id=123)
```

## Integración con ConfigurationService y Cache

### Sistema de Configuración Dinámica
El GamificationService ahora se integra con el ConfigurationService para obtener configuraciones en tiempo real:

- **ActionConfig**: Lee puntos configurados para cada acción
- **LevelConfig**: Obtiene rangos y requisitos actualizados
- **BadgeConfig**: Consulta definiciones de badges dinámicamente
- **RewardConfig**: Accede a recompensas configurables
- **MissionConfig**: Gestiona misiones y objetivos

### Sistema de Cache
Todas las configuraciones se cachean con TTL configurable para mejorar el rendimiento:
- Cache de acciones: 5 minutos por defecto
- Cache de niveles: 5 minutos por defecto
- Cache de puntos específicos: 1 minuto
- Estadísticas de cache disponibles para monitoreo

## Integración con Notificaciones

### Sistema de RewardBatch
Cuando un usuario realiza una acción que otorga múltiples recompensas, se agrupan en un RewardBatch:

```python
# Ejemplo: Usuario reacciona → Gana Besitos + Puede desbloquear badge + Puede subir de rango
batch = await container.notifications.create_reward_batch(
    user_id=event.user_id,
    action="Reaccionaste a un mensaje importante"
)

batch.add_besitos(50, "Reacción")
batch.add_badge("🔥 Reactor Pro", "50 reacciones totales")
batch.add_rank_up("Novato", "Bronce")

await container.notifications.send_reward_batch(batch)
```

## Estadísticas y Métricas

### Seguimiento de Gamificación
- Total de Besitos otorgados
- Badges desbloqueados por tipo
- Cambios de rango
- Login diario promedio
- Reacciones totales del sistema

### Métricas Disponibles
- `total_besitos_otorgados`: Total de puntos en el sistema
- `usuarios_activos_gamificacion`: Usuarios con Besitos
- `badges_totales_desbloqueados`: Total de insignias otorgadas
- `rango_promedio`: Nivel promedio de usuarios

## Rate Limiting y Protección

### Control de Reacciones
- Límite diario estricto para prevenir abuso
- Tiempo mínimo entre reacciones
- Validación antes de otorgar recompensas
- Logging de intentos de abuso

### Seguridad
- Validación de estado de usuario antes de otorgar recompensas
- Control de acceso a funciones de gamificación
- Protección contra spam de eventos

## Ejemplos de Implementación

### Flujo Completo de Reacción
```python
# 1. Usuario reacciona a mensaje (desde handler de reacciones)
# 2. Verificar rate limiting
puede_reaccionar = await container.gamification.can_react_to_message(user_id)

if not puede_reaccionar:
    return  # No otorgar Besitos

# 3. Registrar reacción
await container.gamification.record_reaction(user_id)

# 4. Otorgar Besitos base
amount, ranked_up, new_rank = await container.gamification.award_besitos(
    user_id=user_id,
    action="message_reacted"
)

# 5. Otorgar bonus si es primera reacción del día
progress = await container.gamification.get_or_create_progress(user_id)
if progress.reactions_today == 1:
    bonus_amount, _, _ = await container.gamification.award_besitos(
        user_id=user_id,
        action="first_reaction_of_day"
    )

# 6. Verificar badges
new_badges = await container.gamification.check_and_unlock_badges(user_id)

# 7. Enviar notificación unificada
batch = await container.notifications.create_reward_batch(
    user_id=user_id,
    action=f"Reaccionaste con ❤️"
)
batch.add_besitos(amount + bonus_amount, "Reacción")
for badge_id in new_badges:
    badge_def = container.gamification.config.get_badge_definition(badge_id)
    batch.add_badge(f"{badge_def.icon} {badge_def.name}", badge_def.description)
await container.notifications.send_reward_batch(batch)
```

## Testing y Validación

### Pruebas del Sistema
- Validación de otorgamiento correcto de Besitos
- Pruebas de desbloqueo de badges
- Verificación de cambios de rango
- Testing de rate limiting
- Pruebas de daily login
- Validación de RewardBatch

## Performance y Optimización

- Uso eficiente de base de datos con sesiones optimizadas
- Sistema de cache con TTL configurable para configuraciones de gamificación
- Procesamiento asincrónico de eventos
- Logging eficiente
- Gestión de memoria optimizada
- Estadísticas de rendimiento del cache disponibles

## Mejores Prácticas

- Usar RewardBatch para múltiples recompensas
- Implementar rate limiting adecuado
- Validar estado del usuario antes de otorgar recompensas
- Usar eventos para desacoplar lógica de recompensas
- Implementar logging detallado para seguimiento
- Probar límites y casos extremos