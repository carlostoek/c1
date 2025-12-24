# PROMPT G1.6: Tests Unitarios - Modelos de BD

---

## ROL

Actúa como QA Engineer especializado en testing de modelos SQLAlchemy, bases de datos en memoria y pytest async.

---

## TAREA

Implementa la suite de tests unitarios para los 13 modelos del módulo de gamificación en `tests/gamification/test_models.py`, verificando creación, relaciones, constraints y validaciones.

---

## CONTEXTO

### Stack de Testing
- pytest 7.4+
- pytest-asyncio para tests async
- SQLAlchemy 2.0 con SQLite in-memory
- aiosqlite

### Estructura de Tests Existente
```
tests/
├── conftest.py                    # Fixtures globales
├── test_e2e_flows.py              # Tests E2E sistema core
└── gamification/                  # ← NUEVO
    ├── __init__.py
    ├── conftest.py                # Fixtures del módulo
    └── test_models.py             # ← ESTE ARCHIVO
```

### Modelos a Testear
```
1. UserGamification
2. Reaction
3. UserReaction
4. UserStreak
5. Level
6. Mission
7. UserMission
8. Reward
9. UserReward
10. Badge
11. UserBadge
12. ConfigTemplate
13. GamificationConfig
```

---

## RESTRICCIONES TÉCNICAS

### Fixtures Requeridas

Crear en `tests/gamification/conftest.py`:

```python
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from bot.gamification.database.models import Base

@pytest_asyncio.fixture
async def db_session():
    """Sesión de BD en memoria para tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
    
    await engine.dispose()

@pytest_asyncio.fixture
async def sample_user(db_session):
    """Usuario de prueba."""
    from bot.gamification.database.models import UserGamification
    user = UserGamification(user_id=12345, total_besitos=0)
    db_session.add(user)
    await db_session.commit()
    return user
```

### Estrategia de Testing

Para cada modelo, testear:

1. **Happy Path:** Creación exitosa con valores válidos
2. **Relaciones:** FKs y relationships funcionan
3. **Constraints:** UNIQUEs, NOT NULLs se respetan
4. **Defaults:** Valores por defecto se aplican
5. **Cascades:** Deletes en cascada funcionan

---

## CASOS DE PRUEBA POR MODELO

### UserGamification

```python
@pytest.mark.asyncio
async def test_create_user_gamification(db_session):
    """Debe crear perfil de gamificación con defaults"""
    user = UserGamification(user_id=12345)
    db_session.add(user)
    await db_session.commit()
    
    assert user.total_besitos == 0
    assert user.besitos_earned == 0
    assert user.besitos_spent == 0
    assert user.current_level_id is None

@pytest.mark.asyncio
async def test_user_gamification_relationship_with_level(db_session, sample_level):
    """Debe relacionarse con Level"""
    user = UserGamification(user_id=12345, current_level_id=sample_level.id)
    db_session.add(user)
    await db_session.commit()
    
    # Lazy load de relación
    await db_session.refresh(user, ['current_level'])
    assert user.current_level.name == sample_level.name
```

### Reaction

```python
@pytest.mark.asyncio
async def test_create_reaction(db_session):
    """Debe crear reacción con emoji único"""
    reaction = Reaction(emoji="❤️", besitos_value=1)
    db_session.add(reaction)
    await db_session.commit()
    
    assert reaction.emoji == "❤️"
    assert reaction.active is True

@pytest.mark.asyncio
async def test_reaction_emoji_unique_constraint(db_session):
    """No debe permitir emojis duplicados"""
    from sqlalchemy.exc import IntegrityError
    
    reaction1 = Reaction(emoji="🔥", besitos_value=1)
    reaction2 = Reaction(emoji="🔥", besitos_value=2)
    
    db_session.add(reaction1)
    await db_session.commit()
    
    db_session.add(reaction2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
```

### UserReaction

```python
@pytest.mark.asyncio
async def test_create_user_reaction(db_session, sample_user, sample_reaction):
    """Debe registrar reacción de usuario"""
    user_reaction = UserReaction(
        user_id=sample_user.user_id,
        reaction_id=sample_reaction.id,
        channel_id=-1001234567890,
        message_id=123
    )
    db_session.add(user_reaction)
    await db_session.commit()
    
    assert user_reaction.user_id == sample_user.user_id
    assert user_reaction.reacted_at is not None
```

### UserStreak

```python
@pytest.mark.asyncio
async def test_user_streak_defaults(db_session, sample_user):
    """Debe iniciar con racha en 0"""
    streak = UserStreak(user_id=sample_user.user_id)
    db_session.add(streak)
    await db_session.commit()
    
    assert streak.current_streak == 0
    assert streak.longest_streak == 0
    assert streak.last_reaction_date is None

@pytest.mark.asyncio
async def test_user_streak_unique_per_user(db_session, sample_user):
    """Solo debe permitir 1 racha por usuario"""
    from sqlalchemy.exc import IntegrityError
    
    streak1 = UserStreak(user_id=sample_user.user_id)
    streak2 = UserStreak(user_id=sample_user.user_id)
    
    db_session.add(streak1)
    await db_session.commit()
    
    db_session.add(streak2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
```

### Level

```python
@pytest.mark.asyncio
async def test_create_level(db_session):
    """Debe crear nivel con mínimo de besitos"""
    level = Level(name="Novato", min_besitos=0, order=1)
    db_session.add(level)
    await db_session.commit()
    
    assert level.active is True

@pytest.mark.asyncio
async def test_level_name_unique(db_session):
    """No debe permitir nombres duplicados"""
    from sqlalchemy.exc import IntegrityError
    
    level1 = Level(name="Novato", min_besitos=0, order=1)
    level2 = Level(name="Novato", min_besitos=500, order=2)
    
    db_session.add(level1)
    await db_session.commit()
    
    db_session.add(level2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
```

### Mission

```python
@pytest.mark.asyncio
async def test_create_mission(db_session):
    """Debe crear misión con criterios JSON"""
    from bot.gamification.database.enums import MissionType
    
    mission = Mission(
        name="Primera Racha",
        description="Completa 7 días consecutivos",
        mission_type=MissionType.STREAK,
        criteria='{"type": "streak", "days": 7}',
        besitos_reward=500
    )
    db_session.add(mission)
    await db_session.commit()
    
    assert mission.active is True
    assert mission.repeatable is False
```

### UserMission

```python
@pytest.mark.asyncio
async def test_user_mission_progress(db_session, sample_user, sample_mission):
    """Debe trackear progreso de misión"""
    from bot.gamification.database.enums import MissionStatus
    
    user_mission = UserMission(
        user_id=sample_user.user_id,
        mission_id=sample_mission.id,
        progress='{"days_completed": 3}',
        status=MissionStatus.IN_PROGRESS
    )
    db_session.add(user_mission)
    await db_session.commit()
    
    assert user_mission.status == MissionStatus.IN_PROGRESS
    assert user_mission.completed_at is None

@pytest.mark.asyncio
async def test_user_mission_unique_constraint(db_session, sample_user, sample_mission):
    """No debe permitir mismo user+mission si no es repeatable"""
    from sqlalchemy.exc import IntegrityError
    from bot.gamification.database.enums import MissionStatus
    
    um1 = UserMission(user_id=sample_user.user_id, mission_id=sample_mission.id, status=MissionStatus.IN_PROGRESS)
    um2 = UserMission(user_id=sample_user.user_id, mission_id=sample_mission.id, status=MissionStatus.IN_PROGRESS)
    
    db_session.add(um1)
    await db_session.commit()
    
    db_session.add(um2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
```

### Reward y Badge (herencia)

```python
@pytest.mark.asyncio
async def test_create_badge(db_session):
    """Debe crear badge como subtipo de reward"""
    from bot.gamification.database.enums import RewardType, BadgeRarity
    
    reward = Reward(
        name="Primer Paso",
        description="Completaste tu primera misión",
        reward_type=RewardType.BADGE
    )
    db_session.add(reward)
    await db_session.commit()
    
    badge = Badge(
        id=reward.id,
        icon="🏆",
        rarity=BadgeRarity.COMMON
    )
    db_session.add(badge)
    await db_session.commit()
    
    assert badge.icon == "🏆"
```

### GamificationConfig (singleton)

```python
@pytest.mark.asyncio
async def test_gamification_config_singleton(db_session):
    """Debe permitir solo 1 registro de config"""
    config = GamificationConfig(id=1, besitos_per_reaction=1)
    db_session.add(config)
    await db_session.commit()
    
    assert config.id == 1
```

---

## FORMATO DE SALIDA

Entregar **DOS ARCHIVOS**:

### 1. tests/gamification/conftest.py

```python
# tests/gamification/conftest.py

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from bot.gamification.database.models import Base, UserGamification, Reaction, Level, Mission

@pytest_asyncio.fixture
async def db_session():
    """..."""
    pass

@pytest_asyncio.fixture
async def sample_user(db_session):
    """..."""
    pass

# ... más fixtures
```

### 2. tests/gamification/test_models.py

```python
# tests/gamification/test_models.py

import pytest
from sqlalchemy.exc import IntegrityError
from bot.gamification.database.models import *
from bot.gamification.database.enums import *

# ============================================
# TESTS UserGamification
# ============================================

@pytest.mark.asyncio
async def test_create_user_gamification(db_session):
    """..."""
    pass

# ... todos los tests
```

---

## VALIDACIÓN

La suite debe cumplir:
- ✅ Al menos 2 tests por modelo (happy + constraint/relación)
- ✅ Tests de unique constraints
- ✅ Tests de foreign keys
- ✅ Tests de defaults
- ✅ Uso de fixtures para datos de prueba
- ✅ Todos los tests pasan: `pytest tests/gamification/test_models.py -v`

---

**ENTREGABLES:** 
1. `conftest.py` con fixtures
2. `test_models.py` con 26+ tests (2 por modelo mínimo)
