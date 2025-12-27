"""
Tests de integración FASE N3: Integración con Orquestadores.

Valida:
- Creación de recompensas con condiciones narrativas
- Validación de unlock conditions
- NarrativeOrchestrator
- ConfigurationOrchestrator.narrative property
- check_unlock_conditions en RewardService con condiciones narrativas
"""

import pytest
from bot.database import get_session
from bot.narrative.database import (
    NarrativeChapter, ChapterType, ArchetypeType
)
from bot.gamification.database.enums import RewardType, BadgeRarity
from bot.gamification.services.orchestrator.reward import RewardOrchestrator
from bot.gamification.services.orchestrator.configuration import ConfigurationOrchestrator
from bot.gamification.services.reward import RewardService
from bot.gamification.utils.validators import validate_unlock_conditions
from bot.narrative.services.orchestrator import NarrativeOrchestrator
from bot.narrative.services.chapter import ChapterService
from bot.narrative.services.progress import ProgressService


# ========================================
# TEST VALIDATORS
# ========================================

def test_validate_narrative_chapter_condition():
    """Valida condición narrative_chapter."""
    condition = {
        'type': 'narrative_chapter',
        'chapter_slug': 'los-kinkys'
    }
    is_valid, error = validate_unlock_conditions(condition)
    assert is_valid
    assert error == "OK"


def test_validate_narrative_fragment_condition():
    """Valida condición narrative_fragment."""
    condition = {
        'type': 'narrative_fragment',
        'fragment_key': 'scene_3a'
    }
    is_valid, error = validate_unlock_conditions(condition)
    assert is_valid
    assert error == "OK"


def test_validate_archetype_condition():
    """Valida condición archetype."""
    condition = {
        'type': 'archetype',
        'archetype': 'impulsive'
    }
    is_valid, error = validate_unlock_conditions(condition)
    assert is_valid
    assert error == "OK"


def test_validate_invalid_archetype():
    """Rechaza arquetipo inválido."""
    condition = {
        'type': 'archetype',
        'archetype': 'invalid_type'
    }
    is_valid, error = validate_unlock_conditions(condition)
    assert not is_valid
    assert 'Invalid archetype' in error


# ========================================
# TEST REWARD ORCHESTRATOR
# ========================================

@pytest.mark.asyncio
async def test_reward_orchestrator_with_narrative_chapter():
    """Crea recompensa con condición narrative_chapter."""
    async with get_session() as session:
        # Setup: Crear capítulo
        chapter_service = ChapterService(session)
        chapter = await chapter_service.create_chapter(
            name="Test Chapter",
            slug="test-chapter",
            chapter_type=ChapterType.FREE
        )

        # Test: Crear recompensa con condición narrativa
        orchestrator = RewardOrchestrator(session)
        result = await orchestrator.create_reward_with_unlock_condition(
            reward_data={
                'name': 'Explorador Kinky',
                'description': 'Completaste capítulo',
                'reward_type': RewardType.BADGE,
                'metadata': {'icon': '🎭', 'rarity': BadgeRarity.EPIC.value}
            },
            unlock_narrative_chapter='test-chapter',
            created_by=1
        )

        # Validar
        assert result['reward'] is not None
        assert result['unlock_condition']['type'] == 'narrative_chapter'
        assert result['unlock_condition']['chapter_slug'] == 'test-chapter'
        assert len(result['validation_errors']) == 0


@pytest.mark.asyncio
async def test_reward_orchestrator_with_narrative_fragment():
    """Crea recompensa con condición narrative_fragment."""
    async with get_session() as session:
        orchestrator = RewardOrchestrator(session)
        result = await orchestrator.create_reward_with_unlock_condition(
            reward_data={
                'name': 'Alma Impulsiva',
                'description': 'Tomaste la decisión impulsiva',
                'reward_type': RewardType.BADGE,
                'metadata': {'icon': '⚡', 'rarity': BadgeRarity.RARE.value}
            },
            unlock_narrative_fragment='scene_3a',
            created_by=1
        )

        # Validar
        assert result['reward'] is not None
        assert result['unlock_condition']['type'] == 'narrative_fragment'
        assert result['unlock_condition']['fragment_key'] == 'scene_3a'


@pytest.mark.asyncio
async def test_reward_orchestrator_with_archetype():
    """Crea recompensa con condición archetype."""
    async with get_session() as session:
        orchestrator = RewardOrchestrator(session)
        result = await orchestrator.create_reward_with_unlock_condition(
            reward_data={
                'name': 'Personalidad Impulsiva',
                'description': 'Demuestras ser impulsivo',
                'reward_type': RewardType.BADGE,
                'metadata': {'icon': '🔥', 'rarity': BadgeRarity.LEGENDARY.value}
            },
            unlock_archetype='impulsive',
            created_by=1
        )

        # Validar
        assert result['reward'] is not None
        assert result['unlock_condition']['type'] == 'archetype'
        assert result['unlock_condition']['archetype'] == 'impulsive'


@pytest.mark.asyncio
async def test_reward_orchestrator_multiple_conditions():
    """Crea recompensa con múltiples condiciones (besitos + narrativa)."""
    async with get_session() as session:
        orchestrator = RewardOrchestrator(session)
        result = await orchestrator.create_reward_with_unlock_condition(
            reward_data={
                'name': 'Maestro Diana',
                'description': 'Fan dedicado',
                'reward_type': RewardType.BADGE,
                'metadata': {'icon': '👑', 'rarity': BadgeRarity.LEGENDARY.value}
            },
            unlock_besitos=1000,
            unlock_narrative_chapter='test-chap',
            created_by=1
        )

        # Validar
        assert result['reward'] is not None
        assert result['unlock_condition']['type'] == 'multiple'
        assert len(result['unlock_condition']['conditions']) == 2


# ========================================
# TEST CONFIGURATION ORCHESTRATOR
# ========================================

@pytest.mark.asyncio
async def test_configuration_orchestrator_narrative_property():
    """Valida property narrative en ConfigurationOrchestrator."""
    async with get_session() as session:
        config_orch = ConfigurationOrchestrator(session)

        # Lazy load debe retornar NarrativeOrchestrator
        narrative_orch = config_orch.narrative
        assert isinstance(narrative_orch, NarrativeOrchestrator)

        # Segunda llamada debe retornar misma instancia
        narrative_orch_2 = config_orch.narrative
        assert narrative_orch is narrative_orch_2


# ========================================
# TEST NARRATIVE ORCHESTRATOR
# ========================================

@pytest.mark.asyncio
async def test_narrative_orchestrator_create_fragment_with_rewards():
    """Crea fragmento con recompensas usando NarrativeOrchestrator."""
    async with get_session() as session:
        # Setup: Crear capítulo
        chapter_service = ChapterService(session)
        chapter = await chapter_service.create_chapter(
            name="Test Chapter N3",
            slug="test-chapter-n3",
            chapter_type=ChapterType.FREE
        )

        # Test: Crear fragmento con recompensa de llegada
        orchestrator = NarrativeOrchestrator(session)
        result = await orchestrator.create_fragment_with_rewards(
            fragment_data={
                'chapter_id': chapter.id,
                'fragment_key': 'scene_test',
                'title': 'Escena de Prueba',
                'speaker': 'diana',
                'content': 'Contenido de prueba',
                'order': 1
            },
            arrival_rewards=[
                {
                    'name': 'Badge de Llegada',
                    'description': 'Llegaste a la escena',
                    'reward_type': RewardType.BADGE,
                    'metadata': {'icon': '🎯', 'rarity': BadgeRarity.COMMON.value}
                }
            ],
            created_by=1
        )

        # Validar
        assert result['fragment'] is not None
        assert result['fragment'].fragment_key == 'scene_test'
        assert len(result['created_rewards']) == 1
        assert result['created_rewards'][0].name == 'Badge de Llegada'


# ========================================
# TEST REWARD SERVICE CHECK UNLOCK CONDITIONS
# ========================================

@pytest.mark.asyncio
async def test_check_unlock_narrative_chapter():
    """Verifica unlock condition narrative_chapter en RewardService."""
    async with get_session() as session:
        # Setup: Crear capítulo
        chapter_service = ChapterService(session)
        chapter = await chapter_service.create_chapter(
            name="Test Unlock",
            slug="test-unlock",
            chapter_type=ChapterType.FREE
        )

        # Crear progreso y marcar completado
        progress_service = ProgressService(session)
        await progress_service.complete_chapter(user_id=1, chapter_id=chapter.id)

        # Crear recompensa con condición
        orchestrator = RewardOrchestrator(session)
        result = await orchestrator.create_reward_with_unlock_condition(
            reward_data={
                'name': 'Test Reward Unlock',
                'description': 'Test',
                'reward_type': RewardType.BADGE,
                'metadata': {'icon': '🎯', 'rarity': BadgeRarity.COMMON.value}
            },
            unlock_narrative_chapter='test-unlock',
            created_by=1
        )

        # Test: Verificar unlock conditions
        reward_service = RewardService(session)
        can_unlock, reason = await reward_service.check_unlock_conditions(
            user_id=1,
            reward_id=result['reward'].id
        )

        # El usuario debería poder desbloquear (completó el capítulo)
        assert can_unlock
        assert reason == "Available"


@pytest.mark.asyncio
async def test_check_unlock_archetype():
    """Verifica unlock condition archetype en RewardService."""
    async with get_session() as session:
        # Setup: Crear usuario con arquetipo
        progress_service = ProgressService(session)
        await progress_service.update_archetype(
            user_id=2,
            archetype=ArchetypeType.IMPULSIVE,
            confidence=0.9
        )

        # Crear recompensa con condición archetype
        orchestrator = RewardOrchestrator(session)
        result = await orchestrator.create_reward_with_unlock_condition(
            reward_data={
                'name': 'Impulsive Badge Test',
                'description': 'Para impulsivos',
                'reward_type': RewardType.BADGE,
                'metadata': {'icon': '⚡', 'rarity': BadgeRarity.RARE.value}
            },
            unlock_archetype='impulsive',
            created_by=1
        )

        # Test: Verificar unlock conditions
        reward_service = RewardService(session)
        can_unlock, reason = await reward_service.check_unlock_conditions(
            user_id=2,
            reward_id=result['reward'].id
        )

        # El usuario debería poder desbloquear (tiene arquetipo impulsive)
        assert can_unlock
        assert reason == "Available"


# ========================================
# TEST UNLOCK REQUIREMENT TEXT
# ========================================

@pytest.mark.asyncio
async def test_unlock_requirement_text_narrative():
    """Valida mensajes descriptivos de requisitos narrativos."""
    async with get_session() as session:
        reward_service = RewardService(session)

        # Test narrative_chapter
        text = reward_service._get_unlock_requirement_text({
            'type': 'narrative_chapter',
            'chapter_slug': 'los-kinkys'
        })
        assert 'los-kinkys' in text

        # Test narrative_fragment
        text = reward_service._get_unlock_requirement_text({
            'type': 'narrative_fragment',
            'fragment_key': 'scene_5'
        })
        assert 'scene_5' in text

        # Test archetype
        text = reward_service._get_unlock_requirement_text({
            'type': 'archetype',
            'archetype': 'contemplative'
        })
        assert 'contemplative' in text
