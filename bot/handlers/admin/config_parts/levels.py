"""
Handlers para la configuración de niveles.
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares.database import DatabaseMiddleware
from bot.middlewares.admin_auth import AdminAuthMiddleware
from bot.services.container import ServiceContainer
from bot.states.configuration import LevelConfigStates
from bot.utils.config_keyboards import config_list_keyboard, config_item_keyboard, confirm_keyboard

logger = logging.getLogger(__name__)

# Router para niveles
levels_router = Router(name="config_levels")


@levels_router.callback_query(F.data == "config:levels")
async def callback_config_levels(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Mostrar lista de niveles configurados."""
    await state.update_data(current_menu="levels")

    container = ServiceContainer(session, callback.bot)
    levels = await container.configuration.list_levels()

    # Crear texto con la lista de niveles
    if levels:
        levels_list = "\n".join([
            f"• {level.name} (≥{level.min_points} pts) - {level.icon}"
            for level in levels
        ])
        text = (
            "📈 <b>Niveles Configurados</b>\n\n"
            f"Se encontraron {len(levels)} niveles:\n\n"
            f"{levels_list}\n\n"
            "<i>Funcionalidad de edición en desarrollo</i>"
        )
    else:
        text = (
            "📈 <b>Niveles Configurados</b>\n\n"
            "No hay niveles configurados aún.\n\n"
            "<i>Funcionalidad de creación en desarrollo</i>"
        )

    # Convertir niveles para usar con config_list_keyboard
    items = [(level.id, f"{level.name} (≥{level.min_points} pts)") for level in levels]

    keyboard = config_list_keyboard(
        items=items,
        prefix="config:levels",
        show_create=False,  # Temporalmente deshabilitado hasta que se implemente
        show_back=True
    )

    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await state.set_state(LevelConfigStates.list_levels)
    await callback.answer()


@levels_router.callback_query(F.data.startswith("config:levels:view:"))
async def callback_config_view_level(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Ver detalles de un nivel específico."""
    level_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        level = await configuration_service.get_level(level_id)

        text = (
            f"📈 <b>Detalles del Nivel</b>\n\n"
            f"<b>Nombre:</b> {level.name}\n"
            f"<b>Icono:</b> {level.icon}\n"
            f"<b>Puntos mínimos:</b> {level.min_points}\n"
            f"<b>Puntos máximos:</b> {level.max_points or '∞'}\n"
            f"<b>Multiplicador:</b> {level.multiplier}x\n"
            f"<b>Color:</b> {level.color or 'Sin color'}\n"
            f"<b>Orden:</b> {level.order}\n"
            f"<b>Activo:</b> {'Sí' if level.is_active else 'No'}\n\n"
            "<i>¿Qué deseas hacer con este nivel?</i>"
        )

        keyboard = config_item_keyboard(
            item_id=level_id,
            prefix="config:levels",
            can_delete=True
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        await state.update_data(editing_id=level_id, editing_type="level")
        await state.set_state(LevelConfigStates.edit_select)
    except Exception as e:
        logger.error(f"Error al ver nivel {level_id}: {e}")
        await callback.answer("❌ Error al cargar el nivel", show_alert=True)

    await callback.answer()


@levels_router.callback_query(F.data == "config:levels:create")
async def callback_config_create_level(
    callback: CallbackQuery,
    state: FSMContext
):
    """Iniciar creación de nuevo nivel."""
    await state.clear()
    await state.set_state(LevelConfigStates.create_name)

    text = (
        "📈 <b>Creando Nuevo Nivel</b>\n\n"
        "Primero, ingresa el nombre del nivel.\n\n"
        "<b>Ejemplo:</b> Principiante, Intermedio, Experto"
    )

    await callback.message.edit_text(
        text=text,
        parse_mode="HTML"
    )
    await callback.answer()


@levels_router.callback_query(F.data.startswith("config:levels:edit:"))
async def callback_config_edit_level(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Editar un nivel específico."""
    level_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        level = await configuration_service.get_level(level_id)

        await state.update_data(editing_id=level_id)
        await state.set_state(LevelConfigStates.edit_field)

        text = (
            "✏️ <b>Editando Nivel</b>\n\n"
            f"<b>Actual:</b> {level.name}\n\n"
            "Selecciona qué campo deseas editar:"
        )

        from bot.utils.config_keyboards import InlineKeyboardBuilder
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
            InlineKeyboardButton(text="◀️ Volver", callback_data=f"config:levels:view:{level_id}")
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error al editar nivel {level_id}: {e}")
        await callback.answer("❌ Error al cargar el nivel para editar", show_alert=True)

    await callback.answer()


@levels_router.callback_query(F.data.startswith("config:levels:delete:"))
async def callback_config_delete_level(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """Eliminar un nivel específico."""
    level_id = int(callback.data.split(":")[-1])

    container = ServiceContainer(session, callback.bot)
    configuration_service = container.configuration

    try:
        level = await configuration_service.get_level(level_id)

        text = (
            f"🗑️ <b>Eliminar Nivel</b>\n\n"
            f"<b>Nombre:</b> {level.name}\n"
            f"<b>Icono:</b> {level.icon}\n\n"
            "<b>¿Estás seguro de que deseas eliminar este nivel?</b>\n\n"
            "Esta operación no se puede deshacer."
        )

        keyboard = confirm_keyboard(
            confirm_callback=f"confirm_delete:level:{level_id}",
            cancel_callback=f"config:levels:view:{level_id}"
        )

        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error al preparar eliminación de nivel {level_id}: {e}")
        await callback.answer("❌ Error al preparar la eliminación", show_alert=True)

    await callback.answer()


@levels_router.message(LevelConfigStates.edit_value)
async def message_edit_level_value(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """Recibe el nuevo valor para editar un campo de nivel."""
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
        elif editing_field == "min_points":
            try:
                points = int(new_value)
                if points < 0:
                    await message.answer("❌ Los puntos no pueden ser negativos.\n\nInténtalo de nuevo:")
                    return
                update_kwargs["min_points"] = points
            except ValueError:
                await message.answer("❌ Por favor ingresa un número válido para los puntos mínimos.\n\nInténtalo de nuevo:")
                return
        elif editing_field == "max_points":
            try:
                if new_value.lower() in ["none", "null", "n/a", ""]:
                    update_kwargs["max_points"] = None
                else:
                    points = int(new_value)
                    if points < 0:
                        await message.answer("❌ Los puntos no pueden ser negativos.\n\nInténtalo de nuevo:")
                        return
                    update_kwargs["max_points"] = points
            except ValueError:
                await message.answer("❌ Por favor ingresa un número válido para los puntos máximos o 'none'.\n\nInténtalo de nuevo:")
                return
        elif editing_field == "multiplier":
            try:
                multiplier = float(new_value)
                if multiplier < 0.1 or multiplier > 10:
                    await message.answer("❌ El multiplicador debe estar entre 0.1 y 10.\n\nInténtalo de nuevo:")
                    return
                update_kwargs["multiplier"] = multiplier
            except ValueError:
                await message.answer("❌ Por favor ingresa un número válido para el multiplicador.\n\nInténtalo de nuevo:")
                return
        elif editing_field == "icon":
            # Validar que sea un emoji o caracteres válidos
            if len(new_value) > 4:  # Permitir un emoji o texto corto
                await message.answer("❌ El icono debe ser un emoji o texto corto.\n\nInténtalo de nuevo:")
                return
            update_kwargs["icon"] = new_value
        elif editing_field == "color":
            # Puede ser un código de color o texto, aceptamos cualquier valor o vacío
            update_kwargs["color"] = new_value if new_value else None
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

        # Actualizar el nivel
        updated_level = await configuration_service.update_level(
            level_id=editing_id,
            **update_kwargs
        )

        await message.answer(
            f"✅ Nivel actualizado correctamente:\n"
            f"<b>{editing_field.upper()}:</b> {new_value}",
            parse_mode="HTML"
        )

        # Volver a la vista de edición del nivel
        await state.update_data(editing_id=editing_id, editing_type="level")
        await state.set_state(LevelConfigStates.edit_select)

        # Volver a mostrar los detalles del nivel
        text = (
            f"📈 <b>Detalles del Nivel</b>\n\n"
            f"<b>Nombre:</b> {updated_level.name}\n"
            f"<b>Icono:</b> {updated_level.icon}\n"
            f"<b>Puntos mínimos:</b> {updated_level.min_points}\n"
            f"<b>Puntos máximos:</b> {updated_level.max_points or '∞'}\n"
            f"<b>Multiplicador:</b> {updated_level.multiplier}x\n"
            f"<b>Color:</b> {updated_level.color or 'Sin color'}\n"
            f"<b>Orden:</b> {updated_level.order}\n"
            f"<b>Activo:</b> {'Sí' if updated_level.is_active else 'No'}\n\n"
            "<i>¿Qué deseas hacer con este nivel?</i>"
        )

        keyboard = config_item_keyboard(
            item_id=editing_id,
            prefix="config:levels",
            can_delete=True
        )

        await message.answer(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Error al editar valor de nivel: {e}")
        await message.answer("❌ Error al actualizar el nivel. Inténtalo de nuevo.")