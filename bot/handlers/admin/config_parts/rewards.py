"""
Handlers para la configuración de recompensas.
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares.database import DatabaseMiddleware
from bot.middlewares.admin_auth import AdminAuthMiddleware
from bot.services.container import ServiceContainer
from bot.states.configuration import RewardConfigStates
from bot.utils.config_keyboards import config_list_keyboard, config_item_keyboard, confirm_keyboard

logger = logging.getLogger(__name__)

# Router para recompensas
rewards_router = Router(name="config_rewards")


@rewards_router.callback_query(F.data == "config:rewards")
async def callback_config_rewards(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Mostrar lista de recompensas configuradas."""
    await state.update_data(current_menu="rewards")

    container = ServiceContainer(session, callback.bot)
    rewards = await container.configuration.list_rewards()

    # Crear texto con la lista de recompensas
    if rewards:
        rewards_list = "\n".join([
            f"• {reward.name} ({reward.reward_type})"
            for reward in rewards
        ])
        text = (
            "🎁 <b>Recompensas Configuradas</b>\n\n"
            f"Se encontraron {len(rewards)} recompensas:\n\n"
            f"{rewards_list}\n\n"
            "<i>Funcionalidad de edición en desarrollo</i>"
        )
    else:
        text = (
            "🎁 <b>Recompensas Configuradas</b>\n\n"
            "No hay recompensas configuradas aún.\n\n"
            "<i>Funcionalidad de creación en desarrollo</i>"
        )

    # Convertir recompensas para usar con config_list_keyboard
    items = [(reward.id, f"🎁 {reward.name}") for reward in rewards]

    keyboard = config_list_keyboard(
        items=items,
        prefix="config:rewards",
        show_create=False,  # Temporalmente deshabilitado hasta que se implemente
        show_back=True
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await state.set_state(RewardConfigStates.list_rewards)
    await callback.answer()


@rewards_router.callback_query(F.data.startswith("config:rewards:view:"))
async def callback_config_view_reward(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Ver detalles de una recompensa específica."""
    reward_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        reward = await configuration_service.get_reward(reward_id)

        badge_info = ""
        if reward.badge:
            badge_info = f"\n<b>Badge:</b> {reward.badge.icon} {reward.badge.name}"

        text = (
            f"🎁 <b>Detalles de la Recompensa</b>\n\n"
            f"<b>Nombre:</b> {reward.name}\n"
            f"<b>Tipo:</b> {reward.reward_type}\n"
            f"<b>Puntos:</b> {reward.points_amount or 'N/A'}\n"
            f"<b>Descripción:</b> {reward.description or 'Sin descripción'}\n"
            f"{badge_info}\n"
            f"<b>Activa:</b> {'Sí' if reward.is_active else 'No'}\n\n"
            "<i>¿Qué deseas hacer con esta recompensa?</i>"
        )

        keyboard = config_item_keyboard(
            item_id=reward_id,
            prefix="config:rewards",
            can_delete=True
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        await state.update_data(editing_id=reward_id, editing_type="reward")
        await state.set_state(RewardConfigStates.edit_select)
    except Exception as e:
        logger.error(f"Error al ver recompensa {reward_id}: {e}")
        await callback.answer("❌ Error al cargar la recompensa", show_alert=True)

    await callback.answer()


@rewards_router.callback_query(F.data == "config:rewards:create")
async def callback_config_create_reward(
    callback: CallbackQuery,
    state: FSMContext
):
    """Iniciar creación de nueva recompensa."""
    await state.clear()
    await state.set_state(RewardConfigStates.create_name)

    text = (
        "🎁 <b>Creando Nueva Recompensa</b>\n\n"
        "Primero, ingresa el nombre de la recompensa.\n\n"
        "<b>Ejemplo:</b> Bonus Points, Special Badge, Premium Access"
    )

    await callback.message.edit_text(
        text=text,
        parse_mode="HTML"
    )
    await callback.answer()


@rewards_router.callback_query(F.data.startswith("config:rewards:edit:"))
async def callback_config_edit_reward(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Editar una recompensa específica."""
    reward_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        reward = await configuration_service.get_reward(reward_id)

        await state.update_data(editing_id=reward_id)
        await state.set_state(RewardConfigStates.edit_field)

        text = (
            "✏️ <b>Editando Recompensa</b>\n\n"
            f"<b>Actual:</b> {reward.name}\n\n"
            "Selecciona qué campo deseas editar:"
        )

        from bot.utils.config_keyboards import InlineKeyboardBuilder
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
            InlineKeyboardButton(text="◀️ Volver", callback_data=f"config:rewards:view:{reward_id}")
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error al editar recompensa {reward_id}: {e}")
        await callback.answer("❌ Error al cargar la recompensa para editar", show_alert=True)

    await callback.answer()


@rewards_router.callback_query(F.data.startswith("config:rewards:delete:"))
async def callback_config_delete_reward(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Eliminar una recompensa específica."""
    reward_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        reward = await configuration_service.get_reward(reward_id)

        text = (
            f"🗑️ <b>Eliminar Recompensa</b>\n\n"
            f"<b>Nombre:</b> {reward.name}\n"
            f"<b>Tipo:</b> {reward.reward_type}\n\n"
            "<b>¿Estás seguro de que deseas eliminar esta recompensa?</b>\n\n"
            "Esta operación no se puede deshacer."
        )

        keyboard = confirm_keyboard(
            confirm_callback=f"confirm_delete:reward:{reward_id}",
            cancel_callback=f"config:rewards:view:{reward_id}"
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error al preparar eliminación de recompensa {reward_id}: {e}")
        await callback.answer("❌ Error al preparar la eliminación", show_alert=True)

    await callback.answer()


@rewards_router.message(RewardConfigStates.edit_value)
async def message_edit_reward_value(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Recibe el nuevo valor para editar un campo de recompensa."""
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
            valid_types = ["points", "badge", "both", "custom"]
            if new_value.lower() not in valid_types:
                await message.answer(
                    f"❌ Tipo de recompensa inválido.\n"
                    f"Opciones válidas: {', '.join(valid_types)}\n\n"
                    "Inténtalo de nuevo:"
                )
                return
            update_kwargs["reward_type"] = new_value.lower()
        elif editing_field == "points":
            try:
                if new_value.lower() in ["none", "null", "n/a", ""]:
                    update_kwargs["points_amount"] = None
                else:
                    points = int(new_value)
                    if points < 0:
                        await message.answer("❌ Los puntos no pueden ser negativos.\n\nInténtalo de nuevo:")
                        return
                    update_kwargs["points_amount"] = points
            except ValueError:
                await message.answer("❌ Por favor ingresa un número válido para los puntos o 'none'.\n\nInténtalo de nuevo:")
                return
        elif editing_field == "badge":
            try:
                if new_value.lower() in ["none", "null", "n/a", ""]:
                    update_kwargs["badge_id"] = None
                else:
                    badge_id = int(new_value)
                    # Validar que el badge exista
                    await configuration_service.get_badge_by_id(badge_id)
                    update_kwargs["badge_id"] = badge_id
            except ValueError:
                await message.answer("❌ Por favor ingresa un ID de badge válido o 'none'.\n\nInténtalo de nuevo:")
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

        # Actualizar la recompensa
        updated_reward = await configuration_service.update_reward(
            reward_id=editing_id,
            **update_kwargs
        )

        await message.answer(
            f"✅ Recompensa actualizada correctamente:\n"
            f"<b>{editing_field.upper()}:</b> {new_value}",
            parse_mode="HTML"
        )

        # Volver a la vista de edición de la recompensa
        await state.update_data(editing_id=editing_id, editing_type="reward")
        await state.set_state(RewardConfigStates.edit_select)

        # Volver a mostrar los detalles de la recompensa
        badge_info = ""
        if updated_reward.badge:
            badge_info = f"\n<b>Badge:</b> {updated_reward.badge.icon} {updated_reward.badge.name}"

        text = (
            f"🎁 <b>Detalles de la Recompensa</b>\n\n"
            f"<b>Nombre:</b> {updated_reward.name}\n"
            f"<b>Tipo:</b> {updated_reward.reward_type}\n"
            f"<b>Puntos:</b> {updated_reward.points_amount or 'N/A'}\n"
            f"<b>Descripción:</b> {updated_reward.description or 'Sin descripción'}\n"
            f"{badge_info}\n"
            f"<b>Activa:</b> {'Sí' if updated_reward.is_active else 'No'}\n\n"
            "<i>¿Qué deseas hacer con esta recompensa?</i>"
        )

        keyboard = config_item_keyboard(
            item_id=editing_id,
            prefix="config:rewards",
            can_delete=True
        )

        await message.answer(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Error al editar valor de recompensa: {e}")
        await message.answer("❌ Error al actualizar la recompensa. Inténtalo de nuevo.")