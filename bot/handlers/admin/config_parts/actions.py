"""
Handlers para la configuración de acciones.
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares.database import DatabaseMiddleware
from bot.middlewares.admin_auth import AdminAuthMiddleware
from bot.services.container import ServiceContainer
from bot.states.configuration import ActionConfigStates, ConfigDataKeys
from bot.utils.config_keyboards import config_list_keyboard, config_item_keyboard, confirm_keyboard

logger = logging.getLogger(__name__)

# Router para acciones
actions_router = Router(name="config_actions")


@actions_router.callback_query(F.data == "config:actions")
async def callback_config_actions(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Mostrar lista de acciones configuradas."""
    await state.update_data(current_menu="actions")

    container = ServiceContainer(session, callback.bot)
    actions = await container.configuration.list_actions()

    # Crear texto con la lista de acciones
    if actions:
        actions_list = "\n".join([
            f"• {action.display_name} ({action.points_amount} pts) - {action.action_key}"
            for action in actions
        ])
        text = (
            "📊 <b>Acciones Configuradas</b>\n\n"
            f"Se encontraron {len(actions)} acciones:\n\n"
            f"{actions_list}\n\n"
            "<i>Funcionalidad de edición en desarrollo</i>"
        )
    else:
        text = (
            "📊 <b>Acciones Configuradas</b>\n\n"
            "No hay acciones configuradas aún.\n\n"
            "<i>Funcionalidad de creación en desarrollo</i>"
        )

    # Convertir acciones para usar con config_list_keyboard
    items = [(action.id, f"{action.display_name} ({action.points_amount} pts)") for action in actions]

    keyboard = config_list_keyboard(
        items=items,
        prefix="config:actions",
        show_create=False,  # Temporalmente deshabilitado hasta que se implemente
        show_back=True
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await state.set_state(ActionConfigStates.list_actions)
    await callback.answer()


@actions_router.callback_query(F.data.startswith("config:actions:view:"))
async def callback_config_view_action(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Ver detalles de una acción específica."""
    action_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        action = await configuration_service.get_action_by_id(action_id)

        text = (
            f"📊 <b>Detalles de la Acción</b>\n\n"
            f"<b>Nombre:</b> {action.display_name}\n"
            f"<b>Clave:</b> {action.action_key}\n"
            f"<b>Puntos:</b> {action.points_amount}\n"
            f"<b>Descripción:</b> {action.description or 'Sin descripción'}\n"
            f"<b>Activa:</b> {'Sí' if action.is_active else 'No'}\n"
            f"<b>Creada:</b> {action.created_at.strftime('%d/%m/%Y %H:%M')}\n\n"
            "<i>¿Qué deseas hacer con esta acción?</i>"
        )

        keyboard = config_item_keyboard(
            item_id=action_id,
            prefix="config:actions",
            can_delete=True
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        await state.update_data(editing_id=action_id, editing_type="action")
        await state.set_state(ActionConfigStates.edit_select)
    except Exception as e:
        logger.error(f"Error al ver acción {action_id}: {e}")
        await callback.answer("❌ Error al cargar la acción", show_alert=True)

    await callback.answer()


@actions_router.callback_query(F.data == "config:actions:create")
async def callback_config_create_action(
    callback: CallbackQuery,
    state: FSMContext
):
    """Iniciar creación de nueva acción."""
    await state.clear()
    await state.set_state(ActionConfigStates.create_key)

    text = (
        "📊 <b>Creando Nueva Acción</b>\n\n"
        "Primero, ingresa la clave única de la acción.\n\n"
        "<b>Ejemplo:</b> custom_reaction, daily_checkin, post_share\n"
        "<b>Requisitos:</b> Solo letras, números y guiones bajos. Mínimo 3 caracteres."
    )

    await callback.message.edit_text(
        text=text,
        parse_mode="HTML"
    )
    await callback.answer()


@actions_router.callback_query(F.data.startswith("config:actions:edit:"))
async def callback_config_edit_action(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Editar una acción específica."""
    action_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        action = await configuration_service.get_action_by_id(action_id)

        await state.update_data(editing_id=action_id)
        await state.set_state(ActionConfigStates.edit_field)

        text = (
            "✏️ <b>Editando Acción</b>\n\n"
            f"<b>Actual:</b> {action.display_name}\n\n"
            "Selecciona qué campo deseas editar:"
        )

        from bot.utils.config_keyboards import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(text="📝 Nombre", callback_data="edit_field:name"),
            InlineKeyboardButton(text="🔢 Puntos", callback_data="edit_field:points")
        )
        builder.row(
            InlineKeyboardButton(text="💬 Descripción", callback_data="edit_field:description"),
            InlineKeyboardButton(text="✅ Estado", callback_data="edit_field:status")
        )
        builder.row(
            InlineKeyboardButton(text="◀️ Volver", callback_data=f"config:actions:view:{action_id}")
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error al editar acción {action_id}: {e}")
        await callback.answer("❌ Error al cargar la acción para editar", show_alert=True)

    await callback.answer()


@actions_router.callback_query(F.data.startswith("config:actions:delete:"))
async def callback_config_delete_action(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Eliminar una acción específica."""
    action_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        action = await configuration_service.get_action_by_id(action_id)

        text = (
            f"🗑️ <b>Eliminar Acción</b>\n\n"
            f"<b>Nombre:</b> {action.display_name}\n"
            f"<b>Clave:</b> {action.action_key}\n\n"
            "<b>¿Estás seguro de que deseas eliminar esta acción?</b>\n\n"
            "Esta operación no se puede deshacer."
        )

        keyboard = confirm_keyboard(
            confirm_callback=f"confirm_delete:action:{action_id}",
            cancel_callback=f"config:actions:view:{action_id}"
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error al preparar eliminación de acción {action_id}: {e}")
        await callback.answer("❌ Error al preparar la eliminación", show_alert=True)

    await callback.answer()


@actions_router.message(ActionConfigStates.edit_value)
async def message_edit_action_value(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Recibe el nuevo valor para editar un campo de acción."""
    try:
        data = await state.get_data()
        editing_id = data.get("editing_id")
        editing_field = data.get("editing_field")

        container = ServiceContainer(session, message.bot)
        configuration_service = container.configuration

        # Obtener la acción actual para obtener la action_key
        action = await configuration_service.get_action_by_id(editing_id)
        action_key = action.action_key

        # Validar y procesar el nuevo valor según el campo
        new_value = message.text.strip()
        update_kwargs = {}

        if editing_field == "name":
            if len(new_value) < 2:
                await message.answer("❌ El nombre debe tener al menos 2 caracteres.\n\nInténtalo de nuevo:")
                return
            update_kwargs["display_name"] = new_value
        elif editing_field == "points":
            try:
                points = int(new_value)
                if points < 0:
                    await message.answer("❌ Los puntos no pueden ser negativos.\n\nInténtalo de nuevo:")
                    return
                update_kwargs["points_amount"] = points
            except ValueError:
                await message.answer("❌ Por favor ingresa un número válido para los puntos.\n\nInténtalo de nuevo:")
                return
        elif editing_field == "description":
            update_kwargs["description"] = new_value if new_value else None
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

        # Actualizar la acción
        updated_action = await configuration_service.update_action(
            action_key=action_key,
            **update_kwargs
        )

        await message.answer(
            f"✅ Acción actualizada correctamente:\n"
            f"<b>{editing_field.upper()}:</b> {new_value}",
            parse_mode="HTML"
        )

        # Volver a la vista de edición de la acción
        await state.update_data(editing_id=editing_id, editing_type="action")
        await state.set_state(ActionConfigStates.edit_select)

        # Volver a mostrar los detalles de la acción
        text = (
            f"📊 <b>Detalles de la Acción</b>\n\n"
            f"<b>Nombre:</b> {updated_action.display_name}\n"
            f"<b>Clave:</b> {updated_action.action_key}\n"
            f"<b>Puntos:</b> {updated_action.points_amount}\n"
            f"<b>Descripción:</b> {updated_action.description or 'Sin descripción'}\n"
            f"<b>Activa:</b> {'Sí' if updated_action.is_active else 'No'}\n"
            f"<b>Creada:</b> {updated_action.created_at.strftime('%d/%m/%Y %H:%M')}\n\n"
            "<i>¿Qué deseas hacer con esta acción?</i>"
        )

        keyboard = config_item_keyboard(
            item_id=editing_id,
            prefix="config:actions",
            can_delete=True
        )

        await message.answer(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Error al editar valor de acción: {e}")
        await message.answer("❌ Error al actualizar la acción. Inténtalo de nuevo.")


from aiogram.types import InlineKeyboardButton