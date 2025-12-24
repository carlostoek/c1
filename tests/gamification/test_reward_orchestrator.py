"""Tests para RewardOrchestrator."""

import pytest
from bot.gamification.database.enums import RewardType, BadgeRarity, MissionType
from bot.gamification.services.orchestrator.reward import RewardOrchestrator, REWARD_TEMPLATES


@pytest.mark.asyncio
async def test_create_reward_simple(db_session):
    """Test creación de recompensa sin unlock conditions."""
    orchestrator = RewardOrchestrator(db_session)
    
    reward_data = {
        "name": "Simple Reward",
        "description": "Test reward",
        "reward_type": RewardType.BESITOS,
        "metadata": {"amount": 100}
    }
    
    result = await orchestrator.create_reward_with_unlock_condition(
        reward_data,
        created_by=1
    )
    
    assert result['validation_errors'] == []
    assert result['reward'] is not None
    assert result['reward'].name == "Simple Reward"
    assert result['unlock_condition'] is None


@pytest.mark.asyncio
async def test_create_reward_with_mission_unlock(db_session):
    """Test recompensa con unlock condition de misión."""
    orchestrator = RewardOrchestrator(db_session)
    
    # Crear misión primero
    from bot.gamification.services.mission import MissionService
    mission_service = MissionService(db_session)
    mission = await mission_service.create_mission(
        name="Test Mission",
        description="Test",
        mission_type=MissionType.ONE_TIME,
        criteria={"type": MissionType.ONE_TIME},
        besitos_reward=100,
        created_by=1
    )
    
    reward_data = {
        "name": "Mission Reward",
        "description": "Requires mission completion",
        "reward_type": RewardType.BADGE,
        "metadata": {"icon": "🏆", "rarity": BadgeRarity.RARE}
    }
    
    result = await orchestrator.create_reward_with_unlock_condition(
        reward_data,
        unlock_mission_id=mission.id,
        created_by=1
    )
    
    assert result['validation_errors'] == []
    assert result['reward'] is not None
    assert result['unlock_condition'] == {"type": "mission", "mission_id": mission.id}


@pytest.mark.asyncio
async def test_create_reward_with_level_unlock(db_session):
    """Test recompensa con unlock condition de nivel."""
    orchestrator = RewardOrchestrator(db_session)
    
    # Crear nivel primero
    level = await orchestrator.level_service.create_level(
        name="Test Level",
        min_besitos=100,
        order=1
    )
    
    reward_data = {
        "name": "Level Reward",
        "description": "Requires level",
        "reward_type": RewardType.BADGE,
        "metadata": {"icon": "⭐", "rarity": BadgeRarity.COMMON}
    }
    
    result = await orchestrator.create_reward_with_unlock_condition(
        reward_data,
        unlock_level_id=level.id,
        created_by=1
    )
    
    assert result['validation_errors'] == []
    assert result['reward'] is not None
    assert result['unlock_condition'] == {"type": "level", "level_id": level.id}


@pytest.mark.asyncio
async def test_create_reward_with_besitos_unlock(db_session):
    """Test recompensa con unlock condition de besitos."""
    orchestrator = RewardOrchestrator(db_session)
    
    reward_data = {
        "name": "Besitos Reward",
        "description": "Requires 1000 besitos",
        "reward_type": RewardType.ITEM,
        "metadata": {"item_type": "premium"}
    }
    
    result = await orchestrator.create_reward_with_unlock_condition(
        reward_data,
        unlock_besitos=1000,
        created_by=1
    )
    
    assert result['validation_errors'] == []
    assert result['reward'] is not None
    assert result['unlock_condition'] == {"type": "besitos", "min_besitos": 1000}


@pytest.mark.asyncio
async def test_create_reward_with_multiple_unlocks(db_session):
    """Test recompensa con múltiples unlock conditions."""
    orchestrator = RewardOrchestrator(db_session)
    
    # Crear nivel
    level = await orchestrator.level_service.create_level(
        name="Level 3",
        min_besitos=500,
        order=3
    )
    
    reward_data = {
        "name": "Multi Unlock Reward",
        "description": "Requires level + besitos",
        "reward_type": RewardType.BADGE,
        "metadata": {"icon": "🔥", "rarity": BadgeRarity.EPIC}
    }
    
    result = await orchestrator.create_reward_with_unlock_condition(
        reward_data,
        unlock_level_id=level.id,
        unlock_besitos=2000,
        created_by=1
    )
    
    assert result['validation_errors'] == []
    assert result['reward'] is not None
    assert result['unlock_condition']['type'] == "multiple"
    assert len(result['unlock_condition']['conditions']) == 2


@pytest.mark.asyncio
async def test_create_reward_invalid_metadata(db_session):
    """Test validación de metadata inválida."""
    orchestrator = RewardOrchestrator(db_session)
    
    reward_data = {
        "name": "Invalid Badge",
        "description": "Invalid metadata",
        "reward_type": RewardType.BADGE,
        "metadata": {"icon": "invalid", "rarity": BadgeRarity.COMMON}  # emoji inválido
    }
    
    result = await orchestrator.create_reward_with_unlock_condition(
        reward_data,
        created_by=1
    )
    
    assert len(result['validation_errors']) > 0
    assert result['reward'] is None


@pytest.mark.asyncio
async def test_create_badge_set_success(db_session):
    """Test creación exitosa de set de badges."""
    orchestrator = RewardOrchestrator(db_session)
    
    # Crear niveles primero
    for i in range(1, 4):
        await orchestrator.level_service.create_level(
            name=f"Level {i}",
            min_besitos=i * 100,
            order=i
        )
    
    badges_data = [
        {
            "name": "Badge 1",
            "description": "Level 1",
            "icon": "🌱",
            "rarity": BadgeRarity.COMMON,
            "unlock_level_order": 1
        },
        {
            "name": "Badge 2",
            "description": "Level 2",
            "icon": "⭐",
            "rarity": BadgeRarity.COMMON,
            "unlock_level_order": 2
        },
        {
            "name": "Badge 3",
            "description": "Level 3",
            "icon": "💫",
            "rarity": BadgeRarity.RARE,
            "unlock_level_order": 3
        }
    ]
    
    result = await orchestrator.create_badge_set(
        badge_set_name="Test Badges",
        badges_data=badges_data,
        created_by=1
    )
    
    assert len(result['created_badges']) == 3
    assert len(result['failed']) == 0
    assert result['created_badges'][0].name == "Badge 1"


@pytest.mark.asyncio
async def test_create_badge_set_partial_failure(db_session):
    """Test set de badges con fallas parciales."""
    orchestrator = RewardOrchestrator(db_session)
    
    # Crear solo 1 nivel
    await orchestrator.level_service.create_level(
        name="Level 1",
        min_besitos=100,
        order=1
    )
    
    badges_data = [
        {
            "name": "Badge 1",
            "description": "Level 1",
            "icon": "🌱",
            "rarity": BadgeRarity.COMMON,
            "unlock_level_order": 1
        },
        {
            "name": "Badge 2 Missing Level",
            "description": "Level 99 doesn't exist",
            "icon": "⭐",
            "rarity": BadgeRarity.COMMON,
            "unlock_level_order": 99  # No existe
        }
    ]
    
    result = await orchestrator.create_badge_set(
        badge_set_name="Partial Badges",
        badges_data=badges_data,
        created_by=1
    )
    
    # Badge 1 se crea, Badge 2 también pero sin unlock condition
    assert len(result['created_badges']) == 2
    assert len(result['failed']) == 0


@pytest.mark.asyncio
async def test_create_from_template_level_badges(db_session):
    """Test creación desde plantilla level_badges."""
    orchestrator = RewardOrchestrator(db_session)
    
    # Crear niveles
    for i in range(1, 6):
        await orchestrator.level_service.create_level(
            name=f"Level {i}",
            min_besitos=i * 200,
            order=i
        )
    
    result = await orchestrator.create_from_template(
        "level_badges",
        created_by=1
    )
    
    assert 'created_badges' in result
    assert len(result['created_badges']) == 5
    assert result['created_badges'][0].name == "Novato"
    assert result['created_badges'][4].name == "Leyenda"


@pytest.mark.asyncio
async def test_create_from_template_welcome_pack(db_session):
    """Test creación desde plantilla welcome_pack."""
    orchestrator = RewardOrchestrator(db_session)
    
    result = await orchestrator.create_from_template(
        "welcome_pack",
        created_by=1
    )
    
    assert 'created_rewards' in result
    assert len(result['created_rewards']) == 2
    assert any("Bienvenida" in r.name for r in result['created_rewards'])
    assert any("Bonus" in r.name for r in result['created_rewards'])


@pytest.mark.asyncio
async def test_create_from_template_not_found(db_session):
    """Test error con plantilla inexistente."""
    orchestrator = RewardOrchestrator(db_session)
    
    with pytest.raises(ValueError, match="Template not found"):
        await orchestrator.create_from_template(
            "nonexistent_template",
            created_by=1
        )


@pytest.mark.asyncio
async def test_templates_exist():
    """Test que las plantillas predefinidas existen."""
    assert "level_badges" in REWARD_TEMPLATES
    assert "welcome_pack" in REWARD_TEMPLATES
