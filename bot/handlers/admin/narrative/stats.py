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
    NarrativeChapter, NarrativeFragment, UserNarrativeProgress,
    UserDecisionHistory
)
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

    # Contar capítulos
    stmt_chapters = select(func.count()).select_from(NarrativeChapter).where(
        NarrativeChapter.is_active == True
    )
    result = await session.execute(stmt_chapters)
    total_chapters = result.scalar_one()

    # Contar fragmentos
    stmt_fragments = select(func.count()).select_from(NarrativeFragment).where(
        NarrativeFragment.is_active == True
    )
    result = await session.execute(stmt_fragments)
    total_fragments = result.scalar_one()

    # Contar usuarios con progreso
    stmt_users = select(func.count()).select_from(UserNarrativeProgress)
    result = await session.execute(stmt_users)
    total_users = result.scalar_one()

    # Contar decisiones tomadas
    stmt_decisions = select(func.count()).select_from(UserDecisionHistory)
    result = await session.execute(stmt_decisions)
    total_decisions = result.scalar_one()

    text = (
        "📊 <b>Estadísticas de Narrativa</b>\n\n"
        "<b>Contenido:</b>\n"
        f"📚 Capítulos activos: {total_chapters}\n"
        f"📄 Fragmentos activos: {total_fragments}\n\n"
        "<b>Usuarios:</b>\n"
        f"👥 Usuarios con progreso: {total_users}\n"
        f"🎯 Decisiones tomadas: {total_decisions}\n"
    )

    keyboard = create_inline_keyboard([
        [{"text": "🔙 Volver", "callback_data": "admin:narrative"}]
    ])

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
