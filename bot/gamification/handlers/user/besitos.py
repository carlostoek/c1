"""
Handler para visualización de Besitos del usuario con voz de Lucien.

Muestra:
- Balance actual de Besitos
- Comentario contextual de Lucien según cantidad
- Transacciones recientes (opcional)
- Nivel actual
- Historial de transacciones con paginación
"""
import logging
from typing import Optional
from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares import DatabaseMiddleware
from bot.gamification.services.container import GamificationContainer
from bot.gamification.database.models import UserGamification, BesitoTransaction
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

    # Botón de historial
    buttons.append([InlineKeyboardButton(text="📊 Ver Historial", callback_data="user:besitos:history:0")])

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


# ========================================
# HISTORIAL DE TRANSACCIONES
# ========================================

async def show_transaction_history(
    callback: CallbackQuery,
    session: AsyncSession,
    user_id: int,
    page: int = 0
):
    """Muestra historial de transacciones del usuario.

    Args:
        callback: Callback query
        session: Sesión de BD
        user_id: ID del usuario
        page: Página actual (0-indexed)
    """
    container = GamificationContainer(session, callback.bot)

    # Paginación: 10 transacciones por página
    per_page = 10
    offset = page * per_page

    # Obtener transacciones
    transactions = await container.besito.get_transaction_history(
        user_id=user_id,
        limit=per_page,
        offset=offset
    )

    # Obtener total para calcular páginas
    total_count = await container.besito.get_total_transactions_count(user_id=user_id)
    total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1

    # Construir texto con voz de Lucien
    text = LucienMessages.besitos("HISTORY_HEADER")

    if not transactions:
        text += "\n\n" + LucienMessages.besitos("EMPTY_STATE")
    else:
        for tx in transactions:
            # Emoji según tipo (positivo/negativo)
            emoji = "💋" if tx.amount > 0 else "💸"

            # Signo y formato
            sign = "+" if tx.amount > 0 else ""
            amount_str = f"{sign}{int(tx.amount)}"

            # Tipo legible
            type_map = {
                "reaction": "Reacción",
                "reaction_custom": "Reacción Especial",
                "mission_reward": "Misión",
                "purchase": "Compra",
                "admin_grant": "Admin +",
                "admin_deduct": "Admin -",
                "refund": "Reembolso",
                "streak_bonus": "Bonus Racha",
                "level_up_bonus": "Level Up",
                "daily_gift": "Regalo Diario"
            }
            type_name = type_map.get(tx.transaction_type, tx.transaction_type.replace("_", " ").title())

            # Formatear fecha
            date_str = tx.created_at.strftime("%d/%m %H:%M")

            text += f"\n{emoji} <b>{amount_str}</b> | {type_name}"
            text += f"\n   💰 Saldo: {int(tx.balance_after)} | {date_str}"

            if tx.description:
                text += f"\n   📝 {tx.description}"
            text += "\n"

    # Info de paginación
    text += f"\n━━━━━━━━━━━━━━━━\n"
    text += f"<i>Página {page + 1}/{total_pages} • {total_count} transacciones</i>"

    # Botones de paginación
    keyboard = []

    pagination_row = []
    if page > 0:
        pagination_row.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"user:besitos:history:{page - 1}")
        )

    # Botón central con número de página
    pagination_row.append(
        InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="user:besitos:history:ignore")
    )

    if page < total_pages - 1:
        pagination_row.append(
            InlineKeyboardButton(text="➡️", callback_data=f"user:besitos:history:{page + 1}")
        )

    if pagination_row:
        keyboard.append(pagination_row)

    # Botón volver
    keyboard.append([InlineKeyboardButton(text="🔙 Volver a Besitos", callback_data="user:besitos")])

    await callback.message.edit_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("user:besitos:history:"))
async def callback_transaction_history(callback: CallbackQuery, session: AsyncSession):
    """Muestra historial de transacciones.

    Callback data format: user:besitos:history:{page}
    """
    try:
        parts = callback.data.split(":")
        page = int(parts[3])

        await show_transaction_history(
            callback=callback,
            session=session,
            user_id=callback.from_user.id,
            page=page
        )

    except Exception as e:
        logger.error(f"Error en callback_transaction_history: {e}")
        await callback.answer(
            LucienMessages.errors("ERROR_SHORT"),
            show_alert=True
        )
