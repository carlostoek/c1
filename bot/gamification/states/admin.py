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
    2. Configurar nombre y descripción
    3. Configurar criterios específicos
    4. Definir recompensa en besitos
    5. (Opcional) Configurar auto level-up
    6. (Opcional) Configurar recompensas unlock
    7. Confirmar creación
    """

    # Paso 1: Tipo
    select_type = State()

    # Paso 2: Nombre y descripción
    enter_mission_name = State()
    enter_mission_description = State()

    # Paso 3: Criterios
    enter_streak_days = State()
    enter_daily_count = State()
    enter_weekly_target = State()
    enter_specific_reaction = State()

    # Paso 4: Recompensa
    enter_besitos_reward = State()

    # Paso 5: Auto level-up
    choose_auto_level = State()
    create_new_level = State()
    enter_level_name = State()
    enter_level_besitos = State()
    enter_level_order = State()

    # Paso 6: Recompensas
    choose_rewards = State()
    create_new_reward = State()
    enter_reward_name = State()
    enter_reward_description = State()

    # Paso 7: Confirmación
    confirm = State()


class RewardWizardStates(StatesGroup):
    """
    Estados para wizard de creación de recompensa.

    Flujo:
    1. Seleccionar tipo de recompensa
    2. Configurar nombre y descripción
    3. Configurar metadata específica
    4. Configurar unlock conditions
    5. Confirmar creación
    """

    # Paso 1: Tipo
    select_type = State()

    # Paso 2: Nombre y descripción
    enter_reward_name = State()
    enter_reward_description = State()

    # Paso 3: Metadata (según tipo)
    enter_badge_icon = State()
    enter_badge_rarity = State()
    enter_permission_key = State()
    enter_permission_duration = State()
    enter_besitos_amount = State()
    enter_item_name = State()

    # Paso 4: Unlock conditions
    choose_unlock_type = State()
    select_mission = State()
    select_level = State()
    enter_min_besitos = State()
    add_multiple_conditions = State()

    # Paso 5: Confirmación
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