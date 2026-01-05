"""
Handlers CRUD para configuración de misiones.

Responsabilidades:
- Lista paginada de misiones (10 por página)
- Vista detallada con estadísticas
- Edición de campos individuales
- Edición de criterios dinámicos (JSON)
- Activar/desactivar misiones
- Eliminar con validaciones
"""

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
import json
import math
import logging

from bot.filters.admin import IsAdmin
from bot.middlewares import DatabaseMiddleware
from bot.gamification.states.admin import MissionConfigStates
from bot.gamification.services.container import GamificationContainer
from bot.gamification.database.enums import MissionType
from bot.utils.lucien_messages import Lucien

logger = logging.getLogger(__name__)

PAGE_SIZE = 10

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

# Registrar middleware
router.message.middleware(DatabaseMiddleware())
router.callback_query.middleware(DatabaseMiddleware())


# ========================================
# LISTA PAGINADA
# ========================================

@router.callback_query(F.data == "gamif:missions:list")
@router.callback_query(F.data == "gamif:admin:missions_list")
async def missions_menu(callback: CallbackQuery, gamification: GamificationContainer):
    """Muestra lista de misiones con paginación."""
    await show_missions_page(callback, gamification, page=1)
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:missions:page:"))
async def missions_page_handler(callback: CallbackQuery, gamification: GamificationContainer):
    """Maneja cambio de página."""
    page = int(callback.data.split(":")[-1])
    await show_missions_page(callback, gamification, page)
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:missions:filter:"))
async def filter_missions_by_type(callback: CallbackQuery, gamification: GamificationContainer):
    """Filtra misiones por tipo."""
    mission_type = callback.data.split(":")[-1]
    await show_missions_filtered(callback, gamification, mission_type, page=1)
    await callback.answer()


async def show_missions_page(
    callback: CallbackQuery,
    gamification: GamificationContainer,
    page: int = 1
):
    """Muestra página de misiones.

    Args:
        callback: CallbackQuery
        gamification: GamificationContainer
        page: Número de página (1-indexed)
    """
    missions = await gamification.mission.get_all_missions(active_only=False)

    if not missions:
        text = "📋 <b>MISIONES CONFIGURADAS</b>\n━━━━━━━━━━━━━━━━\n\n"
        text += "No hay misiones configuradas.\n\n"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Crear Misión", callback_data="gamif:wizard:mission")],
            [InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:menu")]
        ])

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        return

    # Calcular paginación
    total_pages = math.ceil(len(missions) / PAGE_SIZE)
    page = max(1, min(page, total_pages))  # Clamp

    start_idx = (page - 1) * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    page_missions = missions[start_idx:end_idx]

    # Construir mensaje
    text = f"📋 <b>MISIONES CONFIGURADAS</b>\n━━━━━━━━━━━━━━━━\n\n"
    text += f"Página {page}/{total_pages}\n\n"

    # Emojis por tipo
    type_emojis = {
        MissionType.ONE_TIME.value: "🎯",
        MissionType.DAILY.value: "📅",
        MissionType.WEEKLY.value: "📆",
        MissionType.STREAK.value: "🔥"
    }

    keyboard_buttons = []

    for idx, mission in enumerate(page_missions, start=start_idx + 1):
        status = "✅" if mission.active else "❌"
        type_emoji = type_emojis.get(mission.mission_type, "📋")
        repeatable = " • Repetible" if mission.repeatable else ""

        text += f"{idx}. {status} {type_emoji} <b>{mission.name}</b>\n"
        text += f"   → {mission.besitos_reward} besitos{repeatable}\n\n"

        # Botón de la misión
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{type_emoji} {mission.name}",
                callback_data=f"gamif:mission:view:{mission.id}"
            )
        ])

    text += f"\n<i>Total: {len(missions)} misión(es)</i>"

    # Botones de paginación
    pagination_row = []
    if page > 1:
        pagination_row.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"gamif:missions:page:{page - 1}")
        )

    pagination_row.append(
        InlineKeyboardButton(text=f"Página {page}/{total_pages}", callback_data="noop")
    )

    if page < total_pages:
        pagination_row.append(
            InlineKeyboardButton(text="➡️", callback_data=f"gamif:missions:page:{page + 1}")
        )

    if pagination_row:
        keyboard_buttons.append(pagination_row)

    # Botones de filtro
    filter_row = [
        InlineKeyboardButton(text="🎯 Una Vez", callback_data="gamif:missions:filter:one_time"),
        InlineKeyboardButton(text="📅 Diaria", callback_data="gamif:missions:filter:daily")
    ]
    keyboard_buttons.append(filter_row)

    filter_row_2 = [
        InlineKeyboardButton(text="📆 Semanal", callback_data="gamif:missions:filter:weekly"),
        InlineKeyboardButton(text="🔥 Racha", callback_data="gamif:missions:filter:streak")
    ]
    keyboard_buttons.append(filter_row_2)

    keyboard_buttons.append([
        InlineKeyboardButton(text="🔄 Todas", callback_data="gamif:missions:list")
    ])

    # Botones de acción
    keyboard_buttons.append([
        InlineKeyboardButton(text="➕ Crear Misión", callback_data="gamif:wizard:mission")
    ])

    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:menu")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


async def show_missions_filtered(
    callback: CallbackQuery,
    gamification: GamificationContainer,
    mission_type: str,
    page: int = 1
):
    """Muestra misiones filtradas por tipo."""
    all_missions = await gamification.mission.get_all_missions(active_only=False)
    missions = [m for m in all_missions if m.mission_type == mission_type]

    if not missions:
        await callback.answer(f"No hay misiones de tipo {mission_type}", show_alert=True)
        return

    # Similar a show_missions_page pero con misiones filtradas
    total_pages = math.ceil(len(missions) / PAGE_SIZE)
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    page_missions = missions[start_idx:end_idx]

    type_emojis = {
        "one_time": "🎯 Una Vez",
        "daily": "📅 Diaria",
        "weekly": "📆 Semanal",
        "streak": "🔥 Racha"
    }

    text = f"📋 <b>MISIONES: {type_emojis.get(mission_type, mission_type.upper())}</b>\n━━━━━━━━━━━━━━━━\n\n"
    text += f"Página {page}/{total_pages}\n\n"

    keyboard_buttons = []

    for idx, mission in enumerate(page_missions, start=start_idx + 1):
        status = "✅" if mission.active else "❌"
        repeatable = " • Repetible" if mission.repeatable else ""

        text += f"{idx}. {status} <b>{mission.name}</b>\n"
        text += f"   → {mission.besitos_reward} besitos{repeatable}\n\n"

        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{mission.name}",
                callback_data=f"gamif:mission:view:{mission.id}"
            )
        ])

    text += f"\n<i>Total: {len(missions)} misión(es)</i>"

    # Paginación
    pagination_row = []
    if page > 1:
        pagination_row.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"gamif:missions:filter:{mission_type}:page:{page - 1}")
        )

    pagination_row.append(
        InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop")
    )

    if page < total_pages:
        pagination_row.append(
            InlineKeyboardButton(text="➡️", callback_data=f"gamif:missions:filter:{mission_type}:page:{page + 1}")
        )

    if pagination_row:
        keyboard_buttons.append(pagination_row)

    keyboard_buttons.append([
        InlineKeyboardButton(text="🔄 Ver Todas", callback_data="gamif:missions:list")
    ])

    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:missions:list")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


# ========================================
# VISTA DETALLADA
# ========================================

@router.callback_query(F.data.startswith("gamif:mission:view:"))
async def view_mission(callback: CallbackQuery, gamification: GamificationContainer):
    """Muestra detalles de misión con estadísticas."""
    mission_id = int(callback.data.split(":")[-1])
    mission = await gamification.mission.get_mission_by_id(mission_id)

    if not mission:
        await callback.answer("❌ Misión no encontrada", show_alert=True)
        return

    # Obtener estadísticas
    stats = await gamification.mission.get_mission_stats(mission_id)

    # Parsear criterios
    criteria = json.loads(mission.criteria)
    criteria_text = _format_criteria(mission.mission_type, criteria)

    # Status
    status = "✅ Activa" if mission.active else "❌ Inactiva"
    repeatable = "✅ Sí" if mission.repeatable else "❌ No"

    # Tipo
    type_names = {
        MissionType.ONE_TIME.value: "🎯 Una Vez",
        MissionType.DAILY.value: "📅 Diaria",
        MissionType.WEEKLY.value: "📆 Semanal",
        MissionType.STREAK.value: "🔥 Racha"
    }
    type_name = type_names.get(mission.mission_type, mission.mission_type)

    text = f"""📊 <b>MISIÓN: {mission.name}</b>
━━━━━━━━━━━━━━━━

{type_name}
📝 {mission.description}

⚙️ <b>CONFIGURACIÓN</b>
• Criterio: {criteria_text}
• Recompensa: {mission.besitos_reward} besitos
• Repetible: {repeatable}
• Estado: {status}

📈 <b>ESTADÍSTICAS</b>
• En progreso: {stats['in_progress']} usuarios
• Completadas: {stats['completed']} veces
• Reclamadas: {stats['claimed']} veces
• Tasa completación: {stats['completion_rate']}%
• Besitos distribuidos: {stats['total_besitos']:,}
• Total usuarios: {stats['total_users']}
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Editar", callback_data=f"gamif:mission:edit:{mission_id}"),
            InlineKeyboardButton(
                text="🔄 Desactivar" if mission.active else "✅ Activar",
                callback_data=f"gamif:mission:toggle:{mission_id}"
            )
        ],
        [
            InlineKeyboardButton(text="🗑️ Eliminar", callback_data=f"gamif:mission:delete:{mission_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Volver a Lista", callback_data="gamif:missions:list")
        ]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


def _format_criteria(mission_type: str, criteria: dict) -> str:
    """Formatea criterios de misión para mostrar."""
    if mission_type == MissionType.STREAK.value:
        days = criteria.get('days', 7)
        consecutive = criteria.get('require_consecutive', True)
        cons_text = "consecutivos" if consecutive else "totales"
        return f"{days} días {cons_text}"

    elif mission_type == MissionType.DAILY.value:
        count = criteria.get('count', 5)
        specific = criteria.get('specific_reaction')
        if specific:
            return f"{count} reacciones con {specific}"
        return f"{count} reacciones"

    elif mission_type == MissionType.WEEKLY.value:
        target = criteria.get('target', 50)
        specific_days = criteria.get('specific_days')
        if specific_days:
            return f"{target} reacciones en días específicos"
        return f"{target} reacciones semanales"

    elif mission_type == MissionType.ONE_TIME.value:
        return "Completar una vez"

    return str(criteria)


# ========================================
# EDICIÓN
# ========================================

@router.callback_query(F.data.startswith("gamif:mission:edit:"))
async def edit_mission_menu(callback: CallbackQuery, gamification: GamificationContainer):
    """Muestra menú de edición."""
    mission_id = int(callback.data.split(":")[-1])
    mission = await gamification.mission.get_mission_by_id(mission_id)

    if not mission:
        await callback.answer("❌ Misión no encontrada", show_alert=True)
        return

    text = f"✏️ <b>EDITAR: {mission.name}</b>\n\n"
    text += "Selecciona el campo a editar:"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📝 Nombre", callback_data=f"gamif:mission:edit_field:{mission_id}:name"),
            InlineKeyboardButton(text="📄 Descripción", callback_data=f"gamif:mission:edit_field:{mission_id}:description")
        ],
        [
            InlineKeyboardButton(text="💰 Besitos", callback_data=f"gamif:mission:edit_field:{mission_id}:besitos"),
            InlineKeyboardButton(text="⚙️ Criterios", callback_data=f"gamif:mission:edit_criteria:{mission_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Volver", callback_data=f"gamif:mission:view:{mission_id}")
        ]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:mission:edit_field:"))
async def start_edit_field(callback: CallbackQuery, state: FSMContext):
    """Inicia edición de campo."""
    parts = callback.data.split(":")
    mission_id = int(parts[3])
    field = parts[4]

    await state.update_data(mission_id=mission_id, field=field)

    field_names = {
        "name": ("📝 Nombre", MissionConfigStates.waiting_for_name),
        "description": ("📄 Descripción", MissionConfigStates.waiting_for_description),
        "besitos": ("💰 Besitos", MissionConfigStates.waiting_for_besitos)
    }

    field_name, state_to_set = field_names[field]

    text = f"✏️ <b>EDITAR {field_name.upper()}</b>\n\n"
    text += f"Envía el nuevo valor para este campo:"

    await callback.message.edit_text(text, parse_mode="HTML")
    await state.set_state(state_to_set)
    await callback.answer()


@router.message(MissionConfigStates.waiting_for_name)
async def process_edit_name(message: Message, state: FSMContext, gamification: GamificationContainer):
    """Procesa edición de nombre."""
    data = await state.get_data()
    mission_id = data['mission_id']

    new_name = message.text.strip()

    if len(new_name) < 3:
        await message.answer("❌ El nombre debe tener al menos 3 caracteres.")
        return

    try:
        mission = await gamification.mission.update_mission(mission_id, name=new_name)
        await message.answer(
            f"✅ Nombre actualizado\n\n"
            f"<b>{mission.name}</b>",
            parse_mode="HTML"
        )
        await state.clear()
    except Exception as e:
        logger.error(f"Error updating mission name: {e}")
        await message.answer("❌ Error al actualizar nombre")
        await state.clear()


@router.message(MissionConfigStates.waiting_for_description)
async def process_edit_description(message: Message, state: FSMContext, gamification: GamificationContainer):
    """Procesa edición de descripción."""
    data = await state.get_data()
    mission_id = data['mission_id']

    new_description = message.text.strip()

    if len(new_description) < 5:
        await message.answer("❌ La descripción debe tener al menos 5 caracteres.")
        return

    try:
        await gamification.mission.update_mission(mission_id, description=new_description)
        await message.answer("✅ Descripción actualizada")
        await state.clear()
    except Exception as e:
        logger.error(f"Error updating mission description: {e}")
        await message.answer("❌ Error al actualizar descripción")
        await state.clear()


@router.message(MissionConfigStates.waiting_for_besitos)
async def process_edit_besitos(message: Message, state: FSMContext, gamification: GamificationContainer):
    """Procesa edición de besitos."""
    data = await state.get_data()
    mission_id = data['mission_id']

    try:
        besitos = int(message.text)
        if besitos <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número positivo.")
        return

    try:
        mission = await gamification.mission.update_mission(mission_id, besitos_reward=besitos)
        await message.answer(
            f"✅ Recompensa actualizada\n\n"
            f"<b>{mission.name}</b>: {mission.besitos_reward} besitos",
            parse_mode="HTML"
        )
        await state.clear()
    except Exception as e:
        logger.error(f"Error updating mission besitos: {e}")
        await message.answer("❌ Error al actualizar recompensa")
        await state.clear()


# ========================================
# EDICIÓN DE CRITERIOS
# ========================================

@router.callback_query(F.data.startswith("gamif:mission:edit_criteria:"))
async def edit_criteria_menu(callback: CallbackQuery, state: FSMContext, gamification: GamificationContainer):
    """Muestra menú de edición de criterios."""
    mission_id = int(callback.data.split(":")[-1])
    mission = await gamification.mission.get_mission_by_id(mission_id)

    if not mission:
        await callback.answer("❌ Misión no encontrada", show_alert=True)
        return

    await state.update_data(mission_id=mission_id, mission_type=mission.mission_type)

    criteria = json.loads(mission.criteria)
    criteria_text = _format_criteria(mission.mission_type, criteria)

    text = f"⚙️ <b>EDITAR CRITERIOS</b>\n\n"
    text += f"Misión: <b>{mission.name}</b>\n"
    text += f"Tipo: {mission.mission_type}\n"
    text += f"Criterio actual: {criteria_text}\n\n"
    text += "Selecciona qué deseas editar:"

    keyboard_buttons = []

    if mission.mission_type == MissionType.STREAK.value:
        keyboard_buttons.append([
            InlineKeyboardButton(text="📅 Días de racha", callback_data=f"gamif:criteria:streak_days:{mission_id}")
        ])
    elif mission.mission_type == MissionType.DAILY.value:
        keyboard_buttons.append([
            InlineKeyboardButton(text="🔢 Cantidad diaria", callback_data=f"gamif:criteria:daily_count:{mission_id}")
        ])
    elif mission.mission_type == MissionType.WEEKLY.value:
        keyboard_buttons.append([
            InlineKeyboardButton(text="🎯 Meta semanal", callback_data=f"gamif:criteria:weekly_target:{mission_id}")
        ])

    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Volver", callback_data=f"gamif:mission:edit:{mission_id}")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:criteria:streak_days:"))
async def edit_streak_days(callback: CallbackQuery, state: FSMContext):
    """Edita días de racha."""
    mission_id = int(callback.data.split(":")[-1])
    await state.update_data(mission_id=mission_id)

    text = "📅 <b>EDITAR DÍAS DE RACHA</b>\n\n"
    text += "Envía el número de días requeridos (ej: 7):"

    await callback.message.edit_text(text, parse_mode="HTML")
    await state.set_state(MissionConfigStates.waiting_for_streak_days)
    await callback.answer()


@router.message(MissionConfigStates.waiting_for_streak_days)
async def process_streak_days(message: Message, state: FSMContext, gamification: GamificationContainer):
    """Procesa días de racha."""
    data = await state.get_data()
    mission_id = data['mission_id']

    try:
        days = int(message.text)
        if days <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número positivo.")
        return

    mission = await gamification.mission.get_mission_by_id(mission_id)
    criteria = json.loads(mission.criteria)
    criteria['days'] = days

    try:
        await gamification.mission.update_mission(mission_id, criteria=criteria)
        await message.answer(f"✅ Criterio actualizado: {days} días de racha")
        await state.clear()
    except Exception as e:
        logger.error(f"Error updating criteria: {e}")
        await message.answer("❌ Error al actualizar criterio")
        await state.clear()


@router.callback_query(F.data.startswith("gamif:criteria:daily_count:"))
async def edit_daily_count(callback: CallbackQuery, state: FSMContext):
    """Edita cantidad diaria."""
    mission_id = int(callback.data.split(":")[-1])
    await state.update_data(mission_id=mission_id)

    text = "🔢 <b>EDITAR CANTIDAD DIARIA</b>\n\n"
    text += "Envía el número de reacciones diarias requeridas (ej: 5):"

    await callback.message.edit_text(text, parse_mode="HTML")
    await state.set_state(MissionConfigStates.waiting_for_daily_count)
    await callback.answer()


@router.message(MissionConfigStates.waiting_for_daily_count)
async def process_daily_count(message: Message, state: FSMContext, gamification: GamificationContainer):
    """Procesa cantidad diaria."""
    data = await state.get_data()
    mission_id = data['mission_id']

    try:
        count = int(message.text)
        if count <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número positivo.")
        return

    mission = await gamification.mission.get_mission_by_id(mission_id)
    criteria = json.loads(mission.criteria)
    criteria['count'] = count

    try:
        await gamification.mission.update_mission(mission_id, criteria=criteria)
        await message.answer(f"✅ Criterio actualizado: {count} reacciones diarias")
        await state.clear()
    except Exception as e:
        logger.error(f"Error updating criteria: {e}")
        await message.answer("❌ Error al actualizar criterio")
        await state.clear()


@router.callback_query(F.data.startswith("gamif:criteria:weekly_target:"))
async def edit_weekly_target(callback: CallbackQuery, state: FSMContext):
    """Edita meta semanal."""
    mission_id = int(callback.data.split(":")[-1])
    await state.update_data(mission_id=mission_id)

    text = "🎯 <b>EDITAR META SEMANAL</b>\n\n"
    text += "Envía el número de reacciones semanales requeridas (ej: 50):"

    await callback.message.edit_text(text, parse_mode="HTML")
    await state.set_state(MissionConfigStates.waiting_for_weekly_target)
    await callback.answer()


@router.message(MissionConfigStates.waiting_for_weekly_target)
async def process_weekly_target(message: Message, state: FSMContext, gamification: GamificationContainer):
    """Procesa meta semanal."""
    data = await state.get_data()
    mission_id = data['mission_id']

    try:
        target = int(message.text)
        if target <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Debe ser un número positivo.")
        return

    mission = await gamification.mission.get_mission_by_id(mission_id)
    criteria = json.loads(mission.criteria)
    criteria['target'] = target

    try:
        await gamification.mission.update_mission(mission_id, criteria=criteria)
        await message.answer(f"✅ Criterio actualizado: {target} reacciones semanales")
        await state.clear()
    except Exception as e:
        logger.error(f"Error updating criteria: {e}")
        await message.answer("❌ Error al actualizar criterio")
        await state.clear()


# ========================================
# ACTIVAR/DESACTIVAR
# ========================================

@router.callback_query(F.data.startswith("gamif:mission:toggle:"))
async def toggle_mission(callback: CallbackQuery, gamification: GamificationContainer):
    """Activa o desactiva misión."""
    mission_id = int(callback.data.split(":")[-1])

    mission = await gamification.mission.get_mission_by_id(mission_id)
    if not mission:
        await callback.answer("❌ Misión no encontrada", show_alert=True)
        return

    new_state = not mission.active

    await gamification.mission.update_mission(mission_id, active=new_state)

    status_text = "activada" if new_state else "desactivada"
    await callback.answer(f"✅ Misión {status_text}", show_alert=True)

    # Refrescar vista
    await view_mission(callback, gamification)


# ========================================
# ELIMINAR
# ========================================

@router.callback_query(F.data.startswith("gamif:mission:delete:"))
async def delete_mission_confirm(callback: CallbackQuery, gamification: GamificationContainer):
    """Pide confirmación para eliminar."""
    mission_id = int(callback.data.split(":")[-1])

    mission = await gamification.mission.get_mission_by_id(mission_id)
    if not mission:
        await callback.answer("❌ Misión no encontrada", show_alert=True)
        return

    # Obtener estadísticas de usuarios activos
    stats = await gamification.mission.get_mission_stats(mission_id)
    users_in_progress = stats['in_progress']

    text = f"⚠️ <b>CONFIRMAR ELIMINACIÓN</b>\n\n"
    text += f"Misión: <b>{mission.name}</b>\n\n"

    if users_in_progress > 0:
        text += f"⚠️ <b>ADVERTENCIA:</b> {users_in_progress} usuario(s) tienen esta misión en progreso.\n\n"
        text += "Al eliminar, perderán el progreso actual.\n\n"

    text += "¿Estás seguro de eliminar esta misión?"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚠️ Sí, Eliminar", callback_data=f"gamif:mission:delete_confirm:{mission_id}"),
            InlineKeyboardButton(text="❌ Cancelar", callback_data=f"gamif:mission:view:{mission_id}")
        ]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:mission:delete_confirm:"))
async def confirm_delete_mission(callback: CallbackQuery, gamification: GamificationContainer):
    """Elimina misión (soft-delete)."""
    mission_id = int(callback.data.split(":")[-1])

    mission = await gamification.mission.get_mission_by_id(mission_id)
    if not mission:
        await callback.answer("❌ Misión no encontrada", show_alert=True)
        return

    await gamification.mission.delete_mission(mission_id)

    await callback.answer("✅ Misión eliminada", show_alert=True)
    await missions_menu(callback, gamification)
