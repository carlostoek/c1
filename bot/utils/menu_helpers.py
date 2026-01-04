"""
Menu Helpers - Funciones auxiliares para construcción de menús.

Reduce duplicación de código entre handlers.
"""
import logging
from datetime import datetime, timezone
from typing import Tuple

from aiogram.types import InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.enums import UserRole
from bot.services.container import ServiceContainer
from bot.utils.keyboards import create_inline_keyboard

logger = logging.getLogger(__name__)


async def build_start_menu(
    session: AsyncSession,
    bot,
    user_id: int,
    user_name: str,
    container: ServiceContainer = None
) -> Tuple[str, InlineKeyboardMarkup]:
    """
    Construye el menú principal de /start para un usuario.

    Menú simplificado único para todos los usuarios.

    Args:
        session: Sesión de BD
        bot: Bot de Telegram
        user_id: ID del usuario de Telegram
        user_name: Nombre del usuario
        container: ServiceContainer opcional (no usado)

    Returns:
        Tuple de (welcome_message, keyboard)
    """
    # Mensaje de bienvenida simple
    welcome_message = (
        f"¡Hola <b>{user_name}</b>! 👋\n\n"
        f"Bienvenido/a al bot. Selecciona una opción del menú:"
    )

    # Keyboard simple y directo con botones principales
    keyboard = create_inline_keyboard([
        [{"text": "📺 Acceder al Canal VIP", "callback_data": "user:vip_access"}],
        [{"text": "📢 Unirse al Canal Free", "callback_data": "user:free_access"}],
        [{"text": "🎟️ Canjear Token VIP", "callback_data": "user:redeem_token"}],
        [{"text": "🏪 Tienda", "callback_data": "shop:main"}],
        [{"text": "📖 Historia", "callback_data": "narr:start"}],
        [{"text": "🎮 Juego Kinky", "callback_data": "user:profile"}],
    ])

    return welcome_message, keyboard


async def build_profile_menu(
    session: AsyncSession,
    bot,
    user_id: int,
    show_back_button: bool = True
) -> Tuple[str, InlineKeyboardMarkup]:
    """
    Construye el menú de perfil de gamificación (Juego Kinky).

    Función auxiliar reutilizable que obtiene el resumen del perfil,
    verifica el estado del regalo diario y construye el keyboard
    con botones de gamificación + botones dinámicos configurados.

    Args:
        session: Sesión de BD
        bot: Bot de Telegram
        user_id: ID del usuario de Telegram
        show_back_button: Si True, incluye botón "Volver al Menú" (default: True)

    Returns:
        Tuple de (summary_text, keyboard)
    """
    from bot.gamification.services.container import GamificationContainer
    from bot.utils.keyboards import create_inline_keyboard

    container = ServiceContainer(session, bot)
    gamification = GamificationContainer(session, bot)

    # Obtener resumen de perfil
    summary = await gamification.user_gamification.get_profile_summary(user_id)

    # Verificar estado del regalo diario
    daily_gift_status = await gamification.daily_gift.get_daily_gift_status(user_id)

    # Texto del botón de regalo diario con indicador visual
    if daily_gift_status['can_claim'] and daily_gift_status['system_enabled']:
        daily_gift_text = "🎁 Regalo Diario ⭐"
    else:
        daily_gift_text = "🎁 Regalo Diario ✅"

    # Construir keyboard con botones de gamificación
    keyboard_buttons = [
        [{"text": daily_gift_text, "callback_data": "user:daily_gift"}],
        [
            {"text": "📋 Mis Misiones", "callback_data": "user:missions"},
            {"text": "🎁 Recompensas", "callback_data": "user:rewards"}
        ],
        [{"text": "🏆 Leaderboard", "callback_data": "user:leaderboard"}],
        [
            {"text": "🎒 Mi Mochila", "callback_data": "backpack:main"},
            {"text": "📔 Diario", "callback_data": "journal:main"}
        ]
    ]

    # Obtener botones dinámicos configurados para "profile"
    profile_buttons = await container.menu.build_keyboard_for_role("profile")
    if profile_buttons:
        keyboard_buttons.extend(profile_buttons)

    # Agregar botón de volver al menú (opcional)
    if show_back_button:
        keyboard_buttons.append([{"text": "🔙 Volver al Menú", "callback_data": "profile:back"}])

    keyboard = create_inline_keyboard(keyboard_buttons)

    return summary, keyboard
