"""
Estados FSM para el wizard de configuración de gamificación.

Estructura jerárquica:
- ConfigMainStates: Menú principal
- ActionConfigStates: Configuración de acciones/puntos
- LevelConfigStates: Configuración de niveles
- BadgeConfigStates: Configuración de badges
- RewardConfigStates: Configuración de recompensas
- MissionConfigStates: Configuración de misiones (más complejo por nested)
"""
from aiogram.fsm.state import State, StatesGroup


class ConfigMainStates(StatesGroup):
    """
    Estados del menú principal de configuración.
    
    Entry point: /config command
    """
    # Menú principal
    main_menu = State()


class ActionConfigStates(StatesGroup):
    """
    Estados para configuración de acciones que otorgan puntos.
    
    Flujo:
    1. list → Ver lista de acciones
    2. create_* → Crear nueva acción
    3. edit_* → Editar acción existente
    """
    # Vista de lista
    list_actions = State()
    
    # Crear acción
    create_key = State()
    create_name = State()
    create_points = State()
    create_description = State()
    create_confirm = State()
    
    # Editar acción
    edit_select = State()
    edit_field = State()
    edit_value = State()
    edit_confirm = State()


class LevelConfigStates(StatesGroup):
    """
    Estados para configuración de niveles/rangos.
    
    Flujo similar a acciones pero con campos diferentes.
    """
    # Vista de lista
    list_levels = State()
    
    # Crear nivel
    create_name = State()
    create_min_points = State()
    create_max_points = State()
    create_multiplier = State()
    create_icon = State()
    create_confirm = State()
    
    # Editar nivel
    edit_select = State()
    edit_field = State()
    edit_value = State()
    edit_confirm = State()
    
    # Reordenar niveles
    reorder = State()


class BadgeConfigStates(StatesGroup):
    """
    Estados para configuración de badges/insignias.
    """
    # Vista de lista
    list_badges = State()
    
    # Crear badge
    create_key = State()
    create_name = State()
    create_icon = State()
    create_requirement_type = State()
    create_requirement_value = State()
    create_description = State()
    create_confirm = State()
    
    # Editar badge
    edit_select = State()
    edit_field = State()
    edit_value = State()
    edit_confirm = State()


class RewardConfigStates(StatesGroup):
    """
    Estados para configuración de recompensas.
    
    Soporta nested creation de badge.
    """
    # Vista de lista
    list_rewards = State()
    
    # Crear recompensa
    create_name = State()
    create_type = State()
    create_points = State()
    create_badge_choice = State()  # Existente o nuevo
    create_description = State()
    create_confirm = State()
    
    # Sub-wizard para crear badge inline
    nested_badge_key = State()
    nested_badge_name = State()
    nested_badge_icon = State()
    nested_badge_confirm = State()
    
    # Editar recompensa
    edit_select = State()
    edit_field = State()
    edit_value = State()
    edit_confirm = State()


class MissionConfigStates(StatesGroup):
    """
    estados para configuración de misiones.
    
    Soporta nested creation de 2 niveles:
    - Mission → Reward
    - Mission → Reward → Badge
    """
    # Vista de lista
    list_missions = State()
    
    # Crear misión - datos básicos
    create_name = State()
    create_description = State()
    create_type = State()
    create_target_action = State()
    create_target_value = State()
    create_time_limit = State()  # Solo para tipo 'timed'
    create_repeatable = State()
    create_cooldown = State()  # Solo si repeatable
    
    # Crear misión - recompensa
    create_reward_choice = State()  # Existente o nueva
    
    # Sub-wizard nivel 1: crear recompensa inline
    nested_reward_name = State()
    nested_reward_type = State()
    nested_reward_points = State()
    nested_reward_badge_choice = State()  # Existente, nuevo, o ninguno
    
    # Sub-wizard nivel 2: crear badge inline
    nested_badge_key = State()
    nested_badge_name = State()
    nested_badge_icon = State()
    
    # Preview y confirmación
    preview = State()
    confirm = State()
    
    # Editar misión
    edit_select = State()
    edit_field = State()
    edit_value = State()
    edit_confirm = State()


# ═══════════════════════════════════════════════════════════════
# DATA KEYS PARA FSMContext
# ═══════════════════════════════════════════════════════════════

class ConfigDataKeys:
    """
    Keys para almacenar datos en FSMContext.data.
    
    Uso:
        await state.update_data({ConfigDataKeys.MISSION_NAME: "Mi Misión"})
        data = await state.get_data()
        name = data.get(ConfigDataKeys.MISSION_NAME)
    """
    # Action data
    ACTION_KEY = "action_key"
    ACTION_NAME = "action_name"
    ACTION_POINTS = "action_points"
    ACTION_DESCRIPTION = "action_description"
    
    # Level data
    LEVEL_NAME = "level_name"
    LEVEL_MIN_POINTS = "level_min_points"
    LEVEL_MAX_POINTS = "level_max_points"
    LEVEL_MULTIPLIER = "level_multiplier"
    LEVEL_ICON = "level_icon"
    
    # Badge data
    BADGE_KEY = "badge_key"
    BADGE_NAME = "badge_name"
    BADGE_ICON = "badge_icon"
    BADGE_REQ_TYPE = "badge_req_type"
    BADGE_REQ_VALUE = "badge_req_value"
    BADGE_DESCRIPTION = "badge_description"
    
    # Reward data
    REWARD_NAME = "reward_name"
    REWARD_TYPE = "reward_type"
    REWARD_POINTS = "reward_points"
    REWARD_BADGE_ID = "reward_badge_id"
    REWARD_DESCRIPTION = "reward_description"
    
    # Mission data
    MISSION_NAME = "mission_name"
    MISSION_DESCRIPTION = "mission_description"
    MISSION_TYPE = "mission_type"
    MISSION_TARGET_ACTION = "mission_target_action"
    MISSION_TARGET_VALUE = "mission_target_value"
    MISSION_TIME_LIMIT = "mission_time_limit"
    MISSION_REPEATABLE = "mission_repeatable"
    MISSION_COOLDOWN = "mission_cooldown"
    MISSION_REWARD_ID = "mission_reward_id"
    
    # Nested creation flags
    CREATING_NESTED_BADGE = "creating_nested_badge"
    CREATING_NESTED_REWARD = "creating_nested_reward"
    
    # Edit context
    EDITING_ID = "editing_id"
    EDITING_FIELD = "editing_field"
    
    # Navigation
    RETURN_TO = "return_to"  # Estado al que volver después de nested