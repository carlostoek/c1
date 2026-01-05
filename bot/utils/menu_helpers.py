"""
Menu Helpers - Funciones auxiliares para construcción de menús.

Reduce duplicación de código entre handlers.
"""
import logging
from datetime import datetime, timezone
from typing import Tuple, Optional

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
) -> Tuple[Optional[str], InlineKeyboardMarkup]:
    """
    Construye el menú principal de /start para un usuario con la voz de Lucien.

    El menú ahora es dinámico basado en el rol del usuario (Free vs VIP).
    El mensaje de bienvenida ya no se genera aquí.

    Args:
        session: Sesión de BD
        bot: Bot de Telegram
        user_id: ID del usuario de Telegram
        user_name: Nombre del usuario (ya no se usa aquí)
        container: ServiceContainer para acceder a servicios.

    Returns:
        Tuple de (None, keyboard)
    """
    if not container:
        container = ServiceContainer(session, bot)

    # El mensaje de bienvenida ahora se gestiona en handlers/user/start.py
    welcome_message = None

    # Obtener el rol del usuario para construir el menú adecuado
    user = await container.user.get_user_by_id(user_id)
    user_role = user.role if user else UserRole.FREE

    # Definir botones para el menú principal según la Fase 1
    keyboard_buttons = [
        [{"text": "📜 Mi Perfil", "callback_data": "user:profile"}],
        [{"text": "🎯 Encargos", "callback_data": "user:missions"}],
        [{"text": "🏛️ El Gabinete", "callback_data": "shop:main"}],
        [{"text": "💋 Mis Besitos", "callback_data": "user:besitos"}],
        [{"text": "📖 Mi Historia", "callback_data": "narrative:main"}],
    ]

    # Añadir botones específicos para roles
    if user_role == UserRole.VIP:
        # Insertar botones VIP en la parte superior del menú
        vip_buttons = [
            [{"text": "⭐ Contenido Premium", "callback_data": "premium:browse"}],
            [{"text": "🗺️ Mapa del Deseo", "callback_data": "mapa:info"}],
        ]
        keyboard_buttons = vip_buttons + keyboard_buttons
    else:
        # Usuario FREE ve el botón de Acceso VIP
        keyboard_buttons.append([{"text": "🔑 Acceso VIP", "callback_data": "vip:info"}])

    keyboard = create_inline_keyboard(keyboard_buttons)

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
