"""
Tests de integración para el sistema de cooldowns narrativos.

Valida:
- Los cooldowns se establecen correctamente
- Los cooldowns bloquean decisiones
- Los cooldowns expiran
- Los mensajes varían
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import select
from unittest.mock import AsyncMock

from bot.database import get_session
from bot.narrative.database import NarrativeChapter, NarrativeFragment
from bot.narrative.database.enums import ChapterType, CooldownType
from bot.narrative.database.models_immersive import NarrativeCooldown
from bot.narrative.services.container import NarrativeContainer
from bot.narrative.services.decision import DecisionService
from bot.narrative.config import NarrativeConfig


@pytest.mark.asyncio
async def test_cooldown_set_and_check():
    """Test establecer y verificar cooldown."""
    async with get_session() as session:
        mock_bot = AsyncMock()
        user_id = 50001
        narrative = NarrativeContainer(session, mock_bot)

        # No debería haber cooldown inicial
        is_active, _, _ = await narrative.cooldown.check_cooldown(
            user_id, CooldownType.DECISION, "global_decision"
        )
        assert not is_active

        # Establecer cooldown
        await narrative.cooldown.set_cooldown(
            user_id=user_id,
            cooldown_type=CooldownType.DECISION,
            target_key="global_decision",
            duration_seconds=120,
            message="Espera..."
        )

        # Ahora debería estar activo
        is_active, expires_at, message = await narrative.cooldown.check_cooldown(
            user_id, CooldownType.DECISION, "global_decision"
        )
        assert is_active
        assert expires_at is not None
        assert "Espera" in message


@pytest.mark.asyncio
async def test_cooldown_blocks_decision():
    """Test que cooldown bloquea decisiones."""
    async with get_session() as session:
        mock_bot = AsyncMock()
        user_id = 50002
        narrative = NarrativeContainer(session, mock_bot)

        # Establecer cooldown
        await narrative.cooldown.set_cooldown(
            user_id=user_id,
            cooldown_type=CooldownType.DECISION,
            target_key="global_decision",
            duration_seconds=60,
            message="Espera un momento..."
        )

        # Verificar activo
        is_active, expires_at, _ = await narrative.cooldown.check_cooldown(
            user_id, CooldownType.DECISION, "global_decision"
        )

        assert is_active
        assert expires_at > datetime.utcnow()


@pytest.mark.asyncio
async def test_cooldown_expires():
    """Test que cooldown expira correctamente."""
    async with get_session() as session:
        mock_bot = AsyncMock()
        user_id = 50003
        narrative = NarrativeContainer(session, mock_bot)

        # Establecer cooldown corto
        await narrative.cooldown.set_cooldown(
            user_id=user_id,
            cooldown_type=CooldownType.DECISION,
            target_key="global_decision",
            duration_seconds=1,
            message="Test"
        )

        # Verificar activo
        is_active_before, _, _ = await narrative.cooldown.check_cooldown(
            user_id, CooldownType.DECISION, "global_decision"
        )
        assert is_active_before

        # Forzar expiración
        stmt = select(NarrativeCooldown).where(
            NarrativeCooldown.user_id == user_id,
            NarrativeCooldown.cooldown_type == CooldownType.DECISION
        )
        result = await session.execute(stmt)
        cooldown = result.scalar_one()
        cooldown.expires_at = datetime.utcnow() - timedelta(seconds=1)
        await session.flush()

        # Verificar expirado
        is_active_after, _, _ = await narrative.cooldown.check_cooldown(
            user_id, CooldownType.DECISION, "global_decision"
        )
        assert not is_active_after


@pytest.mark.asyncio
async def test_intense_fragment_cooldown():
    """Test cooldown para fragmentos intensos."""
    async with get_session() as session:
        mock_bot = AsyncMock()

        chapter = NarrativeChapter(
            name="Test",
            slug="test-intense",
            chapter_type=ChapterType.FREE,
            order=1,
            is_active=True
        )
        session.add(chapter)
        await session.flush()

        intense_fragment = NarrativeFragment(
            chapter_id=chapter.id,
            fragment_key="intense_test",
            title="Test",
            speaker="diana",
            content="Test",
            visual_hint="intense, climax",
            order=1
        )
        session.add(intense_fragment)
        await session.flush()

        decision_service = DecisionService(session)
        user_id = 50004

        await decision_service._apply_fragment_cooldown(user_id, intense_fragment)

        narrative = NarrativeContainer(session, mock_bot)
        is_active, _, _ = await narrative.cooldown.check_cooldown(
            user_id, CooldownType.FRAGMENT, "intense_test"
        )

        assert is_active


@pytest.mark.asyncio
async def test_cooldown_messages():
    """Test variedad de mensajes de cooldown."""
    messages = set()

    for _ in range(10):
        msg = NarrativeConfig.get_cooldown_message("decision")
        messages.add(msg)

    # Deberían variar
    assert len(messages) >= 2

    # Cada tipo debe tener mensaje
    for cooldown_type in ["decision", "fragment", "chapter", "challenge"]:
        msg = NarrativeConfig.get_cooldown_message(cooldown_type)
        assert len(msg) > 0
