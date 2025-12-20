"""
Wizard de creación de misiones paso a paso.
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot.middlewares import AdminAuthMiddleware, DatabaseMiddleware
from bot.gamification.states.admin import MissionWizardStates
from bot.gamification.services.container import GamificationContainer
from bot.gamification.database.enums import MissionType, RewardType
from sqlalchemy.ext.asyncio import AsyncSession

router = Router(name="mission_wizard")

# Aplicar middlewares (orden correcto: Database primero, AdminAuth después)
router.message.middleware(DatabaseMiddleware())
router.message.middleware(AdminAuthMiddleware())
router.callback_query.middleware(DatabaseMiddleware())
router.callback_query.middleware(AdminAuthMiddleware())


# ========================================
# INICIAR WIZARD
# ========================================

@router.callback_query(F.data == "gamif:wizard:mission")
async def start_mission_wizard(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
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
async def select_mission_type(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
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
        f"Paso 2/7: Escribe la descripción:",
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
            "Paso 3/7: ¿Cuántos días consecutivos se requieren?",
            parse_mode="HTML"
        )
        await state.set_state(MissionWizardStates.enter_streak_days)

    elif mission_type == MissionType.DAILY:
        await message.answer(
            "✅ Descripción guardada\n\n"
            "Paso 3/7: ¿Cuántas reacciones diarias se requieren?",
            parse_mode="HTML"
        )
        await state.set_state(MissionWizardStates.enter_daily_count)

    elif mission_type == MissionType.WEEKLY:
        await message.answer(
            "✅ Descripción guardada\n\n"
            "Paso 3/7: ¿Cuál es el objetivo semanal (cantidad)?",
            parse_mode="HTML"
        )
        await state.set_state(MissionWizardStates.enter_weekly_target)

    else:  # ONE_TIME
        await message.answer(
            "✅ Descripción guardada\n\n"
            "Paso 3/7: ¿Requiere una reacción específica? (escribe emoji o 'no')",
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
        f"✅ Criterio: {days} días consecutivos\n\n"
        f"Paso 3/6: ¿Cuántos besitos otorgará?",
        parse_mode="HTML"
    )
    await state.set_state(MissionWizardStates.enter_besitos_reward)


@router.message(MissionWizardStates.enter_daily_count)
async def enter_daily_count(message: Message, state: FSMContext):
    """Procesa cantidad de reacciones diarias."""
    try:
        count = int(message.text)
        if count <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número positivo")
        return
    
    await state.update_data(criteria={'type': 'daily', 'count': count, 'specific_reaction': None})
    
    await message.answer(
        f"✅ Criterio: {count} reacciones diarias\n\n"
        f"Paso 3/6: ¿Cuántos besitos otorgará?",
        parse_mode="HTML"
    )
    await state.set_state(MissionWizardStates.enter_besitos_reward)


@router.message(MissionWizardStates.enter_weekly_target)
async def enter_weekly_target(message: Message, state: FSMContext):
    """Procesa objetivo semanal."""
    try:
        target = int(message.text)
        if target <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número positivo")
        return
    
    await state.update_data(criteria={'type': 'weekly', 'target': target, 'specific_days': None})
    
    await message.answer(
        f"✅ Criterio: {target} objetivos semanales\n\n"
        f"Paso 3/6: ¿Cuántos besitos otorgará?",
        parse_mode="HTML"
    )
    await state.set_state(MissionWizardStates.enter_besitos_reward)


@router.message(MissionWizardStates.enter_specific_reaction)
async def enter_specific_reaction(message: Message, state: FSMContext):
    """Procesa reacción específica para one-time."""
    reaction = message.text.strip()
    
    # Si no es 'no', usar la reacción
    if reaction.lower() != 'no':
        # Validar que es un emoji válido (básico)
        reaction = reaction.strip()
    
    await state.update_data(criteria={'type': 'one_time', 'specific_reaction': reaction if reaction.lower() != 'no' else None})
    
    await message.answer(
        f"✅ Criterio: Reacción {'específica' if reaction.lower() != 'no' else 'cualquiera'}\n\n"
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
async def skip_auto_level(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
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


@router.callback_query(MissionWizardStates.choose_auto_level, F.data == "wizard:level:new")
async def create_new_level(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Empezar creación de nuevo nivel."""
    await callback.message.edit_text(
        "➕ <b>Crear Nivel Nuevo</b>\n\n"
        "Escribe el nombre del nivel:",
        parse_mode="HTML"
    )
    await state.set_state(MissionWizardStates.enter_level_name)
    await callback.answer()


@router.message(MissionWizardStates.enter_level_name)
async def enter_level_name(message: Message, state: FSMContext):
    """Recibe nombre de nivel."""
    await state.update_data(level_name=message.text)
    
    await message.answer(
        f"✅ Nombre: {message.text}\n\n"
        "¿Cuántos besitos se necesitan para este nivel?",
        parse_mode="HTML"
    )
    await state.set_state(MissionWizardStates.enter_level_besitos)


@router.message(MissionWizardStates.enter_level_besitos)
async def enter_level_besitos(message: Message, state: FSMContext):
    """Recibe besitos requeridos para el nivel."""
    try:
        besitos = int(message.text)
        if besitos <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número positivo")
        return
    
    await state.update_data(level_besitos=besitos)
    
    await message.answer(
        "¿Cuál es el orden/posición del nivel? (número)",
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
    
    # Guardar configuración de auto level
    level_data = {
        'name': (await state.get_data())['level_name'],
        'min_besitos': (await state.get_data())['level_besitos'],
        'order': order
    }
    await state.update_data(auto_level=level_data)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Crear Recompensa", callback_data="wizard:reward:new")],
        [InlineKeyboardButton(text="✅ Finalizar", callback_data="wizard:finish")]
    ])
    
    await message.answer(
        f"✅ Nivel: {level_data['name']} (orden {order}, {level_data['min_besitos']} besitos)\n\n"
        f"Paso 5/6: ¿Desbloqueará recompensas?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(MissionWizardStates.choose_rewards)


# ========================================
# PASO 5: RECOMPENSAS
# ========================================

@router.callback_query(MissionWizardStates.choose_rewards, F.data == "wizard:reward:new")
async def create_new_reward(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Empezar creación de nueva recompensa."""
    await callback.message.edit_text(
        "➕ <b>Crear Recompensa</b>\n\n"
        "Escribe el nombre de la recompensa:",
        parse_mode="HTML"
    )
    await state.set_state(MissionWizardStates.enter_reward_name)
    await callback.answer()


@router.message(MissionWizardStates.enter_reward_name)
async def enter_reward_name(message: Message, state: FSMContext):
    """Recibe nombre de recompensa."""
    await state.update_data(reward_name=message.text)
    
    await message.answer(
        f"✅ Nombre: {message.text}\n\n"
        "Escribe la descripción de la recompensa:",
        parse_mode="HTML"
    )
    await state.set_state(MissionWizardStates.enter_reward_description)


@router.message(MissionWizardStates.enter_reward_description)
async def enter_reward_description(message: Message, state: FSMContext):
    """Recibe descripción y pide tipo de recompensa."""
    await state.update_data(reward_description=message.text)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 Badge", callback_data="reward:type:badge")],
        [InlineKeyboardButton(text="🔑 Permiso", callback_data="reward:type:permission")],
        [InlineKeyboardButton(text="💎 Besitos", callback_data="reward:type:besitos")],
        [InlineKeyboardButton(text="🏷️ Título", callback_data="reward:type:title")]
    ])
    
    await message.answer(
        "✅ Descripción guardada\n\n"
        "Selecciona el tipo de recompensa:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(MissionWizardStates.choose_rewards)


@router.callback_query(F.data.startswith("reward:type:"))
async def select_reward_type(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Procesa selección de tipo de recompensa."""
    reward_type_str = callback.data.split(":")[-1]
    reward_type = RewardType(reward_type_str)

    # Obtener datos acumulados
    data = await state.get_data()
    reward_data = {
        'name': data['reward_name'],
        'description': data['reward_description'],
        'reward_type': reward_type_str,
        'metadata': {}
    }

    # Guardar recompensa actual
    existing_rewards = data.get('rewards', [])
    existing_rewards.append(reward_data)
    await state.update_data(rewards=existing_rewards)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Crear Otra", callback_data="wizard:reward:new")],
        [InlineKeyboardButton(text="✅ Finalizar", callback_data="wizard:finish")]
    ])

    await callback.message.edit_text(
        f"✅ Recompensa: {data['reward_name']} ({reward_type_str})\n\n"
        f"Paso 6/7: ¿Crear otra recompensa o finalizar?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(MissionWizardStates.choose_rewards)
    await callback.answer()


# ========================================
# PASO 6: CONFIRMACIÓN
# ========================================

@router.callback_query(F.data == "wizard:finish")
async def finish_wizard(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
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
        level = data['auto_level']
        summary += f"\n<b>Nivel auto:</b> {level['name']} (orden {level['order']}, {level['min_besitos']} besitos)"
    
    if data.get('rewards'):
        summary += f"\n<b>Recompensas:</b> {len(data['rewards'])} recompensas"
    
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
async def confirm_mission(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Crea misión usando orchestrator."""
    data = await state.get_data()
    gamification = GamificationContainer(session)
    
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
async def cancel_wizard(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Cancela wizard."""
    await state.clear()
    await callback.message.edit_text("❌ Wizard cancelado", parse_mode="HTML")
    await callback.answer()