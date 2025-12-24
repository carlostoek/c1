"""
Wizard de creación de recompensas paso a paso.

Flujo completo:
1. Seleccionar tipo de recompensa (BADGE, ITEM, PERMISSION, BESITOS)
2. Configurar metadata específica
3. (Opcional) Configurar unlock conditions
4. Confirmar y crear
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot.filters.admin import IsAdmin
from bot.gamification.states.admin import RewardWizardStates
from bot.gamification.services.container import GamificationContainer
from bot.gamification.database.enums import RewardType, BadgeRarity
from bot.gamification.utils.validators import is_valid_emoji

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


# ========================================
# INICIAR WIZARD
# ========================================

@router.callback_query(F.data == "gamif:wizard:reward")
async def start_reward_wizard(callback: CallbackQuery, state: FSMContext):
    """Inicia wizard de creación de recompensa."""
    await state.clear()
    await state.set_state(RewardWizardStates.select_type)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏆 Badge", callback_data="wizard:type:badge"),
            InlineKeyboardButton(text="🎁 Item", callback_data="wizard:type:item")
        ],
        [
            InlineKeyboardButton(text="🔓 Permiso", callback_data="wizard:type:permission"),
            InlineKeyboardButton(text="💰 Besitos", callback_data="wizard:type:besitos")
        ],
        [
            InlineKeyboardButton(text="❌ Cancelar", callback_data="wizard:cancel")
        ]
    ])

    await callback.message.edit_text(
        "🎁 <b>Wizard: Crear Recompensa</b>\n\n"
        "Paso 1/4: Selecciona el tipo de recompensa\n\n"
        "• <b>Badge:</b> Logro visual (icon + rareza)\n"
        "• <b>Item:</b> Item virtual coleccionable\n"
        "• <b>Permiso:</b> Permiso especial temporal\n"
        "• <b>Besitos:</b> Besitos adicionales",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# ========================================
# PASO 1: TIPO
# ========================================

@router.callback_query(RewardWizardStates.select_type, F.data.startswith("wizard:type:"))
async def select_reward_type(callback: CallbackQuery, state: FSMContext):
    """Procesa selección de tipo."""
    reward_type_str = callback.data.split(":")[-1]
    reward_type = RewardType(reward_type_str)

    await state.update_data(reward_type=reward_type)

    await callback.message.edit_text(
        f"✅ Tipo: <b>{reward_type_str.title()}</b>\n\n"
        f"Escribe el nombre de la recompensa\n\n"
        f"Ejemplo: \"Badge Maestro\"",
        parse_mode="HTML"
    )
    await state.set_state(RewardWizardStates.enter_reward_name)
    await callback.answer()


@router.message(RewardWizardStates.enter_reward_name)
async def enter_reward_name(message: Message, state: FSMContext):
    """Recibe nombre de recompensa."""
    if not message.text or len(message.text.strip()) < 3:
        await message.answer("❌ El nombre debe tener al menos 3 caracteres")
        return

    await state.update_data(reward_name=message.text.strip())

    await message.answer(
        f"✅ Nombre: <b>{message.text}</b>\n\n"
        f"Ahora escribe la descripción de la recompensa:",
        parse_mode="HTML"
    )
    await state.set_state(RewardWizardStates.enter_reward_description)


@router.message(RewardWizardStates.enter_reward_description)
async def enter_reward_description(message: Message, state: FSMContext):
    """Recibe descripción y redirige según tipo."""
    if not message.text or len(message.text.strip()) < 5:
        await message.answer("❌ La descripción debe tener al menos 5 caracteres")
        return

    await state.update_data(reward_description=message.text.strip())

    data = await state.get_data()
    reward_type = data['reward_type']

    # Redirigir según tipo
    if reward_type == RewardType.BADGE:
        await message.answer(
            "✅ Descripción guardada\n\n"
            "Paso 2/4: Envía el emoji/icono del badge\n\n"
            "Ejemplo: 🏆",
            parse_mode="HTML"
        )
        await state.set_state(RewardWizardStates.enter_badge_icon)

    elif reward_type == RewardType.BESITOS:
        await message.answer(
            "✅ Descripción guardada\n\n"
            "Paso 2/4: ¿Cuántos besitos otorgará?\n\n"
            "Ejemplo: 500",
            parse_mode="HTML"
        )
        await state.set_state(RewardWizardStates.enter_besitos_amount)

    elif reward_type == RewardType.PERMISSION:
        await message.answer(
            "✅ Descripción guardada\n\n"
            "Paso 2/4: Escribe la clave del permiso\n\n"
            "Ejemplo: extra_reactions",
            parse_mode="HTML"
        )
        await state.set_state(RewardWizardStates.enter_permission_key)

    elif reward_type == RewardType.ITEM:
        await message.answer(
            "✅ Descripción guardada\n\n"
            "Paso 2/4: Escribe el nombre interno del item\n\n"
            "Ejemplo: golden_heart",
            parse_mode="HTML"
        )
        await state.set_state(RewardWizardStates.enter_item_name)


# ========================================
# PASO 2: METADATA - BADGE
# ========================================

@router.message(RewardWizardStates.enter_badge_icon)
async def enter_badge_icon(message: Message, state: FSMContext):
    """Procesa emoji de badge."""
    if not is_valid_emoji(message.text):
        await message.answer("❌ Debe ser un emoji válido")
        return

    await state.update_data(badge_icon=message.text)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚪ Común", callback_data="wizard:rarity:common"),
            InlineKeyboardButton(text="🔵 Raro", callback_data="wizard:rarity:rare")
        ],
        [
            InlineKeyboardButton(text="🟣 Épico", callback_data="wizard:rarity:epic"),
            InlineKeyboardButton(text="🟠 Legendario", callback_data="wizard:rarity:legendary")
        ]
    ])

    await message.answer(
        f"✅ Icono: {message.text}\n\n"
        f"Selecciona la rareza del badge:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(RewardWizardStates.enter_badge_rarity)


@router.callback_query(RewardWizardStates.enter_badge_rarity, F.data.startswith("wizard:rarity:"))
async def enter_badge_rarity(callback: CallbackQuery, state: FSMContext):
    """Procesa rareza del badge."""
    rarity_str = callback.data.split(":")[-1]
    rarity = BadgeRarity(rarity_str)

    data = await state.get_data()
    await state.update_data(
        metadata={'icon': data['badge_icon'], 'rarity': rarity.value}
    )

    # Pasar a unlock conditions
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Por Misión", callback_data="wizard:unlock:mission"),
            InlineKeyboardButton(text="⭐ Por Nivel", callback_data="wizard:unlock:level")
        ],
        [
            InlineKeyboardButton(text="💰 Por Besitos", callback_data="wizard:unlock:besitos"),
            InlineKeyboardButton(text="⏭️ Sin Condición", callback_data="wizard:unlock:skip")
        ]
    ])

    await callback.message.edit_text(
        f"✅ Rareza: <b>{rarity_str.title()}</b>\n\n"
        f"Paso 3/4: ¿Cómo se desbloquea esta recompensa?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(RewardWizardStates.choose_unlock_type)
    await callback.answer()


# ========================================
# PASO 2: METADATA - BESITOS
# ========================================

@router.message(RewardWizardStates.enter_besitos_amount)
async def enter_besitos_amount(message: Message, state: FSMContext):
    """Procesa cantidad de besitos."""
    try:
        amount = int(message.text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número positivo")
        return

    await state.update_data(metadata={'amount': amount})

    # Besitos generalmente tienen unlock condition
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Por Misión", callback_data="wizard:unlock:mission"),
            InlineKeyboardButton(text="⭐ Por Nivel", callback_data="wizard:unlock:level")
        ],
        [
            InlineKeyboardButton(text="💰 Por Besitos", callback_data="wizard:unlock:besitos"),
            InlineKeyboardButton(text="⏭️ Sin Condición", callback_data="wizard:unlock:skip")
        ]
    ])

    await message.answer(
        f"✅ Cantidad: <b>{amount} besitos</b>\n\n"
        f"Paso 3/4: ¿Cómo se desbloquea?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(RewardWizardStates.choose_unlock_type)


# ========================================
# PASO 2: METADATA - PERMISSION
# ========================================

@router.message(RewardWizardStates.enter_permission_key)
async def enter_permission_key(message: Message, state: FSMContext):
    """Procesa clave del permiso."""
    if not message.text or len(message.text.strip()) < 3:
        await message.answer("❌ La clave debe tener al menos 3 caracteres")
        return

    await state.update_data(permission_key=message.text.strip())

    await message.answer(
        f"✅ Clave: <b>{message.text}</b>\n\n"
        f"¿Cuántos días durará el permiso?\n\n"
        f"Ejemplo: 30 (para 30 días)",
        parse_mode="HTML"
    )
    await state.set_state(RewardWizardStates.enter_permission_duration)


@router.message(RewardWizardStates.enter_permission_duration)
async def enter_permission_duration(message: Message, state: FSMContext):
    """Procesa duración del permiso."""
    try:
        days = int(message.text)
        if days <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número positivo de días")
        return

    data = await state.get_data()
    await state.update_data(
        metadata={'permission_key': data['permission_key'], 'duration_days': days}
    )

    # Pasar a unlock conditions
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Por Misión", callback_data="wizard:unlock:mission"),
            InlineKeyboardButton(text="⭐ Por Nivel", callback_data="wizard:unlock:level")
        ],
        [
            InlineKeyboardButton(text="💰 Por Besitos", callback_data="wizard:unlock:besitos"),
            InlineKeyboardButton(text="⏭️ Sin Condición", callback_data="wizard:unlock:skip")
        ]
    ])

    await message.answer(
        f"✅ Duración: <b>{days} días</b>\n\n"
        f"Paso 3/4: ¿Cómo se desbloquea?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(RewardWizardStates.choose_unlock_type)


# ========================================
# PASO 2: METADATA - ITEM
# ========================================

@router.message(RewardWizardStates.enter_item_name)
async def enter_item_name(message: Message, state: FSMContext):
    """Procesa nombre interno del item."""
    if not message.text or len(message.text.strip()) < 3:
        await message.answer("❌ El nombre debe tener al menos 3 caracteres")
        return

    await state.update_data(metadata={'item_key': message.text.strip()})

    # Pasar a unlock conditions
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Por Misión", callback_data="wizard:unlock:mission"),
            InlineKeyboardButton(text="⭐ Por Nivel", callback_data="wizard:unlock:level")
        ],
        [
            InlineKeyboardButton(text="💰 Por Besitos", callback_data="wizard:unlock:besitos"),
            InlineKeyboardButton(text="⏭️ Sin Condición", callback_data="wizard:unlock:skip")
        ]
    ])

    await message.answer(
        f"✅ Item: <b>{message.text}</b>\n\n"
        f"Paso 3/4: ¿Cómo se desbloquea?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(RewardWizardStates.choose_unlock_type)


# ========================================
# PASO 3: UNLOCK CONDITIONS
# ========================================

@router.callback_query(RewardWizardStates.choose_unlock_type, F.data == "wizard:unlock:skip")
async def skip_unlock(callback: CallbackQuery, state: FSMContext):
    """Sin unlock condition."""
    data = await state.get_data()
    summary = _generate_summary(data)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Confirmar", callback_data="wizard:confirm"),
            InlineKeyboardButton(text="❌ Cancelar", callback_data="wizard:cancel")
        ]
    ])

    await callback.message.edit_text(summary, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(RewardWizardStates.confirm)
    await callback.answer()


@router.callback_query(RewardWizardStates.choose_unlock_type, F.data == "wizard:unlock:mission")
async def unlock_by_mission(callback: CallbackQuery, state: FSMContext, gamification: GamificationContainer):
    """Seleccionar misión requerida."""
    missions = await gamification.mission.get_all_missions()

    if not missions:
        await callback.answer("⚠️ No hay misiones creadas. Crea una primero.", show_alert=True)
        return

    keyboard_buttons = []
    for mission in missions[:10]:  # Máximo 10 misiones
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{mission.name}",
                callback_data=f"wizard:select_mission:{mission.id}"
            )
        ])
    keyboard_buttons.append([
        InlineKeyboardButton(text="❌ Cancelar", callback_data="wizard:cancel")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.edit_text(
        "📋 <b>Seleccionar Misión</b>\n\n"
        "Elige la misión que desbloqueará esta recompensa:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(RewardWizardStates.select_mission)
    await callback.answer()


@router.callback_query(RewardWizardStates.select_mission, F.data.startswith("wizard:select_mission:"))
async def select_mission(callback: CallbackQuery, state: FSMContext, gamification: GamificationContainer):
    """Procesa selección de misión."""
    mission_id = int(callback.data.split(":")[-1])

    # Obtener nombre de misión para mostrar
    mission = await gamification.mission.get_mission(mission_id)
    if not mission:
        await callback.answer("❌ Misión no encontrada", show_alert=True)
        return

    await state.update_data(unlock_mission_id=mission_id, unlock_mission_name=mission.name)

    data = await state.get_data()
    summary = _generate_summary(data)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Confirmar", callback_data="wizard:confirm"),
            InlineKeyboardButton(text="❌ Cancelar", callback_data="wizard:cancel")
        ]
    ])

    await callback.message.edit_text(summary, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(RewardWizardStates.confirm)
    await callback.answer()


@router.callback_query(RewardWizardStates.choose_unlock_type, F.data == "wizard:unlock:level")
async def unlock_by_level(callback: CallbackQuery, state: FSMContext, gamification: GamificationContainer):
    """Seleccionar nivel requerido."""
    levels = await gamification.level.get_all_levels()

    if not levels:
        await callback.answer("⚠️ No hay niveles creados. Crea uno primero.", show_alert=True)
        return

    keyboard_buttons = []
    for level in levels[:10]:  # Máximo 10 niveles
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{level.name} (orden {level.level_order})",
                callback_data=f"wizard:select_level:{level.id}"
            )
        ])
    keyboard_buttons.append([
        InlineKeyboardButton(text="❌ Cancelar", callback_data="wizard:cancel")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.edit_text(
        "⭐ <b>Seleccionar Nivel</b>\n\n"
        "Elige el nivel que desbloqueará esta recompensa:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(RewardWizardStates.select_level)
    await callback.answer()


@router.callback_query(RewardWizardStates.select_level, F.data.startswith("wizard:select_level:"))
async def select_level(callback: CallbackQuery, state: FSMContext, gamification: GamificationContainer):
    """Procesa selección de nivel."""
    level_id = int(callback.data.split(":")[-1])

    # Obtener nombre de nivel para mostrar
    level = await gamification.level.get_level(level_id)
    if not level:
        await callback.answer("❌ Nivel no encontrado", show_alert=True)
        return

    await state.update_data(unlock_level_id=level_id, unlock_level_name=level.name)

    data = await state.get_data()
    summary = _generate_summary(data)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Confirmar", callback_data="wizard:confirm"),
            InlineKeyboardButton(text="❌ Cancelar", callback_data="wizard:cancel")
        ]
    ])

    await callback.message.edit_text(summary, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(RewardWizardStates.confirm)
    await callback.answer()


@router.callback_query(RewardWizardStates.choose_unlock_type, F.data == "wizard:unlock:besitos")
async def unlock_by_besitos(callback: CallbackQuery, state: FSMContext):
    """Configurar unlock por cantidad de besitos."""
    await callback.message.edit_text(
        "💰 <b>Unlock por Besitos</b>\n\n"
        "¿Cuántos besitos se requieren para desbloquear?\n\n"
        "Ejemplo: 1000",
        parse_mode="HTML"
    )
    await state.set_state(RewardWizardStates.enter_min_besitos)
    await callback.answer()


@router.message(RewardWizardStates.enter_min_besitos)
async def enter_min_besitos(message: Message, state: FSMContext):
    """Procesa cantidad mínima de besitos."""
    try:
        besitos = int(message.text)
        if besitos <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número positivo")
        return

    await state.update_data(unlock_besitos=besitos)

    data = await state.get_data()
    summary = _generate_summary(data)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Confirmar", callback_data="wizard:confirm"),
            InlineKeyboardButton(text="❌ Cancelar", callback_data="wizard:cancel")
        ]
    ])

    await message.answer(summary, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(RewardWizardStates.confirm)


# ========================================
# PASO 4: CONFIRMACIÓN
# ========================================

@router.callback_query(RewardWizardStates.confirm, F.data == "wizard:confirm")
async def confirm_reward(callback: CallbackQuery, state: FSMContext, gamification: GamificationContainer):
    """Crea recompensa usando orchestrator."""
    data = await state.get_data()

    await callback.message.edit_text("⚙️ Creando recompensa...", parse_mode="HTML")

    try:
        # Preparar reward_data
        reward_data = {
            'name': data['reward_name'],
            'description': data['reward_description'],
            'reward_type': data['reward_type'],
            'metadata': data.get('metadata', {}),
            'cost_besitos': data.get('cost_besitos')
        }

        # Crear usando orchestrator
        result = await gamification.reward_orchestrator.create_reward_with_unlock_condition(
            reward_data=reward_data,
            unlock_mission_id=data.get('unlock_mission_id'),
            unlock_level_id=data.get('unlock_level_id'),
            unlock_besitos=data.get('unlock_besitos'),
            created_by=callback.from_user.id
        )

        if result.get('validation_errors'):
            error_msg = "❌ <b>Errores de validación:</b>\n\n" + "\n".join(
                f"• {err}" for err in result['validation_errors']
            )
            await callback.message.edit_text(error_msg, parse_mode="HTML")
        else:
            reward = result['reward']
            await callback.message.edit_text(
                f"✅ <b>Recompensa Creada Exitosamente</b>\n\n"
                f"🎁 <b>{reward.name}</b>\n"
                f"Tipo: {reward.reward_type.value.title()}\n\n"
                f"Los usuarios ahora pueden desbloquearla según las condiciones configuradas.",
                parse_mode="HTML"
            )

        await state.clear()

    except Exception as e:
        await callback.message.edit_text(
            f"❌ <b>Error al crear recompensa:</b>\n\n{str(e)}",
            parse_mode="HTML"
        )

    await callback.answer()


# ========================================
# CANCELAR
# ========================================

@router.callback_query(F.data == "wizard:cancel")
async def cancel_wizard(callback: CallbackQuery, state: FSMContext):
    """Cancela wizard."""
    await state.clear()
    await callback.message.edit_text("❌ Wizard cancelado", parse_mode="HTML")
    await callback.answer()


# ========================================
# HELPERS
# ========================================

def _generate_summary(data: dict) -> str:
    """Genera resumen de configuración de recompensa."""
    summary = f"""🎁 <b>RESUMEN DE RECOMPENSA</b>

<b>Nombre:</b> {data['reward_name']}
<b>Tipo:</b> {data['reward_type'].value.title()}
<b>Descripción:</b> {data['reward_description']}
"""

    # Agregar metadata según tipo
    if data.get('metadata'):
        meta = data['metadata']
        if 'icon' in meta and 'rarity' in meta:
            summary += f"<b>Icono:</b> {meta['icon']}\n"
            summary += f"<b>Rareza:</b> {meta['rarity'].title()}\n"
        elif 'amount' in meta:
            summary += f"<b>Cantidad:</b> {meta['amount']} besitos\n"
        elif 'permission_key' in meta:
            summary += f"<b>Permiso:</b> {meta['permission_key']}\n"
            summary += f"<b>Duración:</b> {meta['duration_days']} días\n"
        elif 'item_key' in meta:
            summary += f"<b>Item:</b> {meta['item_key']}\n"

    # Agregar unlock condition
    summary += "\n<b>Condición de Desbloqueo:</b>\n"
    if data.get('unlock_mission_id'):
        mission_name = data.get('unlock_mission_name', f"ID {data['unlock_mission_id']}")
        summary += f"📋 Completar misión: {mission_name}"
    elif data.get('unlock_level_id'):
        level_name = data.get('unlock_level_name', f"ID {data['unlock_level_id']}")
        summary += f"⭐ Alcanzar nivel: {level_name}"
    elif data.get('unlock_besitos'):
        summary += f"💰 Tener {data['unlock_besitos']} besitos"
    else:
        summary += "⏭️ Disponible para todos"

    return summary
