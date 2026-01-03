"""
Handler para visualización y gestión de Encargos del usuario.

Funcionalidades:
- Ver encargos en progreso
- Ver encargos completados
- Reclamar reconocimiento de encargos
- Ver encargos disponibles para iniciar
"""

from typing import Optional

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.middlewares import DatabaseMiddleware
from bot.gamification.services.container import GamificationContainer
from bot.gamification.database.enums import MissionStatus
from bot.utils.lucien_messages import LucienMessages

router = Router()

# Registrar middleware para inyectar session y gamification
router.callback_query.middleware(DatabaseMiddleware())


# =============================================================================
# FASE 3: TRACKING DE COMPORTAMIENTO
# =============================================================================

async def _track_mission_action(
    session,
    user_id: int,
    action_type: str,
    mission_id: Optional[int] = None
):
    """
    Registra acciones de misiones para tracking de comportamiento (FASE 3).

    Args:
        session: Sesión de BD
        user_id: ID del usuario
        action_type: Tipo de acción (view_list, view_mission, claim_reward)
        mission_id: ID de la misión (opcional)
    """
    try:
        from bot.gamification.services.behavior_tracking import BehaviorTrackingService

        tracking = BehaviorTrackingService(session)

        if action_type == "view_list":
            # Ver lista de misiones (exploración)
            await tracking.track_button_click(
                user_id=user_id,
                button_id="user:missions",
                context="mission_list",
                time_to_click=0.0,
                is_exploration=True,
                is_direct_action=False
            )

        elif action_type == "view_mission":
            # Ver detalles de misión (exploración)
            await tracking.track_content_interaction(
                user_id=user_id,
                content_id=f"mission:{mission_id}",
                content_type="mission",
                interaction_type="view",
                is_emotional=False,
                is_personal=False
            )

        elif action_type == "claim_reward":
            # Reclamar recompensa (acción directa/realización)
            await tracking.track_button_click(
                user_id=user_id,
                button_id=f"user:mission:claim:{mission_id}",
                context="mission_claim",
                time_to_click=0.0,
                is_exploration=False,
                is_direct_action=True
            )

        logger.debug(f"📊 Tracking: Usuario {user_id} acción misión: {action_type}")

    except Exception as e:
        # No fallar el flujo principal por errores de tracking
        import logging
        logging.getLogger(__name__).warning(f"⚠️ Error en tracking de misión: {e}")


@router.callback_query(F.data == "user:missions")
async def show_missions(callback: CallbackQuery, gamification: GamificationContainer):
    """
    Lista encargos del usuario agrupados por estado.

    Estados mostrados:
    - En progreso: con botón para ver progreso
    - Completados: con botón para reclamar reconocimiento
    - Disponibles: con información básica

    Args:
        callback: Callback query del usuario
        gamification: Container de servicios de gamificación
    """
    try:
        user_id = callback.from_user.id

        # FASE 3: Tracking de vista de lista de misiones
        await _track_mission_action(callback, user_id, "view_list")

        # Obtener encargos del usuario
        in_progress = await gamification.mission.get_user_missions(
            user_id, status=MissionStatus.IN_PROGRESS
        )
        completed = await gamification.mission.get_user_missions(
            user_id, status=MissionStatus.COMPLETED
        )

        # Obtener encargos disponibles (no iniciados)
        all_missions = await gamification.mission.get_all_missions()
        user_mission_ids = {um.mission_id for um in (in_progress + completed)}
        available = [m for m in all_missions if m.id not in user_mission_ids]

        text = f"🎯 <b>Los Encargos</b>\n\n"
        text += f"{LucienMessages.missions('MISSIONS_WELCOME')}\n\n"
        keyboard_buttons = []

        # Encargos en progreso
        if in_progress:
            text += f"⏳ <b>{LucienMessages.missions('MISSIONS_IN_PROGRESS')}:</b>\n"
            for um in in_progress:
                mission = um.mission
                text += f"• {mission.name}\n"
                text += f"  Reconocimiento: {mission.besitos_reward} Besitos\n"
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text=f"📊 {mission.name}",
                        callback_data=f"user:mission:view:{mission.id}"
                    )
                ])
            text += "\n"

        # Encargos completados
        if completed:
            text += f"✅ <b>{LucienMessages.missions('MISSIONS_COMPLETED')}:</b>\n"
            for um in completed:
                mission = um.mission
                text += f"• {mission.name} - {mission.besitos_reward} Besitos\n"
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text=f"🎁 Reclamar: {mission.name}",
                        callback_data=f"user:mission:claim:{mission.id}"
                    )
                ])
            text += "\n"

        # Encargos disponibles
        if available:
            text += f"🆕 <b>{LucienMessages.missions('MISSIONS_AVAILABLE')}:</b>\n"
            for mission in available[:5]:  # Máximo 5
                text += f"• {mission.name} - {mission.besitos_reward} Besitos\n"

        if not (in_progress or completed or available):
            text += LucienMessages.missions('MISSIONS_EMPTY')

        keyboard_buttons.append([
            InlineKeyboardButton(text="🔙 Perfil", callback_data="user:profile")
        ])

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()

    except Exception as e:
        await callback.answer(
            LucienMessages.errors("ERROR_SHORT"),
            show_alert=True
        )


@router.callback_query(F.data.startswith("user:mission:claim:"))
async def claim_mission_reward(callback: CallbackQuery, gamification: GamificationContainer):
    """
    Reclama reconocimiento de un encargo cumplido.

    Flujo:
    1. Valida que el encargo esté cumplido
    2. Otorga besitos al usuario
    3. Marca como reclamado
    4. Actualiza UI

    Args:
        callback: Callback query con ID de encargo
        gamification: Container de servicios de gamificación
    """
    try:
        mission_id = int(callback.data.split(":")[-1])
        user_id = callback.from_user.id

        # Intentar reclamar reconocimiento
        success, message, rewards_info = await gamification.mission.claim_reward(
            user_id, mission_id
        )

        if success:
            # FASE 3: Tracking de reclamación de recompensa
            await _track_mission_action(callback, user_id, "claim_reward", mission_id)

            await callback.answer(
                LucienMessages.missions('MISSION_CLAIM_SUCCESS'),
                show_alert=True
            )
            # Recargar lista de encargos
            await show_missions(callback, gamification)
        else:
            await callback.answer(message, show_alert=True)

    except Exception as e:
        await callback.answer(
            LucienMessages.errors("ERROR_SHORT"),
            show_alert=True
        )


@router.callback_query(F.data.startswith("user:mission:view:"))
async def view_mission_progress(callback: CallbackQuery, gamification: GamificationContainer):
    """
    Muestra progreso detallado de un encargo en curso.

    Muestra:
    - Nombre y descripción
    - Progreso actual vs requerido
    - Reconocimiento al cumplir
    - Comentario de Lucien según progreso

    Args:
        callback: Callback query con ID de encargo
        gamification: Container de servicios de gamificación
    """
    try:
        mission_id = int(callback.data.split(":")[-1])
        user_id = callback.from_user.id

        # FASE 3: Tracking de vista de detalles de misión
        await _track_mission_action(callback, user_id, "view_mission", mission_id)

        # Obtener encargo y progreso
        mission = await gamification.mission.get_mission(mission_id)
        user_mission = await gamification.mission.get_user_mission(user_id, mission_id)

        if not mission or not user_mission:
            await callback.answer(
                LucienMessages.errors("NOT_FOUND_SHORT"),
                show_alert=True
            )
            return

        # Construir mensaje de progreso
        text = f"🎯 <b>{mission.name}</b>\n\n"
        text += f"{mission.description}\n\n"

        # Mostrar progreso según tipo
        criteria = mission.criteria
        progress = user_mission.progress_data or {}

        if criteria.get('type') == 'streak':
            current_days = progress.get('current_streak', 0)
            required_days = criteria.get('days', 0)
            percentage = int((current_days / required_days * 100)) if required_days > 0 else 0
            text += f"📊 Progreso: {current_days}/{required_days} días ({percentage}%)\n\n"

            # Comentario de Lucien según progreso
            if percentage < 25:
                comment = LucienMessages.missions('MISSION_PROGRESS_LOW')
            elif percentage < 50:
                comment = LucienMessages.missions('MISSION_PROGRESS_MID')
            elif percentage < 75:
                comment = LucienMessages.missions('MISSION_PROGRESS_HIGH')
            else:
                comment = LucienMessages.missions('MISSION_PROGRESS_NEARLY')
            text += f"{comment}\n"

        elif criteria.get('type') in ['daily', 'weekly', 'one_time']:
            current_count = progress.get('count', 0)
            required_count = criteria.get('count', 0)
            percentage = int((current_count / required_count * 100)) if required_count > 0 else 0
            text += f"📊 Progreso: {current_count}/{required_count} reacciones ({percentage}%)\n\n"

            # Comentario de Lucien según progreso
            if percentage < 25:
                comment = LucienMessages.missions('MISSION_PROGRESS_LOW')
            elif percentage < 50:
                comment = LucienMessages.missions('MISSION_PROGRESS_MID')
            elif percentage < 75:
                comment = LucienMessages.missions('MISSION_PROGRESS_HIGH')
            else:
                comment = LucienMessages.missions('MISSION_PROGRESS_NEARLY')
            text += f"{comment}\n"

        text += f"\n🎁 Reconocimiento: {mission.besitos_reward} Besitos"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Encargos", callback_data="user:missions")]
        ])

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()

    except Exception as e:
        await callback.answer(
            LucienMessages.errors("ERROR_SHORT"),
            show_alert=True
        )
