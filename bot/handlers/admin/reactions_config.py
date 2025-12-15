"""
Reactions Config Handlers - Configuración de reacciones inline.

Handlers para:
- Ver menú de configuración de reacciones
- Listar reacciones existentes con estado
- Crear nueva reacción
- Editar reacción existente
- Activar/desactivar reacción
- Eliminar reacción
"""
import logging
from typing import Optional

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states.admin import ReactionConfigStates
from bot.services.container import ServiceContainer
from bot.utils.keyboards import create_inline_keyboard

logger = logging.getLogger(__name__)

# Router para handlers de configuración de reacciones
reactions_config_router = Router(name="reactions_config")


# ===== MENÚ PRINCIPAL =====

@reactions_config_router.callback_query(F.data == "admin:reactions_config")
async def callback_reactions_config_menu(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Muestra el menú principal de configuración de reacciones.
    
    Muestra:
    - Lista de reacciones existentes con estado (activa/inactiva)
    - Contador de reacciones activas (X/6)
    - Botones: Crear nueva, Volver al menú admin
    
    Args:
        callback: Callback query
        session: Sesión de BD
    """
    logger.info(f"📋 Usuario {callback.from_user.id} accedió a config de reacciones")
    
    container = ServiceContainer(session, callback.bot)
    
    # Obtener todas las reacciones
    all_reactions = await container.reactions.get_all_reactions(include_inactive=True)
    active_count = await container.reactions.count_active_reactions()
    
    # Construir texto del menú
    text = "⚙️ <b>Configuración de Reacciones</b>\n\n"
    
    if not all_reactions:
        text += "📭 <i>No hay reacciones configuradas</i>\n\n"
        text += "Las reacciones permiten que los usuarios interactúen con publicaciones "
        text += "y ganen Besitos por reaccionar.\n\n"
    else:
        text += f"📊 <b>Reacciones activas:</b> {active_count}/{container.reactions.MAX_ACTIVE_REACTIONS}\n\n"
        
        # Listar reacciones
        for reaction in all_reactions:
            status_emoji = "✅" if reaction.active else "❌"
            text += (
                f"{status_emoji} {reaction.emoji} <b>{reaction.label}</b> "
                f"→ {reaction.besitos_reward} 💋\n"
            )
        
        text += "\n"
    
    # Construir keyboard
    keyboard_buttons = []
    
    # Botones para cada reacción existente
    for reaction in all_reactions:
        status_icon = "✅" if reaction.active else "❌"
        keyboard_buttons.append([{
            "text": f"{status_icon} {reaction.emoji} {reaction.label}",
            "callback_data": f"reaction:view:{reaction.id}"
        }])
    
    # Botón crear nueva (solo si no se llegó al límite)
    if active_count < container.reactions.MAX_ACTIVE_REACTIONS:
        keyboard_buttons.append([{
            "text": "➕ Crear Nueva Reacción",
            "callback_data": "reaction:create"
        }])
    else:
        text += f"⚠️ <i>Límite de reacciones alcanzado ({container.reactions.MAX_ACTIVE_REACTIONS})</i>\n"
        text += "Desactiva una reacción para crear una nueva.\n\n"
    
    # Botón volver
    keyboard_buttons.append([{
        "text": "🔙 Volver al Menú Admin",
        "callback_data": "admin:main"
    }])
    
    # The create_inline_keyboard utility expects a list of lists of dictionaries.
    # The current structure of keyboard_buttons is already in this format.
    # No need to wrap it in another list.
    
    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard(keyboard_buttons),
        parse_mode="HTML"
    )
    
    await callback.answer()


@reactions_config_router.callback_query(F.data.startswith("reaction:view:"))
async def callback_view_reaction(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Muestra detalles de una reacción específica.
    
    Muestra:
    - Emoji, label, puntaje de besitos
    - Estado (activa/inactiva)
    - Opciones: Editar, Activar/Desactivar, Eliminar, Volver
    
    Args:
        callback: Callback query con formato "reaction:view:{id}"
        session: Sesión de BD
    """
    # Extraer ID de la reacción
    try:
        reaction_id = int(callback.data.split(":")[-1])
    except (ValueError, IndexError):
        logger.warning(f"Callback data malformado: {callback.data}")
        await callback.answer("Error procesando la solicitud.", show_alert=True)
        return

    logger.info(f"👁️ Usuario {callback.from_user.id} viendo reacción {reaction_id}")
    
    container = ServiceContainer(session, callback.bot)
    
    # Obtener reacción
    reaction = await container.reactions.get_reaction_by_id(reaction_id)
    
    if not reaction:
        logger.warning(f"Reacción no encontrada con ID: {reaction_id}")
        await callback.answer("❌ Reacción no encontrada", show_alert=True)
        return
    
    # Construir texto
    status = "✅ Activa" if reaction.active else "❌ Inactiva"
    
    text = (
        f"⚙️ <b>Detalles de Reacción</b>\n\n"
        f"<b>Emoji:</b> {reaction.emoji}\n"
        f"<b>Label:</b> {reaction.label}\n"
        f"<b>Besitos:</b> {reaction.besitos_reward} 💋\n"
        f"<b>Estado:</b> {status}\n"
        f"<b>Creada:</b> {reaction.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
    )
    
    # TODO: Agregar estadísticas de uso (cuántas veces se usó)
    # Esto se implementará cuando tengamos el tracking completo
    
    # Construir keyboard con opciones
    keyboard_buttons = []
    
    # Botones de edición
    keyboard_buttons.append([
        {
            "text": "✏️ Editar Label",
            "callback_data": f"reaction:edit_label:{reaction_id}"
        },
        {
            "text": "💋 Editar Besitos",
            "callback_data": f"reaction:edit_besitos:{reaction_id}"
        }
    ])
    
    # Botón activar/desactivar
    if reaction.active:
        keyboard_buttons.append([{
            "text": "❌ Desactivar",
            "callback_data": f"reaction:deactivate:{reaction_id}"
        }])
    else:
        active_count = await container.reactions.count_active_reactions()
        if active_count < container.reactions.MAX_ACTIVE_REACTIONS:
            keyboard_buttons.append([{
                "text": "✅ Activar",
                "callback_data": f"reaction:activate:{reaction_id}"
            }])
    
    # Botón eliminar
    keyboard_buttons.append([{
        "text": "🗑️ Eliminar",
        "callback_data": f"reaction:delete:{reaction_id}"
    }])
    
    # Botón volver
    keyboard_buttons.append([{
        "text": "🔙 Volver a Configuración",
        "callback_data": "admin:reactions_config"
    }])
    
    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard(keyboard_buttons),
        parse_mode="HTML"
    )
    
    await callback.answer()


# ===== CREAR NUEVA REACCIÓN =====

@reactions_config_router.callback_query(F.data == "reaction:create")
async def callback_create_reaction_start(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """
    Inicia el flujo de creación de nueva reacción.
    
    Paso 1 de 3: Solicita emoji al admin.
    
    Args:
        callback: Callback query
        state: FSM context
        session: Sesión de BD
    """
    logger.info(f"➕ Usuario {callback.from_user.id} iniciando creación de reacción")
    
    container = ServiceContainer(session, callback.bot)
    
    # Verificar límite de reacciones activas
    active_count = await container.reactions.count_active_reactions()
    if active_count >= container.reactions.MAX_ACTIVE_REACTIONS:
        await callback.answer(
            f"❌ Límite de {container.reactions.MAX_ACTIVE_REACTIONS} reacciones activas alcanzado",
            show_alert=True
        )
        return
    
    # Entrar en estado FSM
    await state.set_state(ReactionConfigStates.waiting_for_emoji)
    
    text = (
        "➕ <b>Crear Nueva Reacción</b>\n\n"
        "<b>Paso 1 de 3: Emoji</b>\n\n"
        "Envía el emoji que quieres usar para esta reacción.\n\n"
        "Ejemplos: ❤️ 👍 🔥 😍 💯 ⭐\n\n"
        "⚠️ El emoji debe ser único (no puede estar ya configurado)."
    )
    
    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard([[{
            "text": "❌ Cancelar",
            "callback_data": "reaction:create_cancel"
        }]]),
        parse_mode="HTML"
    )
    
    await callback.answer()


@reactions_config_router.message(ReactionConfigStates.waiting_for_emoji)
async def process_create_emoji(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """
    Procesa el emoji enviado por el admin.
    
    Valida:
    - Es un solo emoji (no texto)
    - No está duplicado
    
    Args:
        message: Mensaje con el emoji
        state: FSM context
        session: Sesión de BD
    """
    emoji = message.text.strip()
    user_id = message.from_user.id
    
    logger.debug(f"📥 User {user_id} envió emoji: '{emoji}'")
    
    container = ServiceContainer(session, message.bot)
    
    # Validación 1: Es un emoji (simple: longitud entre 1-4 chars)
    if not emoji or len(emoji) > 4:
        await message.answer(
            "❌ <b>Emoji Inválido</b>\n\n"
            "Por favor envía un solo emoji válido.\n\n"
            "Ejemplos válidos: ❤️ 👍 🔥",
            parse_mode="HTML"
        )
        return
    
    # Validación 2: No está duplicado
    existing = await container.reactions.get_reaction_by_emoji(emoji)
    if existing:
        await message.answer(
            f"❌ <b>Emoji Duplicado</b>\n\n"
            f"El emoji '{emoji}' ya está configurado como: <b>{existing.label}</b>\n\n"
            f"Estado: {'✅ Activa' if existing.active else '❌ Inactiva'}\n\n"
            "Por favor elige otro emoji.",
            parse_mode="HTML"
        )
        return
    
    # Emoji válido: guardar en FSM data y avanzar al paso 2
    await state.update_data(emoji=emoji)
    await state.set_state(ReactionConfigStates.waiting_for_label)
    
    logger.info(f"✅ User {user_id} - Emoji válido: '{emoji}'")
    
    await message.answer(
        f"✅ <b>Emoji Guardado:</b> {emoji}\n\n"
        f"<b>Paso 2 de 3: Label</b>\n\n"
        f"Envía un label descriptivo para esta reacción.\n\n"
        f"Ejemplos:\n"
        f"• \"Me encanta\"\n"
        f"• \"Me gusta\"\n"
        f"• \"Genial\"\n\n"
        f"⚠️ Máximo 50 caracteres.",
        parse_mode="HTML"
    )


@reactions_config_router.message(ReactionConfigStates.waiting_for_label)
async def process_create_label(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """
    Procesa el label enviado por el admin.
    
    Valida:
    - No está vacío
    - Longitud <= 50 caracteres
    
    Args:
        message: Mensaje con el label
        state: FSM context
        session: Sesión de BD
    """
    label = message.text.strip()
    user_id = message.from_user.id
    
    logger.debug(f"📥 User {user_id} envió label: '{label}'")
    
    # Validación 1: No está vacío
    if not label:
        await message.answer(
            "❌ <b>Label Vacío</b>\n\n"
            "El label no puede estar vacío.\n"
            "Por favor envía un texto descriptivo.",
            parse_mode="HTML"
        )
        return
    
    # Validación 2: Longitud <= 50
    if len(label) > 50:
        await message.answer(
            f"❌ <b>Label Muy Largo</b>\n\n"
            f"El label tiene {len(label)} caracteres.\n"
            f"Máximo permitido: 50 caracteres.\n\n"
            f"Por favor envía un label más corto.",
            parse_mode="HTML"
        )
        return
    
    # Label válido: guardar y avanzar al paso 3
    await state.update_data(label=label)
    await state.set_state(ReactionConfigStates.waiting_for_besitos)
    
    logger.info(f"✅ User {user_id} - Label válido: '{label}'")
    
    data = await state.get_data()
    emoji = data["emoji"]
    
    await message.answer(
        f"✅ <b>Label Guardado:</b> {label}\n\n"
        f"<b>Paso 3 de 3: Besitos</b>\n\n"
        f"¿Cuántos besitos 💋 se otorgarán al usar {emoji}?\n\n"
        f"Envía un número entero positivo (mínimo 1).\n\n"
        f"Ejemplos: 5, 10, 3",
        parse_mode="HTML"
    )


@reactions_config_router.message(ReactionConfigStates.waiting_for_besitos)
async def process_create_besitos(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """
    Procesa los besitos y crea la reacción.
    
    Valida:
    - Es número entero
    - Es >= 1
    
    Args:
        message: Mensaje con los besitos
        state: FSM context
        session: Sesión de BD
    """
    besitos_text = message.text.strip()
    user_id = message.from_user.id
    
    logger.debug(f"📥 User {user_id} envió besitos: '{besitos_text}'")
    
    # Validación 1: Es número entero
    try:
        besitos = int(besitos_text)
    except ValueError:
        await message.answer(
            "❌ <b>Número Inválido</b>\n\n"
            "Por favor envía un número entero válido.\n\n"
            "Ejemplos: 1, 5, 10",
            parse_mode="HTML"
        )
        return
    
    # Validación 2: Es >= 1
    if besitos < 1:
        await message.answer(
            "❌ <b>Besitos Inválidos</b>\n\n"
            "Los besitos deben ser al menos 1.\n\n"
            "Por favor envía un número positivo.",
            parse_mode="HTML"
        )
        return
    
    # Besitos válidos: crear reacción
    container = ServiceContainer(session, message.bot)
    data = await state.get_data()
    emoji = data["emoji"]
    label = data["label"]
    
    logger.info(
        f"➕ User {user_id} creando reacción: {emoji} '{label}' ({besitos} besitos)"
    )
    
    # Crear reacción en BD
    reaction = await container.reactions.create_reaction(
        emoji=emoji,
        label=label,
        besitos_reward=besitos
    )
    
    if reaction:
        # Éxito: limpiar estado y mostrar confirmación
        await state.clear()
        
        await message.answer(
            f"✅ <b>Reacción Creada</b>\n\n"
            f"<b>Emoji:</b> {reaction.emoji}\n"
            f"<b>Label:</b> {reaction.label}\n"
            f"<b>Besitos:</b> {reaction.besitos_reward} 💋\n"
            f"<b>Estado:</b> ✅ Activa\n\n"
            f"Los usuarios ahora podrán usar esta reacción en publicaciones.",
            reply_markup=create_inline_keyboard([[{
                "text": "🔙 Volver a Configuración",
                "callback_data": "admin:reactions_config"
            }]]),
            parse_mode="HTML"
        )
        
        logger.info(f"✅ Reacción {reaction.id} creada exitosamente")
    else:
        # Error al crear (límite alcanzado, duplicado, etc)
        await state.clear()
        
        await message.answer(
            "❌ <b>Error al Crear Reacción</b>\n\n"
            "No se pudo crear la reacción. Posibles causas:\n"
            "• Límite de reacciones alcanzado\n"
            "• Emoji duplicado (creado mientras editabas)\n\n"
            "Por favor intenta nuevamente.",
            reply_markup=create_inline_keyboard([[{
                "text": "🔙 Volver a Configuración",
                "callback_data": "admin:reactions_config"
            }]]),
            parse_mode="HTML"
        )
        
        logger.warning(f"⚠️ No se pudo crear reacción para user {user_id}")


@reactions_config_router.callback_query(F.data == "reaction:create_cancel")
async def callback_create_cancel(
    callback: CallbackQuery,
    state: FSMContext
):
    """
    Cancela el flujo de creación de reacción.
    
    Args:
        callback: Callback query
        state: FSM context
    """
    logger.info(f"❌ Usuario {callback.from_user.id} canceló creación de reacción")
    
    await state.clear()
    
    await callback.message.edit_text(
        "❌ <b>Creación Cancelada</b>\n\n"
        "No se creó ninguna reacción.",
        reply_markup=create_inline_keyboard([[{
            "text": "🔙 Volver a Configuración",
            "callback_data": "admin:reactions_config"
        }]]),
        parse_mode="HTML"
    )
    
    await callback.answer()


# ===== EDITAR REACCIÓN =====

@reactions_config_router.callback_query(F.data.startswith("reaction:edit_label:"))
async def callback_edit_label_start(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """
    Inicia el flujo de edición de label de una reacción.
    
    Args:
        callback: Callback query con formato "reaction:edit_label:{id}"
        state: FSM context
        session: Sesión de BD
    """
    reaction_id = int(callback.data.split(":")[-1])
    
    logger.info(f"✏️ Usuario {callback.from_user.id} editando label de reacción {reaction_id}")
    
    container = ServiceContainer(session, callback.bot)
    reaction = await container.reactions.get_reaction_by_id(reaction_id)
    
    if not reaction:
        await callback.answer("❌ Reacción no encontrada", show_alert=True)
        return
    
    # Guardar ID en FSM y entrar en estado de edición
    await state.update_data(editing_reaction_id=reaction_id)
    await state.set_state(ReactionConfigStates.editing_label)
    
    text = (
        f"✏️ <b>Editar Label</b>\n\n"
        f"<b>Reacción:</b> {reaction.emoji}\n"
        f"<b>Label actual:</b> {reaction.label}\n\n"
        f"Envía el nuevo label (máximo 50 caracteres)."
    )
    
    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard([[{
            "text": "❌ Cancelar",
            "callback_data": f"reaction:view:{reaction_id}"
        }]]),
        parse_mode="HTML"
    )
    
    await callback.answer()


@reactions_config_router.message(ReactionConfigStates.editing_label)
async def process_edit_label(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """
    Procesa el nuevo label y actualiza la reacción.
    
    Args:
        message: Mensaje con el nuevo label
        state: FSM context
        session: Sesión de BD
    """
    new_label = message.text.strip()
    user_id = message.from_user.id
    
    # Validaciones (mismas que en crear)
    if not new_label:
        await message.answer("❌ El label no puede estar vacío.", parse_mode="HTML")
        return
    
    if len(new_label) > 50:
        await message.answer(
            f"❌ Label muy largo ({len(new_label)} caracteres). Máximo: 50.",
            parse_mode="HTML"
        )
        return
    
    # Obtener ID de FSM data
    data = await state.get_data()
    reaction_id = data["editing_reaction_id"]
    
    # Actualizar en BD
    container = ServiceContainer(session, message.bot)
    updated = await container.reactions.update_reaction(
        reaction_id=reaction_id,
        label=new_label
    )
    
    await state.clear()
    
    if updated:
        logger.info(f"✅ User {user_id} actualizó label de reacción {reaction_id}")
        
        await message.answer(
            f"✅ <b>Label Actualizado</b>\n\n"
            f"<b>Reacción:</b> {updated.emoji}\n"
            f"<b>Nuevo label:</b> {updated.label}",
            reply_markup=create_inline_keyboard([[{
                "text": "🔙 Volver a Detalles",
                "callback_data": f"reaction:view:{reaction_id}"
            }]]),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "❌ Error al actualizar label.",
            reply_markup=create_inline_keyboard([[{
                "text": "🔙 Volver a Configuración",
                "callback_data": "admin:reactions_config"
            }]]),
            parse_mode="HTML"
        )


@reactions_config_router.callback_query(F.data.startswith("reaction:edit_besitos:"))
async def callback_edit_besitos_start(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession
):
    """
    Inicia el flujo de edición de besitos de una reacción.
    
    Args:
        callback: Callback query con formato "reaction:edit_besitos:{id}"
        state: FSM context
        session: Sesión de BD
    """
    reaction_id = int(callback.data.split(":")[-1])
    
    logger.info(f"💋 Usuario {callback.from_user.id} editando besitos de reacción {reaction_id}")
    
    container = ServiceContainer(session, callback.bot)
    reaction = await container.reactions.get_reaction_by_id(reaction_id)
    
    if not reaction:
        await callback.answer("❌ Reacción no encontrada", show_alert=True)
        return
    
    # Guardar ID y entrar en estado
    await state.update_data(editing_reaction_id=reaction_id)
    await state.set_state(ReactionConfigStates.editing_besitos)
    
    text = (
        f"💋 <b>Editar Besitos</b>\n\n"
        f"<b>Reacción:</b> {reaction.emoji} {reaction.label}\n"
        f"<b>Besitos actuales:</b> {reaction.besitos_reward} 💋\n\n"
        f"Envía la nueva cantidad de besitos (mínimo 1)."
    )
    
    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard([[{
            "text": "❌ Cancelar",
            "callback_data": f"reaction:view:{reaction_id}"
        }]]),
        parse_mode="HTML"
    )
    
    await callback.answer()


@reactions_config_router.message(ReactionConfigStates.editing_besitos)
async def process_edit_besitos(
    message: Message,
    state: FSMContext,
    session: AsyncSession
):
    """
    Procesa los nuevos besitos y actualiza la reacción.
    
    Args:
        message: Mensaje con los nuevos besitos
        state: FSM context
        session: Sesión de BD
    """
    besitos_text = message.text.strip()
    
    # Validaciones (mismas que en crear)
    try:
        besitos = int(besitos_text)
    except ValueError:
        await message.answer("❌ Por favor envía un número entero válido.")
        return
    
    if besitos < 1:
        await message.answer("❌ Los besitos deben ser al menos 1.")
        return
    
    # Obtener ID y actualizar
    data = await state.get_data()
    reaction_id = data["editing_reaction_id"]
    
    container = ServiceContainer(session, message.bot)
    updated = await container.reactions.update_reaction(
        reaction_id=reaction_id,
        besitos_reward=besitos
    )
    
    await state.clear()
    
    if updated:
        await message.answer(
            f"✅ <b>Besitos Actualizados</b>\n\n"
            f"<b>Reacción:</b> {updated.emoji} {updated.label}\n"
            f"<b>Nuevos besitos:</b> {updated.besitos_reward} 💋",
            reply_markup=create_inline_keyboard([[{
                "text": "🔙 Volver a Detalles",
                "callback_data": f"reaction:view:{reaction_id}"
            }]]),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "❌ Error al actualizar besitos.",
            reply_markup=create_inline_keyboard([[{
                "text": "🔙 Volver a Configuración",
                "callback_data": "admin:reactions_config"
            }]]),
            parse_mode="HTML"
        )


# ===== ACTIVAR/DESACTIVAR REACCIÓN =====

@reactions_config_router.callback_query(F.data.startswith("reaction:activate:"))
async def callback_activate_reaction(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Activa una reacción desactivada.
    
    Args:
        callback: Callback query con formato "reaction:activate:{id}"
        session: Sesión de BD
    """
    reaction_id = int(callback.data.split(":")[-1])
    
    logger.info(f"✅ Usuario {callback.from_user.id} activando reacción {reaction_id}")
    
    container = ServiceContainer(session, callback.bot)
    
    # Verificar límite
    active_count = await container.reactions.count_active_reactions()
    if active_count >= container.reactions.MAX_ACTIVE_REACTIONS:
        await callback.answer(
            f"❌ Límite de {container.reactions.MAX_ACTIVE_REACTIONS} reacciones activas alcanzado.\n"
            f"Desactiva otra reacción primero.",
            show_alert=True
        )
        return
    
    # Activar
    updated = await container.reactions.update_reaction(
        reaction_id=reaction_id,
        active=True
    )
    
    if updated:
        await callback.answer("✅ Reacción activada", show_alert=False)
        
        # Actualizar vista de detalles
        text = (
            f"⚙️ <b>Detalles de Reacción</b>\n\n"
            f"<b>Emoji:</b> {updated.emoji}\n"
            f"<b>Label:</b> {updated.label}\n"
            f"<b>Besitos:</b> {updated.besitos_reward} 💋\n"
            f"<b>Estado:</b> ✅ Activa\n"
        )
        
        keyboard_buttons = [
            [{
                "text": "✏️ Editar Label",
                "callback_data": f"reaction:edit_label:{reaction_id}"
            }, {
                "text": "💋 Editar Besitos",
                "callback_data": f"reaction:edit_besitos:{reaction_id}"
            }],
            [{
                "text": "❌ Desactivar",
                "callback_data": f"reaction:deactivate:{reaction_id}"
            }],
            [{
                "text": "🗑️ Eliminar",
                "callback_data": f"reaction:delete:{reaction_id}"
            }],
            [{
                "text": "🔙 Volver a Configuración",
                "callback_data": "admin:reactions_config"
            }]
        ]
        
        await callback.message.edit_text(
            text=text,
            reply_markup=create_inline_keyboard(keyboard_buttons),
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ Error al activar reacción", show_alert=True)


@reactions_config_router.callback_query(F.data.startswith("reaction:deactivate:"))
async def callback_deactivate_reaction(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Desactiva una reacción activa.
    
    Args:
        callback: Callback query con formato "reaction:deactivate:{id}"
        session: Sesión de BD
    """
    reaction_id = int(callback.data.split(":")[-1])
    
    logger.info(f"❌ Usuario {callback.from_user.id} desactivando reacción {reaction_id}")
    
    container = ServiceContainer(session, callback.bot)
    
    # Desactivar
    updated = await container.reactions.update_reaction(
        reaction_id=reaction_id,
        active=False
    )
    
    if updated:
        await callback.answer("✅ Reacción desactivada", show_alert=False)
        
        # Actualizar vista
        text = (
            f"⚙️ <b>Detalles de Reacción</b>\n\n"
            f"<b>Emoji:</b> {updated.emoji}\n"
            f"<b>Label:</b> {updated.label}\n"
            f"<b>Besitos:</b> {updated.besitos_reward} 💋\n"
            f"<b>Estado:</b> ❌ Inactiva\n"
        )
        
        keyboard_buttons = [
            [{
                "text": "✏️ Editar Label",
                "callback_data": f"reaction:edit_label:{reaction_id}"
            }, {
                "text": "💋 Editar Besitos",
                "callback_data": f"reaction:edit_besitos:{reaction_id}"
            }],
            [{
                "text": "✅ Activar",
                "callback_data": f"reaction:activate:{reaction_id}"
            }],
            [{
                "text": "🗑️ Eliminar",
                "callback_data": f"reaction:delete:{reaction_id}"
            }],
            [{
                "text": "🔙 Volver a Configuración",
                "callback_data": "admin:reactions_config"
            }]
        ]
        
        await callback.message.edit_text(
            text=text,
            reply_markup=create_inline_keyboard(keyboard_buttons),
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ Error al desactivar reacción", show_alert=True)


# ===== ELIMINAR REACCIÓN =====

@reactions_config_router.callback_query(F.data.startswith("reaction:delete:"))
async def callback_delete_reaction_confirm(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Muestra confirmación antes de eliminar una reacción.
    
    Args:
        callback: Callback query con formato "reaction:delete:{id}"
        session: Sesión de BD
    """
    reaction_id = int(callback.data.split(":")[-1])
    
    logger.info(f"🗑️ Usuario {callback.from_user.id} solicitando eliminar reacción {reaction_id}")
    
    container = ServiceContainer(session, callback.bot)
    reaction = await container.reactions.get_reaction_by_id(reaction_id)
    
    if not reaction:
        await callback.answer("❌ Reacción no encontrada", show_alert=True)
        return
    
    text = (
        f"🗑️ <b>Confirmar Eliminación</b>\n\n"
        f"<b>Reacción:</b> {reaction.emoji} {reaction.label}\n\n"
        f"⚠️ Esta acción no se puede deshacer.\n\n"
        f"Si esta reacción tiene histórico de uso, se desactivará en lugar de eliminarse "
        f"para mantener la integridad de los datos.\n\n"
        f"¿Estás seguro de eliminar esta reacción?"
    )
    
    keyboard_buttons = [
        [{
            "text": "✅ Sí, Eliminar",
            "callback_data": f"reaction:delete_confirm:{reaction_id}"
        }],
        [{
            "text": "❌ Cancelar",
            "callback_data": f"reaction:view:{reaction_id}"
        }]
    ]
    
    await callback.message.edit_text(
        text=text,
        reply_markup=create_inline_keyboard(keyboard_buttons),
        parse_mode="HTML"
    )
    
    await callback.answer()


@reactions_config_router.callback_query(F.data.startswith("reaction:delete_confirm:"))
async def callback_delete_reaction_execute(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Ejecuta la eliminación de la reacción.
    
    Args:
        callback: Callback query con formato "reaction:delete_confirm:{id}"
        session: Sesión de BD
    """
    reaction_id = int(callback.data.split(":")[-1])
    
    logger.info(f"🗑️ Usuario {callback.from_user.id} confirmó eliminar reacción {reaction_id}")
    
    container = ServiceContainer(session, callback.bot)
    
    # Eliminar (o desactivar si tiene histórico)
    success = await container.reactions.delete_reaction(reaction_id)
    
    if success:
        await callback.answer("✅ Reacción eliminada/desactivada", show_alert=False)
        
        await callback.message.edit_text(
            "✅ <b>Reacción Eliminada</b>\n\n"
            "La reacción ha sido eliminada (o desactivada si tenía histórico de uso).",
            reply_markup=create_inline_keyboard([[{
                "text": "🔙 Volver a Configuración",
                "callback_data": "admin:reactions_config"
            }]]),
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ Error al eliminar reacción", show_alert=True)
