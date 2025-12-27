"""
Handler de administración de capítulos narrativos.

CRUD completo:
- Listar con paginación
- Crear (wizard 4 pasos)
- Ver detalle
- Editar campos
- Toggle activo
- Eliminar
"""

import logging
from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.admin.narrative import narrative_admin_router
from bot.narrative.services.container import NarrativeContainer
from bot.narrative.database import ChapterType
from bot.states.admin import NarrativeAdminStates
from bot.utils.keyboards import create_inline_keyboard

logger = logging.getLogger(__name__)

CHAPTERS_PER_PAGE = 5


# ========================================
# LISTAR CAPÍTULOS
# ========================================

@narrative_admin_router.callback_query(F.data == "narrative:chapters")
async def callback_chapters_list(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Lista todos los capítulos."""
    await callback.answer()
    await _show_chapters_page(callback.message, session, page=0, edit=True)


@narrative_admin_router.callback_query(F.data.startswith("narrative:chapters:page:"))
async def callback_chapters_page(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Navega entre páginas de capítulos."""
    await callback.answer()
    page = int(callback.data.split(":")[-1])
    await _show_chapters_page(callback.message, session, page=page, edit=True)


async def _show_chapters_page(
    message: Message,
    session: AsyncSession,
    page: int = 0,
    edit: bool = True
):
    """Muestra página de capítulos con paginación a nivel de BD."""
    narrative = NarrativeContainer(session)

    # Obtener total de capítulos con consulta optimizada
    total = await narrative.chapter.get_chapters_count(active_only=False)

    # Calcular offset y obtener solo los capítulos de la página actual
    offset = page * CHAPTERS_PER_PAGE
    page_chapters = await narrative.chapter.get_all_chapters(
        active_only=False,
        limit=CHAPTERS_PER_PAGE,
        offset=offset
    )

    # Header
    text = (
        "📚 <b>Gestión de Capítulos</b>\n\n"
        f"Total: {total} capítulos\n\n"
    )

    if total == 0:
        text += "<i>No hay capítulos creados.</i>\n"
    else:
        for ch in page_chapters:
            status = "✅" if ch.is_active else "❌"
            type_emoji = "👑" if ch.chapter_type == ChapterType.VIP else "🆓"
            text += f"{status} {type_emoji} <b>{ch.name}</b>\n"
            text += f"   └ <code>{ch.slug}</code>\n"

    # Botones de capítulos
    buttons = []
    for ch in page_chapters:
        emoji = "👑" if ch.chapter_type == ChapterType.VIP else "🆓"
        buttons.append([{
            "text": f"{emoji} {ch.name[:25]}",
            "callback_data": f"narrative:chapter:view:{ch.id}"
        }])

    # Paginación
    pagination = []
    if page > 0:
        pagination.append({
            "text": "⬅️ Anterior",
            "callback_data": f"narrative:chapters:page:{page - 1}"
        })
    # Verificar si hay más páginas
    if offset + CHAPTERS_PER_PAGE < total:
        pagination.append({
            "text": "Siguiente ➡️",
            "callback_data": f"narrative:chapters:page:{page + 1}"
        })
    if pagination:
        buttons.append(pagination)

    # Acciones
    buttons.append([{
        "text": "➕ Crear Capítulo",
        "callback_data": "narrative:chapter:create"
    }])
    buttons.append([{
        "text": "🔙 Volver",
        "callback_data": "admin:narrative"
    }])

    keyboard = create_inline_keyboard(buttons)

    if edit:
        await message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


# ========================================
# VER DETALLE DE CAPÍTULO
# ========================================

@narrative_admin_router.callback_query(F.data.startswith("narrative:chapter:view:"))
async def callback_chapter_view(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Muestra detalle de un capítulo."""
    await callback.answer()

    chapter_id = int(callback.data.split(":")[-1])
    narrative = NarrativeContainer(session)
    chapter = await narrative.chapter.get_chapter_by_id(chapter_id)

    if not chapter:
        await callback.message.edit_text(
            "❌ Capítulo no encontrado.",
            reply_markup=create_inline_keyboard([[{
                "text": "🔙 Volver",
                "callback_data": "narrative:chapters"
            }]])
        )
        return

    # Contar fragmentos
    fragments_count = await narrative.chapter.get_chapter_fragments_count(chapter_id)

    status = "✅ Activo" if chapter.is_active else "❌ Inactivo"
    type_text = "👑 VIP" if chapter.chapter_type == ChapterType.VIP else "🆓 FREE"

    text = (
        f"📖 <b>{chapter.name}</b>\n\n"
        f"<b>Slug:</b> <code>{chapter.slug}</code>\n"
        f"<b>Tipo:</b> {type_text}\n"
        f"<b>Estado:</b> {status}\n"
        f"<b>Orden:</b> {chapter.order}\n"
        f"<b>Fragmentos:</b> {fragments_count}\n"
    )

    if chapter.description:
        text += f"\n<b>Descripción:</b>\n{chapter.description}\n"

    toggle_text = "❌ Desactivar" if chapter.is_active else "✅ Activar"

    keyboard = create_inline_keyboard([
        [{
            "text": "📄 Ver Fragmentos",
            "callback_data": f"narrative:fragments:{chapter_id}"
        }],
        [
            {"text": "✏️ Editar", "callback_data": f"narrative:chapter:edit:{chapter_id}"},
            {"text": toggle_text, "callback_data": f"narrative:chapter:toggle:{chapter_id}"}
        ],
        [{
            "text": "🗑️ Eliminar",
            "callback_data": f"narrative:chapter:delete:{chapter_id}"
        }],
        [{
            "text": "🔙 Volver",
            "callback_data": "narrative:chapters"
        }]
    ])

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)


# ========================================
# CREAR CAPÍTULO (WIZARD 4 PASOS)
# ========================================

@narrative_admin_router.callback_query(F.data == "narrative:chapter:create")
async def callback_chapter_create_start(
    callback: CallbackQuery,
    state: FSMContext
):
    """Inicia wizard de creación de capítulo."""
    await callback.answer()

    await state.set_state(NarrativeAdminStates.waiting_for_chapter_name)

    keyboard = create_inline_keyboard([[{
        "text": "❌ Cancelar",
        "callback_data": "narrative:chapters"
    }]])

    await callback.message.edit_text(
        "📚 <b>Crear Capítulo - Paso 1/4</b>\n\n"
        "Envía el <b>nombre</b> del capítulo.\n\n"
        "<i>Ejemplo: Los Kinkys</i>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@narrative_admin_router.message(NarrativeAdminStates.waiting_for_chapter_name)
async def process_chapter_name(
    message: Message,
    state: FSMContext
):
    """Procesa nombre del capítulo."""
    name = message.text.strip()

    if len(name) < 2 or len(name) > 100:
        await message.answer(
            "❌ El nombre debe tener entre 2 y 100 caracteres.\n"
            "Intenta de nuevo:"
        )
        return

    await state.update_data(chapter_name=name)
    await state.set_state(NarrativeAdminStates.waiting_for_chapter_slug)

    keyboard = create_inline_keyboard([[{
        "text": "❌ Cancelar",
        "callback_data": "narrative:chapters"
    }]])

    # Sugerir slug
    suggested_slug = name.lower().replace(" ", "-")[:30]

    await message.answer(
        "📚 <b>Crear Capítulo - Paso 2/4</b>\n\n"
        f"Nombre: <b>{name}</b>\n\n"
        "Envía el <b>slug</b> único (identificador URL).\n\n"
        f"<i>Sugerencia: {suggested_slug}</i>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@narrative_admin_router.message(NarrativeAdminStates.waiting_for_chapter_slug)
async def process_chapter_slug(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Procesa slug del capítulo."""
    slug = message.text.strip().lower().replace(" ", "-")

    if len(slug) < 2 or len(slug) > 50:
        await message.answer(
            "❌ El slug debe tener entre 2 y 50 caracteres.\n"
            "Intenta de nuevo:"
        )
        return

    # Verificar que no exista
    narrative = NarrativeContainer(session)
    existing = await narrative.chapter.get_chapter_by_slug(slug)
    if existing:
        await message.answer(
            f"❌ Ya existe un capítulo con slug '<code>{slug}</code>'.\n"
            "Elige otro slug:",
            parse_mode="HTML"
        )
        return

    await state.update_data(chapter_slug=slug)
    await state.set_state(NarrativeAdminStates.waiting_for_chapter_type)

    data = await state.get_data()

    keyboard = create_inline_keyboard([
        [
            {"text": "🆓 FREE", "callback_data": "narrative:chapter:type:FREE"},
            {"text": "👑 VIP", "callback_data": "narrative:chapter:type:VIP"}
        ],
        [{"text": "❌ Cancelar", "callback_data": "narrative:chapters"}]
    ])

    await message.answer(
        "📚 <b>Crear Capítulo - Paso 3/4</b>\n\n"
        f"Nombre: <b>{data['chapter_name']}</b>\n"
        f"Slug: <code>{slug}</code>\n\n"
        "Selecciona el <b>tipo</b> de capítulo:",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@narrative_admin_router.callback_query(
    NarrativeAdminStates.waiting_for_chapter_type,
    F.data.startswith("narrative:chapter:type:")
)
async def process_chapter_type(
    callback: CallbackQuery,
    state: FSMContext
):
    """Procesa tipo de capítulo."""
    await callback.answer()

    chapter_type = callback.data.split(":")[-1]
    await state.update_data(chapter_type=chapter_type)
    await state.set_state(NarrativeAdminStates.waiting_for_chapter_description)

    data = await state.get_data()
    type_emoji = "👑 VIP" if chapter_type == "VIP" else "🆓 FREE"

    keyboard = create_inline_keyboard([
        [{"text": "⏭️ Omitir descripción", "callback_data": "narrative:chapter:desc:skip"}],
        [{"text": "❌ Cancelar", "callback_data": "narrative:chapters"}]
    ])

    await callback.message.edit_text(
        "📚 <b>Crear Capítulo - Paso 4/4</b>\n\n"
        f"Nombre: <b>{data['chapter_name']}</b>\n"
        f"Slug: <code>{data['chapter_slug']}</code>\n"
        f"Tipo: {type_emoji}\n\n"
        "Envía una <b>descripción</b> (opcional).\n\n"
        "<i>O presiona 'Omitir' para continuar sin descripción.</i>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@narrative_admin_router.callback_query(
    NarrativeAdminStates.waiting_for_chapter_description,
    F.data == "narrative:chapter:desc:skip"
)
async def process_chapter_desc_skip(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Omite descripción y crea capítulo."""
    await callback.answer()
    await _create_chapter(callback.message, state, session, description=None)


@narrative_admin_router.message(NarrativeAdminStates.waiting_for_chapter_description)
async def process_chapter_description(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Procesa descripción y crea capítulo."""
    description = message.text.strip()

    if len(description) > 500:
        await message.answer(
            "❌ La descripción es muy larga (máx 500 caracteres).\n"
            "Intenta de nuevo:"
        )
        return

    await _create_chapter(message, state, session, description=description)


async def _create_chapter(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    description: str | None
):
    """Crea el capítulo con los datos del FSM."""
    data = await state.get_data()
    await state.clear()

    narrative = NarrativeContainer(session)

    chapter_type = ChapterType.VIP if data["chapter_type"] == "VIP" else ChapterType.FREE

    try:
        chapter = await narrative.chapter.create_chapter(
            name=data["chapter_name"],
            slug=data["chapter_slug"],
            chapter_type=chapter_type,
            description=description
        )

        type_emoji = "👑 VIP" if chapter_type == ChapterType.VIP else "🆓 FREE"

        text = (
            "✅ <b>Capítulo Creado</b>\n\n"
            f"<b>Nombre:</b> {chapter.name}\n"
            f"<b>Slug:</b> <code>{chapter.slug}</code>\n"
            f"<b>Tipo:</b> {type_emoji}\n"
        )

        if description:
            text += f"<b>Descripción:</b> {description[:100]}...\n"

        keyboard = create_inline_keyboard([
            [{"text": "📄 Agregar Fragmentos", "callback_data": f"narrative:fragments:{chapter.id}"}],
            [{"text": "🔙 Ver Capítulos", "callback_data": "narrative:chapters"}]
        ])

        if hasattr(message, 'edit_text'):
            await message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        else:
            await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

    except ValueError as e:
        await message.answer(f"❌ Error: {e}")


# ========================================
# EDITAR CAPÍTULO
# ========================================

@narrative_admin_router.callback_query(F.data.startswith("narrative:chapter:edit:"))
async def callback_chapter_edit_menu(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Muestra menú de edición del capítulo."""
    await callback.answer()

    chapter_id = int(callback.data.split(":")[-1])
    narrative = NarrativeContainer(session)
    chapter = await narrative.chapter.get_chapter_by_id(chapter_id)

    if not chapter:
        await callback.message.edit_text("❌ Capítulo no encontrado.")
        return

    text = (
        f"✏️ <b>Editar: {chapter.name}</b>\n\n"
        "Selecciona el campo a editar:"
    )

    keyboard = create_inline_keyboard([
        [{"text": "📝 Nombre", "callback_data": f"narrative:chapter:edit:name:{chapter_id}"}],
        [{"text": "📋 Descripción", "callback_data": f"narrative:chapter:edit:desc:{chapter_id}"}],
        [{"text": "🔢 Orden", "callback_data": f"narrative:chapter:edit:order:{chapter_id}"}],
        [{"text": "🔙 Volver", "callback_data": f"narrative:chapter:view:{chapter_id}"}]
    ])

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)


@narrative_admin_router.callback_query(F.data.regexp(r"narrative:chapter:edit:name:\d+"))
async def callback_edit_chapter_name_start(
    callback: CallbackQuery,
    state: FSMContext
):
    """Inicia edición de nombre."""
    await callback.answer()

    chapter_id = int(callback.data.split(":")[-1])
    await state.update_data(editing_chapter_id=chapter_id)
    await state.set_state(NarrativeAdminStates.editing_chapter_name)

    keyboard = create_inline_keyboard([[{
        "text": "❌ Cancelar",
        "callback_data": f"narrative:chapter:view:{chapter_id}"
    }]])

    await callback.message.edit_text(
        "📝 <b>Editar Nombre</b>\n\n"
        "Envía el nuevo nombre del capítulo:",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@narrative_admin_router.message(NarrativeAdminStates.editing_chapter_name)
async def process_edit_chapter_name(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Procesa nuevo nombre."""
    new_name = message.text.strip()

    if len(new_name) < 2 or len(new_name) > 100:
        await message.answer("❌ El nombre debe tener entre 2 y 100 caracteres.")
        return

    data = await state.get_data()
    chapter_id = data["editing_chapter_id"]
    await state.clear()

    narrative = NarrativeContainer(session)
    await narrative.chapter.update_chapter(chapter_id, name=new_name)

    keyboard = create_inline_keyboard([[{
        "text": "🔙 Volver al capítulo",
        "callback_data": f"narrative:chapter:view:{chapter_id}"
    }]])

    await message.answer(
        f"✅ Nombre actualizado a: <b>{new_name}</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@narrative_admin_router.callback_query(F.data.regexp(r"narrative:chapter:edit:desc:\d+"))
async def callback_edit_chapter_desc_start(
    callback: CallbackQuery,
    state: FSMContext
):
    """Inicia edición de descripción."""
    await callback.answer()

    chapter_id = int(callback.data.split(":")[-1])
    await state.update_data(editing_chapter_id=chapter_id)
    await state.set_state(NarrativeAdminStates.editing_chapter_description)

    keyboard = create_inline_keyboard([[{
        "text": "❌ Cancelar",
        "callback_data": f"narrative:chapter:view:{chapter_id}"
    }]])

    await callback.message.edit_text(
        "📋 <b>Editar Descripción</b>\n\n"
        "Envía la nueva descripción (máx 500 caracteres).\n"
        "Envía '-' para eliminar la descripción.",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@narrative_admin_router.message(NarrativeAdminStates.editing_chapter_description)
async def process_edit_chapter_desc(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Procesa nueva descripción."""
    new_desc = message.text.strip()

    if new_desc == "-":
        new_desc = None
    elif len(new_desc) > 500:
        await message.answer("❌ La descripción es muy larga (máx 500 caracteres).")
        return

    data = await state.get_data()
    chapter_id = data["editing_chapter_id"]
    await state.clear()

    narrative = NarrativeContainer(session)
    await narrative.chapter.update_chapter(chapter_id, description=new_desc)

    result = "eliminada" if new_desc is None else "actualizada"

    keyboard = create_inline_keyboard([[{
        "text": "🔙 Volver al capítulo",
        "callback_data": f"narrative:chapter:view:{chapter_id}"
    }]])

    await message.answer(
        f"✅ Descripción {result}.",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@narrative_admin_router.callback_query(F.data.regexp(r"narrative:chapter:edit:order:\d+"))
async def callback_edit_chapter_order_start(
    callback: CallbackQuery,
    state: FSMContext
):
    """Inicia edición de orden."""
    await callback.answer()

    chapter_id = int(callback.data.split(":")[-1])
    await state.update_data(editing_chapter_id=chapter_id)
    await state.set_state(NarrativeAdminStates.editing_chapter_order)

    keyboard = create_inline_keyboard([[{
        "text": "❌ Cancelar",
        "callback_data": f"narrative:chapter:view:{chapter_id}"
    }]])

    await callback.message.edit_text(
        "🔢 <b>Editar Orden</b>\n\n"
        "Envía el nuevo número de orden (0, 1, 2...).\n"
        "Los capítulos se muestran de menor a mayor.",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@narrative_admin_router.message(NarrativeAdminStates.editing_chapter_order)
async def process_edit_chapter_order(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Procesa nuevo orden."""
    try:
        new_order = int(message.text.strip())
        if new_order < 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ Envía un número entero >= 0.")
        return

    data = await state.get_data()
    chapter_id = data["editing_chapter_id"]
    await state.clear()

    narrative = NarrativeContainer(session)
    await narrative.chapter.update_chapter(chapter_id, order=new_order)

    keyboard = create_inline_keyboard([[{
        "text": "🔙 Volver al capítulo",
        "callback_data": f"narrative:chapter:view:{chapter_id}"
    }]])

    await message.answer(
        f"✅ Orden actualizado a: <b>{new_order}</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )


# ========================================
# TOGGLE ACTIVO
# ========================================

@narrative_admin_router.callback_query(F.data.startswith("narrative:chapter:toggle:"))
async def callback_chapter_toggle(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Toggle estado activo del capítulo."""
    await callback.answer()

    chapter_id = int(callback.data.split(":")[-1])
    narrative = NarrativeContainer(session)
    chapter = await narrative.chapter.get_chapter_by_id(chapter_id)

    if not chapter:
        await callback.message.edit_text("❌ Capítulo no encontrado.")
        return

    new_status = not chapter.is_active
    await narrative.chapter.update_chapter(chapter_id, is_active=new_status)

    status_text = "activado" if new_status else "desactivado"
    await callback.answer(f"✅ Capítulo {status_text}", show_alert=True)

    # Recargar vista
    chapter = await narrative.chapter.get_chapter_by_id(chapter_id)
    fragments_count = await narrative.chapter.get_chapter_fragments_count(chapter_id)

    status = "✅ Activo" if chapter.is_active else "❌ Inactivo"
    type_text = "👑 VIP" if chapter.chapter_type == ChapterType.VIP else "🆓 FREE"

    text = (
        f"📖 <b>{chapter.name}</b>\n\n"
        f"<b>Slug:</b> <code>{chapter.slug}</code>\n"
        f"<b>Tipo:</b> {type_text}\n"
        f"<b>Estado:</b> {status}\n"
        f"<b>Orden:</b> {chapter.order}\n"
        f"<b>Fragmentos:</b> {fragments_count}\n"
    )

    if chapter.description:
        text += f"\n<b>Descripción:</b>\n{chapter.description}\n"

    toggle_text = "❌ Desactivar" if chapter.is_active else "✅ Activar"

    keyboard = create_inline_keyboard([
        [{"text": "📄 Ver Fragmentos", "callback_data": f"narrative:fragments:{chapter_id}"}],
        [
            {"text": "✏️ Editar", "callback_data": f"narrative:chapter:edit:{chapter_id}"},
            {"text": toggle_text, "callback_data": f"narrative:chapter:toggle:{chapter_id}"}
        ],
        [{"text": "🗑️ Eliminar", "callback_data": f"narrative:chapter:delete:{chapter_id}"}],
        [{"text": "🔙 Volver", "callback_data": "narrative:chapters"}]
    ])

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)


# ========================================
# ELIMINAR CAPÍTULO
# ========================================

@narrative_admin_router.callback_query(F.data.startswith("narrative:chapter:delete:"))
async def callback_chapter_delete(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Confirma eliminación de capítulo."""
    await callback.answer()

    chapter_id = int(callback.data.split(":")[-1])
    narrative = NarrativeContainer(session)
    chapter = await narrative.chapter.get_chapter_by_id(chapter_id)

    if not chapter:
        await callback.message.edit_text("❌ Capítulo no encontrado.")
        return

    fragments_count = await narrative.chapter.get_chapter_fragments_count(chapter_id)

    text = (
        f"⚠️ <b>¿Eliminar capítulo?</b>\n\n"
        f"<b>{chapter.name}</b>\n"
        f"Fragmentos: {fragments_count}\n\n"
        "<i>Esta acción desactivará el capítulo (soft delete).</i>"
    )

    keyboard = create_inline_keyboard([
        [
            {"text": "🗑️ Sí, eliminar", "callback_data": f"narrative:chapter:confirm_delete:{chapter_id}"},
            {"text": "❌ Cancelar", "callback_data": f"narrative:chapter:view:{chapter_id}"}
        ]
    ])

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)


@narrative_admin_router.callback_query(F.data.startswith("narrative:chapter:confirm_delete:"))
async def callback_chapter_confirm_delete(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Ejecuta eliminación del capítulo."""
    await callback.answer("🗑️ Capítulo eliminado", show_alert=True)

    chapter_id = int(callback.data.split(":")[-1])
    narrative = NarrativeContainer(session)

    await narrative.chapter.delete_chapter(chapter_id)

    await _show_chapters_page(callback.message, session, page=0, edit=True)
