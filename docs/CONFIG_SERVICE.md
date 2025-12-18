# Configuration Service - Documentación Completa

## Descripción General

El **Configuration Service** es un componente esencial del bot que gestiona la configuración de gamificación mediante un sistema de CRUD unificado para todas las entidades relacionadas. Implementa un sistema de cache en memoria con TTL configurable y proporciona operaciones CRUD completas para:

- **ActionConfig**: Configuración de puntos por acción
- **LevelConfig**: Configuración de niveles/rangos
- **BadgeConfig**: Configuración de insignias
- **RewardConfig**: Configuración de recompensas
- **MissionConfig**: Configuración de misiones

## Responsabilidades

- **CRUD para configuraciones de gamificación:** Operaciones completas para todas las entidades de gamificación
- **Sistema de cache con TTL:** Mejora el rendimiento con cache en memoria configurable
- **Validación de negocio:** Validaciones específicas para cada tipo de configuración
- **Gestión de dependencias:** Verificación de uso antes de eliminar configuraciones
- **Operaciones anidadas:** Creación de recursos relacionados en transacciones atómicas
- **Métricas de rendimiento:** Estadísticas del sistema de cache

## Integración en ServiceContainer

El ConfigurationService está integrado en el ServiceContainer como un servicio más, disponible bajo la propiedad `configuration`. Se carga de forma lazy (solo cuando se accede por primera vez) para optimizar el uso de memoria en entornos como Termux:

```python
# Acceso al servicio a través del container
container = ServiceContainer(session, bot)
config_service = container.configuration

# El servicio se carga lazy en el primer acceso
actions = await container.configuration.list_actions()
```

La integración en ServiceContainer permite:
- Acceso consistente con otros servicios del sistema
- Lazy loading para optimizar memoria
- Gestión centralizada de dependencias
- Integración con el sistema de logging
- Recursos compartidos (sesión de base de datos)

## Arquitectura

### Estructura de Configuración
```python
# ActionConfig: Configura puntos por acción
class ActionConfig:
    action_key: str          # Identificador único (ej: "message_reacted")
    display_name: str        # Nombre para mostrar (ej: "Reacción a mensaje")
    points_amount: int       # Puntos a otorgar
    description: str         # Descripción opcional
    is_active: bool          # Estado activo/inactivo

# LevelConfig: Configura niveles/rangos
class LevelConfig:
    name: str                # Nombre del nivel (ej: "Novato")
    min_points: int          # Puntos mínimos para alcanzar
    max_points: int          # Puntos máximos (None = infinito)
    multiplier: float        # Multiplicador de puntos
    icon: str                # Emoji del nivel (ej: "🌱")
    order: int               # Orden de display
    is_active: bool          # Estado activo/inactivo

# BadgeConfig: Configura insignias
class BadgeConfig:
    badge_key: str           # Identificador único (ej: "reactor")
    name: str                # Nombre para display (ej: "Reactor Pro")
    icon: str                # Emoji del badge (ej: "🔥")
    requirement_type: str    # Tipo de requisito (total_reactions, streak_days, etc)
    requirement_value: int   # Valor necesario para desbloquear
    is_active: bool          # Estado activo/inactivo

# RewardConfig: Configura recompensas
class RewardConfig:
    name: str                # Nombre de la recompensa
    reward_type: str         # Tipo (points, badge, both, custom)
    points_amount: int       # Puntos a otorgar (si aplica)
    badge_id: int            # Badge a otorgar (si aplica)
    is_active: bool          # Estado activo/inactivo

# MissionConfig: Configura misiones
class MissionConfig:
    name: str                # Nombre de la misión
    mission_type: str        # Tipo (single, streak, cumulative, timed)
    target_action: str       # Acción objetivo (referencia a ActionConfig)
    target_value: int        # Valor objetivo (ej: 10 reacciones)
    reward_id: int           # Recompensa al completar
    is_active: bool          # Estado activo/inactivo
```

### Sistema de Cache
El servicio implementa un sistema de cache en memoria con TTL configurable por tipo de dato:

- **TTL por defecto:** 300 segundos (5 minutos) para la mayoría de los datos
- **TTL específico para puntos:** 60 segundos para puntos de acciones específicas
- **Invalidación automática:** Cache se invalida al actualizar/eliminar configuraciones
- **Estadísticas de rendimiento:** Métricas de hits/misses del cache

## API Pública

### ActionConfig CRUD

#### `list_actions(include_inactive: bool = False)` → List[ActionConfig]
Lista todas las acciones configuradas.

**Args:**
- `include_inactive` - Si True, incluye acciones desactivadas

**Returns:** `List[ActionConfig]` - Lista ordenada por action_key

**Ejemplo:**
```python
actions = await container.configuration.list_actions()
print(f"Acciones configuradas: {len(actions)}")

# Incluir desactivadas
all_actions = await container.configuration.list_actions(include_inactive=True)
```

#### `get_action(action_key: str)` → ActionConfig
Obtiene una acción por su key.

**Args:**
- `action_key` - Identificador único de la acción

**Returns:** `ActionConfig` - Configuración encontrada

**Raises:** `ConfigNotFoundError` - Si la acción no existe

**Ejemplo:**
```python
action = await container.configuration.get_action("message_reacted")
print(f"Puntos por reacción: {action.points_amount}")
```

#### `create_action(action_key: str, display_name: str, points_amount: int, description: str = None)` → ActionConfig
Crea una nueva configuración de acción.

**Args:**
- `action_key` - Identificador único (ej: "custom_reaction")
- `display_name` - Nombre para mostrar (ej: "Reacción Custom")
- `points_amount` - Puntos a otorgar
- `description` - Descripción opcional

**Returns:** `ActionConfig` - Configuración creada

**Raises:**
- `ConfigAlreadyExistsError` - Si action_key ya existe
- `ConfigValidationError` - Si los datos son inválidos

**Ejemplo:**
```python
action = await container.configuration.create_action(
    action_key="special_reaction",
    display_name="Reacción Especial",
    points_amount=15,
    description="Reacción para mensajes especiales"
)
```

#### `update_action(action_key: str, **kwargs)` → ActionConfig
Actualiza una configuración de acción existente.

**Args:**
- `action_key` - Key de la acción a actualizar
- `display_name`, `points_amount`, `description`, `is_active` - Campos opcionales a actualizar

**Returns:** `ActionConfig` - Configuración actualizada

**Raises:** `ConfigNotFoundError` - Si la acción no existe

**Ejemplo:**
```python
updated_action = await container.configuration.update_action(
    action_key="message_reacted",
    points_amount=8,
    display_name="Reacción Mejorada"
)
```

#### `delete_action(action_key: str, hard_delete: bool = False)` → bool
Elimina (soft o hard) una configuración de acción.

**Args:**
- `action_key` - Key de la acción a eliminar
- `hard_delete` - Si True, elimina permanentemente

**Returns:** `bool` - True si se eliminó correctamente

**Raises:**
- `ConfigNotFoundError` - Si la acción no existe
- `ConfigInUseError` - Si la acción está siendo usada por misiones

**Ejemplo:**
```python
# Soft delete (desactivar)
await container.configuration.delete_action("old_action", hard_delete=False)

# Hard delete (eliminar permanentemente)
await container.configuration.delete_action("temp_action", hard_delete=True)
```

#### `get_points_for_action(action_key: str)` → int
Obtiene los puntos configurados para una acción (método de conveniencia).

**Args:**
- `action_key` - Key de la acción

**Returns:** `int` - Puntos configurados, o 0 si no existe o está inactiva

**Ejemplo:**
```python
points = await container.configuration.get_points_for_action("message_reacted")
print(f"Puntos por reacción: {points}")
```

### LevelConfig CRUD

#### `list_levels(include_inactive: bool = False)` → List[LevelConfig]
Lista todos los niveles configurados.

**Args:**
- `include_inactive` - Si True, incluye niveles desactivados

**Returns:** `List[LevelConfig]` - Lista ordenada por 'order'

**Ejemplo:**
```python
levels = await container.configuration.list_levels()
print(f"Niveles configurados: {len(levels)}")
```

#### `get_level(level_id: int)` → LevelConfig
Obtiene un nivel por su ID.

**Args:**
- `level_id` - ID del nivel

**Returns:** `LevelConfig` - Nivel encontrado

**Raises:** `ConfigNotFoundError` - Si el nivel no existe

**Ejemplo:**
```python
level = await container.configuration.get_level(1)
print(f"Nivel: {level.name}")
```

#### `get_level_for_points(points: int)` → Optional[LevelConfig]
Obtiene el nivel correspondiente a una cantidad de puntos.

**Args:**
- `points` - Cantidad de puntos

**Returns:** `LevelConfig` - Nivel correspondiente, o None si no hay niveles

**Ejemplo:**
```python
level = await container.configuration.get_level_for_points(1500)
if level:
    print(f"Nivel para 1500 puntos: {level.name}")
```

#### `create_level(name: str, min_points: int, max_points: int, multiplier: float = 1.0, icon: str = "🌱", color: str = None)` → LevelConfig
Crea un nuevo nivel.

**Args:**
- `name` - Nombre del nivel
- `min_points` - Puntos mínimos para alcanzar
- `max_points` - Puntos máximos (None = infinito)
- `multiplier` - Multiplicador de puntos
- `icon` - Emoji del nivel
- `color` - Color para UI (opcional)

**Returns:** `LevelConfig` - Nivel creado

**Raises:** `ConfigValidationError` - Si los datos son inválidos

**Ejemplo:**
```python
level = await container.configuration.create_level(
    name="Diamante",
    min_points=5000,
    max_points=None,  # Infinito
    multiplier=1.5,
    icon="💎"
)
```

#### `update_level(level_id: int, **kwargs)` → LevelConfig
Actualiza un nivel existente.

**Args:**
- `level_id` - ID del nivel a actualizar
- Campos opcionales: `name`, `min_points`, `max_points`, `multiplier`, `icon`, `color`, `is_active`

**Returns:** `LevelConfig` - Nivel actualizado

**Ejemplo:**
```python
updated_level = await container.configuration.update_level(
    level_id=2,
    multiplier=1.2,
    icon="⭐"
)
```

#### `reorder_levels(level_ids: List[int])` → List[LevelConfig]
Reordena los niveles según el orden proporcionado.

**Args:**
- `level_ids` - Lista de IDs en el nuevo orden

**Returns:** `List[LevelConfig]` - Niveles reordenados

**Ejemplo:**
```python
# Reordenar niveles: primero nivel 3, luego 1, luego 2
reordered = await container.configuration.reorder_levels([3, 1, 2])
```

### BadgeConfig CRUD

#### `list_badges(include_inactive: bool = False)` → List[BadgeConfig]
Lista todos los badges configurados.

**Args:**
- `include_inactive` - Si True, incluye badges desactivados

**Returns:** `List[BadgeConfig]` - Lista ordenada por badge_key

**Ejemplo:**
```python
badges = await container.configuration.list_badges()
print(f"Badges configurados: {len(badges)}")
```

#### `get_badge(badge_key: str)` → BadgeConfig
Obtiene un badge por su key.

**Args:**
- `badge_key` - Identificador único del badge

**Returns:** `BadgeConfig` - Badge encontrado

**Raises:** `ConfigNotFoundError` - Si el badge no existe

**Ejemplo:**
```python
badge = await container.configuration.get_badge("super_reactor")
print(f"Badge: {badge.name}")
```

#### `create_badge(badge_key: str, name: str, icon: str, requirement_type: str, requirement_value: int, description: str = None)` → BadgeConfig
Crea un nuevo badge.

**Args:**
- `badge_key` - Identificador único (ej: "super_reactor")
- `name` - Nombre para mostrar (ej: "Super Reactor")
- `icon` - Emoji del badge
- `requirement_type` - Tipo de requisito (total_reactions, streak_days, etc)
- `requirement_value` - Valor requerido
- `description` - Descripción de cómo obtenerlo

**Returns:** `BadgeConfig` - Badge creado

**Raises:**
- `ConfigAlreadyExistsError` - Si badge_key ya existe
- `ConfigValidationError` - Si los datos son inválidos

**Ejemplo:**
```python
badge = await container.configuration.create_badge(
    badge_key="hot_streak",
    name="Racha Caliente",
    icon="🔥",
    requirement_type="streak_days",
    requirement_value=7,
    description="7 días de login consecutivos"
)
```

#### `get_badges_for_user_progress(total_reactions: int, total_points: int, streak_days: int, is_vip: bool)` → List[BadgeConfig]
Obtiene los badges que un usuario califica para desbloquear.

**Args:**
- `total_reactions` - Total de reacciones del usuario
- `total_points` - Total de puntos del usuario
- `streak_days` - Días de racha actual
- `is_vip` - Si el usuario es VIP

**Returns:** `List[BadgeConfig]` - Lista de badges que el usuario cumple requisitos

**Ejemplo:**
```python
qualified_badges = await container.configuration.get_badges_for_user_progress(
    total_reactions=150,
    total_points=2000,
    streak_days=10,
    is_vip=True
)
```

### RewardConfig CRUD

#### `list_rewards(include_inactive: bool = False)` → List[RewardConfig]
Lista todas las recompensas configuradas.

**Args:**
- `include_inactive` - Si True, incluye recompensas desactivadas

**Returns:** `List[RewardConfig]` - Lista con badge relacionado cargado

**Ejemplo:**
```python
rewards = await container.configuration.list_rewards()
print(f"Recompensas configuradas: {len(rewards)}")
```

#### `get_reward(reward_id: int)` → RewardConfig
Obtiene una recompensa por su ID.

**Args:**
- `reward_id` - ID de la recompensa

**Returns:** `RewardConfig` - Recompensa con badge cargado

**Raises:** `ConfigNotFoundError` - Si la recompensa no existe

**Ejemplo:**
```python
reward = await container.configuration.get_reward(1)
print(f"Recompensa: {reward.name}")
```

#### `create_reward(name: str, reward_type: str, points_amount: int = None, badge_id: int = None, description: str = None, custom_data: Dict[str, Any] = None)` → RewardConfig
Crea una nueva recompensa.

**Args:**
- `name` - Nombre de la recompensa
- `reward_type` - Tipo (points, badge, both, custom)
- `points_amount` - Puntos a otorgar (requerido si type incluye points)
- `badge_id` - ID del badge a otorgar (requerido si type incluye badge)
- `description` - Descripción opcional
- `custom_data` - Datos adicionales para recompensas custom

**Returns:** `RewardConfig` - Recompensa creada

**Raises:**
- `ConfigValidationError` - Si los datos son inválidos
- `ConfigNotFoundError` - Si badge_id no existe

**Ejemplo:**
```python
reward = await container.configuration.create_reward(
    name="Recompensa VIP",
    reward_type="both",
    points_amount=100,
    badge_id=1,
    description="Recompensa para usuarios VIP"
)
```

#### `create_reward_with_new_badge(...)` → Tuple[RewardConfig, BadgeConfig]
Crea una recompensa junto con un nuevo badge (operación atómica).

**Args:** Parámetros para crear tanto recompensa como badge

**Returns:** `Tuple[RewardConfig, BadgeConfig]` - Recompensa y badge creados

**Ejemplo:**
```python
reward, badge = await container.configuration.create_reward_with_new_badge(
    name="Recompensa de Prueba",
    reward_type="both",
    points_amount=50,
    badge_key="test_badge",
    badge_name="Badge de Prueba",
    badge_icon="🧪",
    badge_requirement_type="total_points",
    badge_requirement_value=100
)
```

### MissionConfig CRUD

#### `list_missions(include_inactive: bool = False)` → List[MissionConfig]
Lista todas las misiones configuradas.

**Args:**
- `include_inactive` - Si True, incluye misiones desactivadas

**Returns:** `List[MissionConfig]` - Lista con reward y badge cargados

**Ejemplo:**
```python
missions = await container.configuration.list_missions()
print(f"Misiones configuradas: {len(missions)}")
```

#### `get_mission(mission_id: int)` → MissionConfig
Obtiene una misión por su ID.

**Args:**
- `mission_id` - ID de la misión

**Returns:** `MissionConfig` - Misión con reward y badge cargados

**Raises:** `ConfigNotFoundError` - Si la misión no existe

**Ejemplo:**
```python
mission = await container.configuration.get_mission(1)
print(f"Misión: {mission.name}")
```

#### `create_mission(name: str, mission_type: str, target_value: int, target_action: str = None, reward_id: int = None, description: str = None, time_limit_hours: int = None, is_repeatable: bool = False, cooldown_hours: int = None)` → MissionConfig
Crea una nueva misión.

**Args:**
- `name` - Nombre de la misión
- `mission_type` - Tipo (single, streak, cumulative, timed)
- `target_value` - Valor objetivo (ej: 10 reacciones)
- `target_action` - Acción objetivo (referencia a ActionConfig.action_key)
- `reward_id` - ID de la recompensa al completar
- `description` - Descripción de la misión
- `time_limit_hours` - Límite de tiempo (solo para tipo 'timed')
- `is_repeatable` - Si se puede completar múltiples veces
- `cooldown_hours` - Tiempo entre repeticiones

**Returns:** `MissionConfig` - Misión creada

**Raises:**
- `ConfigValidationError` - Si los datos son inválidos
- `ConfigNotFoundError` - Si reward_id o target_action no existen

**Ejemplo:**
```python
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

#### `create_mission_complete(...)` → Tuple[MissionConfig, RewardConfig, BadgeConfig]
Crea una misión completa con recompensa Y badge nuevos (operación atómica nivel 2).

**Args:** Parámetros para crear misión, recompensa y badge

**Returns:** `Tuple[MissionConfig, RewardConfig, BadgeConfig]` - Todos los recursos creados

**Ejemplo:**
```python
mission, reward, badge = await container.configuration.create_mission_complete(
    name="Misión Completa",
    mission_type="single",
    target_value=1,
    target_action="message_reacted",
    reward_name="Recompensa Completa",
    reward_type="both",
    reward_points=100,
    badge_key="completo_badge",
    badge_name="Badge Completo",
    badge_icon="🏆",
    badge_requirement_type="custom",
    badge_requirement_value=1
)
```

### Sistema de Cache

#### `get_config_cache()` → ConfigCache
Obtiene la instancia global del cache.

**Returns:** `ConfigCache` - Instancia singleton del cache

**Ejemplo:**
```python
cache = get_config_cache()
stats = cache.get_stats()
print(f"Cache hits: {stats['hits']}, misses: {stats['misses']}")
```

#### `get_stats()` → Dict[str, Any]
Obtiene estadísticas del cache.

**Returns:** `Dict` con hits, misses, ratio, entries

**Ejemplo:**
```python
stats = cache.get_stats()
print(f"Ratio de cache: {stats['hit_ratio']:.2%}")
print(f"Entradas en cache: {stats['entries']}")
```

#### `invalidate_all()` → int
Invalida todo el cache.

**Returns:** `int` - Número de entradas eliminadas

**Ejemplo:**
```python
deleted_count = cache.invalidate_all()
print(f"Cache limpiado: {deleted_count} entradas eliminadas")
```

### Previews

#### `preview_mission_complete(mission_data: Dict, reward_data: Dict, badge_data: Dict = None)` → str
Genera un preview de texto de lo que se creará.

**Args:**
- `mission_data` - Datos de la misión
- `reward_data` - Datos de la recompensa
- `badge_data` - Datos del badge (opcional)

**Returns:** `str` - String formateado con el preview

**Ejemplo:**
```python
preview = container.configuration.preview_mission_complete(
    mission_data={"name": "Misión Prueba", "target_value": 10},
    reward_data={"name": "Recompensa Prueba", "points_amount": 50},
    badge_data={"badge_key": "test", "name": "Badge Prueba", "icon": "🏆"}
)
print(preview)
```

## Ejemplos de Uso Completo

### 1. Gestión de acciones
```python
# Crear una nueva acción
action = await container.configuration.create_action(
    action_key="custom_action",
    display_name="Acción Custom",
    points_amount=15,
    description="Acción especial para eventos"
)

# Listar todas las acciones
actions = await container.configuration.list_actions()
for action in actions:
    print(f"{action.action_key}: {action.points_amount} pts")

# Actualizar una acción
await container.configuration.update_action(
    action_key="custom_action",
    points_amount=20
)
```

### 2. Gestión de niveles
```python
# Crear niveles
novato = await container.configuration.create_level(
    name="Novato",
    min_points=0,
    max_points=499,
    icon="🌱",
    multiplier=1.0
)

bronce = await container.configuration.create_level(
    name="Bronce",
    min_points=500,
    max_points=1999,
    icon="🥉",
    multiplier=1.1
)

# Obtener nivel para puntos específicos
level = await container.configuration.get_level_for_points(750)
print(f"Nivel para 750 puntos: {level.name}")
```

### 3. Gestión de badges
```python
# Crear badges
reactor_badge = await container.configuration.create_badge(
    badge_key="reactor",
    name="Reactor",
    icon="❤️",
    requirement_type="total_reactions",
    requirement_value=100,
    description="100 reacciones totales"
)

streak_badge = await container.configuration.create_badge(
    badge_key="hot_streak",
    name="Racha Caliente",
    icon="🔥",
    requirement_type="streak_days",
    requirement_value=7,
    description="7 días de login consecutivos"
)

# Verificar badges para un usuario
badges = await container.configuration.get_badges_for_user_progress(
    total_reactions=150,
    total_points=1000,
    streak_days=10,
    is_vip=True
)
print(f"Badges disponibles: {len(badges)}")
```

### 4. Gestión de recompensas y misiones
```python
# Crear recompensa
reward = await container.configuration.create_reward(
    name="Recompensa de Prueba",
    reward_type="points",
    points_amount=100,
    description="Recompensa para probar sistema"
)

# Crear misión completa (misión + recompensa + badge)
mission, reward, badge = await container.configuration.create_mission_complete(
    name="Desafío Completo",
    mission_type="cumulative",
    target_value=25,
    target_action="message_reacted",
    reward_name="Recompensa Desafío",
    reward_type="both",
    reward_points=200,
    badge_key="desafiador",
    badge_name="Desafiador",
    badge_icon="⚔️",
    badge_requirement_type="total_missions",
    badge_requirement_value=1
)

print(f"Creación completa: Misión '{mission.name}', Recompensa '{reward.name}', Badge '{badge.name}'")
```

### 5. Sistema de cache
```python
# Obtener estadísticas del cache
cache = get_config_cache()
stats = cache.get_stats()
print(f"Hit ratio: {stats['hit_ratio']:.2%}")
print(f"Total entries: {stats['entries']}")

# Limpiar cache si es necesario
if stats['hit_ratio'] < 0.5:
    cache.invalidate_all()
    print("Cache limpiado por bajo rendimiento")
```

## Patrones de Diseño

### Cache con TTL
El servicio implementa un sistema de cache en memoria con TTL configurable por tipo de dato, lo que mejora significativamente el rendimiento al reducir accesos a base de datos.

### Validación de Negocio
Cada entidad tiene validaciones específicas de negocio para prevenir configuraciones inconsistentes o inválidas.

### Transacciones Atómicas
Las operaciones de creación anidada (como `create_mission_complete`) se realizan en transacciones atómicas para mantener la consistencia de datos.

### Logging Detallado
El servicio incluye logging detallado para seguimiento de operaciones:
- Creación, actualización y eliminación de configuraciones
- Operaciones de cache (hits, misses, invalidaciones)
- Errores de validación y negocio

## Integración con Otros Servicios

El ConfigurationService se integra con otros servicios del sistema:

- **GamificationService:** Utiliza configuraciones para otorgar puntos y badges
- **ServiceContainer:** Implementa el patrón DI + Lazy Loading
- **EventBus:** Puede integrarse con eventos de sistema para actualizaciones dinámicas

## Consideraciones de Seguridad

- Solo usuarios administradores deben tener acceso a los métodos de configuración
- Validación exhaustiva de entradas para prevenir inyección de datos maliciosos
- Verificación de dependencias antes de eliminar configuraciones
- Logging de todas las modificaciones para auditoría

## Excepciones Comunes

- `ConfigNotFoundError`: Configuración no encontrada
- `ConfigAlreadyExistsError`: Configuración ya existe (duplicado)
- `ConfigValidationError`: Validación de datos fallida
- `ConfigInUseError`: Configuración está en uso y no se puede eliminar
- `SQLAlchemyError`: Errores de base de datos (generalmente manejados por el contenedor de servicios)