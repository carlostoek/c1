"""
Tests de integración para ConfigurationService.
"""
import pytest
from bot.database.engine import init_db, close_db, get_session_factory
from bot.services.configuration.service import ConfigurationService


@pytest.fixture
async def session():
    """Fixture de sesión de BD."""
    await init_db()
    factory = get_session_factory()
    async with factory() as session:
        yield session
        await session.rollback()
    await close_db()


@pytest.mark.asyncio
async def test_create_mission_complete(session):
    """Test de nested creation completa."""
    service = ConfigurationService(session)
    
    # Crear misión completa
    mission, reward, badge = await service.create_mission_complete(
        name="Test Mission",
        mission_type="single",
        target_value=5,
        target_action="message_reacted",
        reward_name="Test Reward",
        reward_type="both",
        reward_points=50,
        badge_key="test_badge",
        badge_name="Test Badge",
        badge_icon="🧪"
    )
    
    # Verificar creación
    assert mission.id is not None
    assert reward.id is not None
    assert badge.id is not None
    
    # Verificar relaciones
    assert mission.reward_id == reward.id
    assert reward.badge_id == badge.id
    
    # Verificar datos
    assert mission.name == "Test Mission"
    assert reward.points_amount == 50
    assert badge.badge_key == "test_badge"


@pytest.mark.asyncio
async def test_cache_invalidation(session):
    """Test de invalidación de cache."""
    service = ConfigurationService(session)
    
    # Primera llamada - llena cache
    actions1 = await service.list_actions()
    
    # Crear nueva acción
    await service.create_action(
        action_key="test_cache",
        display_name="Test Cache",
        points_amount=10
    )
    
    # Segunda llamada - debe tener la nueva
    actions2 = await service.list_actions()
    
    assert len(actions2) == len(actions1) + 1


@pytest.mark.asyncio
async def test_transaction_rollback(session):
    """Test de rollback en caso de error."""
    service = ConfigurationService(session)

    # Intentar crear con badge_key duplicado debe fallar
    await service.create_badge(
        badge_key="unique_badge",
        name="First",
        icon="1️⃣",
        requirement_type="total_points",
        requirement_value=100
    )

    initial_badge_count = len(await service.list_badges())

    with pytest.raises(Exception):
        # Este debe fallar por key duplicada
        await service.create_reward_with_new_badge(
            name="Test Reward",
            reward_type="badge",
            badge_key="unique_badge",  # Duplicado
            badge_name="Duplicate",
            badge_icon="❌"
        )

    # Verificar que no se creó ni el badge ni la recompensa
    final_badge_count = len(await service.list_badges())
    assert initial_badge_count == final_badge_count