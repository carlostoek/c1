"""
Handler de administración de fragmentos narrativos.

CRUD completo:
- Listar por capítulo con paginación
- Crear (wizard 6 pasos)
- Ver detalle con decisiones
- Editar campos
- Toggle flags (entry_point, ending)
- Eliminar
"""

import logging
from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.admin.narrative import narrative_admin_router
from bot.narrative.services.container import NarrativeContainer
from bot.states.admin import NarrativeAdminStates
from bot.utils.keyboards import create_inline_keyboard

logger = logging.getLogger(__name__)

FRAGMENTS_PER_PAGE = 6

SPEAKER_OPTIONS = [
    ("diana", "Diana"),
    ("lucien", "Lucien"),
    ("narrator", "Narrator"),
]


# ========================================
# LISTAR FRAGMENTOS
# ========================================

@narrative_admin_router.callback_query(F.data.regexp(r"narrative:fragments:\d+$"))
async def callback_fragments_list(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Lista fragmentos de un capítulo."""
    await callback.answer()

    chapter_id = int(callback.data.split(":")[-1])
    await _show_fragments_page(callback.message, session, chapter_id, page=0, edit=True)


@narrative_admin_router.callback_query(F.data.regexp(r"narrative:fragments:\d+:page:\d+"))
async def callback_fragments_page(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Navega entre páginas de fragmentos."""
    await callback.answer()

    parts = callback.data.split(":")
    chapter_id = int(parts[2])
    page = int(parts[4])

    await _show_fragments_page(callback.message, session, chapter_id, page=page, edit=True)


async def _show_fragments_page(
    message: Message,
    session: AsyncSession,
    chapter_id: int,
    page: int = 0,
    edit: bool = True
):
    """Muestra página de fragmentos de un capítulo."""
    narrative = NarrativeContainer(session)

    chapter = await narrative.chapter.get_chapter_by_id(chapter_id)
    if not chapter:
        await message.edit_text("❌ Capítulo no encontrado.")
        return

    fragments = await narrative.fragment.get_fragments_by_chapter(chapter_id, active_only=False)

    total = len(fragments)
    start = page * FRAGMENTS_PER_PAGE
    end = start + FRAGMENTS_PER_PAGE
    page_fragments = fragments[start:end]

    # Header
    text = (
        f"📄 <b>Fragmentos de: {chapter.name}</b>\n\n"
        f"Total: {total} fragmentos\n\n"
    )

    if not fragments:
        text += "<i>No hay fragmentos en este capítulo.</i>\n"
    else:
        for frag in page_fragments:
            status = "✅" if frag.is_active else "❌"
            flags = ""
            if frag.is_entry_point:
                flags += "🚪"
            if frag.is_ending:
                flags += "🏁"
            text += f"{status} {flags} <b>{frag.title[:30]}</b>\n"
            text += f"   └ <code>{frag.fragment_key}</code>\n"

    # Botones de fragmentos
    buttons = []
    for frag in page_fragments:
        flags = ""
        if frag.is_entry_point:
            flags += "🚪"
        if frag.is_ending:
            flags += "🏁"
        buttons.append([{
            "text": f"{flags}{frag.title[:28]}",
            "callback_data": f"narrative:fragment:view:{frag.fragment_key}"
        }])

    # Paginación
    pagination = []
    if page > 0:
        pagination.append({
            "text": "⬅️ Anterior",
            "callback_data": f"narrative:fragments:{chapter_id}:page:{page - 1}"
        })
    if end < total:
        pagination.append({
            "text": "Siguiente ➡️",
            "callback_data": f"narrative:fragments:{chapter_id}:page:{page + 1}"
        })
    if pagination:
        buttons.append(pagination)

    # Acciones
    buttons.append([{
        "text": "➕ Crear Fragmento",
        "callback_data": f"narrative:fragment:create:{chapter_id}"
    }])
    buttons.append([{
        "text": "🔙 Volver al Capítulo",
        "callback_data": f"narrative:chapter:view:{chapter_id}"
    }])

    keyboard = create_inline_keyboard(buttons)

    if edit:
        await message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


# ========================================
# VER DETALLE DE FRAGMENTO
# ========================================

@narrative_admin_router.callback_query(F.data.startswith("narrative:fragment:view:"))
async def callback_fragment_view(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Muestra detalle de un fragmento."""
    await callback.answer()

    fragment_key = callback.data.replace("narrative:fragment:view:", "")
    narrative = NarrativeContainer(session)
    fragment = await narrative.fragment.get_fragment_with_decisions(fragment_key)

    if not fragment:
        await callback.message.edit_text(
            "❌ Fragmento no encontrado.",
            reply_markup=create_inline_keyboard([[{
                "text": "🔙 Volver",
                "callback_data": "narrative:chapters"
            }]])
        )
        return

    # Contar decisiones activas
    decisions_count = len([d for d in fragment.decisions if d.is_active]) if fragment.decisions else 0

    status = "✅ Activo" if fragment.is_active else "❌ Inactivo"
    flags = []
    if fragment.is_entry_point:
        flags.append("🚪 Entry Point")
    if fragment.is_ending:
        flags.append("🏁 Ending")

    speaker_emojis = {"diana": "🌸", "lucien": "🎩", "narrator": "📖"}
    speaker_emoji = speaker_emojis.get(fragment.speaker, "💬")

    text = (
        f"📄 <b>{fragment.title}</b>\n\n"
        f"<b>Key:</b> <code>{fragment.fragment_key}</code>\n"
        f"<b>Speaker:</b> {speaker_emoji} {fragment.speaker.title()}\n"
        f"<b>Orden:</b> {fragment.order}\n"
        f"<b>Estado:</b> {status}\n"
        f"<b>Decisiones:</b> {decisions_count}\n"
    )

    if flags:
        text += f"<b>Flags:</b> {', '.join(flags)}\n"

    if fragment.visual_hint:
        text += f"\n<b>Visual Hint:</b>\n<i>{fragment.visual_hint[:100]}...</i>\n"

    # Mostrar preview del contenido
    content_preview = fragment.content[:200] + "..." if len(fragment.content) > 200 else fragment.content
    text += f"\n<b>Contenido:</b>\n{content_preview}\n"

    keyboard = create_inline_keyboard([
        [{
            "text": "📋 Ver Decisiones",
            "callback_data": f"narrative:decisions:{fragment_key}"
        }],
        [
            {"text": "✏️ Editar", "callback_data": f"narrative:fragment:edit:{fragment_key}"},
            {"text": "🏷️ Flags", "callback_data": f"narrative:fragment:flags:{fragment_key}"}
        ],
        [{
            "text": "🗑️ Eliminar",
            "callback_data": f"narrative:fragment:delete:{fragment_key}"
        }],
        [{
            "text": "🔙 Volver",
            "callback_data": f"narrative:fragments:{fragment.chapter_id}"
        }]
    ])

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)


# ========================================
# CREAR FRAGMENTO (WIZARD 6 PASOS)
# ========================================

@narrative_admin_router.callback_query(F.data.regexp(r"narrative:fragment:create:\d+"))
async def callback_fragment_create_start(
    callback: CallbackQuery,
    state: FSMContext
):
    """Inicia wizard de creación de fragmento."""
    await callback.answer()

    chapter_id = int(callback.data.split(":")[-1])
    await state.update_data(fragment_chapter_id=chapter_id)
    await state.set_state(NarrativeAdminStates.waiting_for_fragment_key)

    keyboard = create_inline_keyboard([[{
        "text": "❌ Cancelar",
        "callback_data": f"narrative:fragments:{chapter_id}"
    }]])

    await callback.message.edit_text(
        "📄 <b>Crear Fragmento - Paso 1/6</b>\n\n"
        "Envía el <b>fragment_key</b> único.\n\n"
        "<i>Ejemplo: scene_01, dialog_intro, ending_happy</i>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@narrative_admin_router.message(NarrativeAdminStates.waiting_for_fragment_key)
async def process_fragment_key(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Procesa fragment_key."""
    fragment_key = message.text.strip().lower().replace(" ", "_")

    if len(fragment_key) < 2 or len(fragment_key) > 50:
        await message.answer(
            "❌ El key debe tener entre 2 y 50 caracteres.\n"
            "Intenta de nuevo:"
        )
        return

    # Verificar que no exista
    narrative = NarrativeContainer(session)
    existing = await narrative.fragment.get_fragment(fragment_key)
    if existing:
        await message.answer(
            f"❌ Ya existe un fragmento con key '<code>{fragment_key}</code>'.\n"
            "Elige otro:",
            parse_mode="HTML"
        )
        return

    await state.update_data(fragment_key=fragment_key)
    await state.set_state(NarrativeAdminStates.waiting_for_fragment_title)

    data = await state.get_data()
    chapter_id = data["fragment_chapter_id"]

    keyboard = create_inline_keyboard([[{
        "text": "❌ Cancelar",
        "callback_data": f"narrative:fragments:{chapter_id}"
    }]])

    await message.answer(
        "📄 <b>Crear Fragmento - Paso 2/6</b>\n\n"
        f"Key: <code>{fragment_key}</code>\n\n"
        "Envía el <b>título</b> del fragmento.\n\n"
        "<i>Ejemplo: El Encuentro</i>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@narrative_admin_router.message(NarrativeAdminStates.waiting_for_fragment_title)
async def process_fragment_title(
    message: Message,
    state: FSMContext
):
    """Procesa título del fragmento."""
    title = message.text.strip()

    if len(title) < 2 or len(title) > 100:
        await message.answer(
            "❌ El título debe tener entre 2 y 100 caracteres.\n"
            "Intenta de nuevo:"
        )
        return

    await state.update_data(fragment_title=title)
    await state.set_state(NarrativeAdminStates.waiting_for_fragment_speaker)

    data = await state.get_data()

    buttons = []
    for speaker_id, speaker_name in SPEAKER_OPTIONS:
        buttons.append([{
            "text": f"{'🌸' if speaker_id == 'diana' else '🎩' if speaker_id == 'lucien' else '📖'} {speaker_name}",
            "callback_data": f"narrative:fragment:speaker:{speaker_id}"
        }])
    buttons.append([{
        "text": "❌ Cancelar",
        "callback_data": f"narrative:fragments:{data['fragment_chapter_id']}"
    }])

    await message.answer(
        "📄 <b>Crear Fragmento - Paso 3/6</b>\n\n"
        f"Key: <code>{data['fragment_key']}</code>\n"
        f"Título: <b>{title}</b>\n\n"
        "Selecciona el <b>speaker</b> (quién habla):",
        parse_mode="HTML",
        reply_markup=create_inline_keyboard(buttons)
    )


@narrative_admin_router.callback_query(
    NarrativeAdminStates.waiting_for_fragment_speaker,
    F.data.startswith("narrative:fragment:speaker:")
)
async def process_fragment_speaker(
    callback: CallbackQuery,
    state: FSMContext
):
    """Procesa speaker del fragmento."""
    await callback.answer()

    speaker = callback.data.split(":")[-1]
    await state.update_data(fragment_speaker=speaker)
    await state.set_state(NarrativeAdminStates.waiting_for_fragment_content)

    data = await state.get_data()

    keyboard = create_inline_keyboard([[{
        "text": "❌ Cancelar",
        "callback_data": f"narrative:fragments:{data['fragment_chapter_id']}"
    }]])

    speaker_name = next((s[1] for s in SPEAKER_OPTIONS if s[0] == speaker), speaker)

    await callback.message.edit_text(
        "📄 <b>Crear Fragmento - Paso 4/6</b>\n\n"
        f"Key: <code>{data['fragment_key']}</code>\n"
        f"Título: <b>{data['fragment_title']}</b>\n"
        f"Speaker: <b>{speaker_name}</b>\n\n"
        "Envía el <b>contenido</b> del fragmento.\n\n"
        "<i>Puedes usar HTML: &lt;b&gt;negrita&lt;/b&gt;, &lt;i&gt;cursiva&lt;/i&gt;</i>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@narrative_admin_router.message(NarrativeAdminStates.waiting_for_fragment_content)
async def process_fragment_content(
    message: Message,
    state: FSMContext
):
    """Procesa contenido del fragmento."""
    content = message.text.strip()

    if len(content) < 10:
        await message.answer(
            "❌ El contenido es muy corto (mínimo 10 caracteres).\n"
            "Intenta de nuevo:"
        )
        return

    if len(content) > 4000:
        await message.answer(
            "❌ El contenido es muy largo (máximo 4000 caracteres).\n"
            "Intenta de nuevo:"
        )
        return

    await state.update_data(fragment_content=content)
    await state.set_state(NarrativeAdminStates.waiting_for_fragment_order)

    data = await state.get_data()

    keyboard = create_inline_keyboard([[{
        "text": "❌ Cancelar",
        "callback_data": f"narrative:fragments:{data['fragment_chapter_id']}"
    }]])

    await message.answer(
        "📄 <b>Crear Fragmento - Paso 5/6</b>\n\n"
        f"Key: <code>{data['fragment_key']}</code>\n"
        f"Título: <b>{data['fragment_title']}</b>\n\n"
        "Envía el <b>orden</b> del fragmento (número).\n\n"
        "<i>El orden determina la secuencia en el capítulo (0, 1, 2...)</i>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@narrative_admin_router.message(NarrativeAdminStates.waiting_for_fragment_order)
async def process_fragment_order(
    message: Message,
    state: FSMContext
):
    """Procesa orden del fragmento."""
    try:
        order = int(message.text.strip())
        if order < 0:
            raise ValueError()
    except ValueError:
        await message.answer(
            "❌ Envía un número entero >= 0.\n"
            "Intenta de nuevo:"
        )
        return

    await state.update_data(fragment_order=order)
    await state.set_state(NarrativeAdminStates.waiting_for_fragment_flags)

    data = await state.get_data()

    keyboard = create_inline_keyboard([
        [{"text": "🚪 Entry Point", "callback_data": "narrative:fragment:flag:entry"}],
        [{"text": "🏁 Ending", "callback_data": "narrative:fragment:flag:ending"}],
        [{"text": "✅ Sin flags (normal)", "callback_data": "narrative:fragment:flag:none"}],
        [{"text": "❌ Cancelar", "callback_data": f"narrative:fragments:{data['fragment_chapter_id']}"}]
    ])

    await message.answer(
        "📄 <b>Crear Fragmento - Paso 6/6</b>\n\n"
        f"Key: <code>{data['fragment_key']}</code>\n"
        f"Título: <b>{data['fragment_title']}</b>\n"
        f"Orden: <b>{order}</b>\n\n"
        "Selecciona los <b>flags</b> del fragmento:\n\n"
        "🚪 <b>Entry Point:</b> Punto de entrada del capítulo\n"
        "🏁 <b>Ending:</b> Final del capítulo (no requiere decisiones)",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@narrative_admin_router.callback_query(
    NarrativeAdminStates.waiting_for_fragment_flags,
    F.data.startswith("narrative:fragment:flag:")
)
async def process_fragment_flags(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Procesa flags y crea el fragmento."""
    await callback.answer()

    flag = callback.data.split(":")[-1]

    is_entry_point = flag == "entry"
    is_ending = flag == "ending"

    data = await state.get_data()
    await state.clear()

    narrative = NarrativeContainer(session)

    try:
        fragment = await narrative.fragment.create_fragment(
            chapter_id=data["fragment_chapter_id"],
            fragment_key=data["fragment_key"],
            title=data["fragment_title"],
            speaker=data["fragment_speaker"],
            content=data["fragment_content"],
            order=data["fragment_order"],
            is_entry_point=is_entry_point,
            is_ending=is_ending
        )

        flags_text = []
        if is_entry_point:
            flags_text.append("🚪 Entry Point")
        if is_ending:
            flags_text.append("🏁 Ending")

        text = (
            "✅ <b>Fragmento Creado</b>\n\n"
            f"<b>Key:</b> <code>{fragment.fragment_key}</code>\n"
            f"<b>Título:</b> {fragment.title}\n"
            f"<b>Orden:</b> {fragment.order}\n"
        )

        if flags_text:
            text += f"<b>Flags:</b> {', '.join(flags_text)}\n"

        keyboard = create_inline_keyboard([
            [{"text": "📋 Agregar Decisiones", "callback_data": f"narrative:decisions:{fragment.fragment_key}"}],
            [{"text": "🔙 Ver Fragmentos", "callback_data": f"narrative:fragments:{fragment.chapter_id}"}]
        ])

        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)

    except ValueError as e:
        await callback.message.edit_text(f"❌ Error: {e}")


# ========================================
# EDITAR FRAGMENTO
# ========================================

@narrative_admin_router.callback_query(F.data.startswith("narrative:fragment:edit:"))
async def callback_fragment_edit_menu(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Muestra menú de edición del fragmento."""
    await callback.answer()

    fragment_key = callback.data.replace("narrative:fragment:edit:", "")
    narrative = NarrativeContainer(session)
    fragment = await narrative.fragment.get_fragment(fragment_key)

    if not fragment:
        await callback.message.edit_text("❌ Fragmento no encontrado.")
        return

    text = (
        f"✏️ <b>Editar: {fragment.title}</b>\n\n"
        "Selecciona el campo a editar:"
    )

    keyboard = create_inline_keyboard([
        [{"text": "📝 Título", "callback_data": f"narrative:fragment:edit:title:{fragment_key}"}],
        [{"text": "📋 Contenido", "callback_data": f"narrative:fragment:edit:content:{fragment_key}"}],
        [{"text": "👤 Speaker", "callback_data": f"narrative:fragment:edit:speaker:{fragment_key}"}],
        [{"text": "🖼️ Visual Hint", "callback_data": f"narrative:fragment:edit:visual:{fragment_key}"}],
        [{"text": "🔙 Volver", "callback_data": f"narrative:fragment:view:{fragment_key}"}]
    ])

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)


@narrative_admin_router.callback_query(F.data.regexp(r"narrative:fragment:edit:title:.+"))
async def callback_edit_fragment_title_start(
    callback: CallbackQuery,
    state: FSMContext
):
    """Inicia edición de título."""
    await callback.answer()

    fragment_key = callback.data.replace("narrative:fragment:edit:title:", "")
    await state.update_data(editing_fragment_key=fragment_key)
    await state.set_state(NarrativeAdminStates.editing_fragment_title)

    keyboard = create_inline_keyboard([[{
        "text": "❌ Cancelar",
        "callback_data": f"narrative:fragment:view:{fragment_key}"
    }]])

    await callback.message.edit_text(
        "📝 <b>Editar Título</b>\n\n"
        "Envía el nuevo título del fragmento:",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@narrative_admin_router.message(NarrativeAdminStates.editing_fragment_title)
async def process_edit_fragment_title(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Procesa nuevo título."""
    new_title = message.text.strip()

    if len(new_title) < 2 or len(new_title) > 100:
        await message.answer("❌ El título debe tener entre 2 y 100 caracteres.")
        return

    data = await state.get_data()
    fragment_key = data["editing_fragment_key"]
    await state.clear()

    narrative = NarrativeContainer(session)
    await narrative.fragment.update_fragment(fragment_key, title=new_title)

    keyboard = create_inline_keyboard([[{
        "text": "🔙 Volver al fragmento",
        "callback_data": f"narrative:fragment:view:{fragment_key}"
    }]])

    await message.answer(
        f"✅ Título actualizado a: <b>{new_title}</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@narrative_admin_router.callback_query(F.data.regexp(r"narrative:fragment:edit:content:.+"))
async def callback_edit_fragment_content_start(
    callback: CallbackQuery,
    state: FSMContext
):
    """Inicia edición de contenido."""
    await callback.answer()

    fragment_key = callback.data.replace("narrative:fragment:edit:content:", "")
    await state.update_data(editing_fragment_key=fragment_key)
    await state.set_state(NarrativeAdminStates.editing_fragment_content)

    keyboard = create_inline_keyboard([[{
        "text": "❌ Cancelar",
        "callback_data": f"narrative:fragment:view:{fragment_key}"
    }]])

    await callback.message.edit_text(
        "📋 <b>Editar Contenido</b>\n\n"
        "Envía el nuevo contenido del fragmento (máx 4000 caracteres).\n\n"
        "<i>Puedes usar HTML.</i>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@narrative_admin_router.message(NarrativeAdminStates.editing_fragment_content)
async def process_edit_fragment_content(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Procesa nuevo contenido."""
    new_content = message.text.strip()

    if len(new_content) < 10:
        await message.answer("❌ El contenido es muy corto (mínimo 10 caracteres).")
        return

    if len(new_content) > 4000:
        await message.answer("❌ El contenido es muy largo (máximo 4000 caracteres).")
        return

    data = await state.get_data()
    fragment_key = data["editing_fragment_key"]
    await state.clear()

    narrative = NarrativeContainer(session)
    await narrative.fragment.update_fragment(fragment_key, content=new_content)

    keyboard = create_inline_keyboard([[{
        "text": "🔙 Volver al fragmento",
        "callback_data": f"narrative:fragment:view:{fragment_key}"
    }]])

    await message.answer(
        "✅ Contenido actualizado.",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@narrative_admin_router.callback_query(F.data.regexp(r"narrative:fragment:edit:speaker:.+"))
async def callback_edit_fragment_speaker_start(
    callback: CallbackQuery,
    state: FSMContext
):
    """Inicia edición de speaker."""
    await callback.answer()

    fragment_key = callback.data.replace("narrative:fragment:edit:speaker:", "")
    await state.update_data(editing_fragment_key=fragment_key)
    await state.set_state(NarrativeAdminStates.editing_fragment_speaker)

    buttons = []
    for speaker_id, speaker_name in SPEAKER_OPTIONS:
        emoji = "🌸" if speaker_id == "diana" else "🎩" if speaker_id == "lucien" else "📖"
        buttons.append([{
            "text": f"{emoji} {speaker_name}",
            "callback_data": f"narrative:fragment:set_speaker:{speaker_id}"
        }])
    buttons.append([{
        "text": "❌ Cancelar",
        "callback_data": f"narrative:fragment:view:{fragment_key}"
    }])

    await callback.message.edit_text(
        "👤 <b>Editar Speaker</b>\n\n"
        "Selecciona el nuevo speaker:",
        parse_mode="HTML",
        reply_markup=create_inline_keyboard(buttons)
    )


@narrative_admin_router.callback_query(
    NarrativeAdminStates.editing_fragment_speaker,
    F.data.startswith("narrative:fragment:set_speaker:")
)
async def process_edit_fragment_speaker(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Procesa nuevo speaker."""
    await callback.answer()

    speaker = callback.data.split(":")[-1]
    data = await state.get_data()
    fragment_key = data["editing_fragment_key"]
    await state.clear()

    narrative = NarrativeContainer(session)
    await narrative.fragment.update_fragment(fragment_key, speaker=speaker)

    speaker_name = next((s[1] for s in SPEAKER_OPTIONS if s[0] == speaker), speaker)

    keyboard = create_inline_keyboard([[{
        "text": "🔙 Volver al fragmento",
        "callback_data": f"narrative:fragment:view:{fragment_key}"
    }]])

    await callback.message.edit_text(
        f"✅ Speaker actualizado a: <b>{speaker_name}</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@narrative_admin_router.callback_query(F.data.regexp(r"narrative:fragment:edit:visual:.+"))
async def callback_edit_fragment_visual_start(
    callback: CallbackQuery,
    state: FSMContext
):
    """Inicia edición de visual hint."""
    await callback.answer()

    fragment_key = callback.data.replace("narrative:fragment:edit:visual:", "")
    await state.update_data(editing_fragment_key=fragment_key)
    await state.set_state(NarrativeAdminStates.editing_fragment_visual_hint)

    keyboard = create_inline_keyboard([[{
        "text": "❌ Cancelar",
        "callback_data": f"narrative:fragment:view:{fragment_key}"
    }]])

    await callback.message.edit_text(
        "🖼️ <b>Editar Visual Hint</b>\n\n"
        "Envía la nueva descripción visual.\n"
        "Envía '-' para eliminar el visual hint.",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@narrative_admin_router.message(NarrativeAdminStates.editing_fragment_visual_hint)
async def process_edit_fragment_visual(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Procesa nuevo visual hint."""
    visual_hint = message.text.strip()

    if visual_hint == "-":
        visual_hint = None
    elif len(visual_hint) > 500:
        await message.answer("❌ El visual hint es muy largo (máximo 500 caracteres).")
        return

    data = await state.get_data()
    fragment_key = data["editing_fragment_key"]
    await state.clear()

    narrative = NarrativeContainer(session)
    await narrative.fragment.update_fragment(fragment_key, visual_hint=visual_hint)

    result = "eliminado" if visual_hint is None else "actualizado"

    keyboard = create_inline_keyboard([[{
        "text": "🔙 Volver al fragmento",
        "callback_data": f"narrative:fragment:view:{fragment_key}"
    }]])

    await message.answer(
        f"✅ Visual hint {result}.",
        parse_mode="HTML",
        reply_markup=keyboard
    )


# ========================================
# FLAGS (ENTRY POINT, ENDING)
# ========================================

@narrative_admin_router.callback_query(F.data.startswith("narrative:fragment:flags:"))
async def callback_fragment_flags_menu(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Muestra menú de flags del fragmento."""
    await callback.answer()

    fragment_key = callback.data.replace("narrative:fragment:flags:", "")
    narrative = NarrativeContainer(session)
    fragment = await narrative.fragment.get_fragment(fragment_key)

    if not fragment:
        await callback.message.edit_text("❌ Fragmento no encontrado.")
        return

    entry_status = "✅" if fragment.is_entry_point else "❌"
    ending_status = "✅" if fragment.is_ending else "❌"

    text = (
        f"🏷️ <b>Flags: {fragment.title}</b>\n\n"
        f"🚪 Entry Point: {entry_status}\n"
        f"🏁 Ending: {ending_status}\n\n"
        "<i>Toggle para cambiar estado.</i>"
    )

    keyboard = create_inline_keyboard([
        [{
            "text": f"🚪 Entry Point: {entry_status}",
            "callback_data": f"narrative:fragment:toggle:entry:{fragment_key}"
        }],
        [{
            "text": f"🏁 Ending: {ending_status}",
            "callback_data": f"narrative:fragment:toggle:ending:{fragment_key}"
        }],
        [{"text": "🔙 Volver", "callback_data": f"narrative:fragment:view:{fragment_key}"}]
    ])

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)


@narrative_admin_router.callback_query(F.data.regexp(r"narrative:fragment:toggle:(entry|ending):.+"))
async def callback_fragment_toggle_flag(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Toggle un flag del fragmento."""
    parts = callback.data.split(":")
    flag_type = parts[3]
    fragment_key = parts[4]

    narrative = NarrativeContainer(session)
    fragment = await narrative.fragment.get_fragment(fragment_key)

    if not fragment:
        await callback.answer("❌ Fragmento no encontrado", show_alert=True)
        return

    if flag_type == "entry":
        new_value = not fragment.is_entry_point
        await narrative.fragment.update_fragment(fragment_key, is_entry_point=new_value)
        await callback.answer(f"🚪 Entry Point: {'Activado' if new_value else 'Desactivado'}")
    else:
        new_value = not fragment.is_ending
        await narrative.fragment.update_fragment(fragment_key, is_ending=new_value)
        await callback.answer(f"🏁 Ending: {'Activado' if new_value else 'Desactivado'}")

    # Recargar menú de flags
    fragment = await narrative.fragment.get_fragment(fragment_key)

    entry_status = "✅" if fragment.is_entry_point else "❌"
    ending_status = "✅" if fragment.is_ending else "❌"

    text = (
        f"🏷️ <b>Flags: {fragment.title}</b>\n\n"
        f"🚪 Entry Point: {entry_status}\n"
        f"🏁 Ending: {ending_status}\n\n"
        "<i>Toggle para cambiar estado.</i>"
    )

    keyboard = create_inline_keyboard([
        [{
            "text": f"🚪 Entry Point: {entry_status}",
            "callback_data": f"narrative:fragment:toggle:entry:{fragment_key}"
        }],
        [{
            "text": f"🏁 Ending: {ending_status}",
            "callback_data": f"narrative:fragment:toggle:ending:{fragment_key}"
        }],
        [{"text": "🔙 Volver", "callback_data": f"narrative:fragment:view:{fragment_key}"}]
    ])

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)


# ========================================
# ELIMINAR FRAGMENTO
# ========================================

@narrative_admin_router.callback_query(F.data.startswith("narrative:fragment:delete:"))
async def callback_fragment_delete(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Confirma eliminación de fragmento."""
    await callback.answer()

    fragment_key = callback.data.replace("narrative:fragment:delete:", "")
    narrative = NarrativeContainer(session)
    fragment = await narrative.fragment.get_fragment_with_decisions(fragment_key)

    if not fragment:
        await callback.message.edit_text("❌ Fragmento no encontrado.")
        return

    decisions_count = len([d for d in fragment.decisions if d.is_active]) if fragment.decisions else 0

    text = (
        f"⚠️ <b>¿Eliminar fragmento?</b>\n\n"
        f"<b>{fragment.title}</b>\n"
        f"Key: <code>{fragment.fragment_key}</code>\n"
        f"Decisiones: {decisions_count}\n\n"
        "<i>Esta acción eliminará el fragmento y sus decisiones.</i>"
    )

    keyboard = create_inline_keyboard([
        [
            {"text": "🗑️ Sí, eliminar", "callback_data": f"narrative:fragment:confirm_delete:{fragment_key}"},
            {"text": "❌ Cancelar", "callback_data": f"narrative:fragment:view:{fragment_key}"}
        ]
    ])

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)


@narrative_admin_router.callback_query(F.data.startswith("narrative:fragment:confirm_delete:"))
async def callback_fragment_confirm_delete(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Ejecuta eliminación del fragmento."""
    fragment_key = callback.data.replace("narrative:fragment:confirm_delete:", "")

    narrative = NarrativeContainer(session)
    fragment = await narrative.fragment.get_fragment(fragment_key)

    if not fragment:
        await callback.answer("❌ Fragmento no encontrado", show_alert=True)
        return

    chapter_id = fragment.chapter_id
    await narrative.fragment.delete_fragment(fragment_key)

    await callback.answer("🗑️ Fragmento eliminado", show_alert=True)
    await _show_fragments_page(callback.message, session, chapter_id, page=0, edit=True)
