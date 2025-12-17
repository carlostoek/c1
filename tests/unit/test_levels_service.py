"""
Tests para LevelsService - Servicio de gestión de niveles.

Prueba:
- get_all_levels() - Obtener todos los niveles
- get_level_by_number() - Obtener nivel específico
- get_level_for_points() - Obtener nivel por puntos
- get_level_multiplier() - Obtener multiplicador
- check_level_up() - Verificar level-up
- apply_level_up() - Aplicar level-up
- Cache functionality
"""
import pytest

from sqlalchemy import select

from bot.database.models import Level, User, UserProgress
from bot.database.seeds.levels import LEVEL_DEFINITIONS
from bot.database.enums import UserRole
from bot.services.levels import LevelsService


@pytest.mark.asyncio
async def test_get_all_levels(db_session):
    """Test obtener todos los niveles."""
    # Agregar niveles
    for level_data in LEVEL_DEFINITIONS:
        level = Level(**level_data)
        db_session.add(level)
    await db_session.commit()

    service = LevelsService(db_session)
    levels = await service.get_all_levels()

    assert len(levels) == 7
    assert levels[0].level == 1
    assert levels[6].level == 7


@pytest.mark.asyncio
async def test_get_all_levels_cache(db_session):
    """Test que get_all_levels cachea resultados."""
    # Agregar niveles
    for level_data in LEVEL_DEFINITIONS:
        level = Level(**level_data)
        db_session.add(level)
    await db_session.commit()

    service = LevelsService(db_session)

    # Primera llamada carga desde BD
    levels1 = await service.get_all_levels(use_cache=True)
    # Segunda llamada debe usar cache (sin hit a BD)
    levels2 = await service.get_all_levels(use_cache=True)

    assert len(levels1) == 7
    assert len(levels2) == 7
    assert levels1[0].id == levels2[0].id


@pytest.mark.asyncio
async def test_get_all_levels_no_cache(db_session):
    """Test get_all_levels sin cacheo."""
    # Agregar niveles
    for level_data in LEVEL_DEFINITIONS:
        level = Level(**level_data)
        db_session.add(level)
    await db_session.commit()

    service = LevelsService(db_session)
    levels = await service.get_all_levels(use_cache=False)

    assert len(levels) == 7


@pytest.mark.asyncio
async def test_get_level_by_number(db_session):
    """Test obtener nivel por número."""
    # Agregar niveles
    for level_data in LEVEL_DEFINITIONS:
        level = Level(**level_data)
        db_session.add(level)
    await db_session.commit()

    service = LevelsService(db_session)

    # Obtener nivel 5
    level_5 = await service.get_level_by_number(5)

    assert level_5 is not None
    assert level_5.level == 5
    assert level_5.name == "Experto"


@pytest.mark.asyncio
async def test_get_level_by_number_not_found(db_session):
    """Test get_level_by_number cuando no existe."""
    for level_data in LEVEL_DEFINITIONS:
        level = Level(**level_data)
        db_session.add(level)
    await db_session.commit()

    service = LevelsService(db_session)
    level = await service.get_level_by_number(99)

    assert level is None


@pytest.mark.asyncio
async def test_get_level_for_points_novato(db_session):
    """Test get_level_for_points retorna Novato (0-99)."""
    for level_data in LEVEL_DEFINITIONS:
        level = Level(**level_data)
        db_session.add(level)
    await db_session.commit()

    service = LevelsService(db_session)
    level = await service.get_level_for_points(50)

    assert level.level == 1
    assert level.name == "Novato"


@pytest.mark.asyncio
async def test_get_level_for_points_aprendiz(db_session):
    """Test get_level_for_points retorna Aprendiz (100-249)."""
    for level_data in LEVEL_DEFINITIONS:
        level = Level(**level_data)
        db_session.add(level)
    await db_session.commit()

    service = LevelsService(db_session)
    level = await service.get_level_for_points(150)

    assert level.level == 2
    assert level.name == "Aprendiz"


@pytest.mark.asyncio
async def test_get_level_for_points_leyenda(db_session):
    """Test get_level_for_points retorna Leyenda (5000+)."""
    for level_data in LEVEL_DEFINITIONS:
        level = Level(**level_data)
        db_session.add(level)
    await db_session.commit()

    service = LevelsService(db_session)
    level = await service.get_level_for_points(10000)

    assert level.level == 7
    assert level.name == "Leyenda"


@pytest.mark.asyncio
async def test_get_level_multiplier(db_session):
    """Test obtener multiplicador de nivel."""
    for level_data in LEVEL_DEFINITIONS:
        level = Level(**level_data)
        db_session.add(level)
    await db_session.commit()

    service = LevelsService(db_session)

    mult_1 = await service.get_level_multiplier(1)
    mult_5 = await service.get_level_multiplier(5)
    mult_7 = await service.get_level_multiplier(7)

    assert mult_1 == 1.0
    assert mult_5 == 1.5
    assert mult_7 == 2.0


@pytest.mark.asyncio
async def test_get_level_multiplier_not_found(db_session):
    """Test get_level_multiplier cuando nivel no existe."""
    for level_data in LEVEL_DEFINITIONS:
        level = Level(**level_data)
        db_session.add(level)
    await db_session.commit()

    service = LevelsService(db_session)
    mult = await service.get_level_multiplier(99)

    # Retorna 1.0 por defecto
    assert mult == 1.0


@pytest.mark.asyncio
async def test_check_level_up_true(db_session):
    """Test check_level_up cuando debe subir de nivel."""
    # Agregar niveles
    for level_data in LEVEL_DEFINITIONS:
        level = Level(**level_data)
        db_session.add(level)

    # Crear usuario y progreso
    user = User(user_id=123, username="test", first_name="Test", role=UserRole.FREE)
    progress = UserProgress(
        user_id=123,
        current_level=1,
        besitos_balance=0,
        total_points_earned=0
    )
    db_session.add(user)
    db_session.add(progress)
    await db_session.commit()

    service = LevelsService(db_session)

    # Verificar level-up: de nivel 1 (0-99) a nivel 2 (100-249) con 150 puntos
    should_up, old, new = await service.check_level_up(123, 150)

    assert should_up is True
    assert old.level == 1
    assert new.level == 2


@pytest.mark.asyncio
async def test_check_level_up_false(db_session):
    """Test check_level_up cuando NO debe subir."""
    # Agregar niveles
    for level_data in LEVEL_DEFINITIONS:
        level = Level(**level_data)
        db_session.add(level)

    # Crear usuario en nivel 2
    user = User(user_id=124, username="test2", first_name="Test", role=UserRole.FREE)
    progress = UserProgress(
        user_id=124,
        current_level=2,
        besitos_balance=0,
        total_points_earned=100
    )
    db_session.add(user)
    db_session.add(progress)
    await db_session.commit()

    service = LevelsService(db_session)

    # Verificar sin level-up: ya en nivel 2 con 150 puntos (sigue en 2)
    should_up, old, new = await service.check_level_up(124, 150)

    assert should_up is False
    assert old.level == 2
    assert new.level == 2


@pytest.mark.asyncio
async def test_check_level_up_multiple_levels(db_session):
    """Test check_level_up saltando múltiples niveles."""
    # Agregar niveles
    for level_data in LEVEL_DEFINITIONS:
        level = Level(**level_data)
        db_session.add(level)

    # Crear usuario en nivel 1
    user = User(user_id=125, username="test3", first_name="Test", role=UserRole.FREE)
    progress = UserProgress(
        user_id=125,
        current_level=1,
        besitos_balance=0,
        total_points_earned=0
    )
    db_session.add(user)
    db_session.add(progress)
    await db_session.commit()

    service = LevelsService(db_session)

    # Saltar a nivel 5 (1000 puntos)
    should_up, old, new = await service.check_level_up(125, 1000)

    assert should_up is True
    assert old.level == 1
    assert new.level == 5


@pytest.mark.asyncio
async def test_check_level_up_user_not_found(db_session):
    """Test check_level_up cuando usuario no existe."""
    for level_data in LEVEL_DEFINITIONS:
        level = Level(**level_data)
        db_session.add(level)
    await db_session.commit()

    service = LevelsService(db_session)
    should_up, old, new = await service.check_level_up(99999, 150)

    assert should_up is False
    assert old is None
    assert new is None


@pytest.mark.asyncio
async def test_apply_level_up(db_session):
    """Test aplicar level-up actualiza UserProgress."""
    # Agregar niveles
    for level_data in LEVEL_DEFINITIONS:
        level = Level(**level_data)
        db_session.add(level)

    # Crear usuario
    user = User(user_id=126, username="test4", first_name="Test", role=UserRole.FREE)
    progress = UserProgress(
        user_id=126,
        current_level=1,
        besitos_balance=0,
        total_points_earned=0
    )
    db_session.add(user)
    db_session.add(progress)
    await db_session.commit()

    service = LevelsService(db_session)

    # Aplicar level-up a nivel 3
    success = await service.apply_level_up(126, 3)

    assert success is True

    # Verificar que se actualizó
    result = await db_session.execute(
        select(UserProgress).where(UserProgress.user_id == 126)
    )
    updated_progress = result.scalar_one()

    assert updated_progress.current_level == 3


@pytest.mark.asyncio
async def test_apply_level_up_user_not_found(db_session):
    """Test apply_level_up cuando usuario no existe."""
    for level_data in LEVEL_DEFINITIONS:
        level = Level(**level_data)
        db_session.add(level)
    await db_session.commit()

    service = LevelsService(db_session)
    success = await service.apply_level_up(99999, 3)

    assert success is False


@pytest.mark.asyncio
async def test_clear_cache(db_session):
    """Test limpiar cache de niveles."""
    for level_data in LEVEL_DEFINITIONS:
        level = Level(**level_data)
        db_session.add(level)
    await db_session.commit()

    service = LevelsService(db_session)

    # Cargar y cachear
    await service.get_all_levels()
    assert service._levels_cache is not None

    # Limpiar cache
    await service.clear_cache()
    assert service._levels_cache is None
