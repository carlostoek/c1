"""
Tests de FASE N4: Handlers de Usuario para Narrativa.

Valida:
- Botón "📖 Historia" aparece en menú
- Handler narr:start funciona correctamente
- Mostrar fragmentos con formateo correcto
- Procesar decisiones del usuario
- Integración narrative_router en dispatcher
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from bot.database import get_session
from bot.narrative.database import (
    NarrativeChapter, NarrativeFragment, FragmentDecision,
    ChapterType
)
from bot.narrative.services.chapter import ChapterService
from bot.narrative.services.fragment import FragmentService
from bot.narrative.services.decision import DecisionService
from bot.utils.keyboards import dynamic_user_menu_keyboard


# ========================================
# TEST MENÚ DINÁMICO CON BOTÓN HISTORIA
# ========================================

@pytest.mark.asyncio
async def test_menu_includes_historia_button():
    """Verifica que el botón '📖 Historia' aparece en el menú."""
    async with get_session() as session:
        # Test para rol VIP
        keyboard = await dynamic_user_menu_keyboard(session, 'vip')

        # Convertir keyboard a lista de botones
        buttons = []
        for row in keyboard.inline_keyboard:
            for button in row:
                buttons.append({
                    'text': button.text,
                    'callback_data': button.callback_data
                })

        # Verificar que existe botón "📖 Historia"
        historia_buttons = [b for b in buttons if '📖 Historia' in b['text']]
        assert len(historia_buttons) == 1
        assert historia_buttons[0]['callback_data'] == 'narr:start'

        # Verificar que existe botón "🎮 Juego Kinky"
        kinky_buttons = [b for b in buttons if '🎮 Juego Kinky' in b['text']]
        assert len(kinky_buttons) == 1

        # Verificar orden: Historia debe estar antes de Juego Kinky
        historia_index = buttons.index(historia_buttons[0])
        kinky_index = buttons.index(kinky_buttons[0])
        assert historia_index < kinky_index


@pytest.mark.asyncio
async def test_menu_includes_historia_button_free():
    """Verifica botón Historia para usuarios FREE."""
    async with get_session() as session:
        keyboard = await dynamic_user_menu_keyboard(session, 'free')

        buttons = []
        for row in keyboard.inline_keyboard:
            for button in row:
                buttons.append({'text': button.text, 'callback_data': button.callback_data})

        # Verificar que existe botón "📖 Historia" para FREE también
        historia_buttons = [b for b in buttons if '📖 Historia' in b['text']]
        assert len(historia_buttons) == 1


# ========================================
# TEST CHAPTER SERVICE
# ========================================

@pytest.mark.asyncio
async def test_chapter_service_create():
    """Crea un capítulo usando ChapterService."""
    async with get_session() as session:
        chapter_service = ChapterService(session)

        chapter = await chapter_service.create_chapter(
            name="Capítulo de Prueba",
            slug="test-chapter-n4",
            chapter_type=ChapterType.FREE,
            description="Descripción de prueba"
        )

        assert chapter.id is not None
        assert chapter.name == "Capítulo de Prueba"
        assert chapter.slug == "test-chapter-n4"
        assert chapter.chapter_type == ChapterType.FREE


@pytest.mark.asyncio
async def test_chapter_service_get_by_slug():
    """Obtiene capítulo por slug."""
    async with get_session() as session:
        chapter_service = ChapterService(session)

        # Crear capítulo
        created = await chapter_service.create_chapter(
            name="Test Slug",
            slug="test-slug-unique",
            chapter_type=ChapterType.FREE
        )

        # Obtener por slug
        found = await chapter_service.get_chapter_by_slug("test-slug-unique")

        assert found is not None
        assert found.id == created.id
        assert found.name == "Test Slug"


# ========================================
# TEST FRAGMENT SERVICE
# ========================================

@pytest.mark.asyncio
async def test_fragment_get_entry_point():
    """Obtiene entry point de un capítulo específico."""
    async with get_session() as session:
        # Crear capítulo
        chapter_service = ChapterService(session)
        chapter = await chapter_service.create_chapter(
            name="Capítulo Entry",
            slug="chapter-entry",
            chapter_type=ChapterType.FREE
        )

        # Crear fragmento entry point
        fragment_service = FragmentService(session)
        entry_fragment = await fragment_service.create_fragment(
            chapter_id=chapter.id,
            fragment_key="entry_test",
            title="Inicio",
            speaker="diana",
            content="Bienvenido a la historia",
            is_entry_point=True,
            order=0
        )

        # Obtener entry point por chapter_id
        found = await fragment_service.get_entry_point(chapter.id)

        assert found is not None
        assert found.fragment_key == "entry_test"
        assert found.is_entry_point is True


# ========================================
# TEST DECISION SERVICE
# ========================================

@pytest.mark.asyncio
async def test_decision_service_get_available():
    """Obtiene decisiones disponibles para fragmento."""
    async with get_session() as session:
        # Setup: Crear capítulo y fragmento
        chapter_service = ChapterService(session)
        chapter = await chapter_service.create_chapter(
            name="Test Decisions",
            slug="test-decisions",
            chapter_type=ChapterType.FREE
        )

        fragment_service = FragmentService(session)
        fragment = await fragment_service.create_fragment(
            chapter_id=chapter.id,
            fragment_key="frag_with_decisions",
            title="Fragmento con decisiones",
            speaker="diana",
            content="¿Qué eliges?",
            order=1
        )

        # Crear decisión
        from bot.narrative.database import FragmentDecision
        decision = FragmentDecision(
            fragment_id=fragment.id,
            button_text="Opción A",
            target_fragment_key="next_fragment",
            order=0,
            besitos_cost=0,
            is_active=True
        )
        session.add(decision)
        await session.commit()

        # Test: Obtener decisiones disponibles
        decision_service = DecisionService(session)
        decisions = await decision_service.get_available_decisions(
            user_id=1,
            fragment_key="frag_with_decisions"
        )

        assert len(decisions) == 1
        assert decisions[0].button_text == "Opción A"


# ========================================
# TEST NARRATIVE CONTAINER - CHAPTER PROPERTY
# ========================================

@pytest.mark.asyncio
async def test_narrative_container_chapter_property():
    """Verifica que NarrativeContainer tiene property chapter."""
    async with get_session() as session:
        from bot.narrative.services.container import NarrativeContainer

        narrative = NarrativeContainer(session)

        # Verificar lazy loading (antes de acceder)
        assert '_chapter_service' in dir(narrative)
        assert narrative._chapter_service is None

        # Acceder a chapter (debe cargar)
        chapter_service = narrative.chapter
        assert chapter_service is not None
        assert 'chapter' in narrative.get_loaded_services()

        # Verificar que la property retorna la misma instancia
        chapter_service_2 = narrative.chapter
        assert chapter_service is chapter_service_2


# ========================================
# TEST NARRATIVE ROUTER REGISTRATION
# ========================================

def test_narrative_router_exists():
    """Verifica que narrative_router está definido."""
    from bot.handlers.user.narrative import narrative_router

    assert narrative_router is not None
    assert narrative_router.name == "user_narrative"


def test_narrative_router_imported_in_handlers():
    """Verifica que narrative_router se importa en handlers/__init__.py."""
    from bot.handlers import narrative_router

    assert narrative_router is not None
