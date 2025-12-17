# Level System Documentation

## Overview

The Level System is a gamification component that provides a progressive ranking mechanism for users based on their accumulated points (besitos). The system consists of 7 distinct levels with increasing point thresholds, progressive multipliers, and exclusive benefits.

## Level Definitions

The system defines 7 levels with specific point thresholds and benefits:

| Level | Number | Name | Icon | Min Points | Max Points | Multiplier | Perks |
|-------|--------|------|------|------------|------------|------------|-------|
| 1 | 1 | Novato | 🌱 | 0 | 99 | 1.0x | Welcome to the gamification system |
| 2 | 2 | Aprendiz | 📚 | 100 | 249 | 1.1x | Points multiplier x1.1, First step in your progress |
| 3 | 3 | Competente | 💪 | 250 | 499 | 1.2x | Points multiplier x1.2, Unlock special missions |
| 4 | 4 | Avanzado | 🎯 | 500 | 999 | 1.3x | Points multiplier x1.3, Access to premium rewards |
| 5 | 5 | Experto | 🌟 | 1000 | 2499 | 1.5x | Points multiplier x1.5, Exclusive expert badge, Priority support |
| 6 | 6 | Maestro | 👑 | 2500 | 4999 | 1.8x | Points multiplier x1.8, Golden master badge, Early access to new features |
| 7 | 7 | Leyenda | 🏆 | 5000 | ∞ | 2.0x | Points multiplier x2.0, Legendary exclusive badge, Special community recognition, All system advantages |

## Level Model Structure

### Database Schema

The `Level` model is defined in `bot/database/models.py`:

```python
class Level(Base):
    __tablename__ = "levels"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Level number (1-7)
    level = Column(
        Integer,
        nullable=False,
        unique=True,
        index=True,
        doc="Número de nivel (1-7)"
    )

    # Level name
    name = Column(
        String(50),
        nullable=False,
        doc="Nombre del nivel (ej: Experto)"
    )

    # Emoji icon
    icon = Column(
        String(10),
        nullable=False,
        doc="Emoji del nivel (ej: 🌟)"
    )

    # Minimum points required
    min_points = Column(
        Integer,
        nullable=False,
        doc="Puntos mínimos para alcanzar este nivel"
    )

    # Maximum points for this level (None = no upper limit)
    max_points = Column(
        Integer,
        nullable=True,
        doc="Puntos máximos del nivel (None = sin límite superior)"
    )

    # Points multiplier
    multiplier = Column(
        Float,
        nullable=False,
        default=1.0,
        doc="Multiplicador de puntos para este nivel"
    )

    # Benefits (JSON)
    perks = Column(
        JSON,
        nullable=True,
        doc="Lista de beneficios del nivel"
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
```

### Model Properties

#### `display_name`
Returns the formatted name with emoji:
```python
>>> level.display_name
"🌟 Experto"
```

#### `is_in_range(points: int) -> bool`
Verifies if a given amount of points falls within this level's range:
```python
# For level 3 (Competente): 250-499 points
>>> level.is_in_range(300)  # True
>>> level.is_in_range(200)  # False
>>> level.is_in_range(500)  # False
```

## Level Service

The `LevelsService` in `bot/services/levels.py` manages all level-related operations:

### Key Methods

#### `get_all_levels(use_cache: bool = True) -> List[Level]`
Returns all 7 levels sorted by level number. Uses cache for performance optimization.

#### `get_level_by_number(level_number: int) -> Optional[Level]`
Retrieves a specific level by its number:
```python
>>> level = await service.get_level_by_number(5)
>>> print(level.display_name)
"🌟 Experto"
```

#### `get_level_for_points(points: int) -> Optional[Level]`
Returns the appropriate level for a given point total:
```python
>>> level = await service.get_level_for_points(150)
>>> print(level.name)
"Aprendiz"
```

#### `get_level_multiplier(level_number: int) -> float`
Returns the multiplier for a specific level:
```python
>>> mult = await service.get_level_multiplier(7)
>>> print(mult)
2.0
```

#### `check_level_up(user_id: int, current_points: int) -> Tuple[bool, Optional[Level], Optional[Level]]`
Verifies if a user should level up by comparing their current progress with their points total:
```python
>>> should_up, old, new = await service.check_level_up(123, 150)
>>> if should_up:
...     print(f"Level up! {old.name} → {new.name}")
```

**Parameters:**
- `user_id` (int): ID of the Telegram user
- `current_points` (int): Total points accumulated by the user

**Returns:**
- `Tuple[bool, Optional[Level], Optional[Level]]`: A tuple containing:
  - `should_level_up` (bool): True if user should advance to a new level
  - `old_level` (Optional[Level]): Current level definition of the user
  - `new_level` (Optional[Level]): Target level definition if level-up occurs

**Process:**
1. Retrieves the user's current progress record from the database
2. Fetches the current level definition based on the stored level number
3. Determines the appropriate level for the user's total points
4. Compares levels to check if advancement is needed
5. Returns the comparison result as a tuple

#### `apply_level_up(user_id: int, new_level_number: int) -> bool`
Applies the level up to a user's progress record by updating their current level:
```python
>>> success = await service.apply_level_up(123, 3)  # Update to level 3
>>> if success:
...     print("Level updated successfully")
```

**Parameters:**
- `user_id` (int): ID of the Telegram user
- `new_level_number` (int): New level number to assign to the user

**Returns:**
- `bool`: True if the level was updated successfully, False otherwise

#### `get_user_level_info(user_id: int) -> Optional[Dict]`
Returns comprehensive level information for a user:
```python
>>> info = await service.get_user_level_info(123)
>>> print(info)
{
    'current_level': 3,
    'level_name': 'Competente',
    'level_icon': '💪',
    'display_name': '💪 Competente',
    'multiplier': 1.2,
    'min_points': 250,
    'max_points': 499,
    'perks': ['Multiplicador de puntos x1.2', 'Desbloqueo de misiones especiales'],
    'is_max_level': False
}
```

**Parameters:**
- `user_id` (int): ID of the Telegram user

**Returns:**
- `Optional[Dict]`: Dictionary with detailed level information, or None if user doesn't exist

#### `calculate_progress_to_next_level(user_id: int, total_points: int) -> Optional[Dict]`
Calculates progress toward the next level with detailed metrics:
```python
>>> progress = await service.calculate_progress_to_next_level(123, 350)
>>> print(progress)
{
    'current_level': 3,
    'next_level': 4,
    'current_points': 350,
    'points_in_current_level': 100,
    'points_needed_for_next': 150,
    'total_points_in_level': 250,
    'progress_percentage': 40.0,
    'is_max_level': False
}
```

**Parameters:**
- `user_id` (int): ID of the Telegram user
- `total_points` (int): Total accumulated points for progress calculation

**Returns:**
- `Optional[Dict]`: Dictionary with detailed progress metrics, or None if error occurs

**Progress Calculation Formula:**
- `points_in_current_level` = `total_points` - `current_level.min_points`
- `points_needed_for_next` = `next_level.min_points` - `total_points`
- `progress_percentage` = (`points_in_current_level` / `total_points_in_level`) * 100

#### `get_next_level_info(current_level_number: int) -> Optional[Dict]`
Returns information about the next level:
```python
>>> next_info = await service.get_next_level_info(3)
>>> print(next_info)
{
    'level': 4,
    'name': 'Avanzado',
    'icon': '🎯',
    'display_name': '🎯 Avanzado',
    'min_points': 500,
    'multiplier': 1.3,
    'perks': ['Multiplicador de puntos x1.3', 'Acceso a recompensas premium']
}
```

**Parameters:**
- `current_level_number` (int): Current level number (1-6, 7 returns None)

**Returns:**
- `Optional[Dict]`: Dictionary with next level information, or None if at maximum level

## Integration with Points System

The Level system is integrated with the Points system through:

### Multiplier Application
When users earn points, their level multiplier is applied:
```python
# Example: User at level 3 (1.2x multiplier) earns 10 points
# Final amount: 10 × 1.2 = 12 points
```

### Automatic Level-Up Detection
The system automatically detects when a user should level up when points are awarded:
```python
# In PointsService
async def award_points(self, user_id, amount, reason, multiplier=1.0):
    # ... award points logic ...

    # Check if user should level up
    should_up, old_level, new_level = await container.levels.check_level_up(
        user_id, progress.total_points_earned
    )

    if should_up:
        await container.levels.apply_level_up(user_id, new_level.level)
        # Send level-up notification
```

## Service Container Integration

The LevelsService is available through the ServiceContainer as a lazily-loaded service:

### Access Pattern
```python
# In handlers or other services
container = ServiceContainer(session, bot)

# First access loads the service
level_info = await container.levels.get_user_level_info(user_id)

# Subsequent accesses reuse the instance
progress = await container.levels.calculate_progress_to_next_level(user_id, points)
```

### Property Definition
```python
@property
def levels(self) -> LevelsService:
    """
    Servicio de gestión de niveles (gamificación).

    Proporciona:
    - Verificación y aplicación de level-ups
    - Consulta de información de niveles
    - Cálculo de progreso hacia siguiente nivel
    - Obtención de multiplicadores por nivel
    - Información de perks por nivel

    Returns:
        Instancia de LevelsService

    Example:
        >>> container = ServiceContainer(session, bot)
        >>> # Verificar level-up
        >>> should_up, old, new = await container.levels.check_level_up(
        ...     user_id=123,
        ...     current_points=150
        ... )
        >>> # Obtener información de progreso
        >>> info = await container.levels.get_user_level_info(123)
    """
    if self._levels is None:
        logger.debug("🔄 Lazy loading: LevelsService")
        self._levels = LevelsService(self._session, self._bot)
    return self._levels
```

## Testing Strategy

The LevelsService includes comprehensive testing across multiple scenarios:

### Unit Tests
Located in `tests/unit/test_levels_service.py`, covering:

#### Core Functionality Tests
- `test_get_all_levels`: Verifies retrieval of all 7 levels
- `test_get_all_levels_cache`: Tests caching mechanism
- `test_get_all_levels_no_cache`: Tests cache bypass
- `test_get_level_by_number`: Tests level lookup by number
- `test_get_level_for_points`: Tests level determination by points
- `test_get_level_multiplier`: Tests multiplier retrieval

#### Level-Up Tests
- `test_check_level_up_true`: Tests positive level-up detection
- `test_check_level_up_false`: Tests when level-up should not occur
- `test_check_level_up_multiple_levels`: Tests skipping multiple levels
- `test_check_level_up_user_not_found`: Tests handling missing user
- `test_apply_level_up`: Tests successful level-up application
- `test_apply_level_up_user_not_found`: Tests handling missing user

#### Progress Calculation Tests
- `test_calculate_progress_to_next_level`: Tests progress percentage calculation
- `test_get_user_level_info`: Tests retrieval of comprehensive level info
- `test_get_next_level_info`: Tests next level information retrieval

#### Cache Tests
- `test_clear_cache`: Tests cache invalidation functionality

### Integration Tests
Located in `tests/test_levels_service_complete.py`, testing:

- `test_complete_level_up_flow`: Full level-up process testing
- `test_max_level_handling`: Tests behavior at maximum level
- `test_integration_points_levels`: Points-Levels service integration

### Model Tests
Located in `tests/test_level_model.py`, covering:

- `test_level_model_creation`: Tests Level model creation
- `test_level_display_name`: Tests emoji-name combination
- `test_level_is_in_range`: Tests range validation methods
- `test_level_unique_constraint`: Tests level number uniqueness
- `test_seed_levels_complete`: Tests complete seed data loading
- `test_level_repr`: Tests model string representation
- `test_level_perks_json`: Tests JSON perks field

## Data Seeding

The initial 7 levels are created using the seed file `bot/database/seeds/levels.py`. The seed process:

1. Checks if levels already exist in the database
2. Creates each level only if it doesn't exist
3. Logs creation status for each level

### Seed Execution
```bash
python -m bot.database.seeds.levels
```

## Performance Considerations

### Caching
- Level definitions are cached after first load
- Cache can be cleared when levels are modified (`clear_cache()` method)
- Reduces database queries for level information

### Indexing
- `level` column is indexed for fast lookups
- `user_id` in `UserProgress` is indexed for performance

## API Integration

### Service Container Access
```python
# Access levels service through container
container = ServiceContainer(session, bot)
level_info = await container.levels.get_user_level_info(user_id)
```

### Points Integration
```python
# Get level multiplier when calculating total multiplier
multiplier = await container.points.calculate_multiplier(
    user_id,
    is_vip=True  # VIP status also affects multiplier
)
```

## Level Progression Mechanics

### Threshold System
- Each level has a minimum and maximum point threshold
- Users progress through levels as they accumulate points
- Level 7 (Leyenda) has no maximum limit (infinite progression)

### Progressive Multipliers
- Multipliers increase progressively from 1.0x to 2.0x
- Higher levels provide better point rewards
- Multipliers are applied when earning points

### Perks and Benefits
- Each level provides specific benefits and recognition
- Higher levels unlock exclusive perks
- Benefits are stored as JSON arrays in the database

## User Experience

### Level Display
Users see their current level with emoji and name:
- "🌱 Novato"
- "📚 Aprendiz"
- "💪 Competente"
- etc.

### Progress Tracking
Users can track their progress toward the next level:
- Current level and multiplier
- Points needed for next level
- Progress percentage
- Estimated time to level up

### Notifications
- Level-up notifications when users advance
- Recognition for achieving higher levels
- Special badges for level milestones

## Database Relations

### UserProgress Model
The `UserProgress` model connects users to the level system:
- `current_level`: Current level number (default: 1)
- `besitos_balance`: Current point balance
- `total_points_earned`: Total points accumulated
- `total_points_spent`: Total points spent

### Foreign Key Relationships
- `UserProgress` has a 1:1 relationship with `User`
- `Level` records are referenced by level number in `UserProgress`

## Testing and Validation

### Level Model Tests
- Creation of level records
- Range validation (`is_in_range` method)
- Display name formatting
- Unique constraint enforcement
- Multiplier progression validation

### Service Tests
- Complete level-up flow testing
- Progress calculation accuracy
- Max level handling
- Integration with points service
- Cache functionality

## Migration from Old Rank System

The Level system replaces the old "Rank" system which had fewer levels and different thresholds. Key differences:
- 7 levels instead of 3 ranks
- More granular point thresholds
- Progressive multipliers instead of flat rates
- JSON perks system instead of simple descriptions

## Best Practices

- Always use the service methods for level operations
- Implement proper error handling when working with levels
- Use caching appropriately to optimize performance
- Validate user level information before displaying
- Consider rate limiting level-related operations
- Log level changes for audit purposes