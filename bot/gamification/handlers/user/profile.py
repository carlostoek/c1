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
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares import DatabaseMiddleware
from bot.gamification.services.container import GamificationContainer
from bot.services.container import ServiceContainer
from bot.utils.keyboards import create_inline_keyboard
from bot.utils.menu_helpers import build_profile_menu

router = Router()

# Registrar middleware para inyectar session y gamification
router.message.middleware(DatabaseMiddleware())
router.callback_query.middleware(DatabaseMiddleware())


@router.message(Command("profile"))
@router.message(Command("perfil"))
async def show_profile(message: Message, session: AsyncSession, gamification: GamificationContainer):
    """
    Muestra perfil completo del usuario.

    Accesible mediante:
    - /profile
    - /perfil

    Args:
        message: Mensaje del usuario
        session: Sesión de BD
        gamification: Container de servicios de gamificación
    """
    try:
        # Usar helper con botón de volver al menú principal
        summary, keyboard = await build_profile_menu(
            session=session,
            bot=message.bot,
            user_id=message.from_user.id,
            show_back_button=True
        )

        await message.answer(summary, reply_markup=keyboard, parse_mode="HTML")

    except Exception as e:
        await message.answer(
            f"❌ Error al cargar perfil: {str(e)}",
            parse_mode="HTML"
        )


@router.callback_query(F.data == "user:profile")
async def show_profile_callback(callback: CallbackQuery, session: AsyncSession, gamification: GamificationContainer):
    """
    Muestra perfil completo del usuario (versión callback para navegación).

    Args:
        callback: Callback query del usuario
        session: Sesión de BD
        gamification: Container de servicios de gamificación
    """
    try:
        # Usar helper con botón de volver al menú principal
        summary, keyboard = await build_profile_menu(
            session=session,
            bot=callback.bot,
            user_id=callback.from_user.id,
            show_back_button=True
        )

        await callback.message.edit_text(summary, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()

    except Exception as e:
        await callback.answer(f"❌ Error: {str(e)}", show_alert=True)
