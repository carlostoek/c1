"""
Wizard de creación de misiones paso a paso.

Flujo completo:
1. Seleccionar tipo de misión (ONE_TIME, DAILY, WEEKLY, STREAK)
2. Configurar criterios específicos
3. Definir recompensa en besitos
4. (Opcional) Configurar auto level-up
5. (Opcional) Configurar recompensas
6. Confirmar y crear
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot.filters.admin import IsAdmin
from bot.middlewares import DatabaseMiddleware
from bot.gamification.states.admin import MissionWizardStates
from bot.gamification.services.container import GamificationContainer
from bot.gamification.database.enums import MissionType

PAGE_SIZE = 5

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

# Registrar middleware para inyectar session y gamification
router.message.middleware(DatabaseMiddleware())
router.callback_query.middleware(DatabaseMiddleware())


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
        f"✅ Tipo: <b>{mission_type_str.replace('_', ' ').title()}</b>\n\n"
        f"Paso 2/6: Escribe el nombre de la misión\n\n"
        f"Ejemplo: \"Racha de 7 días\"",
        parse_mode="HTML"
    )
    await state.set_state(MissionWizardStates.enter_mission_name)
    await callback.answer()


@router.message(MissionWizardStates.enter_mission_name)
async def enter_mission_name(message: Message, state: FSMContext):
    """Recibe nombre de misión."""
    if not message.text or len(message.text.strip()) < 3:
        await message.answer("❌ El nombre debe tener al menos 3 caracteres")
        return

    await state.update_data(mission_name=message.text.strip())

    await message.answer(
        f"✅ Nombre: <b>{message.text}</b>\n\n"
        f"Ahora escribe la descripción de la misión:",
        parse_mode="HTML"
    )
    await state.set_state(MissionWizardStates.enter_mission_description)


@router.message(MissionWizardStates.enter_mission_description)
async def enter_mission_description(message: Message, state: FSMContext):
    """Recibe descripción y pide criterios según tipo."""
    if not message.text or len(message.text.strip()) < 5:
        await message.answer("❌ La descripción debe tener al menos 5 caracteres")
        return

    await state.update_data(mission_description=message.text.strip())

    data = await state.get_data()
    mission_type = data['mission_type']

    # Redirigir según tipo
    if mission_type == MissionType.STREAK:
        await message.answer(
            "✅ Descripción guardada\n\n"
            "¿Cuántos días consecutivos se requieren?\n\n"
            "Ejemplo: 7",
            parse_mode="HTML"
        )
        await state.set_state(MissionWizardStates.enter_streak_days)

    elif mission_type == MissionType.DAILY:
        await message.answer(
            "✅ Descripción guardada\n\n"
            "¿Cuántas reacciones diarias se requieren?\n\n"
            "Ejemplo: 10",
            parse_mode="HTML"
        )
        await state.set_state(MissionWizardStates.enter_daily_count)

    elif mission_type == MissionType.WEEKLY:
        await message.answer(
            "✅ Descripción guardada\n\n"
            "¿Cuántas reacciones semanales se requieren?\n\n"
            "Ejemplo: 50",
            parse_mode="HTML"
        )
        await state.set_state(MissionWizardStates.enter_weekly_target)

    elif mission_type == MissionType.ONE_TIME:
        await message.answer(
            "✅ Descripción guardada\n\n"
            "¿Cuántas reacciones se requieren para completar?\n\n"
            "Ejemplo: 100",
            parse_mode="HTML"
        )
        await state.set_state(MissionWizardStates.enter_specific_reaction)


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
        f"✅ Criterio: <b>{days} días consecutivos</b>\n\n"
        f"Paso 3/6: ¿Cuántos besitos otorgará al completarla?",
        parse_mode="HTML"
    )
    await state.set_state(MissionWizardStates.enter_besitos_reward)


@router.message(MissionWizardStates.enter_daily_count)
async def enter_daily_count(message: Message, state: FSMContext):
    """Procesa cantidad diaria."""
    try:
        count = int(message.text)
        if count <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número positivo")
        return

    await state.update_data(criteria={'type': 'daily', 'count': count})

    await message.answer(
        f"✅ Criterio: <b>{count} reacciones diarias</b>\n\n"
        f"Paso 3/6: ¿Cuántos besitos otorgará al completarla?",
        parse_mode="HTML"
    )
    await state.set_state(MissionWizardStates.enter_besitos_reward)


@router.message(MissionWizardStates.enter_weekly_target)
async def enter_weekly_target(message: Message, state: FSMContext):
    """Procesa objetivo semanal."""
    try:
        count = int(message.text)
        if count <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número positivo")
        return

    await state.update_data(criteria={'type': 'weekly', 'count': count})

    await message.answer(
        f"✅ Criterio: <b>{count} reacciones semanales</b>\n\n"
        f"Paso 3/6: ¿Cuántos besitos otorgará al completarla?",
        parse_mode="HTML"
    )
    await state.set_state(MissionWizardStates.enter_besitos_reward)


@router.message(MissionWizardStates.enter_specific_reaction)
async def enter_one_time_count(message: Message, state: FSMContext):
    """Procesa cantidad para misión de una vez."""
    try:
        count = int(message.text)
        if count <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número positivo")
        return

    await state.update_data(criteria={'type': 'one_time', 'count': count})

    await message.answer(
        f"✅ Criterio: <b>{count} reacciones totales</b>\n\n"
        f"Paso 3/6: ¿Cuántos besitos otorgará al completarla?",
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
        f"✅ Recompensa: <b>{besitos} besitos</b>\n\n"
        f"Paso 4/6: ¿Al completar la misión subirá automáticamente de nivel?",
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
        [InlineKeyboardButton(text="🔍 Seleccionar Existente", callback_data="wizard:reward:select")],
        [InlineKeyboardButton(text="✅ Finalizar", callback_data="wizard:finish")]
    ])

    await callback.message.edit_text(
        "⏭️ Sin auto level-up\n\n"
        "Paso 5/6: ¿Desbloqueará recompensas adicionales al completarla?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(MissionWizardStates.choose_rewards)
    await callback.answer()


@router.callback_query(MissionWizardStates.choose_auto_level, F.data == "wizard:level:new")
async def choose_create_new_level(callback: CallbackQuery, state: FSMContext):
    """Iniciar creación de nuevo nivel."""
    await callback.message.edit_text(
        "➕ <b>Crear Nuevo Nivel</b>\n\n"
        "Escribe el nombre del nivel:\n\n"
        "Ejemplo: Fanático Legendario",
        parse_mode="HTML"
    )
    await state.set_state(MissionWizardStates.enter_level_name)
    await callback.answer()


@router.message(MissionWizardStates.enter_level_name)
async def enter_level_name(message: Message, state: FSMContext):
    """Recibe nombre de nivel."""
    if not message.text or len(message.text.strip()) < 3:
        await message.answer("❌ El nombre debe tener al menos 3 caracteres")
        return

    await state.update_data(level_name=message.text.strip())

    await message.answer(
        f"✅ Nivel: <b>{message.text}</b>\n\n"
        f"¿Cuántos besitos mínimos se requieren para este nivel?\n\n"
        f"Ejemplo: 1000",
        parse_mode="HTML"
    )
    await state.set_state(MissionWizardStates.enter_level_besitos)


@router.message(MissionWizardStates.enter_level_besitos)
async def enter_level_besitos(message: Message, state: FSMContext):
    """Recibe besitos mínimos para nivel."""
    try:
        besitos = int(message.text)
        if besitos <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número positivo")
        return

    await state.update_data(level_min_besitos=besitos)

    await message.answer(
        f"✅ Besitos requeridos: <b>{besitos}</b>\n\n"
        f"¿Qué orden tendrá este nivel?\n\n"
        f"Ejemplo: 4 (cuarto nivel)",
        parse_mode="HTML"
    )
    await state.set_state(MissionWizardStates.enter_level_order)


@router.message(MissionWizardStates.enter_level_order)
async def enter_level_order(message: Message, state: FSMContext):
    """Recibe orden del nivel."""
    try:
        order = int(message.text)
        if order <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número positivo")
        return

    # Guardar configuración completa de nivel
    data = await state.get_data()
    auto_level = {
        'name': data['level_name'],
        'min_besitos': data['level_min_besitos'],
        'order': order
    }
    await state.update_data(auto_level=auto_level)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Crear Recompensa", callback_data="wizard:reward:new")],
        [InlineKeyboardButton(text="🔍 Seleccionar Existente", callback_data="wizard:reward:select")],
        [InlineKeyboardButton(text="✅ Finalizar", callback_data="wizard:finish")]
    ])

    await message.answer(
        f"✅ Nivel configurado: <b>{data['level_name']}</b> (orden {order})\n\n"
        f"Paso 5/6: ¿Desbloqueará recompensas adicionales?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(MissionWizardStates.choose_rewards)


@router.callback_query(MissionWizardStates.choose_auto_level, F.data.startswith("wizard:level:select"))
async def choose_select_existing_level(callback: CallbackQuery, state: FSMContext, gamification: GamificationContainer):
    """Mostrar niveles existentes para selección con paginación."""
    parts = callback.data.split(":")
    page = int(parts[3]) if len(parts) > 3 else 1

    levels = await gamification.level.get_all_levels()

    if not levels:
        await callback.answer("⚠️ No hay niveles existentes. Crea uno nuevo.", show_alert=True)
        return

    start_index = (page - 1) * PAGE_SIZE
    end_index = start_index + PAGE_SIZE
    levels_on_page = levels[start_index:end_index]

    keyboard_rows = []
    for level in levels_on_page:
        keyboard_rows.append([
            InlineKeyboardButton(
                text=f"{level.name} (orden {level.order})",
                callback_data=f"wizard:level:id:{level.id}"
            )
        ])

    # Paginación
    total_pages = (len(levels) + PAGE_SIZE - 1) // PAGE_SIZE
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Anterior", callback_data=f"wizard:level:select:page:{page-1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="➡️ Siguiente", callback_data=f"wizard:level:select:page:{page+1}"))

    if nav_buttons:
        keyboard_rows.append(nav_buttons)

    keyboard_rows.append([InlineKeyboardButton(text="❌ Cancelar", callback_data="wizard:level:skip")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

    await callback.message.edit_text(
        f"🔍 <b>Seleccionar Nivel Existente</b> (Página {page}/{total_pages})\n\n"
        "Elige un nivel:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(MissionWizardStates.choose_auto_level, F.data.startswith("wizard:level:id:"))
async def select_existing_level(callback: CallbackQuery, state: FSMContext, gamification: GamificationContainer):
    """Procesa selección de nivel existente."""
    level_id = int(callback.data.split(":")[-1])

    level = await gamification.level.get_level_by_id(level_id)
    if not level:
        await callback.answer("❌ Nivel no encontrado", show_alert=True)
        return

    auto_level = {
        'level_id': level.id,
        'name': level.name,
        'order': level.order
    }
    await state.update_data(auto_level=auto_level)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Crear Recompensa", callback_data="wizard:reward:new")],
        [InlineKeyboardButton(text="🔍 Seleccionar Existente", callback_data="wizard:reward:select")],
        [InlineKeyboardButton(text="✅ Finalizar", callback_data="wizard:finish")]
    ])

    await callback.message.edit_text(
        f"✅ Nivel seleccionado: <b>{level.name}</b>\n\n"
        f"Paso 5/6: ¿Desbloqueará recompensas adicionales?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(MissionWizardStates.choose_rewards)
    await callback.answer()


# ========================================
# PASO 5: RECOMPENSAS
# ========================================

@router.callback_query(MissionWizardStates.choose_rewards, F.data == "wizard:reward:new")
async def choose_create_reward(callback: CallbackQuery, state: FSMContext):
    """Iniciar creación de recompensa."""
    await callback.message.edit_text(
        "➕ <b>Crear Recompensa</b>\n\n"
        "Escribe el nombre de la recompensa:\n\n"
        "Ejemplo: Badge Fanático",
        parse_mode="HTML"
    )
    await state.set_state(MissionWizardStates.enter_reward_name)
    await callback.answer()


@router.callback_query(MissionWizardStates.choose_rewards, F.data.startswith("wizard:reward:select"))
async def choose_select_existing_reward(callback: CallbackQuery, state: FSMContext, gamification: GamificationContainer):
    """Mostrar recompensas existentes para selección con paginación."""
    parts = callback.data.split(":")
    page = int(parts[3]) if len(parts) > 3 else 1

    rewards = await gamification.reward.get_all_rewards()

    if not rewards:
        await callback.answer("⚠️ No hay recompensas existentes. Crea una nueva.", show_alert=True)
        return

    start_index = (page - 1) * PAGE_SIZE
    end_index = start_index + PAGE_SIZE
    rewards_on_page = rewards[start_index:end_index]

    keyboard_rows = []
    for reward in rewards_on_page:
        keyboard_rows.append([
            InlineKeyboardButton(
                text=f"{reward.name}",
                callback_data=f"wizard:reward:id:{reward.id}"
            )
        ])

    # Paginación
    total_pages = (len(rewards) + PAGE_SIZE - 1) // PAGE_SIZE
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Anterior", callback_data=f"wizard:reward:select:page:{page-1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton(text="➡️ Siguiente", callback_data=f"wizard:reward:select:page:{page+1}"))

    if nav_buttons:
        keyboard_rows.append(nav_buttons)

    keyboard_rows.append([InlineKeyboardButton(text="🔙 Volver", callback_data="wizard:finish")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

    await callback.message.edit_text(
        f"🔍 <b>Seleccionar Recompensa Existente</b> (Página {page}/{total_pages})\n\n"
        "Elige una recompensa para desbloquear:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(MissionWizardStates.choose_rewards, F.data.startswith("wizard:reward:id:"))
async def select_existing_reward(callback: CallbackQuery, state: FSMContext, gamification: GamificationContainer):
    """Procesa selección de recompensa existente."""
    reward_id = int(callback.data.split(":")[-1])

    reward = await gamification.reward.get_reward_by_id(reward_id)
    if not reward:
        await callback.answer("❌ Recompensa no encontrada", show_alert=True)
        return

    data = await state.get_data()
    rewards = data.get('rewards', [])
    
    # Evitar duplicados
    if not any(r.get('reward_id') == reward.id for r in rewards):
        rewards.append({
            'mode': 'select',
            'reward_id': reward.id,
            'name': reward.name
        })
        await state.update_data(rewards=rewards)
        message_text = f"✅ Recompensa '{reward.name}' agregada."
    else:
        message_text = f"⚠️ Ya has agregado la recompensa '{reward.name}'."

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Crear Otra", callback_data="wizard:reward:new")],
        [InlineKeyboardButton(text="🔍 Seleccionar Otra", callback_data="wizard:reward:select:page:1")],
        [InlineKeyboardButton(text="✅ Finalizar", callback_data="wizard:finish")]
    ])

    await callback.message.edit_text(
        f"{message_text}\n\n"
        f"Total de recompensas: <b>{len(rewards)}</b>\n\n"
        f"¿Deseas agregar más recompensas?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(MissionWizardStates.choose_rewards)
    await callback.answer()




@router.message(MissionWizardStates.enter_reward_name)
async def enter_reward_name(message: Message, state: FSMContext):
    """Recibe nombre de recompensa."""
    if not message.text or len(message.text.strip()) < 3:
        await message.answer("❌ El nombre debe tener al menos 3 caracteres")
        return

    await state.update_data(reward_name=message.text.strip())

    await message.answer(
        f"✅ Recompensa: <b>{message.text}</b>\n\n"
        f"Ahora escribe la descripción de la recompensa:",
        parse_mode="HTML"
    )
    await state.set_state(MissionWizardStates.enter_reward_description)


@router.message(MissionWizardStates.enter_reward_description)
async def enter_reward_description(message: Message, state: FSMContext):
    """Recibe descripción de recompensa y la agrega a la lista."""
    if not message.text or len(message.text.strip()) < 5:
        await message.answer("❌ La descripción debe tener al menos 5 caracteres")
        return

    data = await state.get_data()

    # Agregar recompensa a la lista
    rewards = data.get('rewards', [])
    new_reward_data = {
        'name': data['reward_name'],
        'description': message.text.strip(),
        'reward_type': 'badge',  # Por defecto badge
        'metadata': {'icon': '🏆', 'rarity': 'epic'}
    }
    rewards.append({
        'mode': 'create',
        'data': new_reward_data
    })
    await state.update_data(rewards=rewards)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Crear Otra", callback_data="wizard:reward:new")],
        [InlineKeyboardButton(text="🔍 Seleccionar Otra", callback_data="wizard:reward:select")],
        [InlineKeyboardButton(text="✅ Finalizar", callback_data="wizard:finish")]
    ])

    await message.answer(
        f"✅ Recompensa '{data['reward_name']}' configurada para ser creada.\n\n"
        f"Total de recompensas: <b>{len(rewards)}</b>\n\n"
        f"¿Deseas agregar más recompensas?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(MissionWizardStates.choose_rewards)


# ========================================
# PASO 6: CONFIRMACIÓN
# ========================================

@router.callback_query(F.data == "wizard:finish")
async def finish_wizard(callback: CallbackQuery, state: FSMContext):
    """Muestra resumen y confirma."""
    data = await state.get_data()

    # Construir resumen
    summary = f"""📋 <b>RESUMEN DE CONFIGURACIÓN</b>

<b>Misión:</b> {data['mission_name']}
<b>Tipo:</b> {data['mission_type'].replace('_', ' ').title()}
<b>Descripción:</b> {data['mission_description']}
<b>Criterio:</b> {_format_criteria(data['criteria'])}
<b>Recompensa:</b> {data['besitos_reward']} besitos
"""

    if data.get('auto_level'):
        level_info = data['auto_level']
        if 'level_id' in level_info:
            summary += f"\n<b>Nivel auto:</b> {level_info['name']} (existente)"
        else:
            summary += f"\n<b>Nivel auto:</b> {level_info['name']} (nuevo, orden {level_info['order']})"

    if data.get('rewards'):
        summary += "\n\n<b>Recompensas a Desbloquear:</b>"
        for reward in data['rewards']:
            if reward['mode'] == 'create':
                summary += f"\n • {reward['data']['name']} (Nueva)"
            else: # mode == 'select'
                summary += f"\n • {reward['name']} (Existente)"

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
        # Preparar configuración
        config = {
            'mission': {
                'name': data['mission_name'],
                'description': data['mission_description'],
                'mission_type': data['mission_type'],
                'criteria': data['criteria'],
                'besitos_reward': data['besitos_reward']
            }
        }

        # Agregar nivel si existe
        if data.get('auto_level'):
            level_info = data['auto_level']
            if 'level_id' in level_info:
                # Nivel existente, usar referencia
                config['mission']['auto_level_id'] = level_info['level_id']
            else:
                # Nuevo nivel, pasar configuración
                config['auto_level'] = {
                    'name': level_info['name'],
                    'min_besitos': level_info['min_besitos'],
                    'order': level_info['order']
                }

        # Procesar recompensas
        if data.get('rewards'):
            rewards_to_create = [r['data'] for r in data['rewards'] if r['mode'] == 'create']
            reward_ids_to_link = [r['reward_id'] for r in data['rewards'] if r['mode'] == 'select']
            
            if rewards_to_create:
                config['rewards_to_create'] = rewards_to_create
            if reward_ids_to_link:
                config['reward_ids_to_link'] = reward_ids_to_link

        # Crear usando orchestrator
        result = await gamification.configuration_orchestrator.create_complete_mission_system(
            config=config,
            created_by=callback.from_user.id
        )

        if result.get('validation_errors'):
            error_msg = "❌ <b>Errores de validación:</b>\n\n" + "\n".join(
                f"• {err}" for err in result['validation_errors']
            )
            await callback.message.edit_text(error_msg, parse_mode="HTML")
        else:
            await callback.message.edit_text(
                result['summary'],
                parse_mode="HTML"
            )

        await state.clear()

    except Exception as e:
        await callback.message.edit_text(
            f"❌ <b>Error al crear misión:</b>\n\n{str(e)}",
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

def _format_criteria(criteria: dict) -> str:
    """Formatea criterios para mostrar en resumen."""
    criteria_type = criteria.get('type', '')

    if criteria_type == 'streak':
        return f"{criteria['days']} días consecutivos"
    elif criteria_type == 'daily':
        return f"{criteria['count']} reacciones diarias"
    elif criteria_type == 'weekly':
        return f"{criteria['count']} reacciones semanales"
    elif criteria_type == 'one_time':
        return f"{criteria['count']} reacciones totales"
    else:
        return str(criteria)
