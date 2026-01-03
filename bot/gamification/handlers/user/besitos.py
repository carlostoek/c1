"""
Handler para visualización de Besitos del usuario con voz de Lucien.

Muestra:
- Balance actual de Besitos
- Comentario contextual de Lucien según cantidad
- Transacciones recientes (opcional)
- Nivel actual
"""
import logging
from typing import Optional

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares import DatabaseMiddleware
from bot.gamification.services.container import GamificationContainer
from bot.gamification.database.models import UserGamification
from bot.utils.lucien_messages import LucienMessages

logger = logging.getLogger(__name__)

router = Router()

# Registrar middleware para inyectar session y gamification
router.message.middleware(DatabaseMiddleware())
router.callback_query.middleware(DatabaseMiddleware())


def _get_comment_for_balance(balance: int) -> str:
    """
    Obtiene comentario de Lucien según cantidad de Besitos.

    Args:
        balance: Cantidad actual de Besitos

    Returns:
        Comentario contextual de Lucien
    """
    if balance < 50:
        return LucienMessages.besitos("COMMENT_LOW")
    elif balance < 200:
        return LucienMessages.besitos("COMMENT_GROWING")
    elif balance < 500:
        return LucienMessages.besitos("COMMENT_GOOD")
    elif balance < 1000:
        return LucienMessages.besitos("COMMENT_HIGH")
    else:
        return LucienMessages.besitos("COMMENT_HOARDER")


def _build_besitos_keyboard(show_back: bool = True) -> InlineKeyboardMarkup:
    """Construye teclado de vista de Besitos."""
    buttons = []

    # Opciones adicionales (futuras)
    # buttons.append([InlineKeyboardButton(text="📊 Ver Historial", callback_data="user:besitos:history")])

    if show_back:
        buttons.append([InlineKeyboardButton(text="🔙 Perfil", callback_data="user:profile")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("besitos"))
async def cmd_besitos(message: Message, session: AsyncSession):
    """
    Comando /besitos - Muestra balance y comentarios de Lucien.

    Args:
        message: Mensaje del usuario
        session: Sesión de BD
    """
    try:
        user_id = message.from_user.id

        # Obtener datos de gamificación del usuario
        user_gamif = await session.get(UserGamification, user_id)

        if not user_gamif:
            # Usuario no existe en gamificación
            text = (
                "💋 <b>Sus Besitos</b>\n\n"
                "Aún no tiene registro en el sistema.\n\n"
                "Use /start para comenzar."
            )
            await message.answer(text, reply_markup=_build_besitos_keyboard(), parse_mode="HTML")
            return

        balance = user_gamif.total_besitos
        comment = _get_comment_for_balance(balance)

        # Construir mensaje
        text = LucienMessages.besitos(
            "VIEW_HEADER",
            balance=balance,
            comment=comment
        )

        keyboard = _build_besitos_keyboard(show_back=True)
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error en cmd_besitos: {e}")
        await message.answer(
            LucienMessages.errors("ERROR_SHORT"),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "user:besitos")
async def callback_besitos(callback: CallbackQuery, session: AsyncSession):
    """
    Callback para ver Besitos desde el menú.

    Args:
        callback: Callback query del usuario
        session: Sesión de BD
    """
    try:
        user_id = callback.from_user.id

        # Obtener datos de gamificación del usuario
        user_gamif = await session.get(UserGamification, user_id)

        if not user_gamif:
            text = (
                "💋 <b>Sus Besitos</b>\n\n"
                "Aún no tiene registro en el sistema."
            )
            await callback.message.edit_text(
                text,
                reply_markup=_build_besitos_keyboard(show_back=True),
                parse_mode="HTML"
            )
            await callback.answer()
            return

        balance = user_gamif.total_besitos
        comment = _get_comment_for_balance(balance)

        # Construir mensaje
        text = LucienMessages.besitos(
            "VIEW_HEADER",
            balance=balance,
            comment=comment
        )

        keyboard = _build_besitos_keyboard(show_back=True)
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()

    except Exception as e:
        logger.error(f"Error en callback_besitos: {e}")
        await callback.answer(
            LucienMessages.errors("ERROR_SHORT"),
            show_alert=True
        )
