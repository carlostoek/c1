"""
Handlers de misiones para usuarios finales.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.gamification.services.container import GamificationContainer
from bot.gamification.database.enums import MissionStatus

router = Router()


@router.callback_query(F.data == "user:missions")
async def show_missions(callback: CallbackQuery, gamification: GamificationContainer):
    """
    Lista misiones disponibles/en progreso.
    
    Botones por misión:
    - IN_PROGRESS: [📊 Ver Progreso]
    - COMPLETED: [🎁 Reclamar]
    - NOT_STARTED: [▶️ Iniciar]
    """
    user_id = callback.from_user.id
    
    # Obtener misiones
    in_progress = await gamification.mission.get_user_missions(
        user_id, status=MissionStatus.IN_PROGRESS
    )
    completed = await gamification.mission.get_user_missions(
        user_id, status=MissionStatus.COMPLETED
    )
    available = await gamification.mission.get_available_missions(user_id)
    
    text = "📋 <b>Mis Misiones</b>\n\n"
    keyboard_buttons = []
    
    # En progreso
    if in_progress:
        text += "<b>En Progreso:</b>\n"
        for um in in_progress:
            progress_info = await gamification.mission.get_mission_progress(user_id, um.mission_id)
            progress_text = f" ({progress_info.get('current', 0)}/{progress_info.get('target', 1)})"
            text += f"• {um.mission.name}{progress_text}\n"
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"📊 {um.mission.name}",
                    callback_data=f"user:mission:view:{um.mission_id}"
                )
            ])
    
    # Completadas
    if completed:
        text += "\n<b>Completadas:</b>\n"
        for um in completed:
            mission = um.mission
            text += f"• {mission.name} - {mission.besitos_reward} besitos\n"
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"🎁 Reclamar: {mission.name}",
                    callback_data=f"user:mission:claim:{mission.id}"
                )
            ])
    
    # Disponibles
    if available:
        text += "\n<b>Disponibles:</b>\n"
        for mission in available:
            text += f"• {mission.name}\n"
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"▶️ Empezar: {mission.name}",
                    callback_data=f"user:mission:start:{mission.id}"
                )
            ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Perfil", callback_data="user:profile")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("user:mission:claim:"))
async def claim_mission_reward(callback: CallbackQuery, gamification: GamificationContainer):
    """
    Reclama recompensa de misión completada.
    
    Usa: gamification.mission.claim_reward()
    """
    mission_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    result = await gamification.mission.claim_reward(user_id, mission_id)
    
    if result.get('success'):
        rewards_info = result.get('rewards', [])
        reward_text = ""
        if rewards_info:
            besitos_reward = result.get('besitos_reward', 0)
            if besitos_reward > 0:
                reward_text = f"Has recibido {besitos_reward} besitos"
            
            # Check for any additional rewards (badges, etc.)
            if len(rewards_info) > 0:
                reward_text += f" y {len(rewards_info)} recompensa(s) adicional(es)"
        else:
            besitos_reward = result.get('besitos_reward', 0)
            reward_text = f"Has recibido {besitos_reward} besitos"
        
        await callback.answer(f"🎉 ¡Misión reclamada! {reward_text}", show_alert=True)
        
        # Actualizar el mensaje de misiones
        await show_missions(callback, gamification)
    else:
        error_message = result.get('error', 'Error desconocido')
        await callback.answer(f"❌ {error_message}", show_alert=True)


@router.callback_query(F.data.startswith("user:mission:start:"))
async def start_mission(callback: CallbackQuery, gamification: GamificationContainer):
    """Inicia una misión disponible."""
    mission_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    success = await gamification.mission.start_mission(user_id, mission_id)
    
    if success:
        await callback.answer("✅ ¡Misión iniciada!", show_alert=True)
        # Actualizar el mensaje de misiones
        await show_missions(callback, gamification)
    else:
        await callback.answer("❌ No se pudo iniciar la misión", show_alert=True)


@router.callback_query(F.data.startswith("user:mission:view:"))
async def view_mission(callback: CallbackQuery, gamification: GamificationContainer):
    """Ver detalles de una misión en progreso."""
    mission_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    # Obtener detalles de la misión y progreso
    user_mission = await gamification.mission.get_user_mission(user_id, mission_id)
    if not user_mission:
        await callback.answer("❌ No tienes acceso a esta misión", show_alert=True)
        return
    
    mission = user_mission.mission
    progress_info = await gamification.mission.get_mission_progress(user_id, mission_id)
    
    current = progress_info.get('current', 0)
    target = progress_info.get('target', 1)
    
    text = f"""📊 <b>{mission.name}</b>

<b>Descripción:</b> {mission.description}
<b>Recompensa:</b> {mission.besitos_reward} besitos
<b>Progreso:</b> {current}/{target}
<b>Estado:</b> {user_mission.status.value.replace('_', ' ').title()}

{progress_info.get('details', '')}
"""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔙 Misiones", callback_data="user:missions")
        ]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()