"""Tests para MissionOrchestrator."""

import pytest
from bot.gamification.database.enums import MissionType, RewardType, BadgeRarity
from bot.gamification.services.orchestrator.mission import MissionOrchestrator, MISSION_TEMPLATES


@pytest.mark.asyncio
async def test_validate_mission_creation_valid(db_session):
    """Test validación exitosa de datos completos."""
    orchestrator = MissionOrchestrator(db_session)
    
    mission_data = {
        "name": "Test Mission",
        "description": "Test description",
        "mission_type": MissionType.DAILY,
        "criteria": {"type": MissionType.DAILY, "count": 5},
        "besitos_reward": 100
    }
    
    is_valid, errors = await orchestrator.validate_mission_creation(mission_data)
    
    assert is_valid is True
    assert errors == []


@pytest.mark.asyncio
async def test_validate_mission_creation_invalid_criteria(db_session):
    """Test detección de criterios inválidos."""
    orchestrator = MissionOrchestrator(db_session)
    
    mission_data = {
        "name": "Test Mission",
        "description": "Test description",
        "mission_type": MissionType.DAILY,
        "criteria": {"type": MissionType.DAILY, "count": -1},  # count inválido
        "besitos_reward": 100
    }
    
    is_valid, errors = await orchestrator.validate_mission_creation(mission_data)
    
    assert is_valid is False
    assert len(errors) > 0
    assert "Invalid criteria" in errors[0]


@pytest.mark.asyncio
async def test_validate_mission_creation_duplicate_level(db_session):
    """Test detección de nivel duplicado."""
    orchestrator = MissionOrchestrator(db_session)
    
    # Crear nivel existente
    await orchestrator.level_service.create_level(
        name="Existing Level",
        min_besitos=0,
        order=1
    )
    
    mission_data = {
        "name": "Test Mission",
        "description": "Test description",
        "mission_type": MissionType.ONE_TIME,
        "criteria": {"type": MissionType.ONE_TIME},
        "besitos_reward": 100
    }
    
    auto_level_data = {
        "name": "Existing Level",  # Duplicado
        "min_besitos": 100,
        "order": 2
    }
    
    is_valid, errors = await orchestrator.validate_mission_creation(
        mission_data, auto_level_data
    )
    
    assert is_valid is False
    assert any("already exists" in e for e in errors)


@pytest.mark.asyncio
async def test_validate_mission_creation_invalid_reward_metadata(db_session):
    """Test detección de metadata inválida en recompensas."""
    orchestrator = MissionOrchestrator(db_session)
    
    mission_data = {
        "name": "Test Mission",
        "description": "Test description",
        "mission_type": MissionType.ONE_TIME,
        "criteria": {"type": MissionType.ONE_TIME},
        "besitos_reward": 100
    }
    
    rewards_data = [
        {
            "name": "Badge",
            "description": "Test badge",
            "reward_type": RewardType.BADGE,
            "metadata": {"icon": "invalid", "rarity": BadgeRarity.COMMON}  # emoji inválido
        }
    ]
    
    is_valid, errors = await orchestrator.validate_mission_creation(
        mission_data, rewards_data=rewards_data
    )
    
    assert is_valid is False
    assert any("Reward 0" in e for e in errors)


@pytest.mark.asyncio
async def test_create_mission_simple(db_session):
    """Test creación de misión sin dependencias."""
    orchestrator = MissionOrchestrator(db_session)
    
    mission_data = {
        "name": "Simple Mission",
        "description": "Test description",
        "mission_type": MissionType.ONE_TIME,
        "criteria": {"type": MissionType.ONE_TIME},
        "besitos_reward": 100,
        "repeatable": False
    }
    
    result = await orchestrator.create_mission_with_dependencies(
        mission_data,
        created_by=1
    )
    
    assert result['validation_errors'] == []
    assert result['mission'] is not None
    assert result['mission'].name == "Simple Mission"
    assert result['created_level'] is None
    assert result['created_rewards'] == []


@pytest.mark.asyncio
async def test_create_mission_with_auto_level(db_session):
    """Test creación de misión con nivel automático."""
    orchestrator = MissionOrchestrator(db_session)
    
    mission_data = {
        "name": "Mission With Level",
        "description": "Test description",
        "mission_type": MissionType.ONE_TIME,
        "criteria": {"type": MissionType.ONE_TIME},
        "besitos_reward": 100,
        "repeatable": False
    }
    
    auto_level_data = {
        "name": "New Level",
        "min_besitos": 500,
        "order": 1
    }
    
    result = await orchestrator.create_mission_with_dependencies(
        mission_data,
        auto_level_data=auto_level_data,
        created_by=1
    )
    
    assert result['validation_errors'] == []
    assert result['mission'] is not None
    assert result['created_level'] is not None
    assert result['created_level'].name == "New Level"
    assert result['mission'].auto_level_up_id == result['created_level'].id


@pytest.mark.asyncio
async def test_create_mission_with_rewards(db_session):
    """Test creación de misión con recompensas."""
    orchestrator = MissionOrchestrator(db_session)
    
    mission_data = {
        "name": "Mission With Rewards",
        "description": "Test description",
        "mission_type": MissionType.ONE_TIME,
        "criteria": {"type": MissionType.ONE_TIME},
        "besitos_reward": 100,
        "repeatable": False
    }
    
    rewards_data = [
        {
            "name": "Badge Reward",
            "description": "Test badge",
            "reward_type": RewardType.BADGE,
            "metadata": {"icon": "🏆", "rarity": BadgeRarity.EPIC}
        },
        {
            "name": "Besitos Reward",
            "description": "Extra besitos",
            "reward_type": RewardType.BESITOS,
            "metadata": {"amount": 500}
        }
    ]
    
    result = await orchestrator.create_mission_with_dependencies(
        mission_data,
        rewards_data=rewards_data,
        created_by=1
    )
    
    assert result['validation_errors'] == []
    assert result['mission'] is not None
    assert len(result['created_rewards']) == 2
    assert result['created_rewards'][0].name == "Badge Reward"
    assert result['created_rewards'][1].name == "Besitos Reward"


@pytest.mark.asyncio
async def test_create_mission_full_dependencies(db_session):
    """Test creación completa con nivel y recompensas."""
    orchestrator = MissionOrchestrator(db_session)
    
    mission_data = {
        "name": "Full Mission",
        "description": "Test description",
        "mission_type": MissionType.STREAK,
        "criteria": {"type": MissionType.STREAK, "days": 7, "require_consecutive": True},
        "besitos_reward": 500,
        "repeatable": True
    }
    
    auto_level_data = {
        "name": "Streak Master",
        "min_besitos": 1000,
        "order": 3
    }
    
    rewards_data = [
        {
            "name": "Streak Badge",
            "description": "7-day streak badge",
            "reward_type": RewardType.BADGE,
            "metadata": {"icon": "🔥", "rarity": BadgeRarity.RARE}
        }
    ]
    
    result = await orchestrator.create_mission_with_dependencies(
        mission_data,
        auto_level_data=auto_level_data,
        rewards_data=rewards_data,
        created_by=1
    )
    
    assert result['validation_errors'] == []
    assert result['mission'] is not None
    assert result['created_level'] is not None
    assert len(result['created_rewards']) == 1
    assert result['mission'].auto_level_up_id == result['created_level'].id


@pytest.mark.asyncio
async def test_create_from_template_welcome(db_session):
    """Test creación desde plantilla 'welcome'."""
    orchestrator = MissionOrchestrator(db_session)
    
    result = await orchestrator.create_from_template(
        "welcome",
        created_by=1
    )
    
    assert result['validation_errors'] == []
    assert result['mission'] is not None
    assert result['mission'].name == "Bienvenido al Sistema"
    assert result['created_level'] is not None
    assert result['created_level'].name == "Nuevo Usuario"
    assert len(result['created_rewards']) == 1


@pytest.mark.asyncio
async def test_create_from_template_weekly_streak(db_session):
    """Test creación desde plantilla 'weekly_streak'."""
    orchestrator = MissionOrchestrator(db_session)
    
    result = await orchestrator.create_from_template(
        "weekly_streak",
        created_by=1
    )
    
    assert result['validation_errors'] == []
    assert result['mission'] is not None
    assert result['mission'].name == "Racha de 7 Días"
    assert result['mission'].mission_type == MissionType.STREAK
    assert result['mission'].besitos_reward == 500


@pytest.mark.asyncio
async def test_create_from_template_daily_reactor(db_session):
    """Test creación desde plantilla 'daily_reactor'."""
    orchestrator = MissionOrchestrator(db_session)
    
    result = await orchestrator.create_from_template(
        "daily_reactor",
        created_by=1
    )
    
    assert result['validation_errors'] == []
    assert result['mission'] is not None
    assert result['mission'].name == "Reactor Diario"
    assert result['mission'].mission_type == MissionType.DAILY


@pytest.mark.asyncio
async def test_create_from_template_customize(db_session):
    """Test customización de plantilla."""
    orchestrator = MissionOrchestrator(db_session)
    
    customize = {
        "besitos_reward": 1000,
        "name": "Custom Welcome",
        "description": "Custom description"
    }
    
    result = await orchestrator.create_from_template(
        "welcome",
        customize=customize,
        created_by=1
    )
    
    assert result['validation_errors'] == []
    assert result['mission'] is not None
    assert result['mission'].besitos_reward == 1000
    assert result['mission'].name == "Custom Welcome"
    assert result['mission'].description == "Custom description"


@pytest.mark.asyncio
async def test_create_from_template_not_found(db_session):
    """Test error con plantilla inexistente."""
    orchestrator = MissionOrchestrator(db_session)
    
    with pytest.raises(ValueError, match="Template not found"):
        await orchestrator.create_from_template(
            "nonexistent_template",
            created_by=1
        )


@pytest.mark.asyncio
async def test_templates_exist():
    """Test que las plantillas predefinidas existen."""
    assert "welcome" in MISSION_TEMPLATES
    assert "weekly_streak" in MISSION_TEMPLATES
    assert "daily_reactor" in MISSION_TEMPLATES
