# Gamification System - Besitos, Badges, Levels, Daily Login, Reacciones y Commit

## Descripción General

El sistema de gamificación es un componente integral que motiva a los usuarios a interactuar con el bot mediante un sistema de puntos (Besitos), insignias (badges), niveles, login diario y reacciones. Utiliza el Event Bus para otorgar recompensas automáticamente cuando ocurren ciertas acciones.

## Componentes del Sistema

### GamificationService
Servicio principal que maneja:
- Otorgamiento de Besitos (en el sistema legacy)
- Verificación y desbloqueo de badges
- Sistema de login diario
- Rate limiting de reacciones

**Nota:** El sistema de niveles ahora está manejado por servicios separados:
- `PointsService` - Gestión de puntos y balances
- `LevelsService` - Gestión de niveles y progresión

### GamificationConfig
Configuración centralizada con:
- Recompensas por acción
- Definiciones de badges
- Niveles y requisitos
- Límites de reacciones

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
success, new_balance = await container.points.award_points(
    user_id=123,
    amount=10,
    reason="Reacción a mensaje",
    multiplier=1.0  # Este puede ser modificado por nivel o VIP status
)

# El sistema de niveles verifica automáticamente level-ups
should_level_up, old_level, new_level = await container.levels.check_level_up(
    user_id=123,
    current_points=await container.points.get_user_balance(123)
)

if should_level_up:
    await container.levels.apply_level_up(123, new_level.level)
```

## Sistema de Niveles

### Definición de Niveles
El sistema consta de 7 niveles progresivos con multiplicadores de puntos y beneficios exclusivos:

- 🌱 **Novato**: 0-99 Besitos (1.0x)
- 📚 **Aprendiz**: 100-249 Besitos (1.1x)
- 💪 **Competente**: 250-499 Besitos (1.2x)
- 🎯 **Avanzado**: 500-999 Besitos (1.3x)
- 🌟 **Experto**: 1000-2499 Besitos (1.5x)
- 👑 **Maestro**: 2500-4999 Besitos (1.8x)
- 🏆 **Leyenda**: 5000+ Besitos (2.0x)

### Cambio de Nivel
- El sistema verifica automáticamente si un usuario sube de nivel al ganar Besitos
- Se emite un evento `RankUpEvent` cuando ocorga un cambio
- Se envía notificación de cambio de nivel
- Los multiplicadores aumentan progresivamente con cada nivel

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
  - `besitos_balance`: Saldo actual de besitos
  - `current_level`: Nivel actual (1-7)
  - `total_points_earned`: Total de puntos ganados (histórico)
  - `total_points_spent`: Total de puntos gastados (histórico)
  - `created_at`: Fecha de creación del registro
  - `updated_at`: Fecha de última actualización

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

### GamificationConfig
```python
# Configuración centralizada
class GamificationConfig:
    MAX_REACTIONS_PER_DAY = 50
    MIN_SECONDS_BETWEEN_REACTIONS = 5
    
    REWARDS = {
        "user_started": RewardConfig(10, "Regalo de bienvenida"),
        "joined_vip": RewardConfig(100, "Activación VIP"),
        # ... más recompensas
    }
    
    BADGES = [
        BadgeConfig("reactor", "Reactor", "❤️", 100, "total_reactions"),
        # ... más badges
    ]
    
    LEVELS = [
        LevelConfig("Novato", 0, 99, 1.0),
        LevelConfig("Aprendiz", 100, 249, 1.1),
        LevelConfig("Competente", 250, 499, 1.2),
        LevelConfig("Avanzado", 500, 999, 1.3),
        LevelConfig("Experto", 1000, 2499, 1.5),
        LevelConfig("Maestro", 2500, 4999, 1.8),
        LevelConfig("Leyenda", 5000, None, 2.0)  # No upper limit
    ]
```

## Uso del Servicio

### Obtener o Crear Progreso
```python
progress = await container.gamification.get_or_create_progress(user_id=123)
```

### Otorgar Besitos
```python
success, new_balance = await container.points.award_points(
    user_id=123,
    amount=10,
    reason="Reacción a mensaje"
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
# Obtener nivel actual para calcular multiplicador
current_level = await container.points.get_user_level(user_id)
level_multiplier = await container.levels.get_level_multiplier(current_level)

# Otorgar puntos con multiplicador
success, new_balance = await container.points.award_points(
    user_id=user_id,
    amount=5,  # Puntos base por reacción
    reason="Reacción a mensaje",
    multiplier=level_multiplier
)

# 5. Verificar si hay level-up
if success:
    should_level_up, old_level, new_level = await container.levels.check_level_up(
        user_id=user_id,
        current_points=new_balance
    )
    if should_level_up:
        await container.levels.apply_level_up(user_id, new_level.level)

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
- Caching de configuración para mejor performance
- Procesamiento asincrónico de eventos
- Logging eficiente
- Gestión de memoria optimizada

## Mejores Prácticas

- Usar RewardBatch para múltiples recompensas
- Implementar rate limiting adecuado
- Validar estado del usuario antes de otorgar recompensas
- Usar eventos para desacoplar lógica de recompensas
- Implementar logging detallado para seguimiento
- Probar límites y casos extremos