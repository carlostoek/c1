"""
Wizard de creación de recompensas paso a paso.
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot.middlewares import AdminAuthMiddleware, DatabaseMiddleware
from bot.gamification.states.admin import RewardWizardStates
from bot.gamification.services.container import GamificationContainer
from bot.gamification.database.enums import RewardType, BadgeRarity
from sqlalchemy.ext.asyncio import AsyncSession


def is_valid_emoji(text: str) -> bool:
    """
    Validador simple para verificar si un texto es un emoji.
    Nota: Esta es una implementación básica. Para validación más robusta,
    considera usar una librería como 'emoji' (pip install emoji).
    """
    # Verificar si es un caracter único que podría ser un emoji
    if len(text.strip()) == 1:
        return True
    # Validar algunos casos comunes de emojis compuestos
    text = text.strip()
    # Verificar si contiene caracteres que suelen formar emojis
    return any(ord(char) > 127 for char in text)


router = Router(name="reward_wizard")

# Aplicar middlewares (orden correcto: Database primero, AdminAuth después)
router.message.middleware(DatabaseMiddleware())
router.message.middleware(AdminAuthMiddleware())
router.callback_query.middleware(DatabaseMiddleware())
router.callback_query.middleware(AdminAuthMiddleware())


# ========================================
# INICIAR WIZARD
# ========================================

@router.callback_query(F.data == "gamif:wizard:reward")
async def start_reward_wizard(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
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
        "Paso 1/5: Selecciona el tipo de recompensa\n\n"
        "• <b>Badge:</b> Logro visual\n"
        "• <b>Item:</b> Item virtual\n"
        "• <b>Permiso:</b> Permiso especial\n"
        "• <b>Besitos:</b> Besitos extra",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# ========================================
# PASO 1: TIPO
# ========================================

@router.callback_query(RewardWizardStates.select_type, F.data.startswith("wizard:type:"))
async def select_reward_type(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Procesa selección de tipo."""
    reward_type_str = callback.data.split(":")[-1]
    reward_type = RewardType(reward_type_str)
    
    await state.update_data(reward_type=reward_type)
    
    await callback.message.edit_text(
        f"✅ Tipo: {reward_type_str}\n\n"
        f"Paso 2/5: Escribe el nombre de la recompensa:",
        parse_mode="HTML"
    )
    await state.set_state(RewardWizardStates.enter_reward_name)
    await callback.answer()


@router.message(RewardWizardStates.enter_reward_name)
async def enter_reward_name(message: Message, state: FSMContext):
    """Recibe nombre."""
    await state.update_data(reward_name=message.text)
    
    await message.answer(
        f"✅ Nombre: {message.text}\n\n"
        f"Paso 2/5: Ahora escribe la descripción:",
        parse_mode="HTML"
    )
    await state.set_state(RewardWizardStates.enter_reward_description)


@router.message(RewardWizardStates.enter_reward_description)
async def enter_reward_description(message: Message, state: FSMContext):
    """Recibe descripción y redirige según tipo."""
    await state.update_data(reward_description=message.text)
    
    data = await state.get_data()
    reward_type = data['reward_type']
    
    if reward_type == RewardType.BADGE:
        await message.answer(
            "✅ Descripción guardada\n\n"
            "Paso 3/5: Envía el emoji del badge (ej: 🏆)",
            parse_mode="HTML"
        )
        await state.set_state(RewardWizardStates.enter_badge_icon)
    
    elif reward_type == RewardType.PERMISSION:
        await message.answer(
            "✅ Descripción guardada\n\n"
            "Paso 3/5: Escribe la clave del permiso (ej: 'custom_emoji', 'change_username')",
            parse_mode="HTML"
        )
        await state.set_state(RewardWizardStates.enter_permission_key)
    
    elif reward_type == RewardType.BESITOS:
        await message.answer(
            "✅ Descripción guardada\n\n"
            "Paso 3/5: ¿Cuántos besitos otorgará?",
            parse_mode="HTML"
        )
        await state.set_state(RewardWizardStates.enter_besitos_amount)
    
    elif reward_type == RewardType.ITEM:
        await message.answer(
            "✅ Descripción guardada\n\n"
            "Paso 3/5: Escribe el nombre del item:",
            parse_mode="HTML"
        )
        await state.set_state(RewardWizardStates.enter_item_name)
    
    else:  # TITLE
        await message.answer(
            "✅ Descripción guardada\n\n"
            "Paso 3/5: Escribe el título a otorgar:",
            parse_mode="HTML"
        )
        await state.set_state(RewardWizardStates.enter_item_name)  # Using enter_item_name for titles too


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
        f"Paso 3/5: Selecciona la rareza:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(RewardWizardStates.enter_badge_rarity)


@router.callback_query(RewardWizardStates.enter_badge_rarity, F.data.startswith("wizard:rarity:"))
async def enter_badge_rarity(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Procesa rareza del badge."""
    rarity_str = callback.data.split(":")[-1]
    rarity = BadgeRarity(rarity_str)
    
    data = await state.get_data()
    await state.update_data(
        metadata={'icon': data['badge_icon'], 'rarity': rarity_str}
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
        f"✅ Rareza: {rarity_str}\n\n"
        f"Paso 4/5: ¿Cómo se desbloquea?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(RewardWizardStates.choose_unlock_type)
    await callback.answer()


# ========================================
# PASO 2: METADATA - PERMISSION
# ========================================

@router.message(RewardWizardStates.enter_permission_key)
async def enter_permission_key(message: Message, state: FSMContext):
    """Procesa clave de permiso."""
    permission_key = message.text.strip()
    
    await state.update_data(metadata={'permission_key': permission_key})
    
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
        f"✅ Permiso: {permission_key}\n\n"
        f"Paso 4/5: ¿Cómo se desbloquea?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(RewardWizardStates.choose_unlock_type)


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
    
    # Pasar a unlock conditions (besitos pueden tener unlock conditions también)
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
        f"✅ Cantidad: {amount} besitos\n\n"
        f"Paso 4/5: ¿Cómo se desbloquea?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(RewardWizardStates.choose_unlock_type)


# ========================================
# PASO 2: METADATA - ITEM
# ========================================

@router.message(RewardWizardStates.enter_item_name)
async def enter_item_name(message: Message, state: FSMContext):
    """Procesa nombre de item o título."""
    item_name = message.text
    data = await state.get_data()
    reward_type = data['reward_type']
    
    if reward_type == RewardType.ITEM:
        metadata = {'item_type': 'general', 'item_name': item_name}
    elif reward_type == RewardType.TITLE:
        metadata = {'title': item_name}
    else:
        metadata = {'item_name': item_name}  # fallback
    
    await state.update_data(metadata=metadata)
    
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
        f"✅ Nombre: {item_name}\n\n"
        f"Paso 4/5: ¿Cómo se desbloquea?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(RewardWizardStates.choose_unlock_type)


# ========================================
# PASO 3: UNLOCK CONDITIONS
# ========================================

@router.callback_query(RewardWizardStates.choose_unlock_type, F.data == "wizard:unlock:skip")
async def skip_unlock(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Sin unlock condition."""
    await state.update_data(unlock_type='none')
    
    data = await state.get_data()
    summary = generate_summary(data)
    
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
async def unlock_by_mission(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Seleccionar misión requerida."""
    gamification = GamificationContainer(session)
    missions = await gamification.mission.get_all_missions()
    
    if not missions:
        await callback.answer("No hay misiones creadas", show_alert=True)
        return
    
    keyboard_buttons = []
    for mission in missions[:10]:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{mission.name}",
                callback_data=f"wizard:select_mission:{mission.id}"
            )
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Volver", callback_data="wizard:back_to_unlock")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(
        "📋 <b>Selecciona la misión requerida:</b>\n\n"
        "(Mostrando primeras 10 misiones)",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(RewardWizardStates.select_mission)
    await callback.answer()


@router.callback_query(RewardWizardStates.select_mission, F.data.startswith("wizard:select_mission:"))
async def select_mission(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Procesa selección de misión."""
    mission_id = int(callback.data.split(":")[-1])
    await state.update_data(unlock_type='mission', unlock_mission_id=mission_id)
    
    data = await state.get_data()
    summary = generate_summary(data)
    
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
async def unlock_by_level(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Seleccionar nivel requerido."""
    gamification = GamificationContainer(session)
    levels = await gamification.level.get_all_levels()
    
    if not levels:
        await callback.answer("No hay niveles creados", show_alert=True)
        return
    
    keyboard_buttons = []
    for level in levels[:10]:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{level.name} (≥{level.min_besitos} besitos)",
                callback_data=f"wizard:select_level:{level.id}"
            )
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Volver", callback_data="wizard:back_to_unlock")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(
        "⭐ <b>Selecciona el nivel requerido:</b>\n\n"
        "(Mostrando primeros 10 niveles)",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(RewardWizardStates.select_level)
    await callback.answer()


@router.callback_query(RewardWizardStates.select_level, F.data.startswith("wizard:select_level:"))
async def select_level(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Procesa selección de nivel."""
    level_id = int(callback.data.split(":")[-1])
    await state.update_data(unlock_type='level', unlock_level_id=level_id)
    
    data = await state.get_data()
    summary = generate_summary(data)
    
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
async def unlock_by_besitos(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Configurar cantidad de besitos requeridos."""
    await callback.message.edit_text(
        "💰 <b>Cantidad de besitos requeridos:</b>\n\n"
        "Escribe el número mínimo de besitos necesarios para desbloquear esta recompensa.",
        parse_mode="HTML"
    )
    await state.set_state(RewardWizardStates.enter_min_besitos)
    await callback.answer()


@router.message(RewardWizardStates.enter_min_besitos)
async def enter_min_besitos(message: Message, state: FSMContext):
    """Procesa cantidad de besitos requeridos."""
    try:
        amount = int(message.text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número positivo")
        return
    
    await state.update_data(unlock_type='besitos', min_besitos=amount)
    
    data = await state.get_data()
    summary = generate_summary(data)
    
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
async def confirm_reward(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Crea recompensa usando orchestrator."""
    data = await state.get_data()
    gamification = GamificationContainer(session)
    
    await callback.message.edit_text("⚙️ Creando recompensa...", parse_mode="HTML")
    
    try:
        # Preparar los datos para crear la recompensa
        reward_data = {
            'name': data['reward_name'],
            'description': data['reward_description'],
            'reward_type': data['reward_type'],
            'metadata': data.get('metadata', {}),
        }
        
        # Determinar la condición de desbloqueo
        unlock_condition = {
            'type': data.get('unlock_type', 'none')
        }
        
        if data.get('unlock_type') == 'mission':
            unlock_condition['mission_id'] = data.get('unlock_mission_id')
        elif data.get('unlock_type') == 'level':
            unlock_condition['level_id'] = data.get('unlock_level_id')
        elif data.get('unlock_type') == 'besitos':
            unlock_condition['min_besitos'] = data.get('min_besitos')
        
        result = await gamification.reward_orchestrator.create_reward_with_unlock_condition(
            reward_data=reward_data,
            unlock_condition=unlock_condition,
            created_by=callback.from_user.id
        )
        
        if result.get('validation_errors'):
            await callback.message.edit_text(
                f"❌ Errores:\n" + "\n".join(result['validation_errors']),
                parse_mode="HTML"
            )
        else:
            reward = result['reward']
            await callback.message.edit_text(
                f"✅ <b>Recompensa Creada</b>\n\n"
                f"🎁 {reward.name}\n"
                f"Tipo: {reward.reward_type}\n\n"
                f"Los usuarios ahora pueden desbloquearla.",
                parse_mode="HTML"
            )
        
        await state.clear()
    
    except Exception as e:
        await callback.message.edit_text(f"❌ Error: {e}", parse_mode="HTML")
    
    await callback.answer()


# ========================================
# HELPERS
# ========================================

def generate_summary(data: dict) -> str:
    """Genera resumen de configuración."""
    summary = f"""🎁 <b>RESUMEN DE RECOMPENSA</b>

<b>Nombre:</b> {data['reward_name']}
<b>Tipo:</b> {data['reward_type']}
<b>Descripción:</b> {data['reward_description']}
"""
    
    if data.get('metadata'):
        meta = data['metadata']
        if 'icon' in meta:
            summary += f"<b>Icono:</b> {meta['icon']}\n"
        if 'rarity' in meta:
            summary += f"<b>Rareza:</b> {meta['rarity']}\n"
        if 'amount' in meta:
            summary += f"<b>Cantidad:</b> {meta['amount']} besitos\n"
        if 'permission_key' in meta:
            summary += f"<b>Clave permiso:</b> {meta['permission_key']}\n"
        if 'item_name' in meta:
            summary += f"<b>Nombre item:</b> {meta['item_name']}\n"
        if 'title' in meta:
            summary += f"<b>Título:</b> {meta['title']}\n"
    
    unlock_type = data.get('unlock_type')
    if unlock_type == 'mission':
        summary += f"\n<b>Unlock:</b> Completar misión ID {data.get('unlock_mission_id', 'N/A')}"
    elif unlock_type == 'level':
        summary += f"\n<b>Unlock:</b> Alcanzar nivel ID {data.get('unlock_level_id', 'N/A')}"
    elif unlock_type == 'besitos':
        summary += f"\n<b>Unlock:</b> Tener {data.get('min_besitos', 'N/A')} besitos"
    else:
        summary += f"\n<b>Unlock:</b> Disponible para todos"
    
    return summary


# ========================================
# CANCELAR
# ========================================

@router.callback_query(F.data == "wizard:cancel")
async def cancel_wizard(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Cancela wizard."""
    await state.clear()
    await callback.message.edit_text("❌ Wizard cancelado", parse_mode="HTML")
    await callback.answer()