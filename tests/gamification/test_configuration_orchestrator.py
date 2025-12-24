"""Tests para ConfigurationOrchestrator."""

import pytest
from bot.gamification.database.enums import MissionType, RewardType, BadgeRarity
from bot.gamification.services.orchestrator.configuration import (
    ConfigurationOrchestrator,
    SYSTEM_TEMPLATES
)


@pytest.mark.asyncio
async def test_validate_complete_config_valid(db_session):
    """Test validación exitosa de configuración completa."""
    orchestrator = ConfigurationOrchestrator(db_session)

    config = {
        "mission": {
            "name": "Test Mission",
            "description": "Test description",
            "mission_type": MissionType.DAILY,
            "criteria": {"type": MissionType.DAILY, "count": 5},
            "besitos_reward": 100
        }
    }

    is_valid, errors = await orchestrator.validate_complete_config(config)

    assert is_valid is True
    assert errors == []


@pytest.mark.asyncio
async def test_validate_complete_config_missing_mission(db_session):
    """Test validación fallida cuando falta configuración de misión."""
    orchestrator = ConfigurationOrchestrator(db_session)

    config = {}  # Sin misión

    is_valid, errors = await orchestrator.validate_complete_config(config)

    assert is_valid is False
    assert "Missing mission configuration" in errors


@pytest.mark.asyncio
async def test_validate_complete_config_incoherent_besitos(db_session):
    """Test validación fallida por besitos incoherentes."""
    orchestrator = ConfigurationOrchestrator(db_session)

    config = {
        "mission": {
            "name": "Test Mission",
            "description": "Test description",
            "mission_type": MissionType.ONE_TIME,
            "criteria": {"type": MissionType.ONE_TIME},
            "besitos_reward": 100  # Menos que el nivel requiere
        },
        "auto_level": {
            "name": "High Level",
            "min_besitos": 500,  # Requiere más besitos que la misión da
            "order": 1
        }
    }

    is_valid, errors = await orchestrator.validate_complete_config(config)

    assert is_valid is False
    assert any("less than level requirement" in e for e in errors)


@pytest.mark.asyncio
async def test_create_complete_mission_system_simple(db_session):
    """Test creación de sistema simple (solo misión)."""
    orchestrator = ConfigurationOrchestrator(db_session)

    config = {
        "mission": {
            "name": "Simple Mission",
            "description": "Test description",
            "mission_type": MissionType.ONE_TIME,
            "criteria": {"type": MissionType.ONE_TIME},
            "besitos_reward": 100
        }
    }

    result = await orchestrator.create_complete_mission_system(
        config,
        created_by=1
    )

    assert 'validation_errors' not in result or result['validation_errors'] == []
    assert result['mission'] is not None
    assert result['mission'].name == "Simple Mission"
    assert result['created_level'] is None
    assert result['created_rewards'] == []
    assert 'summary' in result


@pytest.mark.asyncio
async def test_create_complete_mission_system_with_level(db_session):
    """Test creación de sistema con nivel automático."""
    orchestrator = ConfigurationOrchestrator(db_session)

    config = {
        "mission": {
            "name": "Mission With Level",
            "description": "Test description",
            "mission_type": MissionType.ONE_TIME,
            "criteria": {"type": MissionType.ONE_TIME},
            "besitos_reward": 500
        },
        "auto_level": {
            "name": "New Level",
            "min_besitos": 500,
            "order": 1
        }
    }

    result = await orchestrator.create_complete_mission_system(
        config,
        created_by=1
    )

    assert result['mission'] is not None
    assert result['created_level'] is not None
    assert result['created_level'].name == "New Level"
    assert 'summary' in result
    assert "Nivel creado" in result['summary']


@pytest.mark.asyncio
async def test_create_complete_mission_system_with_rewards(db_session):
    """Test creación de sistema con recompensas."""
    orchestrator = ConfigurationOrchestrator(db_session)

    config = {
        "mission": {
            "name": "Mission With Rewards",
            "description": "Test description",
            "mission_type": MissionType.STREAK,
            "criteria": {"type": MissionType.STREAK, "days": 7, "require_consecutive": True},
            "besitos_reward": 500
        },
        "rewards": [
            {
                "name": "Streak Badge",
                "description": "Badge for 7-day streak",
                "reward_type": RewardType.BADGE,
                "metadata": {"icon": "🔥", "rarity": BadgeRarity.RARE}
            }
        ]
    }

    result = await orchestrator.create_complete_mission_system(
        config,
        created_by=1
    )

    assert result['mission'] is not None
    assert len(result['created_rewards']) == 1
    assert result['created_rewards'][0].name == "Streak Badge"
    assert 'summary' in result
    assert "Recompensas creadas" in result['summary']


@pytest.mark.asyncio
async def test_create_complete_mission_system_full(db_session):
    """Test creación de sistema completo (misión + nivel + recompensas)."""
    orchestrator = ConfigurationOrchestrator(db_session)

    config = {
        "mission": {
            "name": "Complete System",
            "description": "Full test",
            "mission_type": MissionType.STREAK,
            "criteria": {"type": MissionType.STREAK, "days": 7, "require_consecutive": True},
            "besitos_reward": 1000
        },
        "auto_level": {
            "name": "Streak Master",
            "min_besitos": 1000,
            "order": 5
        },
        "rewards": [
            {
                "name": "Fire Badge",
                "description": "Streak badge",
                "reward_type": RewardType.BADGE,
                "metadata": {"icon": "🔥", "rarity": BadgeRarity.EPIC}
            },
            {
                "name": "Bonus Besitos",
                "description": "Extra besitos",
                "reward_type": RewardType.BESITOS,
                "metadata": {"amount": 500}
            }
        ]
    }

    result = await orchestrator.create_complete_mission_system(
        config,
        created_by=1
    )

    assert result['mission'] is not None
    assert result['created_level'] is not None
    assert len(result['created_rewards']) == 2
    assert 'summary' in result
    assert "CONFIGURACIÓN COMPLETA" in result['summary']
    assert result['mission'].name in result['summary']


@pytest.mark.asyncio
async def test_generate_summary(db_session):
    """Test generación de resumen formateado."""
    orchestrator = ConfigurationOrchestrator(db_session)

    # Crear datos primero
    config = {
        "mission": {
            "name": "Test Mission",
            "description": "Test",
            "mission_type": MissionType.ONE_TIME,
            "criteria": {"type": MissionType.ONE_TIME},
            "besitos_reward": 100
        },
        "auto_level": {
            "name": "Test Level",
            "min_besitos": 100,
            "order": 1
        },
        "rewards": [
            {
                "name": "Test Badge",
                "description": "Test badge",
                "reward_type": RewardType.BADGE,
                "metadata": {"icon": "🏆", "rarity": BadgeRarity.COMMON}
            }
        ]
    }

    result = await orchestrator.create_complete_mission_system(config, created_by=1)
    summary = result['summary']

    # Verificar formato
    assert "🎉" in summary
    assert "CONFIGURACIÓN COMPLETA" in summary
    assert "✅ Misión creada" in summary
    assert "Test Mission" in summary
    assert "✅ Nivel creado" in summary
    assert "Test Level" in summary
    assert "✅ Recompensas creadas" in summary
    assert "Test Badge" in summary
    assert "Los usuarios ahora pueden:" in summary


@pytest.mark.asyncio
async def test_apply_system_template_starter_pack(db_session):
    """Test aplicación de plantilla starter_pack."""
    orchestrator = ConfigurationOrchestrator(db_session)

    result = await orchestrator.apply_system_template(
        "starter_pack",
        created_by=1
    )

    # Verificar que se crearon las entidades
    assert len(result['missions_created']) >= 1
    assert len(result['levels_created']) >= 3  # Novato, Regular, Entusiasta + badges
    assert len(result['rewards_created']) >= 1

    # Verificar resumen
    assert 'summary' in result
    assert "starter_pack" in result['summary']
    assert "Creado:" in result['summary']


@pytest.mark.asyncio
async def test_apply_system_template_engagement_system(db_session):
    """Test aplicación de plantilla engagement_system."""
    orchestrator = ConfigurationOrchestrator(db_session)

    result = await orchestrator.apply_system_template(
        "engagement_system",
        created_by=1
    )

    # Verificar misiones creadas
    assert len(result['missions_created']) == 2  # Reactor Diario + Racha Semanal

    # Verificar que la racha tiene badge
    assert len(result['rewards_created']) >= 1

    # Verificar nombres
    mission_names = [m.name for m in result['missions_created']]
    assert "Reactor Diario" in mission_names
    assert "Racha Semanal" in mission_names


@pytest.mark.asyncio
async def test_apply_system_template_not_found(db_session):
    """Test error con plantilla inexistente."""
    orchestrator = ConfigurationOrchestrator(db_session)

    with pytest.raises(ValueError, match="Template not found"):
        await orchestrator.apply_system_template(
            "nonexistent_template",
            created_by=1
        )


@pytest.mark.asyncio
async def test_system_templates_exist():
    """Test que las plantillas de sistema existen."""
    assert "starter_pack" in SYSTEM_TEMPLATES
    assert "engagement_system" in SYSTEM_TEMPLATES

    # Verificar estructura de starter_pack
    starter = SYSTEM_TEMPLATES["starter_pack"]
    assert "description" in starter
    assert "missions" in starter
    assert "additional_levels" in starter
    assert starter["level_badges"] is True

    # Verificar estructura de engagement_system
    engagement = SYSTEM_TEMPLATES["engagement_system"]
    assert "description" in engagement
    assert "missions" in engagement
    assert len(engagement["missions"]) == 2


@pytest.mark.asyncio
async def test_create_complete_mission_system_invalid_config(db_session):
    """Test que retorna validation_errors cuando config es inválida."""
    orchestrator = ConfigurationOrchestrator(db_session)

    config = {
        "mission": {
            "name": "Invalid Mission",
            "description": "Test",
            "mission_type": MissionType.DAILY,
            "criteria": {"type": MissionType.DAILY, "count": -1},  # count inválido
            "besitos_reward": 100
        }
    }

    result = await orchestrator.create_complete_mission_system(config, created_by=1)

    assert 'validation_errors' in result
    assert len(result['validation_errors']) > 0
