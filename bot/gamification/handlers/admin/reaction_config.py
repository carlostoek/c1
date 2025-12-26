"""
Handlers CRUD para configuración de reacciones (emojis).

Responsabilidades:
- Lista de reacciones configuradas
- Agregar nuevo emoji con nombre y valor
- Vista detallada con estadísticas
- Edición de nombre y valor de besitos
- Activar/desactivar reacciones
- Eliminar reacciones
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
import logging

from bot.filters.admin import IsAdmin
from bot.middlewares import DatabaseMiddleware
from bot.gamification.states.admin import ReactionConfigStates
from bot.gamification.services.container import GamificationContainer
from bot.gamification.utils.validators import is_valid_emoji

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

# Registrar middleware
router.message.middleware(DatabaseMiddleware())
router.callback_query.middleware(DatabaseMiddleware())


# ========================================
# LISTA
# ========================================

@router.callback_query(F.data == "gamif:reactions:list")
@router.callback_query(F.data == "gamif:admin:reactions_list")
async def reactions_menu(callback: CallbackQuery, gamification: GamificationContainer):
    """Muestra lista de reacciones configuradas."""
    reactions = await gamification.reaction.get_all_reactions(active_only=False)

    text = "📝 <b>REACCIONES CONFIGURADAS</b>\n━━━━━━━━━━━━━━━━━━━━━\n\n"

    if not reactions:
        text += "No hay emojis configurados.\n\n"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Agregar Primer Emoji", callback_data="gamif:reactions:add")],
            [InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:menu")]
        ])
    else:
        keyboard_buttons = []

        for reaction in reactions:
            status = "✅" if reaction.active else "❌"
            state_text = "" if reaction.active else " (inactivo)"

            text += f"{status} {reaction.emoji} <b>{reaction.name}</b>: {reaction.besitos_value} besito(s){state_text}\n"

            # Botón por reacción
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"{reaction.emoji} {reaction.name}",
                    callback_data=f"gamif:reaction:view:{reaction.id}"
                )
            ])

        text += f"\n<i>Total: {len(reactions)} emoji(s)</i>"

        # Botones de acción
        keyboard_buttons.append([
            InlineKeyboardButton(text="➕ Agregar Emoji", callback_data="gamif:reactions:add")
        ])
        keyboard_buttons.append([
            InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:menu")
        ])

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# ========================================
# AGREGAR NUEVO EMOJI
# ========================================

@router.callback_query(F.data == "gamif:reactions:add")
async def start_add_reaction(callback: CallbackQuery, state: FSMContext):
    """Inicia proceso de agregar emoji."""
    await callback.message.edit_text(
        "➕ <b>Agregar Nuevo Emoji</b>\n\n"
        "Envía el emoji que deseas configurar.\n\n"
        "Ejemplo: ❤️",
        parse_mode="HTML"
    )
    await state.set_state(ReactionConfigStates.waiting_for_emoji)
    await callback.answer()


@router.message(ReactionConfigStates.waiting_for_emoji)
async def receive_emoji(message: Message, state: FSMContext, gamification: GamificationContainer):
    """Recibe y valida emoji."""
    emoji = message.text.strip()

    # Validar emoji
    if not is_valid_emoji(emoji):
        await message.answer("❌ Debe ser un emoji válido. Intenta de nuevo:")
        return

    # Verificar que no exista
    existing = await gamification.reaction.get_reaction_by_emoji(emoji)
    if existing:
        await message.answer(
            f"❌ El emoji {emoji} ya está configurado.\n\n"
            f"Nombre: {existing.name}\n"
            f"Valor actual: {existing.besitos_value} besito(s)"
        )
        await state.clear()
        return

    await state.update_data(emoji=emoji)

    await message.answer(
        f"✅ Emoji: {emoji}\n\n"
        f"Ahora envía un nombre descriptivo.\n\n"
        f"Ejemplos: Corazón, Fuego, Me gusta"
    )
    await state.set_state(ReactionConfigStates.waiting_for_name)


@router.message(ReactionConfigStates.waiting_for_name)
async def receive_name(message: Message, state: FSMContext):
    """Recibe nombre de la reacción."""
    name = message.text.strip()

    if len(name) < 2:
        await message.answer("❌ El nombre debe tener al menos 2 caracteres.")
        return

    await state.update_data(name=name)

    await message.answer(
        f"✅ Nombre: {name}\n\n"
        f"¿Cuántos besitos otorgará este emoji?\n\n"
        f"Envía un número (ej: 1, 2, 5)"
    )
    await state.set_state(ReactionConfigStates.waiting_for_besitos)


@router.message(ReactionConfigStates.waiting_for_besitos)
async def receive_besitos_value(message: Message, state: FSMContext, gamification: GamificationContainer):
    """Recibe valor de besitos y crea reacción."""
    try:
        besitos = int(message.text)
        if besitos <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número positivo. Intenta de nuevo:")
        return

    # Obtener datos acumulados
    data = await state.get_data()

    # Crear reacción
    reaction = await gamification.reaction.create_reaction(
        emoji=data['emoji'],
        name=data['name'],
        besitos_value=besitos
    )

    await message.answer(
        f"✅ <b>Emoji Configurado</b>\n\n"
        f"{reaction.emoji} <b>{reaction.name}</b>\n"
        f"Valor: {reaction.besitos_value} besito(s)\n\n"
        f"Los usuarios ahora ganarán besitos al usar este emoji.",
        parse_mode="HTML"
    )

    await state.clear()


# ========================================
# VISTA DETALLADA
# ========================================

@router.callback_query(F.data.startswith("gamif:reaction:view:"))
async def view_reaction(callback: CallbackQuery, gamification: GamificationContainer):
    """Muestra detalles de reacción con estadísticas."""
    reaction_id = int(callback.data.split(":")[-1])
    reaction = await gamification.reaction.get_reaction_by_id(reaction_id)

    if not reaction:
        await callback.answer("❌ Reacción no encontrada", show_alert=True)
        return

    status = "✅ Activo" if reaction.active else "❌ Inactivo"

    # Obtener estadísticas de uso
    stats = await gamification.reaction.get_reaction_stats(reaction_id)

    text = f"""📊 <b>Detalles de Reacción</b>

{reaction.emoji} <b>{reaction.name}</b>

<b>Valor:</b> {reaction.besitos_value} besito(s)
<b>Estado:</b> {status}

<b>Estadísticas:</b>
• Usos totales: {stats.get('total_uses', 0):,}
• Besitos distribuidos: {stats.get('total_besitos', 0):,}
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Editar", callback_data=f"gamif:reaction:edit:{reaction_id}"),
            InlineKeyboardButton(
                text="🔄 Desactivar" if reaction.active else "✅ Activar",
                callback_data=f"gamif:reaction:toggle:{reaction_id}"
            )
        ],
        [
            InlineKeyboardButton(text="🗑️ Eliminar", callback_data=f"gamif:reaction:delete:{reaction_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:reactions:list")
        ]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# ========================================
# EDICIÓN
# ========================================

@router.callback_query(F.data.startswith("gamif:reaction:edit:"))
async def edit_reaction_menu(callback: CallbackQuery):
    """Muestra menú de edición."""
    reaction_id = int(callback.data.split(":")[-1])

    text = "✏️ <b>EDITAR REACCIÓN</b>\n\n"
    text += "Selecciona qué deseas editar:"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📝 Nombre", callback_data=f"gamif:reaction:edit_name:{reaction_id}"),
            InlineKeyboardButton(text="💰 Valor", callback_data=f"gamif:reaction:edit_value:{reaction_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Volver", callback_data=f"gamif:reaction:view:{reaction_id}")
        ]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:reaction:edit_name:"))
async def start_edit_name(callback: CallbackQuery, state: FSMContext):
    """Inicia edición de nombre."""
    reaction_id = int(callback.data.split(":")[-1])
    await state.update_data(editing_reaction_id=reaction_id)

    await callback.message.edit_text(
        "✏️ <b>Editar Nombre</b>\n\n"
        "Envía el nuevo nombre:",
        parse_mode="HTML"
    )
    await state.set_state(ReactionConfigStates.waiting_for_edit_name)
    await callback.answer()


@router.message(ReactionConfigStates.waiting_for_edit_name)
async def process_edit_name(message: Message, state: FSMContext, gamification: GamificationContainer):
    """Procesa edición de nombre."""
    data = await state.get_data()
    reaction_id = data['editing_reaction_id']

    new_name = message.text.strip()

    if len(new_name) < 2:
        await message.answer("❌ El nombre debe tener al menos 2 caracteres.")
        return

    try:
        reaction = await gamification.reaction.update_reaction(
            reaction_id,
            name=new_name
        )
        await message.answer(
            f"✅ Nombre actualizado\n\n"
            f"{reaction.emoji} {reaction.name}"
        )
        await state.clear()
    except Exception as e:
        logger.error(f"Error updating reaction name: {e}")
        await message.answer("❌ Error al actualizar nombre")
        await state.clear()


@router.callback_query(F.data.startswith("gamif:reaction:edit_value:"))
async def start_change_value(callback: CallbackQuery, state: FSMContext):
    """Inicia edición de valor."""
    reaction_id = int(callback.data.split(":")[-1])
    await state.update_data(editing_reaction_id=reaction_id)

    await callback.message.edit_text(
        "✏️ <b>Editar Valor</b>\n\n"
        "Envía el nuevo valor de besitos:",
        parse_mode="HTML"
    )
    await state.set_state(ReactionConfigStates.waiting_for_edit_besitos)
    await callback.answer()


@router.message(ReactionConfigStates.waiting_for_edit_besitos)
async def receive_new_value(message: Message, state: FSMContext, gamification: GamificationContainer):
    """Actualiza valor de besitos."""
    try:
        besitos = int(message.text)
        if besitos <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número positivo.")
        return

    data = await state.get_data()
    reaction_id = data['editing_reaction_id']

    reaction = await gamification.reaction.update_reaction(
        reaction_id,
        besitos_value=besitos
    )

    await message.answer(
        f"✅ Valor actualizado\n\n"
        f"{reaction.emoji} {reaction.name}: {reaction.besitos_value} besito(s)"
    )

    await state.clear()


# ========================================
# ACTIVAR/DESACTIVAR
# ========================================

@router.callback_query(F.data.startswith("gamif:reaction:toggle:"))
async def toggle_reaction(callback: CallbackQuery, gamification: GamificationContainer):
    """Activa o desactiva reacción."""
    reaction_id = int(callback.data.split(":")[-1])

    reaction = await gamification.reaction.get_reaction_by_id(reaction_id)
    if not reaction:
        await callback.answer("❌ Reacción no encontrada", show_alert=True)
        return

    new_state = not reaction.active

    await gamification.reaction.update_reaction(
        reaction_id,
        active=new_state
    )

    status_text = "activado" if new_state else "desactivado"
    await callback.answer(f"✅ Emoji {status_text}", show_alert=True)

    # Refrescar vista
    await view_reaction(callback, gamification)


# ========================================
# ELIMINAR
# ========================================

@router.callback_query(F.data.startswith("gamif:reaction:delete:"))
async def delete_reaction(callback: CallbackQuery):
    """Pide confirmación para eliminar."""
    reaction_id = callback.data.split(":")[-1]

    text = (
        "⚠️ <b>Confirmar Eliminación</b>\n\n"
        "¿Estás seguro de eliminar este emoji?\n\n"
        "Esta acción no se puede deshacer."
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚠️ Sí, Eliminar", callback_data=f"gamif:reaction:delete_confirm:{reaction_id}"),
            InlineKeyboardButton(text="❌ Cancelar", callback_data=f"gamif:reaction:view:{reaction_id}")
        ]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:reaction:delete_confirm:"))
async def confirm_delete_reaction(callback: CallbackQuery, gamification: GamificationContainer):
    """Elimina reacción."""
    reaction_id = int(callback.data.split(":")[-1])

    await gamification.reaction.delete_reaction(reaction_id)

    await callback.answer("✅ Emoji eliminado", show_alert=True)
    await reactions_menu(callback, gamification)
