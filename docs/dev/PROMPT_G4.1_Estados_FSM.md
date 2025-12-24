# PROMPT G4.1: Estados FSM - Wizards de Configuración

---

## ROL

Actúa como Ingeniero de Software Senior especializado en máquinas de estado finitas (FSM) y flows conversacionales con Aiogram 3.

---

## TAREA

Implementa los estados FSM en `bot/gamification/states/admin.py` para los wizards de creación de misiones y recompensas.

---

## CONTEXTO

### Sistema de Estados Existente
```python
# bot/states/admin.py (referencia)
from aiogram.fsm.state import State, StatesGroup

class ChannelSetupStates(StatesGroup):
    waiting_for_vip_channel = State()
    waiting_for_free_channel = State()
```

### Wizards Requeridos

**Wizard de Misión:** 6 pasos
1. Tipo de misión
2. Criterios específicos
3. Recompensa en besitos
4. Nivel auto (opcional)
5. Recompensas unlock (opcional)
6. Confirmación

**Wizard de Recompensa:** 4 pasos
1. Tipo de recompensa
2. Metadata específica
3. Unlock conditions
4. Confirmación

---

## ESTADOS REQUERIDOS

### MissionWizardStates

```python
class MissionWizardStates(StatesGroup):
    """Estados para wizard de creación de misión."""
    
    # Paso 1: Tipo de misión
    select_type = State()
    
    # Paso 2: Criterios (varía según tipo)
    enter_streak_days = State()
    enter_daily_count = State()
    enter_weekly_target = State()
    
    # Paso 3: Recompensa
    enter_besitos_reward = State()
    
    # Paso 4: Auto level-up (opcional)
    choose_auto_level = State()
    create_new_level = State()
    enter_level_name = State()
    enter_level_besitos = State()
    
    # Paso 5: Recompensas unlock (opcional)
    choose_rewards = State()
    create_new_reward = State()
    
    # Paso 6: Confirmación
    confirm = State()
```

### RewardWizardStates

```python
class RewardWizardStates(StatesGroup):
    """Estados para wizard de creación de recompensa."""
    
    # Paso 1: Tipo
    select_type = State()
    
    # Paso 2: Metadata
    enter_badge_icon = State()
    enter_badge_rarity = State()
    enter_permission_key = State()
    enter_besitos_amount = State()
    
    # Paso 3: Unlock conditions
    choose_unlock_type = State()
    select_mission = State()
    select_level = State()
    enter_min_besitos = State()
    
    # Paso 4: Confirmación
    confirm = State()
```

### BroadcastStates (extra)

```python
class BroadcastStates(StatesGroup):
    """Estados para broadcasting a usuarios."""
    
    waiting_for_message = State()
    confirm_broadcast = State()
```

---

## FORMATO DE SALIDA

```python
# bot/gamification/states/admin.py

"""
Estados FSM para wizards de administración de gamificación.

Estados para:
- Wizard de creación de misiones
- Wizard de creación de recompensas
- Broadcasting a usuarios
"""

from aiogram.fsm.state import State, StatesGroup


class MissionWizardStates(StatesGroup):
    """
    Estados para wizard de creación de misión.
    
    Flujo:
    1. Seleccionar tipo de misión
    2. Configurar criterios específicos
    3. Definir recompensa en besitos
    4. (Opcional) Configurar auto level-up
    5. (Opcional) Configurar recompensas unlock
    6. Confirmar creación
    """
    
    # Paso 1: Tipo
    select_type = State()
    
    # Paso 2: Criterios
    enter_streak_days = State()
    enter_daily_count = State()
    enter_weekly_target = State()
    enter_specific_reaction = State()
    
    # Paso 3: Recompensa
    enter_besitos_reward = State()
    
    # Paso 4: Auto level-up
    choose_auto_level = State()
    create_new_level = State()
    enter_level_name = State()
    enter_level_besitos = State()
    enter_level_order = State()
    
    # Paso 5: Recompensas
    choose_rewards = State()
    create_new_reward = State()
    enter_reward_name = State()
    enter_reward_description = State()
    
    # Paso 6: Confirmación
    confirm = State()


class RewardWizardStates(StatesGroup):
    """
    Estados para wizard de creación de recompensa.
    
    Flujo:
    1. Seleccionar tipo de recompensa
    2. Configurar metadata específica
    3. Configurar unlock conditions
    4. Confirmar creación
    """
    
    # Paso 1: Tipo
    select_type = State()
    
    # Paso 2: Metadata (según tipo)
    enter_badge_icon = State()
    enter_badge_rarity = State()
    enter_permission_key = State()
    enter_permission_duration = State()
    enter_besitos_amount = State()
    enter_item_name = State()
    
    # Paso 3: Unlock conditions
    choose_unlock_type = State()
    select_mission = State()
    select_level = State()
    enter_min_besitos = State()
    add_multiple_conditions = State()
    
    # Paso 4: Confirmación
    confirm = State()


class BroadcastStates(StatesGroup):
    """
    Estados para broadcasting de mensajes.
    
    Flujo:
    1. Esperar mensaje a enviar
    2. Confirmar broadcasting
    """
    
    waiting_for_message = State()
    confirm_broadcast = State()


class EditMissionStates(StatesGroup):
    """Estados para edición de misión existente."""
    
    select_mission = State()
    select_field = State()
    enter_new_value = State()
    confirm = State()


class EditRewardStates(StatesGroup):
    """Estados para edición de recompensa existente."""
    
    select_reward = State()
    select_field = State()
    enter_new_value = State()
    confirm = State()
```

---

## INTEGRACIÓN EN HANDLERS

```python
# bot/gamification/handlers/admin/mission_wizard.py

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from bot.gamification.states.admin import MissionWizardStates

router = Router()

@router.callback_query(F.data == "gamif:wizard:mission")
async def start_mission_wizard(callback: CallbackQuery, state: FSMContext):
    await state.set_state(MissionWizardStates.select_type)
    # ... continuar wizard
```

---

## STORAGE DE DATOS EN FSM

Usar `state.update_data()` para almacenar información entre pasos:

```python
# Paso 1
await state.update_data(mission_type=MissionType.STREAK)

# Paso 2
await state.update_data(criteria={'type': 'streak', 'days': 7})

# Al final
data = await state.get_data()
# data contiene toda la información acumulada
```

---

## VALIDACIÓN

- ✅ Estados para wizard de misión (11 estados)
- ✅ Estados para wizard de recompensa (10 estados)
- ✅ Estados para broadcasting
- ✅ Docstrings explicando flujo
- ✅ Nombres descriptivos

---

**ENTREGABLE:** Archivo `admin.py` con todos los estados FSM.
