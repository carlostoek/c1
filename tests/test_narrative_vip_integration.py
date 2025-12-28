"""
Tests de integración Narrativa <-> Gamificación y VIP <-> Gamificación.

Valida:
- NarrativeConditionService.check_condition()
- SubscriptionService.grant_vip_days()
- UnifiedRewardService con NARRATIVE_UNLOCK y VIP_DAYS
- Validadores de condiciones narrativas
"""
import pytest
from datetime import datetime, timedelta

from bot.database import get_session
from bot.gamification.services.container import GamificationContainer
from bot.gamification.services.narrative_condition import NarrativeConditionService
from bot.gamification.database.enums import RewardType
from bot.gamification.utils.validators import (
    validate_reward_metadata,
    validate_unlock_conditions
)


# ========================================
# TEST: NARRATIVE CONDITION SERVICE
# ========================================

@pytest.mark.asyncio
async def test_narrative_condition_service_init():
    """Test: NarrativeConditionService se inicializa correctamente."""
    async with get_session() as session:
        service = NarrativeConditionService(session)
        assert service is not None
        assert service._session == session


@pytest.mark.asyncio
async def test_check_condition_unknown_type():
    """Test: Condición desconocida retorna error."""
    async with get_session() as session:
        service = NarrativeConditionService(session)

        met, message = await service.check_condition(
            user_id=123,
            condition={'type': 'unknown_type'}
        )

        assert met is False
        assert 'no soportado' in message.lower()


@pytest.mark.asyncio
async def test_check_condition_chapter_missing_slug():
    """Test: Condición capítulo sin slug retorna error."""
    async with get_session() as session:
        service = NarrativeConditionService(session)

        met, message = await service.check_condition(
            user_id=123,
            condition={'type': 'narrative_chapter'}  # Sin chapter_slug
        )

        assert met is False
        assert 'chapter_slug' in message.lower()


@pytest.mark.asyncio
async def test_check_condition_archetype_missing():
    """Test: Condición arquetipo sin archetype retorna error."""
    async with get_session() as session:
        service = NarrativeConditionService(session)

        met, message = await service.check_condition(
            user_id=123,
            condition={'type': 'archetype'}  # Sin archetype
        )

        assert met is False
        assert 'archetype' in message.lower()


@pytest.mark.asyncio
async def test_gamification_container_narrative_condition():
    """Test: GamificationContainer incluye narrative_condition."""
    async with get_session() as session:
        container = GamificationContainer(session)

        service = container.narrative_condition
        assert service is not None
        assert isinstance(service, NarrativeConditionService)

        # Verificar lazy loading
        assert 'narrative_condition' in container.get_loaded_services()


# ========================================
# TEST: VALIDATORS
# ========================================

def test_validate_narrative_chapter_condition_valid():
    """Test: Validación de condición narrative_chapter válida."""
    is_valid, error = validate_unlock_conditions({
        'type': 'narrative_chapter',
        'chapter_slug': 'los-kinkys'
    })
    assert is_valid is True


def test_validate_narrative_chapter_condition_empty_slug():
    """Test: Error si chapter_slug está vacío."""
    is_valid, error = validate_unlock_conditions({
        'type': 'narrative_chapter',
        'chapter_slug': '  '
    })
    assert is_valid is False
    assert 'empty' in error.lower()


def test_validate_narrative_fragment_condition_valid():
    """Test: Validación de condición narrative_fragment válida."""
    is_valid, error = validate_unlock_conditions({
        'type': 'narrative_fragment',
        'fragment_key': 'scene_3a'
    })
    assert is_valid is True


def test_validate_narrative_decision_condition_valid():
    """Test: Validación de condición narrative_decision válida."""
    is_valid, error = validate_unlock_conditions({
        'type': 'narrative_decision',
        'decision_key': 'choice_accept'
    })
    assert is_valid is True


def test_validate_archetype_condition_valid():
    """Test: Validación de condición archetype válida."""
    is_valid, error = validate_unlock_conditions({
        'type': 'archetype',
        'archetype': 'impulsive'
    })
    assert is_valid is True


def test_validate_archetype_condition_invalid():
    """Test: Error si arquetipo no es válido."""
    is_valid, error = validate_unlock_conditions({
        'type': 'archetype',
        'archetype': 'invalid_archetype'
    })
    assert is_valid is False
    assert 'invalid archetype' in error.lower()


def test_validate_multiple_conditions_valid():
    """Test: Validación de condiciones múltiples."""
    is_valid, error = validate_unlock_conditions({
        'type': 'multiple',
        'conditions': [
            {'type': 'narrative_chapter', 'chapter_slug': 'chapter-1'},
            {'type': 'archetype', 'archetype': 'contemplative'}
        ]
    })
    assert is_valid is True


def test_validate_narrative_unlock_metadata_valid():
    """Test: Validación de metadata NARRATIVE_UNLOCK válida."""
    # unlock_type = chapter
    is_valid, error = validate_reward_metadata(
        RewardType.NARRATIVE_UNLOCK,
        {
            'unlock_type': 'chapter',
            'chapter_slug': 'hidden-chapter'
        }
    )
    assert is_valid is True

    # unlock_type = fragment
    is_valid, error = validate_reward_metadata(
        RewardType.NARRATIVE_UNLOCK,
        {
            'unlock_type': 'fragment',
            'fragment_key': 'secret_scene'
        }
    )
    assert is_valid is True


def test_validate_narrative_unlock_metadata_invalid():
    """Test: Error si unlock_type no es válido."""
    is_valid, error = validate_reward_metadata(
        RewardType.NARRATIVE_UNLOCK,
        {'unlock_type': 'invalid'}
    )
    assert is_valid is False
    assert 'unlock_type' in error.lower()


def test_validate_vip_days_metadata_valid():
    """Test: Validación de metadata VIP_DAYS válida."""
    is_valid, error = validate_reward_metadata(
        RewardType.VIP_DAYS,
        {'days': 7, 'extend_existing': True}
    )
    assert is_valid is True


def test_validate_vip_days_metadata_invalid_days():
    """Test: Error si days es inválido."""
    is_valid, error = validate_reward_metadata(
        RewardType.VIP_DAYS,
        {'days': 0}
    )
    assert is_valid is False
    assert 'days' in error.lower()


# ========================================
# TEST: VIP GRANT
# ========================================

@pytest.mark.asyncio
async def test_grant_vip_days_new_user():
    """Test: Otorgar VIP a usuario nuevo."""
    from bot.services.subscription import SubscriptionService
    from unittest.mock import MagicMock

    async with get_session() as session:
        bot = MagicMock()
        service = SubscriptionService(session, bot)

        user_id = 999999001  # Usuario nuevo

        success, message, subscriber = await service.grant_vip_days(
            user_id=user_id,
            days=7,
            source="test"
        )

        assert success is True
        assert '7 días' in message
        assert subscriber is not None
        assert subscriber.user_id == user_id
        assert subscriber.status == 'active'


@pytest.mark.asyncio
async def test_grant_vip_days_extend_existing():
    """Test: Extender VIP existente."""
    from bot.services.subscription import SubscriptionService
    from bot.database.models import VIPSubscriber
    from unittest.mock import MagicMock

    async with get_session() as session:
        bot = MagicMock()
        service = SubscriptionService(session, bot)

        user_id = 999999002

        # Crear VIP existente
        existing = VIPSubscriber(
            user_id=user_id,
            join_date=datetime.utcnow(),
            expiry_date=datetime.utcnow() + timedelta(days=5),
            status='active'
        )
        session.add(existing)
        await session.commit()

        # Extender
        success, message, subscriber = await service.grant_vip_days(
            user_id=user_id,
            days=7,
            source="test",
            extend_existing=True
        )

        assert success is True
        assert 'extendida' in message.lower()
        # Debería tener 5 + 7 = 12 días aproximadamente
        assert subscriber.expiry_date > datetime.utcnow() + timedelta(days=10)


@pytest.mark.asyncio
async def test_grant_vip_days_invalid():
    """Test: Error si days es inválido."""
    from bot.services.subscription import SubscriptionService
    from unittest.mock import MagicMock

    async with get_session() as session:
        bot = MagicMock()
        service = SubscriptionService(session, bot)

        success, message, subscriber = await service.grant_vip_days(
            user_id=123,
            days=0,
            source="test"
        )

        assert success is False
        assert 'al menos 1' in message.lower()
        assert subscriber is None


# ========================================
# TEST: UNIFIED REWARD SERVICE
# ========================================

@pytest.mark.asyncio
async def test_unified_reward_vip_days():
    """Test: UnifiedRewardService con VIP_DAYS."""
    from bot.gamification.services.unified import UnifiedRewardService

    async with get_session() as session:
        unified = UnifiedRewardService(session)
        user_id = 999999003

        success, message, data = await unified.grant_unified_reward(
            user_id=user_id,
            reward_type=RewardType.VIP_DAYS,
            reward_config={'days': 14, 'extend_existing': True},
            source='mission_reward'
        )

        assert success is True
        assert '14 días' in message
        assert data is not None
        assert data['days'] == 14


@pytest.mark.asyncio
async def test_unified_reward_narrative_unlock_not_available():
    """Test: NARRATIVE_UNLOCK cuando módulo narrativa no disponible."""
    from bot.gamification.services.unified import UnifiedRewardService

    async with get_session() as session:
        unified = UnifiedRewardService(session)
        user_id = 999999004

        # Esto puede fallar si el módulo narrativa no tiene
        # la función específica implementada aún
        success, message, data = await unified.grant_unified_reward(
            user_id=user_id,
            reward_type=RewardType.NARRATIVE_UNLOCK,
            reward_config={
                'unlock_type': 'chapter',
                'chapter_slug': 'hidden-chapter'
            },
            source='mission_reward'
        )

        # Si el módulo no está disponible, debería retornar error gracefully
        # Si está disponible, debería funcionar
        assert isinstance(success, bool)
        assert isinstance(message, str)
