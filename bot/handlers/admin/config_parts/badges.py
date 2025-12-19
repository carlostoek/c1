"""
Handlers para la configuración de badges.
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares.database import DatabaseMiddleware
from bot.middlewares.admin_auth import AdminAuthMiddleware
from bot.services.container import ServiceContainer
from bot.states.configuration import BadgeConfigStates
from bot.utils.config_keyboards import config_list_keyboard, config_item_keyboard, confirm_keyboard

logger = logging.getLogger(__name__)

# Router para badges
badges_router = Router(name="config_badges")


@badges_router.callback_query(F.data == "config:badges")
async def callback_config_badges(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Mostrar lista de badges configurados."""
    await state.update_data(current_menu="badges")

    container = ServiceContainer(session, callback.bot)
    badges = await container.configuration.list_badges()

    # Crear texto con la lista de badges
    if badges:
        badges_list = "\n".join([
            f"• {badge.icon} {badge.name} - {badge.badge_key}"
            for badge in badges
        ])
        text = (
            "🏆 <b>Badges Configurados</b>\n\n"
            f"Se encontraron {len(badges)} badges:\n\n"
            f"{badges_list}\n\n"
            "<i>Funcionalidad de edición en desarrollo</i>"
        )
    else:
        text = (
            "🏆 <b>Badges Configurados</b>\n\n"
            "No hay badges configurados aún.\n\n"
            "<i>Funcionalidad de creación en desarrollo</i>"
        )

    # Convertir badges para usar con config_list_keyboard
    items = [(badge.id, f"{badge.icon} {badge.name}") for badge in badges]

    keyboard = config_list_keyboard(
        items=items,
        prefix="config:badges",
        show_create=False,  # Temporalmente deshabilitado hasta que se implemente
        show_back=True
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await state.set_state(BadgeConfigStates.list_badges)
    await callback.answer()


@badges_router.callback_query(F.data.startswith("config:badges:view:"))
async def callback_config_view_badge(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Ver detalles de un badge específico."""
    badge_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        badge = await configuration_service.get_badge_by_id(badge_id)

        text = (
            f"🏆 <b>Detalles del Badge</b>\n\n"
            f"<b>Icono:</b> {badge.icon}\n"
            f"<b>Nombre:</b> {badge.name}\n"
            f"<b>Clave:</b> {badge.badge_key}\n"
            f"<b>Tipo de requisito:</b> {badge.requirement_type}\n"
            f"<b>Valor del requisito:</b> {badge.requirement_value}\n"
            f"<b>Descripción:</b> {badge.description or 'Sin descripción'}\n"
            f"<b>Activo:</b> {'Sí' if badge.is_active else 'No'}\n\n"
            "<i>¿Qué deseas hacer con este badge?</i>"
        )

        keyboard = config_item_keyboard(
            item_id=badge_id,
            prefix="config:badges",
            can_delete=True
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        await state.update_data(editing_id=badge_id, editing_type="badge")
        await state.set_state(BadgeConfigStates.edit_select)
    except Exception as e:
        logger.error(f"Error al ver badge {badge_id}: {e}")
        await callback.answer("❌ Error al cargar el badge", show_alert=True)

    await callback.answer()


@badges_router.callback_query(F.data == "config:badges:create")
async def callback_config_create_badge(
    callback: CallbackQuery,
    state: FSMContext
):
    """Iniciar creación de nuevo badge."""
    await state.clear()
    await state.set_state(BadgeConfigStates.create_key)

    text = (
        "🏆 <b>Creando Nuevo Badge</b>\n\n"
        "Primero, ingresa la clave única del badge.\n\n"
        "<b>Ejemplo:</b> super_reactor, daily_visitor, content_creator\n"
        "<b>Requisitos:</b> Solo letras, números y guiones bajos. Mínimo 3 caracteres."
    )

    await callback.message.edit_text(
        text=text,
        parse_mode="HTML"
    )
    await callback.answer()


@badges_router.callback_query(F.data.startswith("config:badges:edit:"))
async def callback_config_edit_badge(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Editar un badge específico."""
    badge_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        badge = await configuration_service.get_badge_by_id(badge_id)

        await state.update_data(editing_id=badge_id)
        await state.set_state(BadgeConfigStates.edit_field)

        text = (
            "✏️ <b>Editando Badge</b>\n\n"
            f"<b>Actual:</b> {badge.name}\n\n"
            "Selecciona qué campo deseas editar:"
        )

        from bot.utils.config_keyboards import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(text="📝 Nombre", callback_data="edit_field:name"),
            InlineKeyboardButton(text="😊 Icono", callback_data="edit_field:icon")
        )
        builder.row(
            InlineKeyboardButton(text="💬 Descripción", callback_data="edit_field:description"),
            InlineKeyboardButton(text="📋 Tipo Req.", callback_data="edit_field:req_type")
        )
        builder.row(
            InlineKeyboardButton(text="🔢 Valor Req.", callback_data="edit_field:req_value"),
            InlineKeyboardButton(text="✅ Estado", callback_data="edit_field:status")
        )
        builder.row(
            InlineKeyboardButton(text="◀️ Volver", callback_data=f"config:badges:view:{badge_id}")
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error al editar badge {badge_id}: {e}")
        await callback.answer("❌ Error al cargar el badge para editar", show_alert=True)

    await callback.answer()


@badges_router.callback_query(F.data.startswith("config:badges:delete:"))
async def callback_config_delete_badge(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Eliminar un badge específico."""
    badge_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        badge = await configuration_service.get_badge_by_id(badge_id)

        text = (
            f"🗑️ <b>Eliminar Badge</b>\n\n"
            f"<b>Nombre:</b> {badge.name}\n"
            f"<b>Icono:</b> {badge.icon}\n\n"
            "<b>¿Estás seguro de que deseas eliminar este badge?</b>\n\n"
            "Esta operación no se puede deshacer."
        )

        keyboard = confirm_keyboard(
            confirm_callback=f"confirm_delete:badge:{badge_id}",
            cancel_callback=f"config:badges:view:{badge_id}"
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error al preparar eliminación de badge {badge_id}: {e}")
        await callback.answer("❌ Error al preparar la eliminación", show_alert=True)

    await callback.answer()


@badges_router.message(BadgeConfigStates.edit_value)
async def message_edit_badge_value(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Recibe el nuevo valor para editar un campo de badge."""
    try:
        data = await state.get_data()
        editing_id = data.get("editing_id")
        editing_field = data.get("editing_field")

        container = ServiceContainer(session, message.bot)
        configuration_service = container.configuration

        # Obtener el badge actual para obtener la badge_key
        badge = await configuration_service.get_badge_by_id(editing_id)
        badge_key = badge.badge_key

        # Validar y procesar el nuevo valor según el campo
        new_value = message.text.strip()
        update_kwargs = {}

        if editing_field == "name":
            if len(new_value) < 2:
                await message.answer("❌ El nombre debe tener al menos 2 caracteres.\n\nInténtalo de nuevo:")
                return
            update_kwargs["name"] = new_value
        elif editing_field == "icon":
            # Validar que sea un emoji o caracteres válidos
            if len(new_value) > 4:  # Permitir un emoji o texto corto
                await message.answer("❌ El icono debe ser un emoji o texto corto.\n\nInténtalo de nuevo:")
                return
            update_kwargs["icon"] = new_value
        elif editing_field == "description":
            update_kwargs["description"] = new_value if new_value else None
        elif editing_field == "req_type":
            valid_types = [
                "total_reactions",
                "total_points",
                "streak_days",
                "is_vip",
                "total_missions",
                "level_reached",
                "custom"
            ]
            if new_value.lower() not in valid_types:
                await message.answer(
                    f"❌ Tipo de requisito inválido.\n"
                    f"Opciones válidas: {', '.join(valid_types)}\n\n"
                    "Inténtalo de nuevo:"
                )
                return
            update_kwargs["requirement_type"] = new_value.lower()
        elif editing_field == "req_value":
            try:
                value = int(new_value)
                if value < 0:
                    await message.answer("❌ El valor del requisito no puede ser negativo.\n\nInténtalo de nuevo:")
                    return
                update_kwargs["requirement_value"] = value
            except ValueError:
                await message.answer("❌ Por favor ingresa un número válido para el valor del requisito.\n\nInténtalo de nuevo:")
                return
        elif editing_field == "status":
            if new_value.lower() in ["activo", "activo", "true", "1", "sí", "si"]:
                update_kwargs["is_active"] = True
            elif new_value.lower() in ["inactivo", "inactivo", "false", "0", "no"]:
                update_kwargs["is_active"] = False
            else:
                await message.answer(
                    "❌ Por favor ingresa 'activo' o 'inactivo'.\n\n"
                    "Inténtalo de nuevo:"
                )
                return

        # Actualizar el badge
        updated_badge = await configuration_service.update_badge(
            badge_key=badge_key,
            **update_kwargs
        )

        await message.answer(
            f"✅ Badge actualizado correctamente:\n"
            f"<b>{editing_field.upper()}:</b> {new_value}",
            parse_mode="HTML"
        )

        # Volver a la vista de edición del badge
        await state.update_data(editing_id=editing_id, editing_type="badge")
        await state.set_state(BadgeConfigStates.edit_select)

        # Volver a mostrar los detalles del badge
        text = (
            f"🏆 <b>Detalles del Badge</b>\n\n"
            f"<b>Icono:</b> {updated_badge.icon}\n"
            f"<b>Nombre:</b> {updated_badge.name}\n"
            f"<b>Clave:</b> {updated_badge.badge_key}\n"
            f"<b>Tipo de requisito:</b> {updated_badge.requirement_type}\n"
            f"<b>Valor del requisito:</b> {updated_badge.requirement_value}\n"
            f"<b>Descripción:</b> {updated_badge.description or 'Sin descripción'}\n"
            f"<b>Activo:</b> {'Sí' if updated_badge.is_active else 'No'}\n\n"
            "<i>¿Qué deseas hacer con este badge?</i>"
        )

        keyboard = config_item_keyboard(
            item_id=editing_id,
            prefix="config:badges",
            can_delete=True
        )

        await message.answer(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Error al editar valor de badge: {e}")
        await message.answer("❌ Error al actualizar el badge. Inténtalo de nuevo.")