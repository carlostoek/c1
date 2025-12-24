"""
Handler para visualización y gestión de misiones del usuario.

Funcionalidades:
- Ver misiones en progreso
- Ver misiones completadas
- Reclamar recompensas de misiones
- Ver misiones disponibles para iniciar
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.gamification.services.container import GamificationContainer
from bot.gamification.database.enums import MissionStatus

router = Router()


@router.callback_query(F.data == "user:missions")
async def show_missions(callback: CallbackQuery, gamification: GamificationContainer):
    """
    Lista misiones del usuario agrupadas por estado.

    Estados mostrados:
    - En progreso: con botón para ver progreso
    - Completadas: con botón para reclamar
    - Disponibles: con información básica

    Args:
        callback: Callback query del usuario
        gamification: Container de servicios de gamificación
    """
    try:
        user_id = callback.from_user.id

        # Obtener misiones del usuario
        in_progress = await gamification.mission.get_user_missions(
            user_id, status=MissionStatus.IN_PROGRESS
        )
        completed = await gamification.mission.get_user_missions(
            user_id, status=MissionStatus.COMPLETED
        )

        # Obtener misiones disponibles (no iniciadas)
        all_missions = await gamification.mission.get_all_missions()
        user_mission_ids = {um.mission_id for um in (in_progress + completed)}
        available = [m for m in all_missions if m.id not in user_mission_ids]

        text = "📋 <b>Mis Misiones</b>\n\n"
        keyboard_buttons = []

        # Misiones en progreso
        if in_progress:
            text += "⏳ <b>En Progreso:</b>\n"
            for um in in_progress:
                mission = um.mission
                text += f"• {mission.name}\n"
                text += f"  Recompensa: {mission.besitos_reward} besitos\n"
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text=f"📊 {mission.name}",
                        callback_data=f"user:mission:view:{mission.id}"
                    )
                ])
            text += "\n"

        # Misiones completadas
        if completed:
            text += "✅ <b>Completadas (Reclamar):</b>\n"
            for um in completed:
                mission = um.mission
                text += f"• {mission.name} - {mission.besitos_reward} besitos\n"
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text=f"🎁 Reclamar: {mission.name}",
                        callback_data=f"user:mission:claim:{mission.id}"
                    )
                ])
            text += "\n"

        # Misiones disponibles
        if available:
            text += "🆕 <b>Disponibles:</b>\n"
            for mission in available[:5]:  # Máximo 5
                text += f"• {mission.name} - {mission.besitos_reward} besitos\n"

        if not (in_progress or completed or available):
            text += "No hay misiones disponibles en este momento."

        keyboard_buttons.append([
            InlineKeyboardButton(text="🔙 Perfil", callback_data="user:profile")
        ])

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()

    except Exception as e:
        await callback.answer(f"❌ Error: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("user:mission:claim:"))
async def claim_mission_reward(callback: CallbackQuery, gamification: GamificationContainer):
    """
    Reclama recompensa de una misión completada.

    Flujo:
    1. Valida que la misión esté completada
    2. Otorga besitos al usuario
    3. Marca como reclamada
    4. Actualiza UI

    Args:
        callback: Callback query con ID de misión
        gamification: Container de servicios de gamificación
    """
    try:
        mission_id = int(callback.data.split(":")[-1])
        user_id = callback.from_user.id

        # Intentar reclamar recompensa
        success, message, rewards_info = await gamification.mission.claim_reward(
            user_id, mission_id
        )

        if success:
            await callback.answer(f"🎉 {message}", show_alert=True)
            # Recargar lista de misiones
            await show_missions(callback, gamification)
        else:
            await callback.answer(f"❌ {message}", show_alert=True)

    except Exception as e:
        await callback.answer(f"❌ Error: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("user:mission:view:"))
async def view_mission_progress(callback: CallbackQuery, gamification: GamificationContainer):
    """
    Muestra progreso detallado de una misión en progreso.

    Muestra:
    - Nombre y descripción
    - Progreso actual vs requerido
    - Recompensa al completar

    Args:
        callback: Callback query con ID de misión
        gamification: Container de servicios de gamificación
    """
    try:
        mission_id = int(callback.data.split(":")[-1])
        user_id = callback.from_user.id

        # Obtener misión y progreso
        mission = await gamification.mission.get_mission(mission_id)
        user_mission = await gamification.mission.get_user_mission(user_id, mission_id)

        if not mission or not user_mission:
            await callback.answer("❌ Misión no encontrada", show_alert=True)
            return

        # Construir mensaje de progreso
        text = f"📋 <b>{mission.name}</b>\n\n"
        text += f"{mission.description}\n\n"

        # Mostrar progreso según tipo
        criteria = mission.criteria
        progress = user_mission.progress_data or {}

        if criteria.get('type') == 'streak':
            current_days = progress.get('current_streak', 0)
            required_days = criteria.get('days', 0)
            text += f"📊 Progreso: {current_days}/{required_days} días\n"
        elif criteria.get('type') in ['daily', 'weekly', 'one_time']:
            current_count = progress.get('count', 0)
            required_count = criteria.get('count', 0)
            text += f"📊 Progreso: {current_count}/{required_count} reacciones\n"

        text += f"\n🎁 Recompensa: {mission.besitos_reward} besitos"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Misiones", callback_data="user:missions")]
        ])

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()

    except Exception as e:
        await callback.answer(f"❌ Error: {str(e)}", show_alert=True)
