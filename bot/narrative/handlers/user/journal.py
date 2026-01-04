"""
Handler del Diario de Viaje.

Proporciona navegación visual y seguimiento de progreso narrativo:
- Vista de progreso por capítulo
- Lista de fragmentos visitados/bloqueados
- Navegación rápida a fragmentos
- Resumen de pistas encontradas
"""
import logging
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from bot.narrative.services.container import NarrativeContainer
from bot.narrative.services.journal import JournalService, FragmentStatus

logger = logging.getLogger(__name__)

journal_router = Router(name="narrative_journal")


# ========================================
# HELPERS
# ========================================

def get_status_emoji(status: str) -> str:
    """Obtiene emoji según estado del fragmento."""
    emojis = {
        FragmentStatus.VISITED: "✅",
        FragmentStatus.AVAILABLE: "🔓",
        FragmentStatus.LOCKED: "🔒",
        FragmentStatus.CURRENT: "📍",
    }
    return emojis.get(status, "❓")


def format_time(seconds: int) -> str:
    """Formatea segundos a string legible."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"


# ========================================
# HANDLERS
# ========================================

@journal_router.message(Command("diario", "journal"))
async def cmd_journal(message: Message, session: AsyncSession):
    """
    Comando /diario - Muestra el diario de viaje.
    """
    user_id = message.from_user.id

    journal = JournalService(session)
    stats = await journal.get_journey_stats(user_id)

    # Construir mensaje principal
    text = "📔 <b>Tu Diario de Viaje</b>\n\n"

    # Estadísticas generales
    text += "📊 <b>Resumen</b>\n"
    text += f"• Capítulos: {stats['completed_chapters']}/{stats['total_chapters']} "
    text += f"({stats['chapter_progress_percent']}%)\n"
    text += f"• Fragmentos visitados: {stats['fragments_visited']}\n"
    text += f"• Tiempo de lectura: {stats['total_time_formatted']}\n"
    text += f"• Pistas: {stats['clues_found']}/{stats['clues_total']} "
    text += f"({stats['clue_completion_percent']}%)\n"

    # Construir teclado
    keyboard = _build_journal_main_keyboard()

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


@journal_router.callback_query(F.data == "journal:main")
async def callback_journal_main(callback: CallbackQuery, session: AsyncSession):
    """
    Volver al menú principal del diario.
    """
    user_id = callback.from_user.id

    journal = JournalService(session)
    stats = await journal.get_journey_stats(user_id)

    text = "📔 <b>Tu Diario de Viaje</b>\n\n"
    text += "📊 <b>Resumen</b>\n"
    text += f"• Capítulos: {stats['completed_chapters']}/{stats['total_chapters']} "
    text += f"({stats['chapter_progress_percent']}%)\n"
    text += f"• Fragmentos visitados: {stats['fragments_visited']}\n"
    text += f"• Tiempo de lectura: {stats['total_time_formatted']}\n"
    text += f"• Pistas: {stats['clues_found']}/{stats['clues_total']} "
    text += f"({stats['clue_completion_percent']}%)\n"

    keyboard = _build_journal_main_keyboard()

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@journal_router.callback_query(F.data == "journal:chapters")
async def callback_chapters_list(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra lista de capítulos con progreso.
    """
    user_id = callback.from_user.id

    journal = JournalService(session)
    chapters = await journal.get_chapter_progress(user_id)

    text = "📔 <b>Progreso por Capítulo</b>\n\n"

    if not chapters:
        text += "<i>No hay capítulos disponibles.</i>"
    else:
        for chapter in chapters:
            status_icon = "✅" if chapter["is_completed"] else "📖"
            progress = chapter["completion_percent"]

            text += f"{status_icon} <b>{chapter['chapter_name']}</b>\n"
            text += f"   {chapter['visited_fragments']}/{chapter['total_fragments']} "
            text += f"fragmentos ({progress}%)\n"

            if chapter["is_completed"] and chapter["completed_at"]:
                text += f"   <i>Completado: {chapter['completed_at'].strftime('%d/%m/%Y')}</i>\n"
            text += "\n"

    keyboard = _build_chapters_keyboard(chapters)

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@journal_router.callback_query(F.data.startswith("journal:chapter:"))
async def callback_chapter_detail(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra detalle de un capítulo con fragmentos.
    """
    chapter_id = int(callback.data.split(":")[2])
    user_id = callback.from_user.id

    journal = JournalService(session)
    container = NarrativeContainer(session)

    # Obtener capítulo
    chapter = await container.chapter.get_chapter_by_id(chapter_id)
    if not chapter:
        await callback.answer("Capítulo no encontrado", show_alert=True)
        return

    # Obtener fragmentos
    fragments = await journal.get_fragments_by_status(user_id, chapter_id)

    text = f"📖 <b>{chapter.name}</b>\n"
    if chapter.description:
        text += f"<i>{chapter.description}</i>\n"
    text += "\n"

    # Agrupar por estado
    visited = [f for f in fragments if f["status"] == FragmentStatus.VISITED]
    current = [f for f in fragments if f["status"] == FragmentStatus.CURRENT]
    available = [f for f in fragments if f["status"] == FragmentStatus.AVAILABLE]
    locked = [f for f in fragments if f["status"] == FragmentStatus.LOCKED]

    if current:
        text += "📍 <b>Posición actual:</b>\n"
        for f in current:
            text += f"   • {f['title']}\n"
        text += "\n"

    if visited:
        text += f"✅ <b>Visitados:</b> ({len(visited)})\n"
        for f in visited[:5]:  # Mostrar máximo 5
            visits = f"[{f['visit_count']}x]" if f['visit_count'] > 1 else ""
            text += f"   • {f['title']} {visits}\n"
        if len(visited) > 5:
            text += f"   <i>...y {len(visited) - 5} más</i>\n"
        text += "\n"

    if available:
        text += f"🔓 <b>Disponibles:</b> ({len(available)})\n"
        for f in available[:3]:
            text += f"   • {f['title']}\n"
        if len(available) > 3:
            text += f"   <i>...y {len(available) - 3} más</i>\n"
        text += "\n"

    if locked:
        text += f"🔒 <b>Bloqueados:</b> ({len(locked)})\n"
        text += f"   <i>Encuentra pistas y toma decisiones para desbloquear</i>\n"

    keyboard = _build_chapter_detail_keyboard(chapter_id, visited)

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@journal_router.callback_query(F.data == "journal:navigation")
async def callback_quick_navigation(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra fragmentos para navegación rápida.
    """
    user_id = callback.from_user.id

    journal = JournalService(session)
    accessible = await journal.get_accessible_fragments(user_id)

    text = "🧭 <b>Navegación Rápida</b>\n\n"
    text += "Fragmentos que puedes visitar:\n\n"

    if not accessible:
        text += "<i>No has visitado ningún fragmento todavía.</i>\n"
        text += "<i>Inicia la historia con /historia</i>"
    else:
        # Agrupar por capítulo
        by_chapter = {}
        for frag in accessible:
            ch_name = frag["chapter_name"]
            if ch_name not in by_chapter:
                by_chapter[ch_name] = []
            by_chapter[ch_name].append(frag)

        for ch_name, frags in by_chapter.items():
            text += f"📖 <b>{ch_name}</b>\n"
            for f in frags[:3]:
                visits = f"[{f['visit_count']}x]" if f['visit_count'] > 1 else ""
                text += f"   • {f['title']} {visits}\n"
            if len(frags) > 3:
                text += f"   <i>...y {len(frags) - 3} más</i>\n"
            text += "\n"

    keyboard = _build_navigation_keyboard(accessible[:10] if accessible else [])

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@journal_router.callback_query(F.data == "journal:clues")
async def callback_clues_summary(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra resumen de pistas encontradas.
    """
    user_id = callback.from_user.id

    journal = JournalService(session)
    container = NarrativeContainer(session)

    clue_summary = await journal.get_clues_summary(user_id)
    user_clues = await container.clue.get_user_clues(user_id)

    text = "🔍 <b>Tus Pistas</b>\n\n"

    text += f"📊 Progreso: {clue_summary['found_clues']}/{clue_summary['total_clues']} "
    text += f"({clue_summary['completion_percent']}%)\n\n"

    if not user_clues:
        text += "<i>Aún no has encontrado ninguna pista.</i>\n"
        text += "<i>Explora la historia para descubrir pistas ocultas.</i>"
    else:
        # Mostrar pistas por categoría
        by_category = clue_summary.get("by_category", {})
        for category, stats in by_category.items():
            found = stats["found"]
            total = stats["total"]
            text += f"📁 <b>{category.title()}</b>: {found}/{total}\n"

        text += "\n<b>Pistas encontradas:</b>\n"
        for clue in user_clues[:8]:
            icon = clue.get("icon", "🔍")
            name = clue.get("name", "Pista")
            text += f"  {icon} {name}\n"

        if len(user_clues) > 8:
            text += f"\n<i>...y {len(user_clues) - 8} más en tu mochila</i>"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎒 Ver en Mochila",
                callback_data="backpack:filter:clues"
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Volver",
                callback_data="journal:main"
            )
        ]
    ])

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@journal_router.callback_query(F.data.startswith("journal:goto:"))
async def callback_goto_from_journal(callback: CallbackQuery, session: AsyncSession):
    """
    Ir a un fragmento desde el diario.
    """
    fragment_key = callback.data.split(":")[2]

    # Redirigir al handler de story
    # Esto activa el callback_goto_fragment del story_router
    callback.data = f"story:goto:{fragment_key}"

    # Importar y llamar el handler de story
    from bot.narrative.handlers.user.story import show_fragment

    user_id = callback.from_user.id

    await show_fragment(
        message=callback.message,
        session=session,
        fragment_key=fragment_key,
        user_id=user_id,
        is_new_message=False
    )
    await callback.answer("📖 Navegando al fragmento...")


# ========================================
# BUILDERS DE KEYBOARDS
# ========================================

def _build_journal_main_keyboard() -> InlineKeyboardMarkup:
    """Construye teclado principal del diario."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📖 Capítulos",
                callback_data="journal:chapters"
            ),
            InlineKeyboardButton(
                text="🧭 Navegación",
                callback_data="journal:navigation"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔍 Pistas",
                callback_data="journal:clues"
            ),
            InlineKeyboardButton(
                text="🎒 Mochila",
                callback_data="backpack:main"
            )
        ],
        [
            InlineKeyboardButton(
                text="📖 Continuar Historia",
                callback_data="story:continue"
            )
        ]
    ])


def _build_chapters_keyboard(chapters: list) -> InlineKeyboardMarkup:
    """Construye teclado de lista de capítulos."""
    buttons = []

    for chapter in chapters[:6]:  # Máximo 6 capítulos
        status = "✅" if chapter["is_completed"] else "📖"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status} {chapter['chapter_name']}",
                callback_data=f"journal:chapter:{chapter['chapter_id']}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Volver",
            callback_data="journal:main"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _build_chapter_detail_keyboard(
    chapter_id: int,
    visited_fragments: list
) -> InlineKeyboardMarkup:
    """Construye teclado de detalle de capítulo."""
    buttons = []

    # Botones de navegación rápida a fragmentos visitados
    for frag in visited_fragments[:4]:
        buttons.append([
            InlineKeyboardButton(
                text=f"📍 {frag['title'][:25]}...",
                callback_data=f"journal:goto:{frag['fragment_key']}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Capítulos",
            callback_data="journal:chapters"
        ),
        InlineKeyboardButton(
            text="🏠 Diario",
            callback_data="journal:main"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _build_navigation_keyboard(fragments: list) -> InlineKeyboardMarkup:
    """Construye teclado de navegación rápida."""
    buttons = []

    for frag in fragments[:6]:
        title = frag["title"][:20] + "..." if len(frag["title"]) > 20 else frag["title"]
        buttons.append([
            InlineKeyboardButton(
                text=f"📍 {title}",
                callback_data=f"journal:goto:{frag['fragment_key']}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Volver",
            callback_data="journal:main"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
