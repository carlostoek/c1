"""Tests para el sistema de plantillas de configuración."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.gamification.utils.templates import (
    SYSTEM_TEMPLATES,
    apply_template,
    get_template_info,
    list_templates,
)
from bot.gamification.services.level import LevelService
from bot.gamification.services.mission import MissionService
from bot.gamification.services.reward import RewardService


@pytest.mark.asyncio
async def test_system_templates_structure():
    """Verifica estructura de plantillas predefinidas."""
    assert "starter" in SYSTEM_TEMPLATES
    assert "engagement" in SYSTEM_TEMPLATES
    assert "progression" in SYSTEM_TEMPLATES

    # Verificar starter
    starter = SYSTEM_TEMPLATES["starter"]
    assert starter["name"] == "Sistema Inicial"
    assert "components" in starter
    assert "levels" in starter["components"]
    assert "missions" in starter["components"]
    assert "rewards" in starter["components"]

    # Verificar engagement
    engagement = SYSTEM_TEMPLATES["engagement"]
    assert engagement["name"] == "Sistema de Engagement"
    assert "missions" in engagement["components"]

    # Verificar progression
    progression = SYSTEM_TEMPLATES["progression"]
    assert progression["name"] == "Sistema de Progresión"
    assert "levels" in progression["components"]
    assert len(progression["components"]["levels"]) == 6


@pytest.mark.asyncio
async def test_get_template_info():
    """Verifica obtención de información de plantilla."""
    # Template existente
    info = get_template_info("starter")
    assert info is not None
    assert info["name"] == "Sistema Inicial"
    assert info["levels_count"] == 3
    assert info["missions_count"] == 1
    assert info["rewards_count"] == 1

    # Template inexistente
    info = get_template_info("nonexistent")
    assert info is None


@pytest.mark.asyncio
async def test_list_templates():
    """Verifica listado de plantillas."""
    templates = list_templates()
    assert len(templates) == 3

    # Verificar que todas tienen la estructura correcta
    for template in templates:
        assert "key" in template
        assert "name" in template
        assert "description" in template
        assert "levels_count" in template
        assert "missions_count" in template
        assert "rewards_count" in template


@pytest.mark.asyncio
async def test_apply_starter_template(db_session: AsyncSession):
    """Verifica aplicación de plantilla starter."""
    result = await apply_template("starter", db_session, created_by=123)

    # Verificar resultado
    assert "created_levels" in result
    assert "created_missions" in result
    assert "created_rewards" in result
    assert "summary" in result

    # Verificar cantidades
    assert len(result["created_levels"]) == 3
    assert len(result["created_missions"]) == 1
    assert len(result["created_rewards"]) == 1

    # Verificar que se crearon en BD
    level_service = LevelService(db_session)
    levels = await level_service.get_all_levels()
    assert len(levels) == 3

    mission_service = MissionService(db_session)
    missions = await mission_service.get_all_missions()
    assert len(missions) == 1
    assert missions[0].name == "Bienvenido"

    reward_service = RewardService(db_session)
    rewards = await reward_service.get_all_rewards()
    assert len(rewards) == 1
    assert rewards[0].name == "Primer Paso"


@pytest.mark.asyncio
async def test_apply_engagement_template(db_session: AsyncSession):
    """Verifica aplicación de plantilla engagement."""
    result = await apply_template("engagement", db_session, created_by=456)

    # Verificar resultado
    assert len(result["created_levels"]) == 0
    assert len(result["created_missions"]) == 2
    assert len(result["created_rewards"]) == 1

    # Verificar misiones en BD
    mission_service = MissionService(db_session)
    missions = await mission_service.get_all_missions()
    assert len(missions) == 2

    mission_names = [m.name for m in missions]
    assert "Reactor Diario" in mission_names
    assert "Racha de 7 Días" in mission_names


@pytest.mark.asyncio
async def test_apply_progression_template(db_session: AsyncSession):
    """Verifica aplicación de plantilla progression."""
    result = await apply_template("progression", db_session, created_by=789)

    # Verificar resultado
    assert len(result["created_levels"]) == 6
    assert len(result["created_missions"]) == 0
    # 6 badges (uno por nivel) automáticamente
    assert len(result["created_rewards"]) == 6

    # Verificar niveles en BD
    level_service = LevelService(db_session)
    levels = await level_service.get_all_levels()
    assert len(levels) == 6

    level_names = [l.name for l in levels]
    assert "Novato" in level_names
    assert "Leyenda" in level_names

    # Verificar badges en BD
    reward_service = RewardService(db_session)
    rewards = await reward_service.get_all_rewards()
    assert len(rewards) == 6


@pytest.mark.asyncio
async def test_apply_invalid_template(db_session: AsyncSession):
    """Verifica error al aplicar plantilla inexistente."""
    with pytest.raises(ValueError, match="Template not found"):
        await apply_template("nonexistent", db_session, created_by=999)


@pytest.mark.asyncio
async def test_template_transaction_rollback(db_session: AsyncSession):
    """Verifica rollback en caso de error durante aplicación."""
    # Aplicar starter primero
    await apply_template("starter", db_session, created_by=111)

    # Intentar aplicar starter de nuevo (debería fallar por duplicados)
    with pytest.raises(Exception):
        await apply_template("starter", db_session, created_by=111)

    # Verificar que solo existen los datos del primer apply
    level_service = LevelService(db_session)
    levels = await level_service.get_all_levels()
    assert len(levels) == 3  # No duplicados
