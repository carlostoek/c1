"""
Handler para visualización de perfil de usuario.

Muestra información completa del perfil de gamificación:
- Besitos totales y nivel actual
- Misiones completadas
- Badges obtenidos
- Estadísticas generales
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F

from bot.gamification.services.container import GamificationContainer

router = Router()


@router.message(Command("profile"))
@router.message(Command("perfil"))
async def show_profile(message: Message, gamification: GamificationContainer):
    """
    Muestra perfil completo del usuario.

    Accesible mediante:
    - /profile
    - /perfil

    Args:
        message: Mensaje del usuario
        gamification: Container de servicios de gamificación
    """
    try:
        summary = await gamification.user_gamification.get_profile_summary(
            message.from_user.id
        )

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

    except Exception as e:
        await message.answer(
            f"❌ Error al cargar perfil: {str(e)}",
            parse_mode="HTML"
        )


@router.callback_query(F.data == "user:profile")
async def show_profile_callback(callback: CallbackQuery, gamification: GamificationContainer):
    """
    Muestra perfil completo del usuario (versión callback para navegación).

    Args:
        callback: Callback query del usuario
        gamification: Container de servicios de gamificación
    """
    try:
        summary = await gamification.user_gamification.get_profile_summary(
            callback.from_user.id
        )

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

    except Exception as e:
        await callback.answer(f"❌ Error: {str(e)}", show_alert=True)
