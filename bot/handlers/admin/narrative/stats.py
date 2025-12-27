"""
Stats Handler - Estadísticas de uso de narrativa.
"""

import logging
from aiogram import F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from bot.handlers.admin.narrative import narrative_admin_router
from bot.narrative.database import (
    NarrativeChapter, NarrativeFragment, FragmentDecision,
    UserNarrativeProgress, UserDecisionHistory, ChapterType
)
from bot.narrative.services.container import NarrativeContainer
from bot.utils.keyboards import create_inline_keyboard

logger = logging.getLogger(__name__)


@narrative_admin_router.callback_query(F.data == "narrative_admin:stats")
async def callback_narrative_stats(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Muestra estadísticas detalladas de narrativa.

    Args:
        callback: Callback del botón "Ver Estadísticas"
        session: Sesión de BD (inyectada por middleware)
    """
    await callback.answer()

    # Contar capítulos activos
    stmt = select(func.count()).select_from(NarrativeChapter).where(
        NarrativeChapter.is_active == True
    )
    result = await session.execute(stmt)
    active_chapters = result.scalar_one()

    # Contar capítulos totales
    stmt = select(func.count()).select_from(NarrativeChapter)
    result = await session.execute(stmt)
    total_chapters = result.scalar_one()

    # Contar por tipo
    stmt = select(func.count()).select_from(NarrativeChapter).where(
        NarrativeChapter.chapter_type == ChapterType.FREE,
        NarrativeChapter.is_active == True
    )
    result = await session.execute(stmt)
    free_chapters = result.scalar_one()

    stmt = select(func.count()).select_from(NarrativeChapter).where(
        NarrativeChapter.chapter_type == ChapterType.VIP,
        NarrativeChapter.is_active == True
    )
    result = await session.execute(stmt)
    vip_chapters = result.scalar_one()

    # Contar fragmentos activos
    stmt = select(func.count()).select_from(NarrativeFragment).where(
        NarrativeFragment.is_active == True
    )
    result = await session.execute(stmt)
    active_fragments = result.scalar_one()

    # Contar fragmentos totales
    stmt = select(func.count()).select_from(NarrativeFragment)
    result = await session.execute(stmt)
    total_fragments = result.scalar_one()

    # Contar entry points
    stmt = select(func.count()).select_from(NarrativeFragment).where(
        NarrativeFragment.is_entry_point == True,
        NarrativeFragment.is_active == True
    )
    result = await session.execute(stmt)
    entry_points = result.scalar_one()

    # Contar endings
    stmt = select(func.count()).select_from(NarrativeFragment).where(
        NarrativeFragment.is_ending == True,
        NarrativeFragment.is_active == True
    )
    result = await session.execute(stmt)
    endings = result.scalar_one()

    # Contar decisiones configuradas
    stmt = select(func.count()).select_from(FragmentDecision).where(
        FragmentDecision.is_active == True
    )
    result = await session.execute(stmt)
    active_decisions = result.scalar_one()

    # Promedio decisiones por fragmento
    avg_decisions = round(active_decisions / active_fragments, 1) if active_fragments > 0 else 0

    # Contar usuarios con progreso
    stmt = select(func.count()).select_from(UserNarrativeProgress)
    result = await session.execute(stmt)
    total_users = result.scalar_one()

    # Contar decisiones tomadas por usuarios
    stmt = select(func.count()).select_from(UserDecisionHistory)
    result = await session.execute(stmt)
    user_decisions = result.scalar_one()

    # Ejecutar validación rápida
    narrative = NarrativeContainer(session)
    validation = await narrative.validation.validate_all()

    validation_status = "✅" if validation.is_valid else "⚠️"
    validation_text = (
        f"{validation_status} {validation.errors} errores, {validation.warnings} warnings"
    )

    text = (
        "📊 <b>Estadísticas de Narrativa</b>\n\n"
        "<b>📚 Capítulos:</b>\n"
        f"• Activos: {active_chapters}/{total_chapters}\n"
        f"• 🆓 FREE: {free_chapters}  |  👑 VIP: {vip_chapters}\n\n"
        "<b>📄 Fragmentos:</b>\n"
        f"• Activos: {active_fragments}/{total_fragments}\n"
        f"• 🚪 Entry Points: {entry_points}\n"
        f"• 🏁 Endings: {endings}\n\n"
        "<b>📋 Decisiones:</b>\n"
        f"• Configuradas: {active_decisions}\n"
        f"• Promedio por fragmento: {avg_decisions}\n\n"
        "<b>👥 Usuarios:</b>\n"
        f"• Con progreso: {total_users}\n"
        f"• Decisiones tomadas: {user_decisions}\n\n"
        f"<b>🔍 Validación:</b> {validation_text}"
    )

    keyboard = create_inline_keyboard([
        [{"text": "📚 Desglose por Capítulo", "callback_data": "narrative_admin:stats:chapters"}],
        [{"text": "🔍 Ver Validación Completa", "callback_data": "narrative:validate"}],
        [{"text": "🔙 Volver", "callback_data": "admin:narrative"}]
    ])

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


@narrative_admin_router.callback_query(F.data == "narrative_admin:stats:chapters")
async def callback_stats_by_chapter(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Muestra estadísticas desglosadas por capítulo."""
    await callback.answer()

    narrative = NarrativeContainer(session)
    chapters = await narrative.chapter.get_all_chapters(active_only=False)

    text = "📊 <b>Desglose por Capítulo</b>\n\n"

    if not chapters:
        text += "<i>No hay capítulos creados.</i>\n"
    else:
        # Obtener todas las estadísticas con una única consulta optimizada
        stats_by_chapter = await narrative.chapter.get_chapter_stats_bulk()

        for ch in chapters:
            status = "✅" if ch.is_active else "❌"
            type_emoji = "👑" if ch.chapter_type == ChapterType.VIP else "🆓"

            # Obtener estadísticas del diccionario (default 0 si no hay datos)
            stats = stats_by_chapter.get(ch.id, {
                'fragments_count': 0,
                'decisions_count': 0,
                'entry_count': 0,
                'ending_count': 0
            })

            text += (
                f"{status} {type_emoji} <b>{ch.name}</b>\n"
                f"   📄 {stats['fragments_count']} fragmentos | 📋 {stats['decisions_count']} decisiones\n"
                f"   🚪 {stats['entry_count']} entry | 🏁 {stats['ending_count']} endings\n\n"
            )

    keyboard = create_inline_keyboard([
        [{"text": "🔙 Volver", "callback_data": "narrative_admin:stats"}]
    ])

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
