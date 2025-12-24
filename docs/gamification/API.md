# Referencia de API - Servicios del Módulo de Gamificación

## 📚 Índice

1. [GamificationContainer](#gamificationcontainer)
2. [ReactionService](#reactionservice)
3. [BesitoService](#besitoservice)
4. [LevelService](#levelservice)
5. [MissionService](#missionservice)
6. [RewardService](#rewardservice)
7. [UserGamificationService](#usergamificationservice)
8. [NotificationService](#notificationservice)
9. [Orchestrators](#orchestrators)

---

## GamificationContainer

Contenedor de inyección de dependencias que gestiona todos los servicios del módulo de gamificación.

### Instanciación

```python
from bot.gamification.services.container import GamificationContainer

container = GamificationContainer(session, bot=bot)
```

### Propiedades

- `reaction_service` - Servicio de reacciones
- `besito_service` - Servicio de economía de besitos
- `level_service` - Servicio de niveles
- `mission_service` - Servicio de misiones
- `reward_service` - Servicio de recompensas
- `user_gamification_service` - Servicio de perfil de usuario
- `notification_service` - Servicio de notificaciones
- `configuration_orchestrator` - Orquestador de configuración

---

## ReactionService

Gestiona el catálogo de reacciones configuradas y el registro de reacciones de usuarios.

### Métodos

#### `create_reaction(emoji: str, name: str, besitos_value: int, active: bool = True) -> Reaction`
Crea una nueva reacción configurable.

```python
reaction = await container.reaction_service.create_reaction(
    emoji="🔥",
    name="Fuego",
    besitos_value=2
)
```

#### `get_active_reactions() -> List[Reaction]`
Obtiene todas las reacciones activas.

```python
active_reactions = await container.reaction_service.get_active_reactions()
```

#### `record_reaction(user_id: int, emoji: str, message_id: int, channel_id: int, reacted_at: datetime) -> Tuple[bool, str, int]`
Registra una reacción de usuario y otorga besitos.

```python
success, message, besitos_gained = await container.reaction_service.record_reaction(
    user_id=123456789,
    emoji="❤️",
    message_id=12345,
    channel_id=-100123456789,
    reacted_at=datetime.now(UTC)
)
```

#### `get_user_reaction_stats(user_id: int) -> Dict`
Obtiene estadísticas de reacciones de un usuario.

```python
stats = await container.reaction_service.get_user_reaction_stats(123456789)
```

---

## BesitoService

Gestiona la economía de "besitos" (moneda virtual) con operaciones atómicas para prevenir race conditions.

### Métodos

#### `grant_besitos(user_id: int, amount: int, reason: str, transaction_type: str) -> bool`
Otorga besitos a un usuario con auditoría.

```python
success = await container.besito_service.grant_besitos(
    user_id=123456789,
    amount=10,
    reason="Reacción exitosa",
    transaction_type="reaction"
)
```

#### `deduct_besitos(user_id: int, amount: int, reason: str) -> Tuple[bool, str]`
Deduce besitos de un usuario con validación de saldo suficiente.

```python
success, message = await container.besito_service.deduct_besitos(
    user_id=123456789,
    amount=50,
    reason="Compra de recompensa"
)
```

#### `get_user_besitos(user_id: int) -> int`
Obtiene la cantidad de besitos de un usuario.

```python
besitos = await container.besito_service.get_user_besitos(123456789)
```

#### `get_user_transaction_history(user_id: int, limit: int = 10) -> List[Transaction]`
Obtiene historial de transacciones de un usuario.

```python
history = await container.besito_service.get_user_transaction_history(123456789, limit=20)
```

---

## LevelService

Gestiona niveles del sistema, cálculo automático de level-ups, y progresión de usuarios.

### Métodos

#### `create_level(name: str, min_besitos: int, order: int, benefits: Dict = None) -> Level`
Crea un nuevo nivel con beneficios configurables.

```python
level = await container.level_service.create_level(
    name="Iniciado",
    min_besitos=0,
    order=1,
    benefits={"icon": "🌱", "perks": ["access_feature_x"]}
)
```

#### `get_all_levels() -> List[Level]`
Obtiene todos los niveles ordenados por besitos mínimos.

```python
levels = await container.level_service.get_all_levels()
```

#### `get_level_by_id(level_id: int) -> Optional[Level]`
Obtiene un nivel por su ID.

```python
level = await container.level_service.get_level_by_id(1)
```

#### `check_and_apply_level_up(user_id: int) -> Tuple[bool, Level, Level]`
Verifica si un usuario merece un level-up y lo aplica si aplica.

```python
changed, old_level, new_level = await container.level_service.check_and_apply_level_up(123456789)
if changed:
    print(f"¡Subiste de nivel! {old_level.name} → {new_level.name}")
```

---

## MissionService

Gestiona misiones configuradas por admins, tracking de progreso de usuarios, validación de criterios y otorgamiento de recompensas.

### Métodos

#### `create_mission(name: str, description: str, mission_type: MissionType, criteria: Dict, besitos_reward: int, requirements: Dict = None) -> Mission`
Crea una nueva misión con criterios definidos.

```python
mission = await container.mission_service.create_mission(
    name="Reactor Diario",
    description="Reacciona a 5 mensajes hoy",
    mission_type=MissionType.DAILY,
    criteria={"type": "daily", "count": 5},
    besitos_reward=50
)
```

#### `start_mission(user_id: int, mission_id: int) -> UserMission`
Inicia una misión para un usuario específico.

```python
user_mission = await container.mission_service.start_mission(123456789, mission.id)
```

#### `update_mission_progress(user_id: int, mission_id: int, progress_data: Dict) -> bool`
Actualiza el progreso de una misión activa.

```python
updated = await container.mission_service.update_mission_progress(
    user_id=123456789,
    mission_id=mission.id,
    progress_data={"daily_count": 3}
)
```

#### `complete_mission(user_id: int, mission_id: int) -> bool`
Marca una misión como completada.

```python
completed = await container.mission_service.complete_mission(123456789, mission.id)
```

#### `get_user_active_missions(user_id: int) -> List[UserMission]`
Obtiene misiones activas de un usuario.

```python
active_missions = await container.mission_service.get_user_active_missions(123456789)
```

#### `get_mission_by_id(mission_id: int) -> Optional[Mission]`
Obtiene una misión por su ID.

```python
mission = await container.mission_service.get_mission_by_id(1)
```

#### `claim_reward(user_id: int, mission_id: int) -> Tuple[bool, str, Dict]`
Reclama la recompensa de una misión completada.

```python
success, message, reward_info = await container.mission_service.claim_reward(123456789, mission.id)
```

---

## RewardService

Gestiona recompensas configurables, condiciones de desbloqueo, compra con besitos, y tracking de recompensas obtenidas por usuarios.

### Métodos

#### `create_reward(name: str, description: str, reward_type: RewardType, metadata: Dict, unlock_conditions: Dict = None) -> Reward`
Crea una nueva recompensa con condiciones de desbloqueo.

```python
reward = await container.reward_service.create_reward(
    name="Badge de Bienvenida",
    description="Primer badge del bot",
    reward_type=RewardType.BADGE,
    metadata={"icon": "👋", "rarity": "common"},
    unlock_conditions={"type": "mission", "mission_id": 1}
)
```

#### `check_unlock_conditions(user_id: int, reward_id: int) -> Tuple[bool, str]`
Verifica si un usuario puede desbloquear una recompensa.

```python
can_unlock, reason = await container.reward_service.check_unlock_conditions(123456789, reward.id)
```

#### `grant_reward(user_id: int, reward_id: int, granted_by: str = "system") -> Tuple[bool, str]`
Otorga una recompensa a un usuario.

```python
success, message = await container.reward_service.grant_reward(123456789, reward.id, granted_by="admin")
```

#### `purchase_reward(user_id: int, reward_id: int) -> Tuple[bool, str]`
Compra una recompensa con besitos.

```python
success, message = await container.reward_service.purchase_reward(123456789, reward.id)
```

#### `get_user_rewards(user_id: int) -> List[UserReward]`
Obtiene todas las recompensas obtenidas por un usuario.

```python
user_rewards = await container.reward_service.get_user_rewards(123456789)
```

#### `get_reward_by_id(reward_id: int) -> Optional[Reward]`
Obtiene una recompensa por su ID.

```python
reward = await container.reward_service.get_reward_by_id(1)
```

---

## UserGamificationService

Fachada unificada para obtener el perfil completo de gamificación de un usuario, agregando datos de múltiples servicios.

### Métodos

#### `initialize_new_user(user_id: int) -> bool`
Inicializa un nuevo usuario en el sistema de gamificación.

```python
success = await container.user_gamification_service.initialize_new_user(123456789)
```

#### `get_user_profile(user_id: int) -> Dict`
Obtiene el perfil completo de gamificación de un usuario.

```python
profile = await container.user_gamification_service.get_user_profile(123456789)
```

#### `get_user_statistics(user_id: int) -> Dict`
Obtiene estadísticas detalladas de un usuario.

```python
stats = await container.user_gamification_service.get_user_statistics(123456789)
```

#### `get_formatted_profile(user_id: int) -> str`
Obtiene el perfil formateado para mostrar en Telegram.

```python
formatted_profile = await container.user_gamification_service.get_formatted_profile(123456789)
```

---

## NotificationService

Servicio de notificaciones que envía alertas a usuarios sobre eventos de gamificación.

### Métodos

#### `notify_level_up(user_id: int, old_level: Level, new_level: Level) -> bool`
Notifica a un usuario que subió de nivel.

```python
await container.notification_service.notify_level_up(
    user_id=123456789,
    old_level=old_level,
    new_level=new_level
)
```

#### `notify_mission_completed(user_id: int, mission: Mission) -> bool`
Notifica a un usuario que completó una misión.

```python
await container.notification_service.notify_mission_completed(
    user_id=123456789,
    mission=mission
)
```

#### `notify_reward_unlocked(user_id: int, reward: Reward) -> bool`
Notifica a un usuario que desbloqueó una recompensa.

```python
await container.notification_service.notify_reward_unlocked(
    user_id=123456789,
    reward=reward
)
```

#### `notify_streak_milestone(user_id: int, days: int) -> bool`
Notifica hito de racha (7, 14, 30, 60, 100 días).

```python
await container.notification_service.notify_streak_milestone(
    user_id=123456789,
    days=7
)
```

#### `notify_streak_lost(user_id: int, days: int) -> bool`
Notifica pérdida de racha significativa (7+ días).

```python
await container.notification_service.notify_streak_lost(
    user_id=123456789,
    days=10
)
```

---

## Orchestrators

### ConfigurationOrchestrator

Orquestador maestro que coordina `MissionOrchestrator` y `RewardOrchestrator` para crear configuraciones completas.

#### `create_complete_mission_system(config: Dict, created_by: int) -> Dict`
Crea un sistema completo de misión con nivel y recompensas asociadas.

```python
config = {
    'mission': {
        'name': "Desafío de Bienvenida",
        'description': "Completa tu primer desafío",
        'mission_type': MissionType.ONE_TIME,
        'criteria': {"type": "one_time"},
        'besitos_reward': 100
    },
    'auto_level': {
        'name': "Nivel de Bienvenida",
        'min_besitos': 100,
        'order': 2
    },
    'rewards': [
        {
            'name': "Badge de Bienvenida",
            'description': "Primer badge",
            'reward_type': RewardType.BADGE,
            'metadata': {"icon": "👋", "rarity": "common"}
        }
    ]
}

result = await container.configuration_orchestrator.create_complete_mission_system(
    config=config,
    created_by=123456789
)
```

### MissionOrchestrator

Coordina la creación de misiones con auto-creación de niveles y recompensas en una sola transacción.

#### `create_mission_system(config: Dict) -> Dict`
Crea un sistema completo de misión en transacción atómica.

```python
result = await container.mission_orchestrator.create_mission_system(config)
```

### RewardOrchestrator

Coordina la creación de recompensas con unlock conditions y badges en transacciones atómicas.

#### `create_reward_system(config: Dict) -> Dict`
Crea un sistema completo de recompensas en transacción atómica.

```python
result = await container.reward_orchestrator.create_reward_system(config)
```