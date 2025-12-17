"""
Tests para el modelo Level del sistema de gamificación.

Prueba:
- Creación de niveles
- Método is_in_range()
- Propiedad display_name
- Carga de seeds
- Persistencia en BD
"""
import pytest
from sqlalchemy import select

from bot.database.models import Level
from bot.database.seeds.levels import LEVEL_DEFINITIONS


@pytest.mark.asyncio
async def test_level_model_creation(db_session):
    """Test crear un nivel directamente."""
    level = Level(
        level=1,
        name="Novato",
        icon="🌱",
        min_points=0,
        max_points=99,
        multiplier=1.0,
        perks=["Bienvenido"]
    )

    db_session.add(level)
    await db_session.commit()
    await db_session.refresh(level)

    assert level.id is not None
    assert level.level == 1
    assert level.name == "Novato"
    assert level.icon == "🌱"


@pytest.mark.asyncio
async def test_level_display_name(db_session):
    """Test la propiedad display_name."""
    level = Level(
        level=5,
        name="Experto",
        icon="🌟",
        min_points=1000,
        max_points=2499,
        multiplier=1.5
    )

    assert level.display_name == "🌟 Experto"


@pytest.mark.asyncio
async def test_level_is_in_range_true(db_session):
    """Test is_in_range cuando los puntos están en rango."""
    level = Level(
        level=3,
        name="Competente",
        icon="💪",
        min_points=250,
        max_points=499,
        multiplier=1.2
    )

    # Puntos dentro del rango
    assert level.is_in_range(250) is True
    assert level.is_in_range(350) is True
    assert level.is_in_range(499) is True


@pytest.mark.asyncio
async def test_level_is_in_range_false(db_session):
    """Test is_in_range cuando los puntos están fuera de rango."""
    level = Level(
        level=3,
        name="Competente",
        icon="💪",
        min_points=250,
        max_points=499,
        multiplier=1.2
    )

    # Puntos por debajo del mínimo
    assert level.is_in_range(249) is False
    assert level.is_in_range(0) is False

    # Puntos por encima del máximo
    assert level.is_in_range(500) is False
    assert level.is_in_range(1000) is False


@pytest.mark.asyncio
async def test_level_is_in_range_no_max(db_session):
    """Test is_in_range para nivel sin límite superior (Leyenda)."""
    level = Level(
        level=7,
        name="Leyenda",
        icon="🏆",
        min_points=5000,
        max_points=None,  # Sin límite
        multiplier=2.0
    )

    # Todos los puntos >= min_points deben estar en rango
    assert level.is_in_range(5000) is True
    assert level.is_in_range(10000) is True
    assert level.is_in_range(100000) is True

    # Puntos por debajo deben estar fuera de rango
    assert level.is_in_range(4999) is False


@pytest.mark.asyncio
async def test_level_unique_constraint(db_session):
    """Test que el campo level tiene constraint único."""
    level1 = Level(
        level=1,
        name="Novato",
        icon="🌱",
        min_points=0,
        max_points=99,
        multiplier=1.0
    )
    db_session.add(level1)
    await db_session.commit()

    # Intentar agregar otro nivel con el mismo número
    level2 = Level(
        level=1,
        name="Otro",
        icon="🌱",
        min_points=0,
        max_points=50,
        multiplier=1.0
    )
    db_session.add(level2)

    with pytest.raises(Exception):  # SQLAlchemy raise exception on duplicate
        await db_session.commit()


@pytest.mark.asyncio
async def test_seed_levels_complete(db_session):
    """Test que se crean todos los 7 niveles desde el seed."""
    # Agregar todos los niveles del seed
    for level_data in LEVEL_DEFINITIONS:
        level = Level(**level_data)
        db_session.add(level)

    await db_session.commit()

    # Verificar que se crearon todos
    result = await db_session.execute(select(Level).order_by(Level.level))
    levels = result.scalars().all()

    assert len(levels) == 7

    # Verificar cada nivel
    assert levels[0].name == "Novato"
    assert levels[0].multiplier == 1.0

    assert levels[6].name == "Leyenda"
    assert levels[6].multiplier == 2.0
    assert levels[6].max_points is None


@pytest.mark.asyncio
async def test_seed_levels_multipliers_progressive(db_session):
    """Test que los multiplicadores son progresivos."""
    for level_data in LEVEL_DEFINITIONS:
        level = Level(**level_data)
        db_session.add(level)

    await db_session.commit()

    result = await db_session.execute(select(Level).order_by(Level.level))
    levels = result.scalars().all()

    # Verificar que los multiplicadores aumentan
    for i in range(len(levels) - 1):
        assert levels[i].multiplier < levels[i + 1].multiplier


@pytest.mark.asyncio
async def test_seed_levels_points_ranges(db_session):
    """Test que los rangos de puntos son válidos y no se solapan."""
    for level_data in LEVEL_DEFINITIONS:
        level = Level(**level_data)
        db_session.add(level)

    await db_session.commit()

    result = await db_session.execute(select(Level).order_by(Level.level))
    levels = result.scalars().all()

    for i, level in enumerate(levels[:-1]):  # Todos excepto el último
        next_level = levels[i + 1]
        # El máximo del actual debe ser menor que el mínimo del siguiente
        assert level.max_points < next_level.min_points


@pytest.mark.asyncio
async def test_level_repr(db_session):
    """Test la representación en string del nivel."""
    level = Level(
        level=4,
        name="Avanzado",
        icon="🎯",
        min_points=500,
        max_points=999,
        multiplier=1.3
    )

    repr_str = repr(level)
    assert "Level" in repr_str
    assert "level=4" in repr_str
    assert "Avanzado" in repr_str
    assert "1.3" in repr_str


@pytest.mark.asyncio
async def test_level_perks_json(db_session):
    """Test que perks se almacena como JSON."""
    perks = [
        "Multiplicador x1.5",
        "Badge exclusivo",
        "Prioridad en soporte"
    ]

    level = Level(
        level=5,
        name="Experto",
        icon="🌟",
        min_points=1000,
        max_points=2499,
        multiplier=1.5,
        perks=perks
    )

    db_session.add(level)
    await db_session.commit()
    await db_session.refresh(level)

    assert level.perks == perks
    assert isinstance(level.perks, list)
    assert len(level.perks) == 3


@pytest.mark.asyncio
async def test_level_fetch_from_db(db_session):
    """Test recuperar un nivel de la BD."""
    level = Level(
        level=2,
        name="Aprendiz",
        icon="📚",
        min_points=100,
        max_points=249,
        multiplier=1.1,
        perks=["Primer paso"]
    )

    db_session.add(level)
    await db_session.commit()

    # Recuperar de la BD
    result = await db_session.execute(
        select(Level).where(Level.level == 2)
    )
    fetched_level = result.scalar_one_or_none()

    assert fetched_level is not None
    assert fetched_level.name == "Aprendiz"
    assert fetched_level.icon == "📚"
    assert fetched_level.multiplier == 1.1


@pytest.mark.asyncio
async def test_level_all_seeds_perks_not_empty(db_session):
    """Test que todos los niveles del seed tienen perks definidos."""
    for level_data in LEVEL_DEFINITIONS:
        level = Level(**level_data)
        db_session.add(level)

    await db_session.commit()

    result = await db_session.execute(select(Level))
    levels = result.scalars().all()

    for level in levels:
        assert level.perks is not None
        assert isinstance(level.perks, list)
        assert len(level.perks) > 0
