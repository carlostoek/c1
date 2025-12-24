# PROMPT G4.4: Wizard Crear Recompensa

---

## ROL

Actúa como Ingeniero de Software Senior especializado en flujos conversacionales multi-paso con FSM en Aiogram 3.

---

## TAREA

Implementa el wizard completo de creación de recompensas en `bot/gamification/handlers/admin/reward_wizard.py` usando los estados FSM y el RewardOrchestrator.

---

## CONTEXTO

### Flujo del Wizard (4 pasos)

```
1. select_type → Elegir tipo de recompensa
2. enter_metadata → Configurar metadata (varía según tipo)
3. choose_unlock → Configurar unlock conditions (opcional)
4. confirm → Revisar y confirmar
```

### Almacenamiento de Datos

```python
{
    'reward_name': 'Badge Maestro',
    'reward_description': 'Completaste todas las misiones',
    'reward_type': RewardType.BADGE,
    'metadata': {'icon': '🏆', 'rarity': 'legendary'},
    'unlock_mission_id': 5,
    'cost_besitos': None
}
```

---

## HANDLERS REQUERIDOS

### 1. Iniciar Wizard

```python
@router.callback_query(F.data == "gamif:wizard:reward")
async def start_reward_wizard(callback: CallbackQuery, state: FSMContext):
    """Inicia wizard de creación."""
```

### 2. Paso 1: Tipo de Recompensa

```python
@router.callback_query(RewardWizardStates.select_type)
async def select_reward_type(callback: CallbackQuery, state: FSMContext):
    """
    Botones:
    [🏆 Badge] [🎁 Item]
    [🔓 Permiso] [💰 Besitos]
    """
```

### 3. Paso 2: Metadata (múltiples handlers según tipo)

```python
@router.message(RewardWizardStates.enter_badge_icon)
async def enter_badge_icon(message: Message, state: FSMContext):
    """Usuario ingresa emoji para badge."""

@router.callback_query(RewardWizardStates.enter_badge_rarity)
async def enter_badge_rarity(callback: CallbackQuery, state: FSMContext):
    """
    Botones rareza:
    [⚪ Común] [🔵 Raro]
    [🟣 Épico] [🟠 Legendario]
    """
```

### 4. Paso 3: Unlock Conditions

```python
@router.callback_query(RewardWizardStates.choose_unlock_type)
async def choose_unlock_type(callback: CallbackQuery, state: FSMContext):
    """
    Botones:
    [📋 Por Misión] [⭐ Por Nivel]
    [💰 Por Besitos] [⏭️ Sin Condición]
    """
```

### 5. Paso 4: Confirmación

```python
@router.callback_query(RewardWizardStates.confirm, F.data == "wizard:confirm")
async def confirm_reward(callback: CallbackQuery, state: FSMContext, gamification: GamificationContainer):
    """
    Crear usando reward_orchestrator.create_reward_with_unlock_condition()
    """
```

---

## FORMATO DE SALIDA

```python
# bot/gamification/handlers/admin/reward_wizard.py

"""
Wizard de creación de recompensas paso a paso.
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
async def select_reward_type(callback: CallbackQuery, state: FSMContext):
    """Procesa selección de tipo."""
    reward_type_str = callback.data.split(":")[-1]
    reward_type = RewardType(reward_type_str)
    
    await state.update_data(reward_type=reward_type)
    
    await callback.message.edit_text(
        f"✅ Tipo: {reward_type_str}\n\n"
        f"Escribe el nombre de la recompensa:",
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
        f"Ahora escribe la descripción:"
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
            "Paso 2/4: Envía el emoji del badge (ej: 🏆)"
        )
        await state.set_state(RewardWizardStates.enter_badge_icon)
    
    elif reward_type == RewardType.BESITOS:
        await message.answer(
            "✅ Descripción guardada\n\n"
            "¿Cuántos besitos otorgará?"
        )
        await state.set_state(RewardWizardStates.enter_besitos_amount)
    
    # ... otros tipos


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
        f"Selecciona la rareza:",
        reply_markup=keyboard
    )
    await state.set_state(RewardWizardStates.enter_badge_rarity)


@router.callback_query(RewardWizardStates.enter_badge_rarity, F.data.startswith("wizard:rarity:"))
async def enter_badge_rarity(callback: CallbackQuery, state: FSMContext):
    """Procesa rareza del badge."""
    rarity_str = callback.data.split(":")[-1]
    rarity = BadgeRarity(rarity_str)
    
    data = await state.get_data()
    await state.update_data(
        metadata={'icon': data['badge_icon'], 'rarity': rarity}
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
        f"Paso 3/4: ¿Cómo se desbloquea?",
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
    
    # Pasar directamente a confirmación (besitos no tienen unlock)
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
# PASO 3: UNLOCK CONDITIONS
# ========================================

@router.callback_query(RewardWizardStates.choose_unlock_type, F.data == "wizard:unlock:skip")
async def skip_unlock(callback: CallbackQuery, state: FSMContext):
    """Sin unlock condition."""
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
async def unlock_by_mission(callback: CallbackQuery, state: FSMContext, gamification: GamificationContainer):
    """Seleccionar misión requerida."""
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
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(
        "Selecciona la misión requerida:",
        reply_markup=keyboard
    )
    await state.set_state(RewardWizardStates.select_mission)
    await callback.answer()


@router.callback_query(RewardWizardStates.select_mission, F.data.startswith("wizard:select_mission:"))
async def select_mission(callback: CallbackQuery, state: FSMContext):
    """Procesa selección de misión."""
    mission_id = int(callback.data.split(":")[-1])
    await state.update_data(unlock_mission_id=mission_id)
    
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


# ========================================
# PASO 4: CONFIRMACIÓN
# ========================================

@router.callback_query(RewardWizardStates.confirm, F.data == "wizard:confirm")
async def confirm_reward(callback: CallbackQuery, state: FSMContext, gamification: GamificationContainer):
    """Crea recompensa usando orchestrator."""
    data = await state.get_data()
    
    await callback.message.edit_text("⚙️ Creando recompensa...")
    
    try:
        result = await gamification.reward_orchestrator.create_reward_with_unlock_condition(
            reward_data={
                'name': data['reward_name'],
                'description': data['reward_description'],
                'reward_type': data['reward_type'],
                'metadata': data.get('metadata', {}),
                'cost_besitos': data.get('cost_besitos')
            },
            unlock_mission_id=data.get('unlock_mission_id'),
            unlock_level_id=data.get('unlock_level_id'),
            unlock_besitos=data.get('unlock_besitos'),
            created_by=callback.from_user.id
        )
        
        if result.get('validation_errors'):
            await callback.message.edit_text(
                f"❌ Errores:\n" + "\n".join(result['validation_errors'])
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
        await callback.message.edit_text(f"❌ Error: {e}")
    
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
    
    if data.get('unlock_mission_id'):
        summary += f"\n<b>Unlock:</b> Completar misión ID {data['unlock_mission_id']}"
    elif data.get('unlock_level_id'):
        summary += f"\n<b>Unlock:</b> Alcanzar nivel ID {data['unlock_level_id']}"
    elif data.get('unlock_besitos'):
        summary += f"\n<b>Unlock:</b> Tener {data['unlock_besitos']} besitos"
    else:
        summary += f"\n<b>Unlock:</b> Disponible para todos"
    
    return summary


# ========================================
# CANCELAR
# ========================================

@router.callback_query(F.data == "wizard:cancel")
async def cancel_wizard(callback: CallbackQuery, state: FSMContext):
    """Cancela wizard."""
    await state.clear()
    await callback.message.edit_text("❌ Wizard cancelado")
    await callback.answer()
```

---

## VALIDACIÓN

- ✅ Flujo completo de 4 pasos
- ✅ Validación de emojis
- ✅ Metadata por tipo de recompensa
- ✅ Unlock conditions opcionales
- ✅ Integración con RewardOrchestrator
- ✅ Resumen antes de confirmar

---

**ENTREGABLE:** Archivo `reward_wizard.py` con wizard completo.
