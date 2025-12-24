"""
Handler para visualización y gestión de recompensas del usuario.

Funcionalidades:
- Ver recompensas obtenidas
- Ver recompensas disponibles para desbloquear
- Comprar recompensas con besitos
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.gamification.services.container import GamificationContainer

router = Router()


@router.callback_query(F.data == "user:rewards")
async def show_rewards(callback: CallbackQuery, gamification: GamificationContainer):
    """
    Muestra recompensas obtenidas y disponibles del usuario.

    Organizado en secciones:
    - Obtenidas: Recompensas que ya posee
    - Disponibles: Recompensas que puede desbloquear/comprar

    Args:
        callback: Callback query del usuario
        gamification: Container de servicios de gamificación
    """
    try:
        user_id = callback.from_user.id

        # Obtener recompensas del usuario
        obtained = await gamification.reward.get_user_rewards(user_id)

        # Obtener recompensas disponibles
        available = await gamification.reward.get_available_rewards(user_id)

        text = "🎁 <b>Recompensas</b>\n\n"
        text += f"🏆 Obtenidas: {len(obtained)}\n"
        text += f"🔒 Disponibles: {len(available)}\n\n"

        keyboard_buttons = []

        # Mostrar algunas obtenidas
        if obtained:
            text += "<b>Últimas Obtenidas:</b>\n"
            for user_reward in obtained[:5]:  # Máximo 5
                reward = user_reward.reward
                icon = ""
                if reward.reward_type.value == 'badge':
                    metadata = reward.reward_metadata or {}
                    icon = metadata.get('icon', '🏆')
                text += f"• {icon} {reward.name}\n"
            text += "\n"

        # Mostrar disponibles para comprar/desbloquear
        if available:
            text += "<b>Disponibles para desbloquear:</b>\n"
            for reward in available[:5]:  # Máximo 5
                if reward.cost_besitos and reward.cost_besitos > 0:
                    text += f"• {reward.name} - {reward.cost_besitos} besitos\n"
                    keyboard_buttons.append([
                        InlineKeyboardButton(
                            text=f"💰 Comprar: {reward.name} ({reward.cost_besitos} besitos)",
                            callback_data=f"user:reward:buy:{reward.id}"
                        )
                    ])
                else:
                    text += f"• {reward.name} - Desbloquear cumpliendo condiciones\n"

        if not (obtained or available):
            text += "No hay recompensas disponibles en este momento."

        keyboard_buttons.append([
            InlineKeyboardButton(text="🔙 Perfil", callback_data="user:profile")
        ])

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()

    except Exception as e:
        await callback.answer(f"❌ Error: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("user:reward:buy:"))
async def buy_reward(callback: CallbackQuery, gamification: GamificationContainer):
    """
    Compra una recompensa con besitos del usuario.

    Flujo:
    1. Valida que el usuario tenga besitos suficientes
    2. Deduce besitos
    3. Otorga recompensa
    4. Actualiza UI

    Args:
        callback: Callback query con ID de recompensa
        gamification: Container de servicios de gamificación
    """
    try:
        reward_id = int(callback.data.split(":")[-1])
        user_id = callback.from_user.id

        # Intentar comprar recompensa
        success, message = await gamification.reward.purchase_reward(
            user_id, reward_id
        )

        if success:
            await callback.answer(f"🎉 {message}", show_alert=True)
            # Recargar lista de recompensas
            await show_rewards(callback, gamification)
        else:
            await callback.answer(f"❌ {message}", show_alert=True)

    except Exception as e:
        await callback.answer(f"❌ Error: {str(e)}", show_alert=True)
