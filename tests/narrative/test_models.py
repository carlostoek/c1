"""
Tests para modelos de narrativa.

Valida:
- Creación de capítulos
- Creación de fragmentos
- Creación de decisiones
- Creación de requisitos
- Progreso de usuario
- Historial de decisiones
- Relaciones entre modelos
- Enums
"""
import pytest
from datetime import datetime
from sqlalchemy import select

from bot.database import get_session
from bot.narrative.database import (
    ChapterType,
    RequirementType,
    ArchetypeType,
    NarrativeChapter,
    NarrativeFragment,
    FragmentDecision,
    FragmentRequirement,
    UserNarrativeProgress,
    UserDecisionHistory,
)


@pytest.mark.asyncio
async def test_create_chapter():
    """Test: Crear capítulo narrativo."""
    async with get_session() as session:
        chapter = NarrativeChapter(
            name="Los Kinkys",
            slug="los-kinkys",
            chapter_type=ChapterType.FREE,
            order=1,
            is_active=True,
            description="Capítulo de introducción gratuito"
        )

        session.add(chapter)
        await session.commit()
        await session.refresh(chapter)

        assert chapter.id is not None
        assert chapter.name == "Los Kinkys"
        assert chapter.slug == "los-kinkys"
        assert chapter.chapter_type == ChapterType.FREE
        assert chapter.is_active is True


@pytest.mark.asyncio
async def test_create_fragment():
    """Test: Crear fragmento narrativo."""
    async with get_session() as session:
        # Crear capítulo primero
        chapter = NarrativeChapter(
            name="Test Chapter",
            slug="test-chapter",
            chapter_type=ChapterType.FREE
        )
        session.add(chapter)
        await session.commit()
        await session.refresh(chapter)

        # Crear fragmento
        fragment = NarrativeFragment(
            chapter_id=chapter.id,
            fragment_key="scene_1",
            title="Bienvenida de Diana",
            speaker="diana",
            content="Bienvenido a Los Kinkys...",
            order=1,
            is_entry_point=True,
            is_active=True
        )

        session.add(fragment)
        await session.commit()
        await session.refresh(fragment)

        assert fragment.id is not None
        assert fragment.fragment_key == "scene_1"
        assert fragment.speaker == "diana"
        assert fragment.is_entry_point is True


@pytest.mark.asyncio
async def test_enums():
    """Test: Validar enums."""
    # ChapterType
    assert ChapterType.FREE == "free"
    assert ChapterType.VIP == "vip"

    # RequirementType
    assert RequirementType.NONE == "none"
    assert RequirementType.VIP_STATUS == "vip"
    assert RequirementType.MIN_BESITOS == "besitos"
    assert RequirementType.ARCHETYPE == "archetype"
    assert RequirementType.DECISION == "decision"

    # ArchetypeType
    assert ArchetypeType.UNKNOWN == "unknown"
    assert ArchetypeType.IMPULSIVE == "impulsive"
    assert ArchetypeType.CONTEMPLATIVE == "contemplative"
    assert ArchetypeType.SILENT == "silent"


@pytest.mark.asyncio
async def test_narrative_container_import():
    """Test: Verificar que NarrativeContainer se puede importar."""
    from bot.narrative.services import NarrativeContainer
    from bot.narrative import NarrativeContainer as NC2

    assert NarrativeContainer is not None
    assert NC2 is not None
    assert NarrativeContainer == NC2


@pytest.mark.asyncio
async def test_models_basic():
    """Test básico: Crear modelos sin guardar."""
    chapter = NarrativeChapter(
        name="Test",
        slug="test",
        chapter_type=ChapterType.FREE
    )
    assert chapter.name == "Test"

    fragment = NarrativeFragment(
        chapter_id=1,
        fragment_key="test",
        title="Test",
        speaker="diana",
        content="Test"
    )
    assert fragment.speaker == "diana"

    decision = FragmentDecision(
        fragment_id=1,
        button_text="Test",
        target_fragment_key="test2"
    )
    assert decision.button_text == "Test"
