"""
Handlers CRUD para configuración de reacciones (emojis).
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot.gamification.services.container import GamificationContainer
from bot.gamification.utils.validators import is_valid_emoji

router = Router()


class ReactionConfigStates(StatesGroup):
    """Estados para configuración de reacciones."""
    waiting_emoji = State()
    waiting_name = State()  # For compatibility with interface, though we might not use it
    waiting_besitos = State()
    editing_value = State()


# ========================================
# MENÚ PRINCIPAL
# ========================================

@router.callback_query(F.data == "gamif:admin:reactions")
async def reactions_menu(callback: CallbackQuery, session):
    """Muestra lista de reacciones configuradas."""
    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session)
    # Since the model doesn't have a 'name' field, we'll use emoji as name
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

            text += f"{status} {reaction.emoji} <b>{reaction.emoji}</b>: {reaction.besitos_value} besito(s){state_text}\n"

            # Botones por reacción
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"{reaction.emoji} {reaction.emoji}",
                    callback_data=f"gamif:reaction:view:{reaction.id}"
                ),
                InlineKeyboardButton(
                    text="✏️",
                    callback_data=f"gamif:reaction:edit:{reaction.id}"
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
    await state.set_state(ReactionConfigStates.waiting_emoji)
    await callback.answer()


@router.message(ReactionConfigStates.waiting_emoji)
async def receive_emoji(message: Message, state: FSMContext, session):
    """Recibe y valida emoji."""
    emoji = message.text.strip()

    # Validar emoji
    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session)
    if not is_valid_emoji(emoji):
        await message.answer("❌ Debe ser un emoji válido. Intenta de nuevo:")
        return

    # Verificar que no exista
    existing = await gamification.reaction.get_reaction_by_emoji(emoji)
    if existing:
        await message.answer(
            f"❌ El emoji {emoji} ya está configurado.\n\n"
            f"Valor actual: {existing.besitos_value} besito(s)"
        )
        await state.clear()
        return

    await state.update_data(emoji=emoji)

    await message.answer(
        f"✅ Emoji: {emoji}\n\n"
        f"¿Cuántos besitos otorgará este emoji?\n\n"
        f"Envía un número (ej: 1, 2, 5)"
    )
    await state.set_state(ReactionConfigStates.waiting_besitos)


@router.message(ReactionConfigStates.waiting_besitos)
async def receive_besitos_value(message: Message, state: FSMContext, session):
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
    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session)
    reaction = await gamification.reaction.create_reaction(
        emoji=data['emoji'],
        besitos_value=besitos
    )

    await message.answer(
        f"✅ <b>Emoji Configurado</b>\n\n"
        f"{reaction.emoji} <b>{reaction.emoji}</b>\n"
        f"Valor: {reaction.besitos_value} besito(s)\n\n"
        f"Los usuarios ahora ganarán besitos al usar este emoji.",
        parse_mode="HTML"
    )

    await state.clear()


# ========================================
# EDITAR REACCIÓN
# ========================================

@router.callback_query(F.data.startswith("gamif:reaction:edit:"))
async def edit_reaction(callback: CallbackQuery, session):
    """Muestra opciones de edición."""
    reaction_id = int(callback.data.split(":")[-1])

    # Get reaction
    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session)
    reaction = await gamification.reaction.get_by_id(reaction_id)

    if not reaction:
        await callback.answer("❌ Reacción no encontrada", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Cambiar Valor", callback_data=f"gamif:reaction:change_value:{reaction_id}"),
            InlineKeyboardButton(
                text="🔄 Desactivar" if reaction.active else "✅ Activar",
                callback_data=f"gamif:reaction:toggle:{reaction_id}"
            )
        ],
        [
            InlineKeyboardButton(text="🗑️ Eliminar", callback_data=f"gamif:reaction:delete:{reaction_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:admin:reactions")
        ]
    ])

    text = f"""📝 <b>Editar Reacción</b>

{reaction.emoji} <b>{reaction.emoji}</b>

Valor actual: {reaction.besitos_value} besito(s)
Estado: {'Activo' if reaction.active else 'Inactivo'}
"""

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:reaction:view:"))
async def view_reaction(callback: CallbackQuery, session):
    """Muestra detalles de reacción."""
    reaction_id = int(callback.data.split(":")[-1])

    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session)
    reaction = await gamification.reaction.get_by_id(reaction_id)

    if not reaction:
        await callback.answer("❌ Reacción no encontrada", show_alert=True)
        return

    status = "✅ Activo" if reaction.active else "❌ Inactivo"

    # Obtener estadísticas de uso
    stats = await gamification.reaction.get_reaction_stats(reaction_id)

    text = f"""📊 <b>Detalles de Reacción</b>

{reaction.emoji} <b>{reaction.emoji}</b>

<b>Valor:</b> {reaction.besitos_value} besito(s)
<b>Estado:</b> {status}

<b>Estadísticas:</b>
• Usos totales: {stats.get('total_uses', 0):,}
• Besitos distribuidos: {stats.get('total_besitos', 0):,}
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Editar Valor", callback_data=f"gamif:reaction:change_value:{reaction_id}"),
            InlineKeyboardButton(
                text="🔄 Desactivar" if reaction.active else "✅ Activar",
                callback_data=f"gamif:reaction:toggle:{reaction_id}"
            )
        ],
        [
            InlineKeyboardButton(text="🗑️ Eliminar", callback_data=f"gamif:reaction:delete:{reaction_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:admin:reactions")
        ]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:reaction:change_value:"))
async def start_change_value(callback: CallbackQuery, state: FSMContext):
    """Inicia edición de valor."""
    reaction_id = int(callback.data.split(":")[-1])
    await state.update_data(editing_reaction_id=reaction_id)

    await callback.message.edit_text(
        "✏️ <b>Editar Valor</b>\n\n"
        "Envía el nuevo valor de besitos:",
        parse_mode="HTML"
    )
    await state.set_state(ReactionConfigStates.editing_value)
    await callback.answer()


@router.message(ReactionConfigStates.editing_value)
async def receive_new_value(message: Message, state: FSMContext, session):
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

    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session)
    reaction = await gamification.reaction.update_reaction(
        reaction_id,
        besitos_value=besitos
    )

    await message.answer(
        f"✅ Valor actualizado\n\n"
        f"{reaction.emoji} {reaction.emoji}: {reaction.besitos_value} besito(s)"
    )

    await state.clear()


# ========================================
# ACTIVAR/DESACTIVAR
# ========================================

@router.callback_query(F.data.startswith("gamif:reaction:toggle:"))
async def toggle_reaction(callback: CallbackQuery, session):
    """Activa o desactiva reacción."""
    reaction_id = int(callback.data.split(":")[-1])

    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session)
    reaction = await gamification.reaction.get_by_id(reaction_id)
    new_state = not reaction.active

    await gamification.reaction.update_reaction(
        reaction_id,
        active=new_state
    )

    status_text = "activado" if new_state else "desactivado"
    await callback.answer(f"✅ Emoji {status_text}", show_alert=True)

    # Refrescar vista
    await view_reaction(callback, session)


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
async def confirm_delete_reaction(callback: CallbackQuery, session):
    """Elimina reacción."""
    reaction_id = int(callback.data.split(":")[-1])

    from bot.gamification.services.container import GamificationContainer
    gamification = GamificationContainer(session)
    await gamification.reaction.delete_reaction(reaction_id)

    await callback.answer("✅ Emoji eliminado", show_alert=True)
    await reactions_menu(callback, session)