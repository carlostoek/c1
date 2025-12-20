"""
Handlers del perfil de usuario de gamificación.
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.gamification.services.container import GamificationContainer

router = Router()


@router.message(Command("profile"))
@router.message(Command("perfil"))
async def show_profile(message: Message, gamification: GamificationContainer):
    """
    Muestra perfil completo del usuario.
    
    Usa: gamification.user_gamification.get_profile_summary()
    
    Botones:
    [📋 Misiones] [🎁 Recompensas]
    [🏆 Leaderboard]
    """
    user_id = message.from_user.id
    
    summary = await gamification.user_gamification.get_profile_summary(user_id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Mis Misiones", callback_data="user:missions"),
            InlineKeyboardButton(text="🎁 Recompensas", callback_data="user:rewards")
        ],
        [
            InlineKeyboardButton(text="🏆 Leaderboard", callback_data="user:leaderboard")
        ]
    ])
    
    await message.answer(summary, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "user:profile")
async def show_profile_callback(callback: CallbackQuery, gamification: GamificationContainer):
    """Muestra perfil desde callback."""
    user_id = callback.from_user.id
    
    summary = await gamification.user_gamification.get_profile_summary(user_id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Mis Misiones", callback_data="user:missions"),
            InlineKeyboardButton(text="🎁 Recompensas", callback_data="user:rewards")
        ],
        [
            InlineKeyboardButton(text="🏆 Leaderboard", callback_data="user:leaderboard")
        ]
    ])
    
    await callback.message.edit_text(summary, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()