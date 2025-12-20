# API Reference - Módulo de Gamificación

## Índice
- [Introducción](#introducción)
- [ReactionService](#reactionservice)
- [BesitoService](#besitoservice)
- [LevelService](#levelservice)
- [MissionService](#missionservice)
- [RewardService](#rewardservice)
- [BadgeService](#badgeservice)
- [StatsService](#statsservice)
- [Configuración del Contenedor DI](#configuración-del-contenedor-di)

## Introducción

Esta documentación referencia todos los servicios principales del módulo de gamificación, sus métodos públicos y cómo utilizarlos programáticamente. Todos los servicios están disponibles a través del contenedor de inyección de dependencias.

## ReactionService

Maneja el registro y procesamiento de reacciones de usuarios.

### `record_reaction(user_id: int, emoji: str, message_id: int, channel_id: int, reacted_at: datetime) -> bool`

Registra una reacción de un usuario a un mensaje específico.

**Parámetros:**
- `user_id` (int): ID del usuario que recibió la reacción (emisor del mensaje original)
- `emoji` (str): Emoji de la reacción (ej: ❤️, 👍)
- `message_id` (int): ID del mensaje que recibió la reacción
- `channel_id` (int): ID del canal donde ocurrió la interacción
- `reacted_at` (datetime): Fecha y hora de la reacción

**Retorna:**
- `bool`: True si la reacción fue registrada exitosamente, False si fue rechazada (spam, límite, etc.)

**Validaciones:**
- Anti-spam (no duplicar en mismo mensaje)
- Límite diario por usuario
- Emoji válido según configuración

**Efectos:**
- Otorga besitos al emisor del mensaje
- Actualiza racha de besitos
- Actualiza progreso de misiones relacionadas

**Ejemplo de uso:**
```python
from bot.container import Container
from datetime import datetime

container = Container()
reaction_service = container.reaction_service()

success = reaction_service.record_reaction(
    user_id=123456789,
    emoji='❤️',
    message_id=123,
    channel_id=-1001234567890,
    reacted_at=datetime.utcnow()
)
```

### `validate_reaction(emoji: str, message_id: int, user_id: int) -> dict`

Valida si una reacción es válida según las reglas del sistema.

**Parámetros:**
- `emoji` (str): Emoji a validar
- `message_id` (int): ID del mensaje destino
- `user_id` (int): ID del usuario que reacciona

**Retorna:**
- `dict`: {'valid': bool, 'reason': str, 'details': dict}

### `get_reaction_rules() -> dict`

Obtiene las reglas actuales de reacciones configuradas.

**Retorna:**
- `dict`: Configuración de emojis y reglas de reacción

## BesitoService

Gestiona la economía de besitos (moneda virtual del sistema).

### `award_besitos(user_id: int, amount: int, reason: str = '', transaction_details: dict = None) -> bool`

Otorga besitos a un usuario.

**Parámetros:**
- `user_id` (int): ID del usuario a quien otorgar besitos
- `amount` (int): Cantidad de besitos a otorgar (debe ser positivo)
- `reason` (str): Razón del otorgamiento
- `transaction_details` (dict): Información adicional de la transacción

**Retorna:**
- `bool`: True si los besitos fueron otorgados exitosamente

**Ejemplo de uso:**
```python
besito_service = container.besito_service()
success = besito_service.award_besitos(
    user_id=123456789,
    amount=5,
    reason='Reacción ❤️ a mensaje',
    transaction_details={'message_id': 123, 'channel_id': -1001234567890}
)
```

### `get_user_balance(user_id: int) -> int`

Obtiene el saldo actual de besitos de un usuario.

**Parámetros:**
- `user_id` (int): ID del usuario

**Retorna:**
- `int`: Saldo actual de besitos

### `transfer_besitos(sender_id: int, receiver_id: int, amount: int) -> bool`

Transfiere besitos entre usuarios.

**Parámetros:**
- `sender_id` (int): ID del usuario que envía
- `receiver_id` (int): ID del usuario que recibe
- `amount` (int): Cantidad a transferir

**Retorna:**
- `bool`: True si la transferencia fue exitosa

### `get_top_users(limit: int = 10) -> list`

Obtiene los usuarios con más besitos.

**Parámetros:**
- `limit` (int): Número de usuarios a retornar

**Retorna:**
- `list`: Lista de tuplas (user_id, balance)

## LevelService

Maneja el sistema de niveles y progresión.

### `calculate_level(xp_points: int) -> tuple`

Calcula el nivel basado en puntos de experiencia.

**Parámetros:**
- `xp_points` (int): Puntos de experiencia totales

**Retorna:**
- `tuple`: (nivel_actual, xp_para_siguiente_nivel, xp_restante_en_nivel_actual)

### `update_user_level(user_id: int, new_xp: int = 0) -> dict`

Actualiza el nivel de un usuario basado en XP.

**Parámetros:**
- `user_id` (int): ID del usuario
- `new_xp` (int): XP adicional a sumar (opcional)

**Retorna:**
- `dict`: Información del nivel actualizada

### `check_level_up(user_id: int) -> dict`

Verifica si un usuario ha subido de nivel.

**Parámetros:**
- `user_id` (int): ID del usuario

**Retorna:**
- `dict`: {'leveled_up': bool, 'previous_level': int, 'current_level': int, 'rewards': list}

### `get_user_level_info(user_id: int) -> dict`

Obtiene información completa del nivel de un usuario.

**Parámetros:**
- `user_id` (int): ID del usuario

**Retorna:**
- `dict`: Información completa del nivel y progreso

**Ejemplo de uso:**
```python
level_service = container.level_service()
level_info = level_service.get_user_level_info(123456789)
print(f"Nivel: {level_info['level']}, XP: {level_info['xp']}/{level_info['xp_for_next']}")
```

## MissionService

Administra misiones y progreso de usuarios.

### `create_daily_missions() -> list`

Crea las misiones diarias para todos los usuarios.

**Retorna:**
- `list`: IDs de misiones creadas

### `update_mission_progress(user_id: int, mission_id: int, increment: int = 1) -> dict`

Actualiza el progreso de una misión para un usuario.

**Parámetros:**
- `user_id` (int): ID del usuario
- `mission_id` (int): ID de la misión
- `increment` (int): Valor a incrementar (por defecto 1)

**Retorna:**
- `dict`: {'progress': int, 'completed': bool, 'rewards': list}

### `claim_mission_rewards(user_id: int, mission_id: int) -> dict`

Reclama las recompensas de una misión completada.

**Parámetros:**
- `user_id` (int): ID del usuario
- `mission_id` (int): ID de la misión completada

**Retorna:**
- `dict`: Información de recompensas entregadas

### `get_user_daily_missions(user_id: int) -> list`

Obtiene las misiones diarias de un usuario.

**Parámetros:**
- `user_id` (int): ID del usuario

**Retorna:**
- `list`: Lista de misiones diarias con estado

### `get_available_missions(user_id: int) -> list`

Obtiene todas las misiones disponibles para un usuario.

**Parámetros:**
- `user_id` (int): ID del usuario

**Retorna:**
- `list`: Lista de misiones disponibles

**Ejemplo de uso:**
```python
mission_service = container.mission_service()
daily_missions = mission_service.get_user_daily_missions(123456789)
for mission in daily_missions:
    print(f"Misión: {mission['title']}, Progreso: {mission['progress']}/{mission['target']}")
```

## RewardService

Gestiona recompensas y condiciones de desbloqueo.

### `grant_reward(user_id: int, reward_id: int) -> bool`

Otorga una recompensa específica a un usuario.

**Parámetros:**
- `user_id` (int): ID del usuario
- `reward_id` (int): ID de la recompensa

**Retorna:**
- `bool`: True si la recompensa fue otorgada exitosamente

### `check_unlock_conditions(user_id: int, item_id: str) -> dict`

Verifica si un usuario cumple condiciones para desbloquear un elemento.

**Parámetros:**
- `user_id` (int): ID del usuario
- `item_id` (str): ID del ítem a verificar

**Retorna:**
- `dict`: {'unlocked': bool, 'conditions_met': list, 'remaining_requirements': list}

### `apply_template_rewards(template_id: str) -> bool`

Aplica recompensas desde una plantilla.

**Parámetros:**
- `template_id` (str): ID de la plantilla de recompensas

**Retorna:**
- `bool`: True si la plantilla fue aplicada exitosamente

### `get_user_rewards(user_id: int) -> list`

Obtiene todas las recompensas obtenidas por un usuario.

**Parámetros:**
- `user_id` (int): ID del usuario

**Retorna:**
- `list`: Lista de recompensas obtenidas

## BadgeService

Maneja badges e insignias coleccionables.

### `award_badge(user_id: int, badge_id: str) -> bool`

Otorga un badge específico a un usuario.

**Parámetros:**
- `user_id` (int): ID del usuario
- `badge_id` (str): ID único del badge

**Retorna:**
- `bool`: True si el badge fue otorgado

### `get_user_badges(user_id: int) -> list`

Obtiene todos los badges de un usuario.

**Parámetros:**
- `user_id` (int): ID del usuario

**Retorna:**
- `list`: Lista de badges obtenidos

### `create_badge_definition(badge_data: dict) -> str`

Crea una definición de badge nueva.

**Parámetros:**
- `badge_data` (dict): Datos del nuevo badge (nombre, descripción, condiciones, etc.)

**Retorna:**
- `str`: ID del badge creado

### `get_badge_collection_stats(user_id: int) -> dict`

Obtiene estadísticas de colección de badges de un usuario.

**Parámetros:**
- `user_id` (int): ID del usuario

**Retorna:**
- `dict`: Estadísticas de colección de badges

## StatsService

Calcula y proporciona estadísticas del sistema.

### `get_user_statistics(user_id: int) -> dict`

Obtiene estadísticas detalladas de un usuario.

**Parámetros:**
- `user_id` (int): ID del usuario

**Retorna:**
- `dict`: Estadísticas completas del usuario

### `get_leaderboard(limit: int = 10) -> list`

Obtiene el ranking de usuarios según diferentes criterios.

**Parámetros:**
- `limit` (int): Número de usuarios en el leaderboard

**Retorna:**
- `list`: Ranking de usuarios

### `get_channel_stats(channel_id: int) -> dict`

Obtiene estadísticas de un canal específico.

**Parámetros:**
- `channel_id` (int): ID del canal

**Retorna:**
- `dict`: Estadísticas del canal

### `get_system_metrics() -> dict`

Obtiene métricas generales del sistema de gamificación.

**Retorna:**
- `dict`: Métricas generales del sistema

**Ejemplo de uso:**
```python
stats_service = container.stats_service()
leaderboard = stats_service.get_leaderboard(limit=5)
for rank, (user_id, score) in enumerate(leaderboard, 1):
    print(f"{rank}. User {user_id}: {score} pts")
```

## Configuración del Contenedor DI

Todos los servicios están disponibles a través del contenedor de inyección de dependencias:

```python
from bot.container import Container

container = Container()

# Acceder a servicios
reaction_service = container.reaction_service()
besito_service = container.besito_service()
level_service = container.level_service()
mission_service = container.mission_service()
reward_service = container.reward_service()
badge_service = container.badge_service()
stats_service = container.stats_service()
```

Los servicios están configurados con dependencias inyectadas y listos para usar sin necesidad de manejar manualmente conexiones a base de datos u otros recursos.