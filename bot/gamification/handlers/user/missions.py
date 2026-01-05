"""
Handler para visualización y gestión de Encargos del Diván.
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.middlewares import DatabaseMiddleware
from bot.gamification.services.container import GamificationContainer
from bot.gamification.database.enums import MissionStatus
from bot.utils.lucien_messages import Lucien

logger = logging.getLogger(__name__)
router = Router()
router.callback_query.middleware(DatabaseMiddleware())


def _get_progress_comment(percentage: float) -> str:
    """Retorna el comentario de Lucien según el porcentaje de progreso."""
    if percentage >= 100:
        return "Debería reclamar su reconocimiento."
    if percentage >= 75:
        return "Casi lo logra. Un último esfuerzo."
    if percentage >= 50:
        return "Más de la mitad. No se detenga ahora."
    if percentage >= 25:
        return "Va por buen camino."
    return "Apenas ha comenzado."


def _get_progress_data(mission, user_mission) -> (int, int, float):
    """Calcula el progreso de una misión."""
    if not user_mission or not mission.criteria:
        return 0, 0, 0.0

    criteria = mission.criteria
    progress = user_mission.progress_data or {}
    
    current = progress.get('count', 0)
    target = criteria.get('count', 0)
    
    if criteria.get('type') == 'streak':
        current = progress.get('current_streak', 0)
        target = criteria.get('days', 0)

    if target > 0:
        percentage = min((current / target) * 100, 100)
    else:
        percentage = 0

    return current, target, percentage


@router.callback_query(F.data == "user:missions")
async def show_missions(callback: CallbackQuery, gamification: GamificationContainer):
    """Lista los Encargos del usuario agrupados por tipo."""
    user_id = callback.from_user.id
    text = Lucien.ENCARGOS_WELCOME + "\n"
    keyboard_buttons = []

    # 1. Obtener todas las misiones y el progreso del usuario
    all_missions = await gamification.mission.get_all_missions()
    user_missions = await gamification.mission.get_user_missions(user_id, status=None)
    user_missions_map = {um.mission_id: um for um in user_missions}

    # 2. Agrupar misiones
    groups = {"daily": [], "weekly": [], "one_time": []}
    claimable = []

    for mission in all_missions:
        if not mission.active:
            continue
        
        user_mission = user_missions_map.get(mission.id)
        status = user_mission.status if user_mission else None

        if status == MissionStatus.CLAIMED:
            continue
        
        if status == MissionStatus.COMPLETED:
            claimable.append(mission)
            continue

        mission_type = mission.criteria.get('type')
        if mission_type in groups:
            groups[mission_type].append(mission)

    # 3. Construir el texto y los botones
    if claimable:
        text += "✅ <b>Encargos Cumplidos (Reclamar):</b>\n"
        for mission in claimable:
            text += f"• {mission.name} - {mission.besitos_reward} Besitos\n"
            keyboard_buttons.append([
                InlineKeyboardButton(text=f"🎁 Reclamar: {mission.name}", callback_data=f"user:mission:claim:{mission.id}")
            ])
        text += "\n"

    group_titles = {
        "daily": "📅 Protocolos Diarios",
        "weekly": "📆 Encargos Semanales",
        "one_time": "⭐ Encargos Especiales",
    }

    for group, title in group_titles.items():
        if groups[group]:
            text += f"{title}:\n"
            for mission in groups[group]:
                user_mission = user_missions_map.get(mission.id)
                current, target, _ = _get_progress_data(mission, user_mission)
                text += f"• {mission.name} ({current}/{target})\n"
                keyboard_buttons.append([
                    InlineKeyboardButton(text=f"👁️ Ver: {mission.name}", callback_data=f"user:mission:view:{mission.id}")
                ])
            text += "\n"

    if not any(groups.values()) and not claimable:
        text = Lucien.ENCARGOS_EMPTY

    keyboard_buttons.append([InlineKeyboardButton(text="🔙 Volver al Perfil", callback_data="user:profile")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("user:mission:claim:"))
async def claim_mission_reward(callback: CallbackQuery, gamification: GamificationContainer):
    """Reclama el reconocimiento de un encargo cumplido."""
    try:
        mission_id = int(callback.data.split(":")[-1])
        user_id = callback.from_user.id
        success, message, rewards_info = await gamification.mission.claim_reward(user_id, mission_id)

        if success:
            besitos_granted = rewards_info.get('besitos_granted', 0)
            alert_text = Lucien.ENCARGOS_COMPLETED.format(mission_name=rewards_info.get('mission_name', ''), reward=besitos_granted)
            await callback.answer(alert_text, show_alert=True)
            await show_missions(callback, gamification)
        else:
            await callback.answer(f"❌ {message}", show_alert=True)
    except Exception as e:
        logger.error(f"Error al reclamar encargo: {e}", exc_info=True)
        await callback.answer(Lucien.ERROR_GENERIC, show_alert=True)


@router.callback_query(F.data.startswith("user:mission:view:"))
async def view_mission_progress(callback: CallbackQuery, gamification: GamificationContainer):
    """Muestra progreso detallado de un encargo."""
    try:
        mission_id = int(callback.data.split(":")[-1])
        user_id = callback.from_user.id

        mission = await gamification.mission.get_mission(mission_id)
        user_mission = await gamification.mission.get_user_mission(user_id, mission_id)

        if not mission:
            await callback.answer(Lucien.ERROR_NOT_FOUND, show_alert=True)
            return

        current, target, percentage = _get_progress_data(mission, user_mission)
        comment = _get_progress_comment(percentage)

        text = (
            f"📋 <b>{mission.name}</b>\n\n"
            f"<i>{mission.description}</i>\n\n"
            f"<b>Progreso:</b> {current}/{target}\n"
            f"<b>Reconocimiento:</b> {mission.besitos_reward} Besitos\n\n"
            f"<i>Lucien anota: \"{comment}\"</i>"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Volver a Encargos", callback_data="user:missions")]])
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
    except Exception as e:
        logger.error(f"Error al ver encargo: {e}", exc_info=True)
        await callback.answer(Lucien.ERROR_GENERIC, show_alert=True)
