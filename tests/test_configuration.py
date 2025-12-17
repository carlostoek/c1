"""
Tests para ConfigurationService.

Verifica:
- Creación de misiones con recompensas
- Creación de badges
- Vinculación automática de recursos
- Transacciones atómicas
"""
import pytest
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.configuration import ConfigurationService, ConfigurationError
from bot.services.container import ServiceContainer
from bot.database.models import Mission, Reward, Badge, MissionType, ObjectiveType


@pytest.mark.asyncio
async def test_create_mission_complete_minimal(db_session: AsyncSession):
    """Test crear misión simple sin recompensa."""
    mock_bot = AsyncMock()
    container = ServiceContainer(db_session, mock_bot)
    config_service = ConfigurationService(db_session, container)

    mission_data = {
        "name": "Test Mission",
        "description": "A test mission",
        "icon": "🎯",
        "mission_type": "permanent",
        "objective_type": "points",
        "objective_value": 100
    }

    result = await config_service.create_mission_complete(mission_data)

    assert "mission" in result
    assert result["mission"].name == "Test Mission"
    assert result["mission"].objective_value == 100
    assert "reward" not in result


@pytest.mark.asyncio
async def test_create_mission_with_badge(db_session: AsyncSession):
    """Test crear misión con badge nuevo."""
    mock_bot = AsyncMock()
    container = ServiceContainer(db_session, mock_bot)
    config_service = ConfigurationService(db_session, container)

    mission_data = {
        "name": "Mission with Badge",
        "description": "Mission that gives a badge",
        "mission_type": "permanent",
        "objective_type": "points",
        "objective_value": 100
    }

    badge_data = {
        "name": "Test Badge",
        "emoji": "🏆",
        "description": "A test badge",
        "rarity": "rare"
    }

    reward_data = {
        "name": "Reward with Badge",
        "description": "Reward that gives a badge",
        "reward_type": "badge",
        "cost": 0,
        "limit_type": "once"
    }

    result = await config_service.create_mission_complete(
        mission_data=mission_data,
        reward_data=reward_data,
        badge_data=badge_data
    )

    assert "mission" in result
    assert "reward" in result
    assert "badge" in result
    assert result["badge"].name == "Test Badge"
    assert result["reward"].badge_id == result["badge"].id
    assert result["mission"].reward_id == result["reward"].id


@pytest.mark.asyncio
async def test_create_mission_invalid_objective_value(db_session: AsyncSession):
    """Test crear misión con valor objetivo inválido."""
    mock_bot = AsyncMock()
    container = ServiceContainer(db_session, mock_bot)
    config_service = ConfigurationService(db_session, container)

    mission_data = {
        "name": "Invalid Mission",
        "description": "Mission with invalid objective",
        "mission_type": "permanent",
        "objective_type": "points",
        "objective_value": 0  # Inválido
    }

    with pytest.raises(ConfigurationError):
        await config_service.create_mission_complete(mission_data)


@pytest.mark.asyncio
async def test_create_mission_invalid_name(db_session: AsyncSession):
    """Test crear misión sin nombre."""
    mock_bot = AsyncMock()
    container = ServiceContainer(db_session, mock_bot)
    config_service = ConfigurationService(db_session, container)

    mission_data = {
        "name": "",  # Inválido
        "description": "Mission without name",
        "mission_type": "permanent",
        "objective_type": "points",
        "objective_value": 100
    }

    with pytest.raises(ConfigurationError):
        await config_service.create_mission_complete(mission_data)


@pytest.mark.asyncio
async def test_create_reward_complete(db_session: AsyncSession):
    """Test crear recompensa con badge."""
    mock_bot = AsyncMock()
    container = ServiceContainer(db_session, mock_bot)
    config_service = ConfigurationService(db_session, container)

    reward_data = {
        "name": "Test Reward",
        "description": "A test reward",
        "icon": "🎁",
        "reward_type": "badge",
        "cost": 50,
        "limit_type": "once"
    }

    badge_data = {
        "name": "Reward Badge",
        "emoji": "⭐",
        "description": "Badge from reward",
        "rarity": "epic"
    }

    result = await config_service.create_reward_complete(
        reward_data=reward_data,
        badge_data=badge_data
    )

    assert "reward" in result
    assert "badge" in result
    assert result["reward"].badge_id == result["badge"].id


@pytest.mark.asyncio
async def test_get_existing_badges(db_session: AsyncSession):
    """Test obtener lista de badges existentes."""
    mock_bot = AsyncMock()
    container = ServiceContainer(db_session, mock_bot)
    config_service = ConfigurationService(db_session, container)

    # Primero crear un badge
    badge_data = {
        "name": "Existing Badge",
        "emoji": "✨",
        "description": "An existing badge",
        "rarity": "common"
    }
    await config_service._create_badge(badge_data)

    # Obtener lista
    badges = await config_service.get_existing_badges()
    assert len(badges) > 0
    assert any(b.name == "Existing Badge" for b in badges)


@pytest.mark.asyncio
async def test_get_badge_by_name(db_session: AsyncSession):
    """Test obtener badge por nombre."""
    mock_bot = AsyncMock()
    container = ServiceContainer(db_session, mock_bot)
    config_service = ConfigurationService(db_session, container)

    badge_data = {
        "name": "Named Badge",
        "emoji": "🎖️",
        "description": "A named badge",
        "rarity": "legendary"
    }
    created_badge = await config_service._create_badge(badge_data)

    # Buscar por nombre
    found = await config_service.get_badge_by_name("Named Badge")
    assert found is not None
    assert found.id == created_badge.id


@pytest.mark.asyncio
async def test_duplicate_badge_name(db_session: AsyncSession):
    """Test crear badge con nombre duplicado."""
    mock_bot = AsyncMock()
    container = ServiceContainer(db_session, mock_bot)
    config_service = ConfigurationService(db_session, container)

    badge_data = {
        "name": "Duplicate",
        "emoji": "📌",
        "description": "First badge",
        "rarity": "common"
    }

    # Crear primero
    await config_service._create_badge(badge_data)

    # Intentar crear otro con mismo nombre
    with pytest.raises(ConfigurationError):
        await config_service._create_badge(badge_data)


@pytest.mark.asyncio
async def test_mission_all_types(db_session: AsyncSession):
    """Test crear misiones de todos los tipos."""
    mock_bot = AsyncMock()
    container = ServiceContainer(db_session, mock_bot)
    config_service = ConfigurationService(db_session, container)

    types = ["daily", "weekly", "permanent"]

    for mission_type in types:
        mission_data = {
            "name": f"Mission {mission_type}",
            "description": f"A {mission_type} mission",
            "mission_type": mission_type,
            "objective_type": "points",
            "objective_value": 50
        }

        result = await config_service.create_mission_complete(mission_data)
        assert result["mission"].mission_type.value == mission_type


@pytest.mark.asyncio
async def test_mission_all_objective_types(db_session: AsyncSession):
    """Test crear misiones con todos los tipos de objetivo."""
    mock_bot = AsyncMock()
    container = ServiceContainer(db_session, mock_bot)
    config_service = ConfigurationService(db_session, container)

    objectives = ["points", "reactions", "level"]

    for obj_type in objectives:
        mission_data = {
            "name": f"Objective {obj_type}",
            "description": f"Objective type {obj_type}",
            "mission_type": "permanent",
            "objective_type": obj_type,
            "objective_value": 100 if obj_type != "level" else 5
        }

        result = await config_service.create_mission_complete(mission_data)
        assert result["mission"].objective_type.value == obj_type
