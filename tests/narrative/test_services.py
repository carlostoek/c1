"""
Tests unitarios para servicios de narrativa.

Valida:
- FragmentService: CRUD de fragmentos
- ProgressService: Avance del usuario
- DecisionService: Procesamiento de decisiones
"""
import pytest
from bot.database import get_session
from bot.narrative.database import (
    ChapterType,
    ArchetypeType,
    NarrativeChapter,
    NarrativeFragment,
    FragmentDecision,
)
from bot.narrative.services import (
    FragmentService,
    ProgressService,
    DecisionService,
)


# ======================
# FragmentService Tests
# ======================

@pytest.mark.asyncio
async def test_fragment_service_create():
    """Test: Crear fragmento con FragmentService."""
    async with get_session() as session:
        # Crear capítulo primero
        chapter = NarrativeChapter(
            name="Test Chapter",
            slug="test-chapter-create",
            chapter_type=ChapterType.FREE
        )
        session.add(chapter)
        await session.commit()
        await session.refresh(chapter)

        # Crear fragmento con service
        fragment_service = FragmentService(session)
        fragment = await fragment_service.create_fragment(
            chapter_id=chapter.id,
            fragment_key="test_scene_1",
            title="Test Scene",
            speaker="diana",
            content="Test content",
            order=1,
            is_entry_point=True
        )

        assert fragment is not None
        assert fragment.fragment_key == "test_scene_1"
        assert fragment.speaker == "diana"
        assert fragment.is_entry_point is True


@pytest.mark.asyncio
async def test_fragment_service_get():
    """Test: Obtener fragmento por key."""
    async with get_session() as session:
        # Crear capítulo y fragmento
        chapter = NarrativeChapter(
            name="Test",
            slug="test-1",
            chapter_type=ChapterType.FREE
        )
        session.add(chapter)
        await session.commit()
        await session.refresh(chapter)

        fragment = NarrativeFragment(
            chapter_id=chapter.id,
            fragment_key="fragment_get",
            title="Test",
            speaker="diana",
            content="Test"
        )
        session.add(fragment)
        await session.commit()

        # Obtener con service
        fragment_service = FragmentService(session)
        found = await fragment_service.get_fragment("test_get")

        assert found is not None
        assert found.fragment_key == "test_get"


@pytest.mark.asyncio
async def test_fragment_service_get_entry_point():
    """Test: Obtener entry point de capítulo."""
    async with get_session() as session:
        # Crear capítulo
        chapter = NarrativeChapter(
            name="Test",
            slug="test-2",
            chapter_type=ChapterType.FREE
        )
        session.add(chapter)
        await session.commit()
        await session.refresh(chapter)

        # Crear fragmento entry point
        fragment = NarrativeFragment(
            chapter_id=chapter.id,
            fragment_key="entry",
            title="Entry",
            speaker="diana",
            content="Start",
            is_entry_point=True
        )
        session.add(fragment)
        await session.commit()

        # Obtener entry point
        fragment_service = FragmentService(session)
        entry = await fragment_service.get_entry_point(chapter.id)

        assert entry is not None
        assert entry.fragment_key == "entry"
        assert entry.is_entry_point is True


@pytest.mark.asyncio
async def test_fragment_service_format_message():
    """Test: Formatear fragmento para Telegram."""
    async with get_session() as session:
        chapter = NarrativeChapter(
            name="Test",
            slug="test-3",
            chapter_type=ChapterType.FREE
        )
        session.add(chapter)
        await session.commit()
        await session.refresh(chapter)

        fragment = NarrativeFragment(
            chapter_id=chapter.id,
            fragment_key="test_format",
            title="Test",
            speaker="diana",
            content="Bienvenido a la historia",
            visual_hint="Diana entre sombras"
        )
        session.add(fragment)
        await session.commit()

        # Formatear
        fragment_service = FragmentService(session)
        message = await fragment_service.format_fragment_message(fragment)

        assert "🌸" in message  # Emoji de Diana
        assert "Diana" in message
        assert "Bienvenido a la historia" in message
        assert "Diana entre sombras" in message


# ======================
# ProgressService Tests
# ======================

@pytest.mark.asyncio
async def test_progress_service_create():
    """Test: Crear progreso de usuario."""
    async with get_session() as session:
        progress_service = ProgressService(session)
        progress = await progress_service.get_or_create_progress(123456)

        assert progress is not None
        assert progress.user_id == 123456
        assert progress.detected_archetype == ArchetypeType.UNKNOWN
        assert progress.total_decisions == 0


@pytest.mark.asyncio
async def test_progress_service_advance():
    """Test: Avanzar a fragmento."""
    async with get_session() as session:
        progress_service = ProgressService(session)

        # Avanzar a fragmento
        progress = await progress_service.advance_to(
            user_id=123456,
            fragment_key="scene_2",
            chapter_id=1
        )

        assert progress.current_fragment_key == "scene_2"
        assert progress.current_chapter_id == 1


@pytest.mark.asyncio
async def test_progress_service_increment_decisions():
    """Test: Incrementar contador de decisiones."""
    async with get_session() as session:
        progress_service = ProgressService(session)

        # Incrementar varias veces
        progress = await progress_service.increment_decisions(123456)
        assert progress.total_decisions == 1

        progress = await progress_service.increment_decisions(123456)
        assert progress.total_decisions == 2


@pytest.mark.asyncio
async def test_progress_service_update_archetype():
    """Test: Actualizar arquetipo detectado."""
    async with get_session() as session:
        progress_service = ProgressService(session)

        # Actualizar arquetipo
        progress = await progress_service.update_archetype(
            user_id=123456,
            archetype=ArchetypeType.IMPULSIVE,
            confidence=0.85
        )

        assert progress.detected_archetype == ArchetypeType.IMPULSIVE
        assert progress.archetype_confidence == 0.85


@pytest.mark.asyncio
async def test_progress_service_reset():
    """Test: Resetear progreso."""
    async with get_session() as session:
        progress_service = ProgressService(session)

        # Crear progreso con datos
        await progress_service.advance_to(123456, "scene_5")
        await progress_service.increment_decisions(123456)
        await progress_service.update_archetype(123456, ArchetypeType.IMPULSIVE, 0.9)

        # Resetear
        result = await progress_service.reset_progress(123456)
        assert result is True

        # Verificar reset
        progress = await progress_service.get_progress(123456)
        assert progress.current_fragment_key is None
        assert progress.total_decisions == 0
        assert progress.detected_archetype == ArchetypeType.UNKNOWN


# ======================
# DecisionService Tests
# ======================

@pytest.mark.asyncio
async def test_decision_service_get_available():
    """Test: Obtener decisiones disponibles."""
    async with get_session() as session:
        # Crear estructura
        chapter = NarrativeChapter(
            name="Test",
            slug="test-4",
            chapter_type=ChapterType.FREE
        )
        session.add(chapter)
        await session.commit()
        await session.refresh(chapter)

        fragment = NarrativeFragment(
            chapter_id=chapter.id,
            fragment_key="scene_test",
            title="Test",
            speaker="diana",
            content="Test"
        )
        session.add(fragment)
        await session.commit()
        await session.refresh(fragment)

        # Crear decisiones
        decision1 = FragmentDecision(
            fragment_id=fragment.id,
            button_text="Opción 1",
            target_fragment_key="scene_2",
            order=1,
            is_active=True
        )
        decision2 = FragmentDecision(
            fragment_id=fragment.id,
            button_text="Opción 2",
            target_fragment_key="scene_3",
            order=2,
            is_active=True
        )
        session.add_all([decision1, decision2])
        await session.commit()

        # Obtener decisiones
        decision_service = DecisionService(session)
        decisions = await decision_service.get_available_decisions("scene_test")

        assert len(decisions) == 2
        assert decisions[0].button_text == "Opción 1"
        assert decisions[1].button_text == "Opción 2"


@pytest.mark.asyncio
async def test_decision_service_get_by_id():
    """Test: Obtener decisión por ID."""
    async with get_session() as session:
        chapter = NarrativeChapter(
            name="Test",
            slug="test-5",
            chapter_type=ChapterType.FREE
        )
        session.add(chapter)
        await session.commit()
        await session.refresh(chapter)

        fragment = NarrativeFragment(
            chapter_id=chapter.id,
            fragment_key="test",
            title="Test",
            speaker="diana",
            content="Test"
        )
        session.add(fragment)
        await session.commit()
        await session.refresh(fragment)

        decision = FragmentDecision(
            fragment_id=fragment.id,
            button_text="Test Decision",
            target_fragment_key="next"
        )
        session.add(decision)
        await session.commit()
        await session.refresh(decision)

        # Obtener por ID
        decision_service = DecisionService(session)
        found = await decision_service.get_decision_by_id(decision.id)

        assert found is not None
        assert found.button_text == "Test Decision"


@pytest.mark.asyncio
async def test_decision_service_record():
    """Test: Registrar decisión en historial."""
    async with get_session() as session:
        # Crear estructura
        chapter = NarrativeChapter(
            name="Test",
            slug="test-6",
            chapter_type=ChapterType.FREE
        )
        session.add(chapter)
        await session.commit()
        await session.refresh(chapter)

        fragment = NarrativeFragment(
            chapter_id=chapter.id,
            fragment_key="test_record",
            title="Test",
            speaker="diana",
            content="Test"
        )
        session.add(fragment)
        await session.commit()
        await session.refresh(fragment)

        decision = FragmentDecision(
            fragment_id=fragment.id,
            button_text="Test",
            target_fragment_key="next"
        )
        session.add(decision)
        await session.commit()
        await session.refresh(decision)

        # Registrar decisión
        decision_service = DecisionService(session)
        history = await decision_service.record_decision(
            user_id=123456,
            decision=decision,
            response_time=5
        )

        assert history is not None
        assert history.user_id == 123456
        assert history.fragment_key == "test_record"
        assert history.response_time_seconds == 5


@pytest.mark.asyncio
async def test_services_import():
    """Test: Verificar que servicios se pueden importar."""
    from bot.narrative.services import (
        FragmentService,
        ProgressService,
        DecisionService
    )

    assert FragmentService is not None
    assert ProgressService is not None
    assert DecisionService is not None
