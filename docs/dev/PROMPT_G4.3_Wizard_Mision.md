# PROMPT G4.3: Wizard Crear Misión

---

## ROL

Actúa como Ingeniero de Software Senior especializado en flujos conversacionales multi-paso con FSM en Aiogram 3.

---

## TAREA

Implementa el wizard completo de creación de misiones en `bot/gamification/handlers/admin/mission_wizard.py` usando los estados FSM y el ConfigurationOrchestrator.

---

## CONTEXTO

### Flujo del Wizard (6 pasos)

```
1. select_type → Elegir tipo de misión
2. enter_criteria → Configurar criterios (varía según tipo)
3. enter_besitos_reward → Definir recompensa
4. choose_auto_level → ¿Crear nivel nuevo? (opcional)
5. choose_rewards → ¿Crear recompensas? (opcional)
6. confirm → Revisar y confirmar
```

### Almacenamiento de Datos

```python
# Se acumula en state.update_data():
{
    'mission_type': MissionType.STREAK,
    'mission_name': 'Racha de 7 días',
    'mission_description': 'Reacciona 7 días consecutivos',
    'criteria': {'type': 'streak', 'days': 7},
    'besitos_reward': 500,
    'auto_level': {'name': 'Fanático', 'min_besitos': 1000, 'order': 4},
    'rewards': [{'name': 'Badge X', 'reward_type': 'badge', ...}]
}
```

---

## HANDLERS REQUERIDOS

### 1. Iniciar Wizard

```python
@router.callback_query(F.data == "gamif:wizard:mission")
async def start_mission_wizard(callback: CallbackQuery, state: FSMContext):
    """Inicia wizard de creación."""
```

### 2. Paso 1: Tipo de Misión

```python
@router.callback_query(MissionWizardStates.select_type)
async def select_mission_type(callback: CallbackQuery, state: FSMContext):
    """
    Botones:
    [🎯 Una Vez] [📅 Diaria]
    [📆 Semanal] [🔥 Racha]
    """
```

### 3. Paso 2: Criterios (múltiples handlers según tipo)

```python
@router.message(MissionWizardStates.enter_streak_days)
async def enter_streak_days(message: Message, state: FSMContext):
    """Usuario ingresa número de días para racha."""

@router.message(MissionWizardStates.enter_daily_count)
async def enter_daily_count(message: Message, state: FSMContext):
    """Usuario ingresa cantidad de reacciones diarias."""
```

### 4. Paso 3: Recompensa

```python
@router.message(MissionWizardStates.enter_besitos_reward)
async def enter_besitos_reward(message: Message, state: FSMContext):
    """Usuario ingresa cantidad de besitos."""
```

### 5. Paso 4: Auto Level (opcional)

```python
@router.callback_query(MissionWizardStates.choose_auto_level)
async def choose_auto_level(callback: CallbackQuery, state: FSMContext):
    """
    Botones:
    [➕ Crear Nivel Nuevo]
    [🔍 Seleccionar Existente]
    [⏭️ Saltar]
    """
```

### 6. Paso 5: Recompensas (opcional)

```python
@router.callback_query(MissionWizardStates.choose_rewards)
async def choose_rewards(callback: CallbackQuery, state: FSMContext):
    """
    Botones:
    [➕ Crear Recompensa]
    [✅ Finalizar]
    """
```

### 7. Paso 6: Confirmación

```python
@router.callback_query(MissionWizardStates.confirm)
async def confirm_mission(callback: CallbackQuery, state: FSMContext, gamification: GamificationContainer):
    """
    Muestra resumen completo.
    Botones: [✅ Confirmar] [✏️ Editar] [❌ Cancelar]
    
    Al confirmar:
    - Llamar a configuration_orchestrator.create_complete_mission_system()
    - Mostrar resultado
    - Limpiar estado
    """
```

### 8. Cancelar

```python
@router.callback_query(F.data == "wizard:cancel")
async def cancel_wizard(callback: CallbackQuery, state: FSMContext):
    """Cancela wizard en cualquier punto."""
```

---

## FORMATO DE SALIDA

```python
# bot/gamification/handlers/admin/mission_wizard.py

"""
Wizard de creación de misiones paso a paso.
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot.filters.admin import IsAdmin
from bot.gamification.states.admin import MissionWizardStates
from bot.gamification.services.container import GamificationContainer
from bot.gamification.database.enums import MissionType

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


# ========================================
# INICIAR WIZARD
# ========================================

@router.callback_query(F.data == "gamif:wizard:mission")
async def start_mission_wizard(callback: CallbackQuery, state: FSMContext):
    """Inicia wizard de creación de misión."""
    await state.clear()
    await state.set_state(MissionWizardStates.select_type)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎯 Una Vez", callback_data="wizard:type:one_time"),
            InlineKeyboardButton(text="📅 Diaria", callback_data="wizard:type:daily")
        ],
        [
            InlineKeyboardButton(text="📆 Semanal", callback_data="wizard:type:weekly"),
            InlineKeyboardButton(text="🔥 Racha", callback_data="wizard:type:streak")
        ],
        [
            InlineKeyboardButton(text="❌ Cancelar", callback_data="wizard:cancel")
        ]
    ])
    
    await callback.message.edit_text(
        "🎯 <b>Wizard: Crear Misión</b>\n\n"
        "Paso 1/6: Selecciona el tipo de misión\n\n"
        "• <b>Una Vez:</b> Completar una sola vez\n"
        "• <b>Diaria:</b> Se repite cada día\n"
        "• <b>Semanal:</b> Objetivo semanal\n"
        "• <b>Racha:</b> Días consecutivos",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# ========================================
# PASO 1: TIPO
# ========================================

@router.callback_query(MissionWizardStates.select_type, F.data.startswith("wizard:type:"))
async def select_mission_type(callback: CallbackQuery, state: FSMContext):
    """Procesa selección de tipo."""
    mission_type_str = callback.data.split(":")[-1]
    mission_type = MissionType(mission_type_str)
    
    await state.update_data(mission_type=mission_type)
    
    # Pedir nombre
    await callback.message.edit_text(
        f"✅ Tipo: {mission_type_str}\n\n"
        f"Paso 2/6: Escribe el nombre de la misión\n\n"
        f"Ejemplo: \"Racha de 7 días\"",
        parse_mode="HTML"
    )
    await state.set_state(MissionWizardStates.enter_mission_name)
    await callback.answer()


@router.message(MissionWizardStates.enter_mission_name)
async def enter_mission_name(message: Message, state: FSMContext):
    """Recibe nombre de misión."""
    await state.update_data(mission_name=message.text)
    
    await message.answer(
        f"✅ Nombre: {message.text}\n\n"
        f"Ahora escribe la descripción:",
        parse_mode="HTML"
    )
    await state.set_state(MissionWizardStates.enter_mission_description)


@router.message(MissionWizardStates.enter_mission_description)
async def enter_mission_description(message: Message, state: FSMContext):
    """Recibe descripción y pide criterios según tipo."""
    await state.update_data(mission_description=message.text)
    
    data = await state.get_data()
    mission_type = data['mission_type']
    
    # Redirigir según tipo
    if mission_type == MissionType.STREAK:
        await message.answer(
            "✅ Descripción guardada\n\n"
            "¿Cuántos días consecutivos se requieren?",
            parse_mode="HTML"
        )
        await state.set_state(MissionWizardStates.enter_streak_days)
    
    elif mission_type == MissionType.DAILY:
        await message.answer(
            "✅ Descripción guardada\n\n"
            "¿Cuántas reacciones diarias se requieren?",
            parse_mode="HTML"
        )
        await state.set_state(MissionWizardStates.enter_daily_count)
    
    # ... otros tipos


# ========================================
# PASO 2: CRITERIOS
# ========================================

@router.message(MissionWizardStates.enter_streak_days)
async def enter_streak_days(message: Message, state: FSMContext):
    """Procesa días de racha."""
    try:
        days = int(message.text)
        if days <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número positivo")
        return
    
    await state.update_data(criteria={'type': 'streak', 'days': days, 'require_consecutive': True})
    
    await message.answer(
        f"✅ Criterio: {days} días consecutivos\n\n"
        f"Paso 3/6: ¿Cuántos besitos otorgará?",
        parse_mode="HTML"
    )
    await state.set_state(MissionWizardStates.enter_besitos_reward)


# ========================================
# PASO 3: RECOMPENSA
# ========================================

@router.message(MissionWizardStates.enter_besitos_reward)
async def enter_besitos_reward(message: Message, state: FSMContext):
    """Procesa cantidad de besitos."""
    try:
        besitos = int(message.text)
        if besitos <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número positivo")
        return
    
    await state.update_data(besitos_reward=besitos)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Crear Nivel Nuevo", callback_data="wizard:level:new")],
        [InlineKeyboardButton(text="🔍 Seleccionar Existente", callback_data="wizard:level:select")],
        [InlineKeyboardButton(text="⏭️ Saltar", callback_data="wizard:level:skip")]
    ])
    
    await message.answer(
        f"✅ Recompensa: {besitos} besitos\n\n"
        f"Paso 4/6: ¿Subirá automáticamente de nivel?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(MissionWizardStates.choose_auto_level)


# ========================================
# PASO 4: AUTO LEVEL
# ========================================

@router.callback_query(MissionWizardStates.choose_auto_level, F.data == "wizard:level:skip")
async def skip_auto_level(callback: CallbackQuery, state: FSMContext):
    """Saltar auto level."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Crear Recompensa", callback_data="wizard:reward:new")],
        [InlineKeyboardButton(text="✅ Finalizar", callback_data="wizard:finish")]
    ])
    
    await callback.message.edit_text(
        "⏭️ Sin auto level-up\n\n"
        "Paso 5/6: ¿Desbloqueará recompensas?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(MissionWizardStates.choose_rewards)
    await callback.answer()


# ========================================
# PASO 6: CONFIRMACIÓN
# ========================================

@router.callback_query(F.data == "wizard:finish")
async def finish_wizard(callback: CallbackQuery, state: FSMContext):
    """Muestra resumen y confirma."""
    data = await state.get_data()
    
    summary = f"""📋 <b>RESUMEN DE CONFIGURACIÓN</b>

<b>Misión:</b> {data['mission_name']}
<b>Tipo:</b> {data['mission_type']}
<b>Descripción:</b> {data['mission_description']}
<b>Criterio:</b> {data['criteria']}
<b>Recompensa:</b> {data['besitos_reward']} besitos
"""
    
    if data.get('auto_level'):
        summary += f"\n<b>Nivel auto:</b> {data['auto_level']['name']}"
    
    if data.get('rewards'):
        summary += f"\n<b>Recompensas:</b> {len(data['rewards'])}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Confirmar", callback_data="wizard:confirm"),
            InlineKeyboardButton(text="❌ Cancelar", callback_data="wizard:cancel")
        ]
    ])
    
    await callback.message.edit_text(summary, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(MissionWizardStates.confirm)
    await callback.answer()


@router.callback_query(MissionWizardStates.confirm, F.data == "wizard:confirm")
async def confirm_mission(callback: CallbackQuery, state: FSMContext, gamification: GamificationContainer):
    """Crea misión usando orchestrator."""
    data = await state.get_data()
    
    await callback.message.edit_text("⚙️ Creando configuración...", parse_mode="HTML")
    
    try:
        result = await gamification.configuration_orchestrator.create_complete_mission_system(
            config={
                'mission': {
                    'name': data['mission_name'],
                    'description': data['mission_description'],
                    'mission_type': data['mission_type'],
                    'criteria': data['criteria'],
                    'besitos_reward': data['besitos_reward']
                },
                'auto_level': data.get('auto_level'),
                'rewards': data.get('rewards')
            },
            created_by=callback.from_user.id
        )
        
        if result.get('validation_errors'):
            await callback.message.edit_text(
                f"❌ Errores:\n" + "\n".join(result['validation_errors']),
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                result['summary'],
                parse_mode="HTML"
            )
        
        await state.clear()
    
    except Exception as e:
        await callback.message.edit_text(f"❌ Error: {e}", parse_mode="HTML")
    
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
```

---

## VALIDACIÓN

- ✅ Flujo completo de 6 pasos
- ✅ Validación de inputs
- ✅ Almacenamiento en state
- ✅ Resumen antes de confirmar
- ✅ Integración con ConfigurationOrchestrator
- ✅ Cancelación en cualquier punto

---

**ENTREGABLE:** Archivo `mission_wizard.py` con wizard completo.
