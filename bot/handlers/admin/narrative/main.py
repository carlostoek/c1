"""
Main Narrative Admin Handler - Menú principal de gestión de narrativa.
"""

import logging
from aiogram import F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.admin.narrative import narrative_admin_router
from bot.narrative.services.container import NarrativeContainer
from bot.utils.keyboards import create_inline_keyboard

logger = logging.getLogger(__name__)


@narrative_admin_router.callback_query(F.data == "admin:narrative")
async def callback_narrative_menu(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Muestra menú principal de gestión de narrativa.

    Args:
        callback: Callback del botón "Gestión Narrativa"
        session: Sesión de BD (inyectada por middleware)
    """
    await callback.answer()

    narrative = NarrativeContainer(session)

    # Obtener estadísticas rápidas
    chapters = await narrative.chapter.get_all_chapters(active_only=False)
    active_chapters = [c for c in chapters if c.is_active]

    # Contar fragmentos totales
    total_fragments = 0
    for ch in chapters:
        count = await narrative.chapter.get_chapter_fragments_count(ch.id)
        total_fragments += count

    text = (
        "📖 <b>Gestión de Narrativa</b>\n\n"
        f"📚 Capítulos: {len(active_chapters)}/{len(chapters)} activos\n"
        f"📄 Fragmentos: {total_fragments}\n\n"
        "<i>Gestiona capítulos, fragmentos y decisiones.</i>"
    )

    keyboard = create_inline_keyboard([
        [{"text": "📚 Capítulos", "callback_data": "narrative:chapters"}],
        [{"text": "🔍 Validar Narrativa", "callback_data": "narrative:validate"}],
        [{"text": "📥 Importar JSON", "callback_data": "narrative_admin:import"}],
        [{"text": "📊 Estadísticas", "callback_data": "narrative_admin:stats"}],
        [{"text": "🔙 Volver", "callback_data": "admin:main"}]
    ])

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
