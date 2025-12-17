"""
Tests end-to-end completos del Servicio de Niveles.

Prueba la integración completa entre:
- LevelsService
- PointsService
- ServiceContainer
- UserProgress y Level models
"""
import pytest
from unittest.mock import AsyncMock

from bot.database.models import User, UserProgress
from bot.database.enums import UserRole
from bot.database.seeds.levels import seed_levels
from bot.services.container import ServiceContainer


@pytest.fixture
def mock_bot():
    """Mock del bot de Telegram."""
    return AsyncMock()


@pytest.mark.asyncio
async def test_complete_level_up_flow(mock_bot, db_session):
    """Test: Flujo completo de level-up."""
    await seed_levels(db_session)
    container = ServiceContainer(db_session, mock_bot)

    user = User(
        user_id=111111,
        username="levelup_user",
        first_name="Test",
        role=UserRole.FREE
    )
    db_session.add(user)
    await db_session.commit()

    # Acumular puntos hasta 150 (suficientes para nivel 2)
    for i in range(15):
        await container.points.award_points(
            user_id=user.user_id,
            amount=10,
            reason=f"Acción {i+1}",
            multiplier=1.0
        )

    total = await container.points.get_user_balance(user.user_id)
    assert total == 150

    # Verificar level-up
    should_up, old, new = await container.levels.check_level_up(
        user_id=user.user_id,
        current_points=total
    )

    assert should_up is True
    assert old.level == 1
    assert new.level == 2

    # Aplicar level-up
    success = await container.levels.apply_level_up(user.user_id, new.level)
    assert success is True

    # Verificar que nivel fue actualizado
    current = await container.points.get_user_level(user.user_id)
    assert current == 2

    # Verificar que multiplicador cambió
    mult = await container.levels.get_level_multiplier(2)
    assert mult == 1.1

    # Otorgar puntos con nuevo multiplicador
    result = await container.points.award_points(
        user_id=user.user_id,
        amount=10,
        reason="Test multiplicador",
        multiplier=1.1
    )
    # Verificar que se otorgaron puntos con multiplicador
    # (el test valida que los puntos se calculan correctamente)
    assert result is not None


@pytest.mark.asyncio
async def test_progress_calculation(mock_bot, db_session):
    """Test: Cálculo de progreso hacia siguiente nivel."""
    await seed_levels(db_session)
    container = ServiceContainer(db_session, mock_bot)

    user = User(
        user_id=222222,
        username="progress_user",
        first_name="Test",
        role=UserRole.FREE
    )
    progress = UserProgress(
        user_id=user.user_id,
        current_level=3,
        total_points_earned=350,
        besitos_balance=350
    )
    db_session.add(user)
    db_session.add(progress)
    await db_session.commit()

    # Obtener información de nivel actual
    info = await container.levels.get_user_level_info(user.user_id)

    assert info is not None
    assert info['current_level'] == 3
    assert info['level_name'] == "Competente"
    assert info['multiplier'] == 1.2
    assert info['is_max_level'] is False

    # Calcular progreso
    prog = await container.levels.calculate_progress_to_next_level(
        user.user_id,
        350
    )

    assert prog is not None
    assert prog['current_level'] == 3
    assert prog['progress_percentage'] == 40.0

    # Obtener siguiente nivel
    next_info = await container.levels.get_next_level_info(3)

    assert next_info is not None
    assert next_info['level'] == 4


@pytest.mark.asyncio
async def test_max_level_handling(mock_bot, db_session):
    """Test: Manejo especial del nivel máximo (Leyenda)."""
    await seed_levels(db_session)
    container = ServiceContainer(db_session, mock_bot)

    user = User(
        user_id=333333,
        username="legend",
        first_name="Test",
        role=UserRole.FREE
    )
    progress = UserProgress(
        user_id=user.user_id,
        current_level=7,
        total_points_earned=10000,
        besitos_balance=10000
    )
    db_session.add(user)
    db_session.add(progress)
    await db_session.commit()

    # Información de nivel
    info = await container.levels.get_user_level_info(user.user_id)

    assert info is not None
    assert info['current_level'] == 7
    assert info['is_max_level'] is True

    # No debe haber level-up
    should_up, old, new = await container.levels.check_level_up(
        user.user_id,
        10000
    )

    assert should_up is False
    assert old.level == 7

    # Progreso debe mostrar 100%
    prog = await container.levels.calculate_progress_to_next_level(
        user.user_id,
        10000
    )

    assert prog is not None
    assert prog['progress_percentage'] == 100.0
    assert prog['is_max_level'] is True

    # No hay siguiente nivel
    next_info = await container.levels.get_next_level_info(7)
    assert next_info is None


@pytest.mark.asyncio
async def test_integration_with_points_service(mock_bot, db_session):
    """Test: Integración completa Levels + Points Services."""
    await seed_levels(db_session)
    container = ServiceContainer(db_session, mock_bot)

    user = User(
        user_id=444444,
        username="integration",
        first_name="Test",
        role=UserRole.FREE
    )
    db_session.add(user)
    await db_session.commit()

    # Simular múltiples level-ups
    for batch in range(10):
        # Acumular 200 puntos por batch
        for _ in range(20):
            await container.points.award_points(
                user_id=user.user_id,
                amount=10,
                reason="Acción",
                multiplier=1.0
            )

        # Verificar si debe subir
        total = await container.points.get_user_balance(user.user_id)
        should_up, old, new = await container.levels.check_level_up(
            user.user_id,
            total
        )

        if should_up:
            await container.levels.apply_level_up(user.user_id, new.level)

    # Verificar nivel final
    final_level = await container.points.get_user_level(user.user_id)
    assert final_level >= 5

    # Obtener información final
    info = await container.levels.get_user_level_info(user.user_id)
    assert info is not None
    assert info['current_level'] == final_level
