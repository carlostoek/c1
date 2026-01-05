"""
Handler para mostrar el balance de Besitos del usuario.

Muestra el balance actual de Besitos, el nivel, y el progreso hacia el siguiente nivel,
todo con la voz y el contexto de Lucien.
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from bot.middlewares import DatabaseMiddleware
from bot.gamification.services.container import GamificationContainer
from bot.utils.lucien_messages import Lucien

logger = logging.getLogger(__name__)
router = Router()
router.callback_query.middleware(DatabaseMiddleware())


def _get_besitos_balance_comment(total_besitos: int) -> str:
    """Retorna el comentario de Lucien basado en la cantidad de Besitos."""
    if total_besitos >= 200: # Hoarder
        return Lucien.BESITOS_BALANCE_HOARDER.format(total=total_besitos)
    if total_besitos >= 100: # High
        return Lucien.BESITOS_BALANCE_HIGH.format(total=total_besitos)
    if total_besitos >= 51: # Good
        return Lucien.BESITOS_BALANCE_GOOD.format(total=total_besitos)
    if total_besitos >= 11: # Growing
        return Lucien.BESITOS_BALANCE_GROWING.format(total=total_besitos)
    return Lucien.BESITOS_BALANCE_LOW.format(total=total_besitos)


@router.callback_query(F.data == "user:besitos")
async def show_besitos_balance(callback: CallbackQuery, gamification: GamificationContainer):
    """
    Muestra el balance de Besitos, nivel y progreso del usuario.
    """
    user_id = callback.from_user.id
    profile_data = await gamification.user_gamification.get_user_profile(user_id)

    total_besitos = profile_data.get('besitos', {}).get('total', 0)
    level_info = profile_data.get('level', {})
    current_level = level_info.get('current')
    next_level = level_info.get('next')
    besitos_to_next = level_info.get('besitos_to_next')

    level_name = current_level.name if current_level else "Sin Nivel"
    
    # Comentario de Lucien
    lucien_comment = _get_besitos_balance_comment(total_besitos)

    # Construir mensaje
    text = f"{lucien_comment}\n\n"
    text += f"💋 <b>Sus Besitos</b>\n\n"
    text += f"Balance actual: {total_besitos}\n"
    text += f"Nivel: {level_name}\n"

    if next_level and besitos_to_next is not None:
        text += f"Para siguiente nivel ({next_level.name}): {besitos_to_next} más\n"
    elif current_level and not next_level:
        text += "Ha alcanzado el nivel máximo. No hay más niveles por delante.\n"
    
    # TODO: Historial reciente si aplica. Esto requiere un servicio de transacciones.

    keyboard_buttons = [
        [InlineKeyboardButton(text="🏛️ Ir al Gabinete", callback_data="shop:main")],
        # [{{"text": "📊 Ver Historial", "callback_data": "besitos:history"}}], # Opcional: requiere implementación
        [InlineKeyboardButton(text="🔙 Volver", callback_data="user:profile")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()
