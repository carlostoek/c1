"""
Handlers de recompensas para usuarios finales.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.gamification.services.container import GamificationContainer

router = Router()


@router.callback_query(F.data == "user:rewards")
async def show_rewards(callback: CallbackQuery, gamification: GamificationContainer):
    """
    Muestra recompensas obtenidas y disponibles.
    
    Tabs:
    [🏆 Obtenidas] [🔒 Bloqueadas]
    """
    user_id = callback.from_user.id
    
    obtained_rewards = await gamification.reward.get_user_rewards(user_id)
    available_rewards = await gamification.reward.get_available_rewards(user_id)
    
    text = "🎁 <b>Recompensas</b>\n\n"
    text += f"<b>Obtenidas:</b> {len(obtained_rewards)}\n"
    text += f"<b>Disponibles:</b> {len(available_rewards)}\n\n"
    
    keyboard_buttons = []
    
    # Mostrar recompensas obtenidas
    if obtained_rewards:
        text += "<b>Tus Recompensas:</b>\n"
        for reward in obtained_rewards[:5]:  # Mostrar primeras 5
            icon = "🏆" if reward.reward_type == "badge" else "🎁"
            text += f"{icon} {reward.name}\n"
    
    # Disponibles para comprar/desbloquear
    if available_rewards:
        text += "\n<b>Disponibles para Desbloquear:</b>\n"
        for reward in available_rewards[:5]:  # Mostrar primeras 5
            if reward.cost_besitos and reward.cost_besitos > 0:
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text=f"💰 Comprar: {reward.name} ({reward.cost_besitos} besitos)",
                        callback_data=f"user:reward:buy:{reward.id}"
                    )
                ])
            else:
                icon = "🏆" if reward.reward_type == "badge" else "🎁"
                text += f"{icon} {reward.name} (Desbloqueo automático)\n"
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Perfil", callback_data="user:profile")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("user:reward:buy:"))
async def buy_reward(callback: CallbackQuery, gamification: GamificationContainer):
    """
    Compra recompensa con besitos.
    
    Usa: gamification.reward.purchase_reward()
    """
    reward_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    result = await gamification.reward.purchase_reward(user_id, reward_id)
    
    if result.get('success'):
        reward_name = result.get('reward_name', 'Recompensa')
        await callback.answer(f"🎉 ¡Compra exitosa! Obtuviste: {reward_name}", show_alert=True)
        
        # Actualizar el mensaje de recompensas
        await show_rewards(callback, gamification)
    else:
        error_message = result.get('error', 'Error desconocido')
        await callback.answer(f"❌ {error_message}", show_alert=True)


@router.callback_query(F.data.startswith("user:reward:claim:"))
async def claim_reward(callback: CallbackQuery, gamification: GamificationContainer):
    """Reclama una recompensa que se desbloqueó automáticamente."""
    reward_id = int(callback.data.split(":")[-1])
    user_id = callback.from_user.id
    
    result = await gamification.reward.claim_reward(user_id, reward_id)
    
    if result.get('success'):
        reward_name = result.get('reward_name', 'Recompensa')
        await callback.answer(f"🎉 ¡Recompensa reclamada! Obtuviste: {reward_name}", show_alert=True)
        
        # Actualizar el mensaje de recompensas
        await show_rewards(callback, gamification)
    else:
        error_message = result.get('error', 'Error desconocido')
        await callback.answer(f"❌ {error_message}", show_alert=True)