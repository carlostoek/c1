"""
Handlers CRUD para configuración de misiones de gamificación.
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional, List
from math import ceil
import json
from datetime import datetime

from bot.gamification.services.container import GamificationContainer
from bot.gamification.database.enums import MissionType
from bot.gamification.utils.validators import validate_mission_criteria

router = Router()


class MissionConfigStates(StatesGroup):
    """Estados para configuración de misiones."""
    waiting_name = State()
    waiting_description = State()
    waiting_mission_type = State()
    waiting_criteria = State()
    waiting_besitos_reward = State()
    editing_field = State()
    editing_criteria = State()
    waiting_level_up = State()
    waiting_unlock_rewards = State()


# ========================================
# CONSTANTES Y AYUDANTES
# ========================================
PER_PAGE = 10

MISSION_TYPE_EMOJIS = {
    MissionType.STREAK: "🔥",
    MissionType.DAILY: "📅",
    MissionType.WEEKLY: "🗓️",
    MissionType.ONE_TIME: "⭐"
}

MISSION_TYPE_NAMES = {
    MissionType.STREAK: "Racha",
    MissionType.DAILY: "Diaria",
    MissionType.WEEKLY: "Semanal",
    MissionType.ONE_TIME: "Única"
}


def format_criteria_display(criteria: dict) -> str:
    """Formatea criterios para mostrar de forma legible."""
    try:
        criteria_data = criteria if isinstance(criteria, dict) else json.loads(criteria)
        mission_type = criteria_data.get('type', '').upper()
        
        if mission_type == 'STREAK':
            days = criteria_data.get('days', '?')
            consecutive = criteria_data.get('require_consecutive', True)
            cons_text = "consecutivos" if consecutive else "en total"
            return f"{days} días {cons_text}"
        
        elif mission_type == 'DAILY':
            count = criteria_data.get('count', '?')
            emoji = criteria_data.get('specific_reaction', 'cualquier reacción')
            return f"{count} reacciones con {emoji}"
        
        elif mission_type == 'WEEKLY':
            target = criteria_data.get('target', '?')
            days = criteria_data.get('specific_days')
            if days:
                day_names = {0: 'Dom', 1: 'Lun', 2: 'Mar', 3: 'Mié', 4: 'Jue', 5: 'Vie', 6: 'Sáb'}
                day_str = ', '.join([day_names.get(d, f'Día {d}') for d in days])
                return f"{target} reacciones en {day_str}"
            return f"{target} reacciones en la semana"
        
        elif mission_type == 'ONE_TIME':
            return "una vez"
        
        return str(criteria_data)
    except:
        return str(criteria)


def paginate_missions(missions: List, page: int, per_page: int = 10):
    """Helper para paginar lista de misiones."""
    total_pages = max(1, ceil(len(missions) / per_page))
    page = max(1, min(page, total_pages))
    
    start = (page - 1) * per_page
    end = start + per_page
    
    return {
        'items': missions[start:end],
        'page': page,
        'total_pages': total_pages,
        'has_next': page < total_pages,
        'has_prev': page > 1,
        'total_items': len(missions)
    }


# ========================================
# MENÚ PRINCIPAL DE MISIONES (Paginado)
# ========================================

@router.callback_query(F.data == "gamif:admin:missions")
async def missions_menu(callback: CallbackQuery, state: FSMContext):
    """Muestra lista de misiones configuradas con paginación."""
    await state.update_data(current_page=1, filter_type=None)
    await show_missions_page(callback, state, 1)


async def show_missions_page(callback: CallbackQuery, state: FSMContext, page: int, filter_type: str = None):
    """Muestra una página específica de misiones."""
    gamification = callback.bot['services']['gamification']
    
    # Obtener misiones
    all_missions = await gamification.mission.get_all_missions(active_only=True)
    
    if filter_type and filter_type != 'all':
        all_missions = [m for m in all_missions if m.mission_type == filter_type]
    
    # Paginar
    paginated = paginate_missions(all_missions, page, PER_PAGE)
    
    text = f"📋 <b>MISIONES CONFIGURADAS</b>\n━━━━━━━━━━━━━━━━\n\n"
    
    if not paginated['items']:
        text += "No hay misiones configuradas.\n\n"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Crear Primera Misión", callback_data="gamif:mission:create:start")],
            [InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:menu")]
        ])
    else:
        # Mostrar misiones en la página actual
        for i, mission in enumerate(paginated['items'], 1):
            status = "✅" if mission.active else "❌"
            emoji = MISSION_TYPE_EMOJIS.get(mission.mission_type, "❓")
            type_name = MISSION_TYPE_NAMES.get(mission.mission_type, mission.mission_type)
            criteria_text = format_criteria_display(mission.criteria)
            
            # Obtener estadísticas de completadas
            stats = await gamification.mission.get_mission_stats(mission.id)
            completed_count = stats.get('completed_count', 0)
            
            text += f"{status} {emoji} <b>{mission.name}</b>\n"
            text += f"   • {type_name}: {criteria_text}\n"
            text += f"   • Recompensa: {mission.besitos_reward:,} besitos"
            if mission.repeatable:
                text += " | Repetible"
            if completed_count > 0:
                text += f" | {completed_count} completadas"
            text += "\n\n"
        
        text += f"<i>Página {paginated['page']}/{paginated['total_pages']}</i>\n"
        
        # Botones de paginación
        keyboard_buttons = []
        
        # Botones de cada misión
        for mission in paginated['items']:
            emoji = MISSION_TYPE_EMOJIS.get(mission.mission_type, "❓")
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"{emoji} {mission.name}",
                    callback_data=f"gamif:mission:view:{mission.id}"
                ),
                InlineKeyboardButton(
                    text="✏️",
                    callback_data=f"gamif:mission:edit:{mission.id}"
                )
            ])
        
        # Botones de paginación
        pagination_row = []
        if paginated['has_prev']:
            pagination_row.append(InlineKeyboardButton(
                text="⬅️ Anterior",
                callback_data=f"gamif:missions:page:{paginated['page']-1}"
            ))
        
        pagination_row.append(InlineKeyboardButton(
            text=f"{paginated['page']}/{paginated['total_pages']}",
            callback_data=f"gamif:none"
        ))
        
        if paginated['has_next']:
            pagination_row.append(InlineKeyboardButton(
                text="Siguiente ➡️",
                callback_data=f"gamif:missions:page:{paginated['page']+1}"
            ))
        
        keyboard_buttons.append(pagination_row)
        
        # Botones de acción
        keyboard_buttons.extend([
            [InlineKeyboardButton(text="➕ Crear Misión", callback_data="gamif:mission:create:start")],
            [InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:menu")]
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:missions:page:"))
async def change_page(callback: CallbackQuery, state: FSMContext):
    """Cambia entre páginas de misiones."""
    page = int(callback.data.split(":")[-1])
    data = await state.get_data()
    filter_type = data.get('filter_type')
    await show_missions_page(callback, state, page, filter_type)


# ========================================
# CREAR NUEVA MISIÓN
# ========================================

@router.callback_query(F.data == "gamif:mission:create:start")
async def start_create_mission(callback: CallbackQuery, state: FSMContext):
    """Inicia proceso de crear misión."""
    await callback.message.edit_text(
        "➕ <b>Crear Nueva Misión</b>\n\n"
        "Envía el nombre de la nueva misión.\n\n"
        "Ejemplo: 'Racha de 7 días' o 'Reactúa 10 veces diarias'",
        parse_mode="HTML"
    )
    await state.set_state(MissionConfigStates.waiting_name)
    await callback.answer()


@router.message(MissionConfigStates.waiting_name)
async def receive_mission_name(message: Message, state: FSMContext):
    """Recibe nombre de la misión."""
    name = message.text.strip()
    
    if len(name) < 2:
        await message.answer("❌ El nombre debe tener al menos 2 caracteres. Intenta de nuevo:")
        return
    
    await state.update_data(name=name)
    
    await message.answer(
        f"✅ Nombre: <b>{name}</b>\n\n"
        f"Ahora envía la descripción de la misión.\n\n"
        f"Ejemplo: 'Reacciona al menos una vez durante 7 días consecutivos'",
        parse_mode="HTML"
    )
    await state.set_state(MissionConfigStates.waiting_description)


@router.message(MissionConfigStates.waiting_description)
async def receive_mission_description(message: Message, state: FSMContext):
    """Recibe descripción de la misión."""
    description = message.text.strip()
    
    if len(description) < 5:
        await message.answer("❌ La descripción debe tener al menos 5 caracteres. Intenta de nuevo:")
        return
    
    await state.update_data(description=description)
    
    # Mostrar opciones de tipo de misión
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔥 Racha (Streak)", callback_data="gamif:mission:type:streak"),
            InlineKeyboardButton(text="📅 Diaria (Daily)", callback_data="gamif:mission:type:daily")
        ],
        [
            InlineKeyboardButton(text="🗓️ Semanal (Weekly)", callback_data="gamif:mission:type:weekly"),
            InlineKeyboardButton(text="⭐ Única (One-time)", callback_data="gamif:mission:type:one_time")
        ]
    ])
    
    await message.answer(
        f"✅ Nombre: {state.current_state().data['name']}\n"
        f"✅ Descripción: {description}\n\n"
        f"Selecciona el tipo de misión:",
        reply_markup=keyboard
    )
    await state.set_state(MissionConfigStates.waiting_mission_type)


@router.callback_query(F.data.startswith("gamif:mission:type:"))
async def receive_mission_type(callback: CallbackQuery, state: FSMContext):
    """Recibe tipo de misión."""
    mission_type = callback.data.split(":")[-1]
    
    try:
        # Validar tipo de misión
        MissionType(mission_type)
    except ValueError:
        await callback.answer("❌ Tipo de misión no válido", show_alert=True)
        return
    
    await state.update_data(mission_type=mission_type)
    
    # Pedir criterios según tipo
    if mission_type == 'streak':
        await callback.message.edit_text(
            "🔥 <b>Misión Racha</b>\n\n"
            "Envía los criterios en formato JSON:\n\n"
            "<code>{\"type\": \"streak\", \"days\": 7, \"require_consecutive\": true}</code>\n\n"
            "O envía solo el número de días (ej: 7):",
            parse_mode="HTML"
        )
    elif mission_type == 'daily':
        await callback.message.edit_text(
            "📅 <b>Misión Diaria</b>\n\n"
            "Envía los criterios en formato JSON:\n\n"
            "<code>{\"type\": \"daily\", \"count\": 5, \"specific_reaction\": \"❤️\"}</code>\n\n"
            "O envía solo el número de reacciones (ej: 5):",
            parse_mode="HTML"
        )
    elif mission_type == 'weekly':
        await callback.message.edit_text(
            "🗓️ <b>Misión Semanal</b>\n\n"
            "Envía los criterios en formato JSON:\n\n"
            "<code>{\"type\": \"weekly\", \"target\": 25, \"specific_days\": [1, 3, 5]}</code>\n\n"
            "O envía solo el objetivo semanal (ej: 25):",
            parse_mode="HTML"
        )
    else:  # one_time
        await callback.message.edit_text(
            "⭐ <b>Misión Única</b>\n\n"
            "Envía los criterios en formato JSON:\n\n"
            "<code>{\"type\": \"one_time\"}</code>\n\n"
            "O envía 'ok' para confirmar:",
            parse_mode="HTML"
        )
    
    await state.set_state(MissionConfigStates.waiting_criteria)
    await callback.answer()


@router.message(MissionConfigStates.waiting_criteria)
async def receive_criteria(message: Message, state: FSMContext):
    """Recibe criterios de la misión."""
    criteria_input = message.text.strip()
    
    # Obtener tipo de misión
    data = await state.get_data()
    mission_type = data['mission_type']
    
    try:
        # Si es un número, construir criterios básicos
        if criteria_input.isdigit():
            if mission_type == 'streak':
                criteria = {
                    "type": mission_type,
                    "days": int(criteria_input),
                    "require_consecutive": True
                }
            elif mission_type == 'daily':
                criteria = {
                    "type": mission_type,
                    "count": int(criteria_input),
                    "specific_reaction": None
                }
            elif mission_type == 'weekly':
                criteria = {
                    "type": mission_type,
                    "target": int(criteria_input),
                    "specific_days": None
                }
            else:  # one_time
                criteria = {"type": mission_type}
        elif criteria_input.lower() in ['ok', 'ok.', 'sí', 'si']:
            criteria = {"type": mission_type}
        else:
            # Intentar parsear como JSON
            criteria = json.loads(criteria_input)
        
        # Validar con el validador existente
        is_valid, error = validate_mission_criteria(MissionType(mission_type), criteria)
        if not is_valid:
            await message.answer(f"❌ Criterios inválidos: {error}\n\nIntenta de nuevo:")
            return
        
        await state.update_data(criteria=criteria)
        
        await message.answer(
            f"✅ Criterios válidos para {mission_type}\n\n"
            f"Ahora envía la recompensa en besitos (número positivo):",
            parse_mode="HTML"
        )
        await state.set_state(MissionConfigStates.waiting_besitos_reward)
        
    except json.JSONDecodeError:
        await message.answer("❌ Formato JSON inválido. Envía criterios válidos:")
    except Exception as e:
        await message.answer(f"❌ Error en criterios: {str(e)}\n\nIntenta de nuevo:")


@router.message(MissionConfigStates.waiting_besitos_reward)
async def receive_besitos_reward(message: Message, state: FSMContext, gamification: GamificationContainer):
    """Recibe recompensa en besitos."""
    try:
        reward = int(message.text)
        if reward <= 0:
            raise ValueError("La recompensa debe ser positiva")
    except ValueError:
        await message.answer("❌ Debe ser un número entero positivo. Intenta de nuevo:")
        return
    
    await state.update_data(besitos_reward=reward)
    
    # Crear misión
    data = await state.get_data()
    
    try:
        mission = await gamification.mission.create_mission(
            name=data['name'],
            description=data['description'],
            mission_type=MissionType(data['mission_type']),
            criteria=data['criteria'],
            besitos_reward=data['besitos_reward'],
            created_by=message.from_user.id  # Usar ID del admin que crea
        )
        
        await message.answer(
            f"✅ <b>Misión Creada Exitosamente</b>\n\n"
            f"ID: {mission.id}\n"
            f"Nombre: {mission.name}\n"
            f"Tipo: {mission.mission_type}\n"
            f"Recompensa: {mission.besitos_reward:,} besitos\n\n"
            f"La misión está lista para que los usuarios la inicien.",
            parse_mode="HTML"
        )
        
        await state.clear()

        # Volver a la lista de misiones - need to redirect to callback-based navigation
        # Instead of calling show_missions_page with message, send a new message with navigation options
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Ver Misiones", callback_data="gamif:admin:missions")],
            [InlineKeyboardButton(text="🔙 Volver al Menú", callback_data="gamif:menu")]
        ])

        await message.answer(
            "✅ <b>Misión Creada Exitosamente</b>\n\n"
            "¿Qué deseas hacer ahora?",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        await message.answer(f"❌ Error al crear misión: {str(e)}")


# ========================================
# VER DETALLES DE MISIÓN
# ========================================

@router.callback_query(F.data.startswith("gamif:mission:view:"))
async def view_mission_details(callback: CallbackQuery, gamification: GamificationContainer):
    """Muestra detalles de una misión específica."""
    mission_id = int(callback.data.split(":")[-1])
    mission = await gamification.mission.get_mission_by_id(mission_id)
    
    if not mission:
        await callback.answer("❌ Misión no encontrada", show_alert=True)
        return
    
    status = "✅ Activa" if mission.active else "❌ Inactiva"
    emoji = MISSION_TYPE_EMOJIS.get(mission.mission_type, "❓")
    type_name = MISSION_TYPE_NAMES.get(mission.mission_type, mission.mission_type)
    
    # Obtener estadísticas
    stats = await gamification.mission.get_mission_stats(mission_id)
    
    # Formatear criterios
    try:
        criteria_data = json.loads(mission.criteria) if isinstance(mission.criteria, str) else mission.criteria
        criteria_display = format_criteria_display(criteria_data)
    except:
        criteria_display = str(mission.criteria)
    
    # Obtener información del nivel de auto-level-up
    level_up_info = "Ninguno"
    if mission.auto_level_up_id:
        auto_level = await gamification.level.get_level_by_id(mission.auto_level_up_id)
        if auto_level:
            level_up_info = f"{auto_level.name} (ID: {auto_level.id})"
        else:
            level_up_info = f"Nivel ID: {mission.auto_level_up_id} (no encontrado)"
    
    text = f"""📊 <b>MISIÓN: {mission.name}</b>
{emoji} Tipo: {type_name}
{status}

📝 <b>DESCRIPCIÓN</b>
{mission.description}

⚙️ <b>CONFIGURACIÓN</b>
• Criterio: {criteria_display}
• Recompensa: {mission.besitos_reward:,} besitos
• Nivel auto: {level_up_info}
• Repetible: {'✅ Sí' if mission.repeatable else '❌ No'}

📈 <b>ESTADÍSTICAS</b>
• Usuarios activos: {stats.get('active_users', 0):,}
• Completadas: {stats.get('completed_count', 0):,}
• Tasa completación: {stats.get('completion_rate', 0.0)}%
• Besitos distribuidos: {stats.get('total_distributed_besitos', 0):,}
"""
    
    # Prepare keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Editar", callback_data=f"gamif:mission:edit:{mission_id}"),
            InlineKeyboardButton(
                text="🔄 Activar/Desactivar",
                callback_data=f"gamif:mission:toggle:{mission_id}"
            )
        ],
        [
            InlineKeyboardButton(text="🗑️ Eliminar", callback_data=f"gamif:mission:delete:{mission_id}"),
            InlineKeyboardButton(text="📋 Duplicar", callback_data=f"gamif:mission:duplicate:{mission_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:admin:missions")
        ]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# ========================================
# EDITAR MISIÓN
# ========================================

@router.callback_query(F.data.startswith("gamif:mission:edit:"))
async def edit_mission_menu(callback: CallbackQuery, gamification: GamificationContainer):
    """Muestra menú de edición de misión."""
    mission_id = int(callback.data.split(":")[-1])
    mission = await gamification.mission.get_mission_by_id(mission_id)
    
    if not mission:
        await callback.answer("❌ Misión no encontrada", show_alert=True)
        return
    
    criteria_text = format_criteria_display(mission.criteria)
    
    text = f"""✏️ <b>Editar Misión: {mission.name}</b>

Selecciona qué campo deseas editar:

• <b>Nombre:</b> {mission.name}
• <b>Descripción:</b> {mission.description[:50]}...
• <b>Criterios:</b> {criteria_text}
• <b>Recompensa:</b> {mission.besitos_reward:,} besitos
• <b>Repetible:</b> {'Sí' if mission.repeatable else 'No'}
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📝 Nombre", callback_data=f"gamif:mission:edit_field:{mission_id}:name"),
            InlineKeyboardButton(text="📄 Descripción", callback_data=f"gamif:mission:edit_field:{mission_id}:description")
        ],
        [
            InlineKeyboardButton(text="⚙️ Criterios", callback_data=f"gamif:mission:edit_field:{mission_id}:criteria"),
            InlineKeyboardButton(text="💰 Recompensa", callback_data=f"gamif:mission:edit_field:{mission_id}:besitos_reward")
        ],
        [
            InlineKeyboardButton(text="🔄 Repetible", callback_data=f"gamif:mission:edit_field:{mission_id}:repeatable"),
            InlineKeyboardButton(text="🎯 Auto Level-Up", callback_data=f"gamif:mission:edit_field:{mission_id}:auto_level_up_id")
        ],
        [
            InlineKeyboardButton(text="🔄 Activar/Desactivar", callback_data=f"gamif:mission:toggle:{mission_id}"),
            InlineKeyboardButton(text="🗑️ Eliminar", callback_data=f"gamif:mission:delete:{mission_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Volver", callback_data=f"gamif:mission:view:{mission_id}")
        ]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:mission:edit_field:"))
async def start_edit_field(callback: CallbackQuery, state: FSMContext):
    """Inicia edición de campo específico."""
    parts = callback.data.split(":")
    mission_id = int(parts[3])
    field = parts[4]
    
    await state.update_data(editing_mission_id=mission_id, editing_field=field)
    
    field_names = {
        'name': 'nombre',
        'description': 'descripción', 
        'criteria': 'criterios (JSON)',
        'besitos_reward': 'recompensa en besitos',
        'repeatable': 'repetible (sí/no)',
        'auto_level_up_id': 'auto level-up ID'
    }
    
    if field == 'repeatable':
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Sí", callback_data="gamif:edit_repeatable:yes"),
                InlineKeyboardButton(text="❌ No", callback_data="gamif:edit_repeatable:no")
            ],
            [InlineKeyboardButton(text="❌ Cancelar", callback_data=f"gamif:mission:edit:{mission_id}")]
        ])
        
        await callback.message.edit_text(
            f"🔄 <b>Editar Repetible</b>\n\n"
            f"¿La misión debe ser repetible?",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    elif field == 'auto_level_up_id':
        # Obtener todos los niveles para elegir
        levels = await callback.bot['services']['gamification'].level.get_all_levels()
        keyboard_buttons = []
        
        # Opción de "ninguno"
        keyboard_buttons.append([
            InlineKeyboardButton(text="❌ Ninguno", callback_data="gamif:edit_level_up:0")
        ])
        
        for level in levels:
            keyboard_buttons.append([
                InlineKeyboardButton(text=f"🎯 {level.name}", callback_data=f"gamif:edit_level_up:{level.id}")
            ])
        
        keyboard_buttons.append([
            InlineKeyboardButton(text="❌ Cancelar", callback_data=f"gamif:mission:edit:{mission_id}")
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_text(
            f"🎯 <b>Editar Auto Level-Up</b>\n\n"
            f"Elige un nivel para subir automáticamente al completar la misión:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    await callback.message.edit_text(
        f"✏️ <b>Editar {field_names.get(field, field)}</b>\n\n"
        f"Envía el nuevo valor:",
        parse_mode="HTML"
    )
    await state.set_state(MissionConfigStates.editing_field)
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:edit_repeatable:"))
async def edit_repeatable_selection(callback: CallbackQuery, state: FSMContext, gamification: GamificationContainer):
    """Maneja selección de repetible."""
    parts = callback.data.split(":")
    value = parts[2] == 'yes'
    
    data = await state.get_data()
    mission_id = data['editing_mission_id']
    
    try:
        await gamification.mission.update_mission(mission_id, repeatable=value)
        
        await callback.answer(f"✅ Repetible actualizado a {'sí' if value else 'no'}", show_alert=True)
        
        # Volver al menú de edición
        await edit_mission_menu(callback, gamification)
        await state.clear()
    except Exception as e:
        await callback.answer(f"❌ Error al actualizar: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("gamif:edit_level_up:"))
async def edit_level_up_selection(callback: CallbackQuery, state: FSMContext, gamification: GamificationContainer):
    """Maneja selección de nivel de auto-level-up."""
    level_id_str = callback.data.split(":")[2]
    level_id = int(level_id_str) if level_id_str != '0' else None
    
    data = await state.get_data()
    mission_id = data['editing_mission_id']
    
    # Validar que el nivel exista si se especifica
    if level_id:
        level = await gamification.level.get_level_by_id(level_id)
        if not level:
            await callback.answer("❌ Nivel no encontrado", show_alert=True)
            return
    
    try:
        await gamification.mission.update_mission(mission_id, auto_level_up_id=level_id)
        
        level_name = "Ninguno" if level_id is None else level.name
        await callback.answer(f"✅ Auto level-up actualizado a: {level_name}", show_alert=True)
        
        # Volver al menú de edición
        await edit_mission_menu(callback, gamification)
        await state.clear()
    except Exception as e:
        await callback.answer(f"❌ Error al actualizar: {str(e)}", show_alert=True)


@router.message(MissionConfigStates.editing_field)
async def receive_edited_field(message: Message, state: FSMContext, gamification: GamificationContainer):
    """Recibe valor editado para campo específico."""
    data = await state.get_data()
    mission_id = data['editing_mission_id']
    field = data['editing_field']
    
    mission = await gamification.mission.get_mission_by_id(mission_id)
    if not mission:
        await message.answer("❌ Misión no encontrada")
        await state.clear()
        return
    
    update_data = {}
    
    try:
        if field == 'name':
            new_value = message.text.strip()
            if len(new_value) < 2:
                await message.answer("❌ El nombre debe tener al menos 2 caracteres. Intenta de nuevo:")
                return
            update_data[field] = new_value
        elif field == 'description':
            new_value = message.text.strip()
            if len(new_value) < 5:
                await message.answer("❌ La descripción debe tener al menos 5 caracteres. Intenta de nuevo:")
                return
            update_data[field] = new_value
        elif field == 'besitos_reward':
            new_value = int(message.text)
            if new_value <= 0:
                raise ValueError
            update_data[field] = new_value
        elif field == 'auto_level_up_id':
            new_value = int(message.text)
            if new_value <= 0:
                new_value = None
            else:
                # Validar que el nivel exista
                level = await gamification.level.get_level_by_id(new_value)
                if not level:
                    await message.answer("❌ ID de nivel no encontrado. Intenta de nuevo:")
                    return
            update_data[field] = new_value
        else:
            await message.answer("❌ Campo no válido para editar")
            await state.clear()
            return
        
        # Actualizar la misión
        await gamification.mission.update_mission(mission_id, **update_data)
        
        await message.answer(
            f"✅ <b>Misión Actualizada</b>\n\n"
            f"Campo: {field}\n"
            f"Nuevo valor: {update_data[field]}"
        )

        await state.clear()

        # Volver a detalles de la misión - send navigation options
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Ver Detalles", callback_data=f"gamif:mission:view:{mission_id}")],
            [InlineKeyboardButton(text="📋 Volver a Misiones", callback_data="gamif:admin:missions")]
        ])

        await message.answer(
            "¿Qué deseas hacer ahora?",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except ValueError:
        await message.answer("❌ Debe ser un número válido. Intenta de nuevo:")
    except Exception as e:
        await message.answer(f"❌ Error al actualizar: {str(e)}")


@router.callback_query(F.data.startswith("gamif:mission:edit_field:criteria"))
async def start_edit_criteria(callback: CallbackQuery, state: FSMContext):
    """Inicia edición de criterios (mostrar form especial según tipo)."""
    mission_id = int(callback.data.split(":")[3])
    
    await state.update_data(editing_mission_id=mission_id, editing_field='criteria')
    
    # Obtener la misión para saber el tipo
    gamification = callback.bot['services']['gamification']
    mission = await gamification.mission.get_mission_by_id(mission_id)
    
    if not mission:
        await callback.answer("❌ Misión no encontrada", show_alert=True)
        return
    
    # Mostrar instrucciones según tipo de misión
    if mission.mission_type == 'streak':
        await callback.message.edit_text(
            f"⚙️ <b>Editar Criterios de Misión Racha</b>\n\n"
            f"Envía los nuevos criterios en formato JSON:\n\n"
            f"<code>{{\"type\": \"streak\", \"days\": 7, \"require_consecutive\": true}}</code>\n\n"
            f"O solo el número de días (ej: 7):",
            parse_mode="HTML"
        )
    elif mission.mission_type == 'daily':
        await callback.message.edit_text(
            f"⚙️ <b>Editar Criterios de Misión Diaria</b>\n\n"
            f"Envía los nuevos criterios en formato JSON:\n\n"
            f"<code>{{\"type\": \"daily\", \"count\": 5, \"specific_reaction\": \"❤️\"}}</code>\n\n"
            f"O solo el número de reacciones (ej: 5):",
            parse_mode="HTML"
        )
    elif mission.mission_type == 'weekly':
        await callback.message.edit_text(
            f"⚙️ <b>Editar Criterios de Misión Semanal</b>\n\n"
            f"Envía los nuevos criterios en formato JSON:\n\n"
            f"<code>{{\"type\": \"weekly\", \"target\": 25, \"specific_days\": [1, 3, 5]}}</code>\n\n"
            f"O solo el objetivo (ej: 25):",
            parse_mode="HTML"
        )
    else:  # one_time
        await callback.message.edit_text(
            f"⭐ <b>Editar Criterios de Misión Única</b>\n\n"
            f"Envía los nuevos criterios en formato JSON:\n\n"
            f"<code>{{\"type\": \"one_time\"}}</code>\n\n"
            f"O envía 'ok' para confirmar:",
            parse_mode="HTML"
        )
    
    await state.set_state(MissionConfigStates.editing_criteria)
    await callback.answer()


@router.message(MissionConfigStates.editing_criteria)
async def receive_edited_criteria(message: Message, state: FSMContext, gamification: GamificationContainer):
    """Recibe criterios editados."""
    criteria_input = message.text.strip()
    data = await state.get_data()
    mission_id = data['editing_mission_id']
    
    mission = await gamification.mission.get_mission_by_id(mission_id)
    if not mission:
        await message.answer("❌ Misión no encontrada")
        await state.clear()
        return
    
    try:
        # Si es un número, construir criterios según tipo
        if criteria_input.isdigit():
            if mission.mission_type == 'streak':
                criteria = {
                    "type": mission.mission_type,
                    "days": int(criteria_input),
                    "require_consecutive": True
                }
            elif mission.mission_type == 'daily':
                criteria = {
                    "type": mission.mission_type,
                    "count": int(criteria_input),
                    "specific_reaction": None
                }
            elif mission.mission_type == 'weekly':
                criteria = {
                    "type": mission.mission_type,
                    "target": int(criteria_input),
                    "specific_days": None
                }
            else:  # one_time
                criteria = {"type": mission.mission_type}
        elif criteria_input.lower() in ['ok', 'ok.', 'sí', 'si']:
            criteria = {"type": mission.mission_type}
        else:
            # Intentar parsear como JSON
            criteria = json.loads(criteria_input)
        
        # Validar con el validador existente
        is_valid, error = validate_mission_criteria(MissionType(mission.mission_type), criteria)
        if not is_valid:
            await message.answer(f"❌ Criterios inválidos: {error}\n\nIntenta de nuevo:")
            return
        
        # Actualizar la misión
        await gamification.mission.update_mission(mission_id, criteria=criteria)
        
        await message.answer(
            f"✅ <b>Criterios Actualizados</b>\n\n"
            f"Tipo: {mission.mission_type}\n"
            f"Criterios: {format_criteria_display(criteria)}"
        )

        await state.clear()

        # Volver a detalles de la misión - send navigation options
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Ver Detalles", callback_data=f"gamif:mission:view:{mission_id}")],
            [InlineKeyboardButton(text="📋 Volver a Misiones", callback_data="gamif:admin:missions")]
        ])

        await message.answer(
            "¿Qué deseas hacer ahora?",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except json.JSONDecodeError:
        await message.answer("❌ Formato JSON inválido. Intenta de nuevo:")
    except Exception as e:
        await message.answer(f"❌ Error al actualizar criterios: {str(e)}")


# ========================================
# TOGGLE ACTIVAR/DESACTIVAR
# ========================================

@router.callback_query(F.data.startswith("gamif:mission:toggle:"))
async def toggle_mission(callback: CallbackQuery, gamification: GamificationContainer):
    """Activa o desactiva una misión."""
    mission_id = int(callback.data.split(":")[-1])
    
    mission = await gamification.mission.get_mission_by_id(mission_id)
    if not mission:
        await callback.answer("❌ Misión no encontrada", show_alert=True)
        return
    
    await gamification.mission.update_mission(mission_id, active=not mission.active)
    
    status_text = "activada" if not mission.active else "desactivada"
    await callback.answer(f"✅ Misión {status_text}", show_alert=True)
    
    # Refresh the view
    await view_mission_details(callback, gamification)


# ========================================
# DUPLICAR MISIÓN
# ========================================

@router.callback_query(F.data.startswith("gamif:mission:duplicate:"))
async def duplicate_mission(callback: CallbackQuery, gamification: GamificationContainer):
    """Duplica una misión existente."""
    mission_id = int(callback.data.split(":")[-1])
    
    original = await gamification.mission.get_mission_by_id(mission_id)
    if not original:
        await callback.answer("❌ Misión no encontrada", show_alert=True)
        return
    
    # Crear nombre duplicado
    duplicate_name = f"Copia de {original.name}"
    
    try:
        # Extraer criterios
        criteria = json.loads(original.criteria) if isinstance(original.criteria, str) else original.criteria
        
        # Crear nueva misión con los mismos datos
        new_mission = await gamification.mission.create_mission(
            name=duplicate_name,
            description=original.description,
            mission_type=MissionType(original.mission_type),
            criteria=criteria,
            besitos_reward=original.besitos_reward,
            auto_level_up_id=original.auto_level_up_id,
            unlock_rewards=json.loads(original.unlock_rewards) if original.unlock_rewards else None,
            repeatable=original.repeatable,
            created_by=callback.from_user.id
        )
        
        await callback.answer(f"✅ Misión duplicada como: {duplicate_name}", show_alert=True)
        
        # Mostrar detalles de la nueva misión
        await view_mission_details(callback, gamification)
        
    except Exception as e:
        await callback.answer(f"❌ Error al duplicar misión: {str(e)}", show_alert=True)


# ========================================
# ELIMINAR MISIÓN
# ========================================

@router.callback_query(F.data.startswith("gamif:mission:delete:"))
async def delete_mission_prompt(callback: CallbackQuery, gamification: GamificationContainer):
    """Pide confirmación para eliminar misión."""
    mission_id = int(callback.data.split(":")[-1])
    
    mission = await gamification.mission.get_mission_by_id(mission_id)
    if not mission:
        await callback.answer("❌ Misión no encontrada", show_alert=True)
        return
    
    # Check if mission has active users
    stats = await gamification.mission.get_mission_stats(mission_id)
    active_users = stats.get('active_users', 0)
    
    if active_users > 0:
        text = f"""⚠️ <b>Advertencia: Eliminación con Usuarios Activos</b>

Misión: <b>{mission.name}</b> (ID: {mission.id})
Usuarios afectados: <b>{active_users}</b>

⚠️ Esta misión tiene {active_users} usuarios con la misión en progreso.
Al eliminarla, se cancelarán todas las instancias activas.

¿Deseas continuar con la eliminación?

<b>Esta acción no se puede deshacer.</b>"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🗑️ Sí, Eliminar", callback_data=f"gamif:mission:delete_confirm:{mission_id}"),
                InlineKeyboardButton(text="❌ Cancelar", callback_data=f"gamif:mission:view:{mission_id}")
            ]
        ])
    else:
        text = f"""⚠️ <b>Confirmar Eliminación</b>

¿Estás seguro de eliminar la misión?

Nombre: <b>{mission.name}</b>
ID: {mission.id}
Tipo: {MISSION_TYPE_NAMES.get(mission.mission_type, mission.mission_type)}
Recompensa: {mission.besitos_reward:,} besitos

<b>Esta acción no se puede deshacer.</b>"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🗑️ Sí, Eliminar", callback_data=f"gamif:mission:delete_confirm:{mission_id}"),
                InlineKeyboardButton(text="❌ Cancelar", callback_data=f"gamif:mission:view:{mission_id}")
            ]
        ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:mission:delete_confirm:"))
async def confirm_delete_mission(callback: CallbackQuery, state: FSMContext, gamification: GamificationContainer):
    """Confirma eliminación de misión (soft delete)."""
    mission_id = int(callback.data.split(":")[-1])

    mission = await gamification.mission.get_mission_by_id(mission_id)
    if not mission:
        await callback.answer("❌ Misión no encontrada", show_alert=True)
        return

    # Since the service already does a soft-delete, we'll use that
    success = await gamification.mission.delete_mission(mission_id)

    if success:
        await callback.answer("✅ Misión eliminada", show_alert=True)
        # Go back to main missions menu
        await state.update_data(current_page=1)
        await show_missions_page(callback, state, 1)
    else:
        await callback.answer("❌ Error al eliminar misión", show_alert=True)