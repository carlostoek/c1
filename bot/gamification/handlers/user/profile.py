"""
Handler para visualización de perfil de usuario con voz de Lucien.

Muestra información completa del perfil de gamificación:
- Comentario de Lucien según nivel
- Besitos totales y nivel actual
- Barra de progreso visual
- Misiones completadas
- Badges obtenidos
"""
import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram import F
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares import DatabaseMiddleware
from bot.gamification.services.container import GamificationContainer
from bot.services.container import ServiceContainer
from bot.utils.lucien_messages import LucienMessages

logger = logging.getLogger(__name__)

router = Router()

# Registrar middleware para inyectar session y gamification
router.message.middleware(DatabaseMiddleware())
router.callback_query.middleware(DatabaseMiddleware())


@router.message(Command("profile"))
@router.message(Command("perfil"))
async def show_profile(message: Message, session: AsyncSession):
    """
    Muestra perfil completo del usuario con voz de Lucien.

    Accesible mediante:
    - /profile
    - /perfil

    Args:
        message: Mensaje del usuario
        session: Sesión de BD
    """
    try:
        from bot.utils.menu_helpers import build_profile_menu_lucien

        # Usar nueva función con voz de Lucien
        summary, keyboard = await build_profile_menu_lucien(
            session=session,
            bot=message.bot,
            user_id=message.from_user.id,
            show_back_button=True
        )

        await message.answer(summary, reply_markup=keyboard, parse_mode="HTML")

    except Exception as e:
        logger.error(f"❌ Error cargando perfil: {e}", exc_info=True)
        await message.answer(
            LucienMessages.errors("ERROR_SHORT"),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "user:profile")
async def show_profile_callback(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra perfil completo del usuario con voz de Lucien (versión callback).

    Args:
        callback: Callback query del usuario
        session: Sesión de BD
    """
    try:
        from bot.utils.menu_helpers import build_profile_menu_lucien

        # Usar nueva función con voz de Lucien
        summary, keyboard = await build_profile_menu_lucien(
            session=session,
            bot=callback.bot,
            user_id=callback.from_user.id,
            show_back_button=True
        )

        await callback.message.edit_text(summary, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()

    except Exception as e:
        logger.error(f"❌ Error cargando perfil: {e}", exc_info=True)
        await callback.answer(
            LucienMessages.errors("ERROR_SHORT"),
            show_alert=True
        )
