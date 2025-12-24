"""
Estados FSM para wizards de administración de gamificación.

Estados para:
- Wizard de creación de misiones
- Wizard de creación de recompensas
- Broadcasting a usuarios
- Edición de misiones existentes
- Edición de recompensas existentes
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
    enter_mission_name = State()
    enter_mission_description = State()

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
    enter_reward_name = State()
    enter_reward_description = State()

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


class LevelWizardStates(StatesGroup):
    """
    Estados para wizard de creación de nivel.

    Flujo:
    1. Introducir nombre del nivel
    2. Introducir besitos mínimos
    3. Introducir orden
    4. (Opcional) Introducir beneficios
    5. Confirmar creación
    """

    enter_level_name = State()
    enter_min_besitos = State()
    enter_level_order = State()
    enter_level_benefits = State() # Opcional, como JSON
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
