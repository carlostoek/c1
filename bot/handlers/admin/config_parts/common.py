"""
Handlers comunes para la configuración de gamificación.
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares.database import DatabaseMiddleware
from bot.middlewares.admin_auth import AdminAuthMiddleware
from bot.services.container import ServiceContainer
from bot.states.configuration import (
    ConfigMainStates,
    ActionConfigStates,
    LevelConfigStates,
    BadgeConfigStates,
    RewardConfigStates,
    MissionConfigStates,
    ConfigDataKeys
)
from bot.utils.config_keyboards import config_main_menu_keyboard, confirm_keyboard, InlineKeyboardBuilder

logger = logging.getLogger(__name__)

# Router para handlers comunes
common_router = Router(name="config_common")


@common_router.callback_query(F.data.startswith("edit_field:"))
async def callback_config_select_edit_field(
    callback: CallbackQuery,
    state: FSMContext
):
    """Seleccionar campo específico para editar."""
    field = callback.data.split(":")[1]
    data = await state.get_data()
    editing_id = data.get("editing_id")
    editing_type = data.get("editing_type")

    # Mensaje genérico - cada tipo de entidad manejará la lógica específica
    await state.update_data(editing_field=field)

    if editing_type == "action":
        await state.set_state(ActionConfigStates.edit_value)
        text = f"✏️ <b>Editando campo '{field}' de la acción</b>\n\nIngresa el nuevo valor:"
    elif editing_type == "level":
        await state.set_state(LevelConfigStates.edit_value)
        text = f"✏️ <b>Editando campo '{field}' del nivel</b>\n\nIngresa el nuevo valor:"
    elif editing_type == "badge":
        await state.set_state(BadgeConfigStates.edit_value)
        text = f"✏️ <b>Editando campo '{field}' del badge</b>\n\nIngresa el nuevo valor:"
    elif editing_type == "reward":
        await state.set_state(RewardConfigStates.edit_value)
        text = f"✏️ <b>Editando campo '{field}' de la recompensa</b>\n\nIngresa el nuevo valor:"
    elif editing_type == "mission":
        await state.set_state(MissionConfigStates.edit_value)
        text = f"✏️ <b>Editando campo '{field}' de la misión</b>\n\nIngresa el nuevo valor:"
    else:
        await callback.answer("❌ Tipo de entidad desconocido", show_alert=True)
        return

    await callback.message.edit_text(
        text=text,
        parse_mode="HTML"
    )
    await callback.answer()


@common_router.callback_query(F.data == "edit_confirm:continue")
async def callback_edit_confirm_continue(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Continuar editando el mismo elemento."""
    data = await state.get_data()
    editing_type = data.get("editing_type")
    editing_id = data.get("editing_id")

    if editing_type == "action":
        await state.set_state(ActionConfigStates.edit_field)

        text = (
            "✏️ <b>Editando Acción</b>\n\n"
            "Selecciona qué campo deseas editar:"
        )

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
            InlineKeyboardButton(text="◀️ Volver", callback_data=f"config:actions:view:{editing_id}")
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    elif editing_type == "level":
        await state.set_state(LevelConfigStates.edit_field)

        text = (
            "✏️ <b>Editando Nivel</b>\n\n"
            "Selecciona qué campo deseas editar:"
        )

        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(text="📝 Nombre", callback_data="edit_field:name"),
            InlineKeyboardButton(text="🔢 Min Puntos", callback_data="edit_field:min_points")
        )
        builder.row(
            InlineKeyboardButton(text="🔢 Max Puntos", callback_data="edit_field:max_points"),
            InlineKeyboardButton(text="🔄 Multiplicador", callback_data="edit_field:multiplier")
        )
        builder.row(
            InlineKeyboardButton(text="😊 Icono", callback_data="edit_field:icon"),
            InlineKeyboardButton(text="🎨 Color", callback_data="edit_field:color")
        )
        builder.row(
            InlineKeyboardButton(text="✅ Estado", callback_data="edit_field:status"),
            InlineKeyboardButton(text="◀️ Volver", callback_data=f"config:levels:view:{editing_id}")
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    elif editing_type == "badge":
        await state.set_state(BadgeConfigStates.edit_field)

        text = (
            "✏️ <b>Editando Badge</b>\n\n"
            "Selecciona qué campo deseas editar:"
        )

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
            InlineKeyboardButton(text="◀️ Volver", callback_data=f"config:badges:view:{editing_id}")
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    elif editing_type == "reward":
        await state.set_state(RewardConfigStates.edit_field)

        text = (
            "✏️ <b>Editando Recompensa</b>\n\n"
            "Selecciona qué campo deseas editar:"
        )

        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(text="📝 Nombre", callback_data="edit_field:name"),
            InlineKeyboardButton(text="🏷️ Tipo", callback_data="edit_field:type")
        )
        builder.row(
            InlineKeyboardButton(text="🔢 Puntos", callback_data="edit_field:points"),
            InlineKeyboardButton(text="🏆 Badge", callback_data="edit_field:badge")
        )
        builder.row(
            InlineKeyboardButton(text="💬 Descripción", callback_data="edit_field:description"),
            InlineKeyboardButton(text="✅ Estado", callback_data="edit_field:status")
        )
        builder.row(
            InlineKeyboardButton(text="◀️ Volver", callback_data=f"config:rewards:view:{editing_id}")
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    elif editing_type == "mission":
        await state.set_state(MissionConfigStates.edit_field)

        text = (
            "✏️ <b>Editando Misión</b>\n\n"
            "Selecciona qué campo deseas editar:"
        )

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
            InlineKeyboardButton(text="◀️ Volver", callback_data=f"config:missions:view:{editing_id}")
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )

    await callback.answer()


@common_router.callback_query(F.data == "edit_confirm:finish")
async def callback_edit_confirm_finish(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Finalizar edición y volver al listado."""
    data = await state.get_data()
    editing_type = data.get("editing_type")

    # Limpiar estado y volver al listado correspondiente
    await state.clear()

    if editing_type == "action":
        from bot.handlers.admin.config_parts.actions import callback_config_actions
        await callback_config_actions(callback, state, session)
    elif editing_type == "level":
        from bot.handlers.admin.config_parts.levels import callback_config_levels
        await callback_config_levels(callback, state, session)
    elif editing_type == "badge":
        from bot.handlers.admin.config_parts.badges import callback_config_badges
        await callback_config_badges(callback, state, session)
    elif editing_type == "reward":
        from bot.handlers.admin.config_parts.rewards import callback_config_rewards
        await callback_config_rewards(callback, state, session)
    elif editing_type == "mission":
        from bot.handlers.admin.config_parts.missions import callback_config_missions
        await callback_config_missions(callback, state, session)
    else:
        # Si no se reconoce el tipo, volver al menú principal
        from bot.handlers.admin.configuration import callback_config_main
        await callback_config_main(callback, state, session)

    await callback.answer()


@common_router.callback_query(F.data.startswith("confirm_delete:"))
async def callback_config_confirm_delete(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Confirmar eliminación de un elemento."""
    _, entity_type, entity_id_str = callback.data.split(":")
    entity_id = int(entity_id_str)

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        # Determinar qué servicio usar según el tipo
        if entity_type == "action":
            # Para acciones, necesitamos obtener la key primero
            action = await configuration_service.get_action_by_id(entity_id)
            await configuration_service.delete_action(action.action_key)
            message = "acción"
        elif entity_type == "level":
            await configuration_service.delete_level(entity_id)
            message = "nivel"
        elif entity_type == "badge":
            # Para badges, necesitamos obtener la key primero
            badge = await configuration_service.get_badge_by_id(entity_id)
            await configuration_service.delete_badge(badge.badge_key)
            message = "badge"
        elif entity_type == "reward":
            await configuration_service.delete_reward(entity_id)
            message = "recompensa"
        elif entity_type == "mission":
            await configuration_service.delete_mission(entity_id)
            message = "misión"
        else:
            await callback.answer("❌ Tipo de entidad desconocido", show_alert=True)
            return

        await callback.message.edit_text(
            text=f"✅ {message.capitalize()} eliminado/a correctamente.",
            parse_mode="HTML"
        )

        # Limpiar estado y volver al menú principal
        await state.clear()

    except Exception as e:
        logger.error(f"Error al eliminar {entity_type} {entity_id}: {e}")
        await callback.answer(f"❌ Error al eliminar el/la {message}", show_alert=True)

    await callback.answer()


@common_router.callback_query(F.data.endswith(":list"))
async def callback_config_back_to_list(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Volver a la lista correspondiente al tipo de configuración."""
    # Extraer el tipo de configuración del callback data
    config_type = callback.data.replace(":list", "").replace("config:", "")

    # Redirigir al handler correspondiente
    if config_type == "actions":
        from bot.handlers.admin.config_parts.actions import callback_config_actions
        await callback_config_actions(callback, state, session)
    elif config_type == "levels":
        from bot.handlers.admin.config_parts.levels import callback_config_levels
        await callback_config_levels(callback, state, session)
    elif config_type == "badges":
        from bot.handlers.admin.config_parts.badges import callback_config_badges
        await callback_config_badges(callback, state, session)
    elif config_type == "rewards":
        from bot.handlers.admin.config_parts.rewards import callback_config_rewards
        await callback_config_rewards(callback, state, session)
    elif config_type == "missions":
        from bot.handlers.admin.config_parts.missions import callback_config_missions
        await callback_config_missions(callback, state, session)
    else:
        # Si no coincide con ninguno, volver al menú principal
        from bot.handlers.admin.configuration import callback_config_main
        await callback_config_main(callback, state, session)


@common_router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """
    Cancelar operación actual y volver al menú principal.

    Disponible en cualquier estado del wizard.
    """
    current_state = await state.get_state()

    if current_state is None:
        await message.answer("No hay operación en curso.")
        return

    await state.clear()
    await message.answer(
        "❌ Operación cancelada.\n\n"
        "Usa /config para volver al menú de configuración."
    )
    logger.debug(f"🚫 Operación cancelada desde estado {current_state}")