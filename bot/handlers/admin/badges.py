"""
Badges Admin Handler - Gestión de badges/insignias.

Handlers:
- Menú de gestión de badges
- Crear nuevo badge (FSM)
- Ver lista de badges
- Activar/desactivar badges
"""
import logging
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.admin.main import admin_router
from bot.states.admin import BadgeManagementStates
from bot.services.container import ServiceContainer
from bot.utils.keyboards import create_inline_keyboard
from bot.database.enums import BadgeRarity

logger = logging.getLogger(__name__)


def create_badges_menu_keyboard() -> InlineKeyboardMarkup:
    """Crea keyboard del menú de gestión de badges."""
    builder = InlineKeyboardBuilder()

    # Gestión
    builder.row(
        InlineKeyboardButton(text="➕ Crear Badge", callback_data="admin:badges:create"),
        InlineKeyboardButton(text="📋 Ver Badges", callback_data="admin:badges:list")
    )

    # Volver
    builder.row(
        InlineKeyboardButton(text="🔙 Volver a Gamificación", callback_data="admin:gamification")
    )

    return builder.as_markup()


@admin_router.callback_query(F.data == "admin:gamification:badges")
async def callback_badges_menu(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Muestra el menú de gestión de badges.

    Opciones:
    - Crear nuevo badge
    - Ver lista de badges existentes
    """
    logger.debug("🏅 Admin abriendo menú de badges")

    container = ServiceContainer(session, callback.bot)

    # Obtener badges activos
    badges = await container.badges.get_all_badges(active_only=True)
    active_count = len(badges)

    text = (
        f"🏅 <b>Gestión de Badges</b>\n\n"
        f"Badges activos: {active_count}\n\n"
        f"Selecciona una opción:"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=create_badges_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.callback_query(F.data == "admin:badges:create")
async def callback_create_badge_start(
    callback: CallbackQuery,
    state: FSMContext
):
    """Inicia el flujo para crear un badge."""
    await state.set_state(BadgeManagementStates.waiting_for_name)

    text = (
        "➕ <b>Crear Nuevo Badge</b>\n\n"
        "Envía el <b>nombre</b> del badge (máx. 100 caracteres).\n\n"
        "<b>Ejemplo:</b> <code>Primer Logro</code>"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard([
            [{"text": "❌ Cancelar", "callback_data": "admin:badges"}]
        ]),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.message(BadgeManagementStates.waiting_for_name)
async def process_badge_name(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Procesa el nombre del badge."""
    name = message.text.strip()

    if len(name) > 100:
        await message.answer(
            "❌ <b>Nombre muy largo</b>\n\n"
            "Máximo 100 caracteres. Intenta nuevamente.",
            parse_mode="HTML"
        )
        return

    # Guardar nombre y pedir emoji
    await state.update_data({"badge_name": name})
    await state.set_state(BadgeManagementStates.waiting_for_emoji)

    text = (
        f"✅ Nombre: <code>{name}</code>\n\n"
        "Envía el <b>emoji</b> del badge.\n\n"
        "<b>Ejemplo:</b> <code>🏅</code>"
    )

    await message.answer(
        text=text,
        reply_markup=create_inline_keyboard([
            [{"text": "❌ Cancelar", "callback_data": "admin:badges"}]
        ]),
        parse_mode="HTML"
    )


@admin_router.message(BadgeManagementStates.waiting_for_emoji)
async def process_badge_emoji(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Procesa el emoji del badge."""
    emoji = message.text.strip()

    # Validar que sea un emoji (básico: verificar longitud)
    if len(emoji) > 10:
        await message.answer(
            "❌ <b>Emoji inválido</b>\n\n"
            "Envía solo el emoji. Intenta nuevamente.",
            parse_mode="HTML"
        )
        return

    # Guardar emoji y pedir descripción
    await state.update_data({"badge_emoji": emoji})
    await state.set_state(BadgeManagementStates.waiting_for_description)

    data = await state.get_data()

    text = (
        f"✅ Nombre: <code>{data['badge_name']}</code>\n"
        f"✅ Emoji: {emoji}\n\n"
        "Envía la <b>descripción</b> del badge (máx. 500 caracteres).\n\n"
        "<b>Ejemplo:</b> <code>Obtenido al reaccionar a 10 publicaciones</code>"
    )

    await message.answer(
        text=text,
        reply_markup=create_inline_keyboard([
            [{"text": "❌ Cancelar", "callback_data": "admin:badges"}]
        ]),
        parse_mode="HTML"
    )


@admin_router.message(BadgeManagementStates.waiting_for_description)
async def process_badge_description(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Procesa la descripción y pide rareza."""
    description = message.text.strip()

    if len(description) > 500:
        await message.answer(
            "❌ <b>Descripción muy larga</b>\n\n"
            "Máximo 500 caracteres. Intenta nuevamente.",
            parse_mode="HTML"
        )
        return

    # Guardar descripción y pedir rareza
    await state.update_data({"badge_description": description})
    await state.set_state(BadgeManagementStates.waiting_for_rarity)

    data = await state.get_data()

    text = (
        f"✅ Nombre: <code>{data['badge_name']}</code>\n"
        f"✅ Emoji: {data['badge_emoji']}\n"
        f"✅ Descripción: <code>{description[:50]}...</code>\n\n"
        "Selecciona la <b>rareza</b> del badge:"
    )

    await message.answer(
        text=text,
        reply_markup=create_inline_keyboard([
            [{"text": "⚪ Común", "callback_data": "admin:badges:rarity:common"}],
            [{"text": "🔵 Raro", "callback_data": "admin:badges:rarity:rare"}],
            [{"text": "🟣 Épico", "callback_data": "admin:badges:rarity:epic"}],
            [{"text": "🟡 Legendario", "callback_data": "admin:badges:rarity:legendary"}],
            [{"text": "❌ Cancelar", "callback_data": "admin:badges"}]
        ]),
        parse_mode="HTML"
    )


@admin_router.callback_query(F.data.startswith("admin:badges:rarity:"))
async def process_badge_rarity(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Procesa la rareza y crea el badge."""
    rarity_str = callback.data.split(":")[-1]

    # Mapear string a enum
    rarity_map = {
        "common": BadgeRarity.COMMON,
        "rare": BadgeRarity.RARE,
        "epic": BadgeRarity.EPIC,
        "legendary": BadgeRarity.LEGENDARY
    }

    rarity = rarity_map.get(rarity_str)

    if rarity is None:
        await callback.answer("Rareza inválida", show_alert=True)
        return

    # Obtener datos del FSM
    data = await state.get_data()

    # Crear badge
    container = ServiceContainer(session, callback.bot)

    from bot.database.gamification_models import Badge
    from datetime import datetime

    badge = Badge(
        name=data["badge_name"],
        emoji=data["badge_emoji"],
        description=data["badge_description"],
        rarity=rarity,
        active=True,
        created_at=datetime.utcnow(),
        created_by=callback.from_user.id
    )

    session.add(badge)
    await session.commit()

    logger.info(
        f"🏅 Badge creado: {badge.emoji} {badge.name} "
        f"(rarity: {rarity.value}, by: {callback.from_user.id})"
    )

    await callback.answer(
        f"✅ Badge creado exitosamente",
        show_alert=True
    )

    text = (
        f"✅ <b>Badge Creado</b>\n\n"
        f"{badge.emoji} <b>{badge.name}</b>\n"
        f"Rarezá: {badge.rarity.value}\n"
        f"{badge.description}\n\n"
        f"El badge ya está disponible para los usuarios."
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=create_badges_menu_keyboard(),
        parse_mode="HTML"
    )

    await state.clear()


@admin_router.callback_query(F.data == "admin:badges:list")
async def callback_list_badges(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Muestra lista de badges existentes."""
    container = ServiceContainer(session, callback.bot)

    # Obtener todos los badges (activos e inactivos)
    badges = await container.badges.get_all_badges(active_only=False)

    if not badges:
        await callback.answer(
            "No hay badges creados",
            show_alert=True
        )
        return

    # Crear keyboard con badges
    keyboard_buttons = []

    for badge in badges:
        status = "✅" if badge.active else "❌"
        keyboard_buttons.append([{
            "text": f"{status} {badge.emoji} {badge.name} ({badge.rarity.value})",
            "callback_data": f"admin:badges:view:{badge.id}"
        }])

    keyboard_buttons.append([{
        "text": "🔙 Volver a Badges",
        "callback_data": "admin:badges"
    }])

    text = (
        f"📋 <b>Badges Existentes</b>\n\n"
        f"Total: {len(badges)} badges\n"
        f"Selecciona un badge para gestionarlo:"
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard(keyboard_buttons),
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith("admin:badges:view:"))
async def callback_view_badge(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Muestra detalles de un badge y permite activar/desactivar."""
    badge_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    badge = await container.badges.get_badge(badge_id)

    if badge is None:
        await callback.answer("Badge no encontrado", show_alert=True)
        return

    status_text = "✅ Activo" if badge.active else "❌ Inactivo"
    action = "Desactivar" if badge.active else "Activar"

    text = (
        f"{badge.emoji} <b>{badge.name}</b>\n\n"
        f"📝 {badge.description}\n\n"
        f"🏷️ Rareza: {badge.rarity.value}\n"
        f"📊 Estado: {status_text}\n"
        f"👤 Creado por: {badge.created_by}\n"
        f"📅 Fecha: {badge.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        f"¿Qué deseas hacer?"
    )

    keyboard = create_inline_keyboard([
        [{
            "text": f"🔄 {action}",
            "callback_data": f"admin:badges:toggle:{badge.id}"
        }],
        [{
            "text": "🔙 Volver a la Lista",
            "callback_data": "admin:badges:list"
        }],
        [{
            "text": "🔙 Volver al Menú",
            "callback_data": "admin:badges"
        }]
    ])

    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@admin_router.callback_query(F.data.startswith("admin:badges:toggle:"))
async def callback_toggle_badge(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Activa/desactiva un badge."""
    badge_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    badge = await container.badges.get_badge(badge_id)

    if badge is None:
        await callback.answer("Badge no encontrado", show_alert=True)
        return

    # Toggle estado
    badge.active = not badge.active
    await session.commit()

    new_status = "activado" if badge.active else "desactivado"

    logger.info(
        f"🏅 Badge {new_status}: {badge.emoji} {badge.name} "
        f"(by: {callback.from_user.id})"
    )

    await callback.answer(
        f"✅ Badge {new_status}",
        show_alert=True
    )

    # Volver a la vista del badge
    # Enviar callback sin editar para evitar error de mensaje no modificado
    # El usuario puede hacer click en "Volver a la Lista"
