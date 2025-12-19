"""
Handlers para la configuración de misiones.
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares.database import DatabaseMiddleware
from bot.middlewares.admin_auth import AdminAuthMiddleware
from bot.services.container import ServiceContainer
from bot.states.configuration import MissionConfigStates
from bot.utils.config_keyboards import config_list_keyboard, config_item_keyboard, confirm_keyboard

logger = logging.getLogger(__name__)

# Router para misiones
missions_router = Router(name="config_missions")


@missions_router.callback_query(F.data == "config:missions")
async def callback_config_missions(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Mostrar lista de misiones configuradas."""
    await state.update_data(current_menu="missions")

    container = ServiceContainer(session, callback.bot)
    missions = await container.configuration.list_missions()

    # Crear texto con la lista de misiones
    if missions:
        missions_list = "\n".join([
            f"• {mission.name} ({mission.mission_type})"
            for mission in missions
        ])
        text = (
            "🎯 <b>Misiones Configuradas</b>\n\n"
            f"Se encontraron {len(missions)} misiones:\n\n"
            f"{missions_list}\n\n"
            "<i>Funcionalidad de edición en desarrollo</i>"
        )
    else:
        text = (
            "🎯 <b>Misiones Configuradas</b>\n\n"
            "No hay misiones configuradas aún.\n\n"
            "<i>Funcionalidad de creación en desarrollo</i>"
        )

    # Convertir misiones para usar con config_list_keyboard
    items = [(mission.id, f"🎯 {mission.name}") for mission in missions]

    keyboard = config_list_keyboard(
        items=items,
        prefix="config:missions",
        show_create=False,  # Temporalmente deshabilitado hasta que se implemente
        show_back=True
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await state.set_state(MissionConfigStates.list_missions)
    await callback.answer()


@missions_router.callback_query(F.data.startswith("config:missions:view:"))
async def callback_config_view_mission(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Ver detalles de una misión específica."""
    mission_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        mission = await configuration_service.get_mission(mission_id)

        reward_info = ""
        if mission.reward:
            reward_info = f"\n<b>Recompensa:</b> {mission.reward.name}"

        text = (
            f"🎯 <b>Detalles de la Misión</b>\n\n"
            f"<b>Nombre:</b> {mission.name}\n"
            f"<b>Tipo:</b> {mission.mission_type}\n"
            f"<b>Acción objetivo:</b> {mission.target_action or 'N/A'}\n"
            f"<b>Valor objetivo:</b> {mission.target_value}\n"
            f"<b>Límite de tiempo:</b> {mission.time_limit_hours or 'N/A'}h\n"
            f"<b>Repetible:</b> {'Sí' if mission.is_repeatable else 'No'}\n"
            f"{reward_info}\n"
            f"<b>Activa:</b> {'Sí' if mission.is_active else 'No'}\n\n"
            "<i>¿Qué deseas hacer con esta misión?</i>"
        )

        keyboard = config_item_keyboard(
            item_id=mission_id,
            prefix="config:missions",
            can_delete=True
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        await state.update_data(editing_id=mission_id, editing_type="mission")
        await state.set_state(MissionConfigStates.edit_select)
    except Exception as e:
        logger.error(f"Error al ver misión {mission_id}: {e}")
        await callback.answer("❌ Error al cargar la misión", show_alert=True)

    await callback.answer()


@missions_router.callback_query(F.data == "config:missions:create")
async def callback_config_create_mission(
    callback: CallbackQuery,
    state: FSMContext
):
    """Iniciar creación de nueva misión."""
    await state.clear()
    await state.set_state(MissionConfigStates.create_name)

    text = (
        "🎯 <b>Creando Nueva Misión</b>\n\n"
        "Primero, ingresa el nombre de la misión.\n\n"
        "<b>Ejemplo:</b> Daily Streak, Reaction Master, Community Helper"
    )

    await callback.message.edit_text(
        text=text,
        parse_mode="HTML"
    )
    await callback.answer()


@missions_router.callback_query(F.data.startswith("config:missions:edit:"))
async def callback_config_edit_mission(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Editar una misión específica."""
    mission_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        mission = await configuration_service.get_mission(mission_id)

        await state.update_data(editing_id=mission_id)
        await state.set_state(MissionConfigStates.edit_field)

        text = (
            "✏️ <b>Editando Misión</b>\n\n"
            f"<b>Actual:</b> {mission.name}\n\n"
            "Selecciona qué campo deseas editar:"
        )

        from bot.utils.config_keyboards import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(text="📝 Nombre", callback_data="edit_field:name"),
            InlineKeyboardButton(text="🏷️ Tipo", callback_data="edit_field:type")
        )
        builder.row(
            InlineKeyboardButton(text="🎯 Acción Obj.", callback_data="edit_field:target_action"),
            InlineKeyboardButton(text="🔢 Valor Obj.", callback_data="edit_field:target_value")
        )
        builder.row(
            InlineKeyboardButton(text="⏰ Límite T.", callback_data="edit_field:time_limit"),
            InlineKeyboardButton(text="🔁 Repetible", callback_data="edit_field:repeatable")
        )
        builder.row(
            InlineKeyboardButton(text="⏱️ Cooldown", callback_data="edit_field:cooldown"),
            InlineKeyboardButton(text="🎁 Recompensa", callback_data="edit_field:reward")
        )
        builder.row(
            InlineKeyboardButton(text="✅ Estado", callback_data="edit_field:status"),
            InlineKeyboardButton(text="◀️ Volver", callback_data=f"config:missions:view:{mission_id}")
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error al editar misión {mission_id}: {e}")
        await callback.answer("❌ Error al cargar la misión para editar", show_alert=True)

    await callback.answer()


@missions_router.callback_query(F.data.startswith("config:missions:delete:"))
async def callback_config_delete_mission(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Eliminar una misión específica."""
    mission_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        mission = await configuration_service.get_mission(mission_id)

        text = (
            f"🗑️ <b>Eliminar Misión</b>\n\n"
            f"<b>Nombre:</b> {mission.name}\n"
            f"<b>Tipo:</b> {mission.mission_type}\n\n"
            "<b>¿Estás seguro de que deseas eliminar esta misión?</b>\n\n"
            "Esta operación no se puede deshacer."
        )

        keyboard = confirm_keyboard(
            confirm_callback=f"confirm_delete:mission:{mission_id}",
            cancel_callback=f"config:missions:view:{mission_id}"
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error al preparar eliminación de misión {mission_id}: {e}")
        await callback.answer("❌ Error al preparar la eliminación", show_alert=True)

    await callback.answer()


@missions_router.message(MissionConfigStates.edit_value)
async def message_edit_mission_value(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Recibe el nuevo valor para editar un campo de misión."""
    try:
        data = await state.get_data()
        editing_id = data.get("editing_id")
        editing_field = data.get("editing_field")

        container = ServiceContainer(session, message.bot)
        configuration_service = container.configuration

        # Validar y procesar el nuevo valor según el campo
        new_value = message.text.strip()
        update_kwargs = {}

        if editing_field == "name":
            if len(new_value) < 2:
                await message.answer("❌ El nombre debe tener al menos 2 caracteres.\n\nInténtalo de nuevo:")
                return
            update_kwargs["name"] = new_value
        elif editing_field == "type":
            valid_types = ["single", "streak", "cumulative", "timed"]
            if new_value.lower() not in valid_types:
                await message.answer(
                    f"❌ Tipo de misión inválido.\n"
                    f"Opciones válidas: {', '.join(valid_types)}\n\n"
                    "Inténtalo de nuevo:"
                )
                return
            update_kwargs["mission_type"] = new_value.lower()
        elif editing_field == "target_action":
            if new_value.lower() in ["none", "null", "n/a", ""]:
                update_kwargs["target_action"] = None
            else:
                # Validar que la acción exista
                try:
                    await configuration_service.get_action(new_value)
                    update_kwargs["target_action"] = new_value
                except Exception:
                    await message.answer(
                        "❌ La acción especificada no existe.\n"
                        "Verifica la clave de la acción e inténtalo de nuevo:"
                    )
                    return
        elif editing_field == "target_value":
            try:
                value = int(new_value)
                if value <= 0:
                    await message.answer("❌ El valor objetivo debe ser positivo.\n\nInténtalo de nuevo:")
                    return
                update_kwargs["target_value"] = value
            except ValueError:
                await message.answer("❌ Por favor ingresa un número válido para el valor objetivo.\n\nInténtalo de nuevo:")
                return
        elif editing_field == "time_limit":
            try:
                if new_value.lower() in ["none", "null", "n/a", ""]:
                    update_kwargs["time_limit_hours"] = None
                else:
                    hours = int(new_value)
                    if hours < 0:
                        await message.answer("❌ Las horas no pueden ser negativas.\n\nInténtalo de nuevo:")
                        return
                    update_kwargs["time_limit_hours"] = hours
            except ValueError:
                await message.answer("❌ Por favor ingresa un número válido para las horas o 'none'.\n\nInténtalo de nuevo:")
                return
        elif editing_field == "repeatable":
            if new_value.lower() in ["activo", "activo", "true", "1", "sí", "si", "yes"]:
                update_kwargs["is_repeatable"] = True
            elif new_value.lower() in ["inactivo", "inactivo", "false", "0", "no"]:
                update_kwargs["is_repeatable"] = False
            else:
                await message.answer(
                    "❌ Por favor ingresa 'sí' o 'no' para repetible.\n\n"
                    "Inténtalo de nuevo:"
                )
                return
        elif editing_field == "cooldown":
            try:
                if new_value.lower() in ["none", "null", "n/a", ""]:
                    update_kwargs["cooldown_hours"] = None
                else:
                    hours = int(new_value)
                    if hours < 0:
                        await message.answer("❌ Las horas no pueden ser negativas.\n\nInténtalo de nuevo:")
                        return
                    update_kwargs["cooldown_hours"] = hours
            except ValueError:
                await message.answer("❌ Por favor ingresa un número válido para las horas o 'none'.\n\nInténtalo de nuevo:")
                return
        elif editing_field == "reward":
            try:
                if new_value.lower() in ["none", "null", "n/a", ""]:
                    update_kwargs["reward_id"] = None
                else:
                    reward_id = int(new_value)
                    # Validar que la recompensa exista
                    await configuration_service.get_reward(reward_id)
                    update_kwargs["reward_id"] = reward_id
            except ValueError:
                await message.answer("❌ Por favor ingresa un ID de recompensa válido o 'none'.\n\nInténtalo de nuevo:")
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

        # Actualizar la misión
        updated_mission = await configuration_service.update_mission(
            mission_id=editing_id,
            **update_kwargs
        )

        await message.answer(
            f"✅ Misión actualizada correctamente:\n"
            f"<b>{editing_field.upper()}:</b> {new_value}",
            parse_mode="HTML"
        )

        # Volver a la vista de edición de la misión
        await state.update_data(editing_id=editing_id, editing_type="mission")
        await state.set_state(MissionConfigStates.edit_select)

        # Volver a mostrar los detalles de la misión
        reward_info = ""
        if updated_mission.reward:
            reward_info = f"\n<b>Recompensa:</b> {updated_mission.reward.name}"

        text = (
            f"🎯 <b>Detalles de la Misión</b>\n\n"
            f"<b>Nombre:</b> {updated_mission.name}\n"
            f"<b>Tipo:</b> {updated_mission.mission_type}\n"
            f"<b>Acción objetivo:</b> {updated_mission.target_action or 'N/A'}\n"
            f"<b>Valor objetivo:</b> {updated_mission.target_value}\n"
            f"<b>Límite de tiempo:</b> {updated_mission.time_limit_hours or 'N/A'}h\n"
            f"<b>Repetible:</b> {'Sí' if updated_mission.is_active else 'No'}\n"
            f"{reward_info}\n"
            f"<b>Activa:</b> {'Sí' if updated_mission.is_active else 'No'}\n\n"
            "<i>¿Qué deseas hacer con esta misión?</i>"
        )

        keyboard = config_item_keyboard(
            item_id=editing_id,
            prefix="config:missions",
            can_delete=True
        )

        await message.answer(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Error al editar valor de misión: {e}")
        await message.answer("❌ Error al actualizar la misión. Inténtalo de nuevo.")