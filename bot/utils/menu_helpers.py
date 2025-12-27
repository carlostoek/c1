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
from bot.utils.keyboards import dynamic_user_menu_keyboard

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

    Función auxiliar reutilizable que detecta el rol del usuario (VIP/FREE),
    calcula días restantes si es VIP, obtiene el mensaje de bienvenida
    configurado y genera el keyboard dinámico.

    Args:
        session: Sesión de BD
        bot: Bot de Telegram
        user_id: ID del usuario de Telegram
        user_name: Nombre del usuario
        container: ServiceContainer opcional (se crea si no se provee)

    Returns:
        Tuple de (welcome_message, keyboard)
    """
    # Crear container si no se provee
    if container is None:
        container = ServiceContainer(session, bot)

    # Verificar si es VIP
    is_vip = await container.subscription.is_vip_active(user_id)
    role = "vip" if is_vip else "free"
    subscription_type = "VIP" if is_vip else "FREE"

    # Calcular días restantes (solo VIP)
    days_remaining = 0
    if is_vip:
        subscriber = await container.subscription.get_vip_subscriber(user_id)
        if subscriber and hasattr(subscriber, 'expiry_date') and subscriber.expiry_date:
            # Asegurar que expiry_date tiene timezone
            expiry = subscriber.expiry_date
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            days_remaining = max(0, (expiry - now).days)

    # Obtener configuración de menú dinámico para el rol
    menu_config = await container.menu.get_or_create_menu_config(role)

    # Interpolar variables en el mensaje de bienvenida
    welcome_message = menu_config.welcome_message.format(
        user_name=user_name,
        days_remaining=days_remaining,
        subscription_type=subscription_type
    )

    # Obtener keyboard dinámico
    keyboard = await dynamic_user_menu_keyboard(session, role)

    return welcome_message, keyboard


async def build_profile_menu(
    session: AsyncSession,
    bot,
    user_id: int
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
        [{"text": "🏆 Leaderboard", "callback_data": "user:leaderboard"}]
    ]

    # Obtener botones dinámicos configurados para "profile"
    profile_buttons = await container.menu.build_keyboard_for_role("profile")
    if profile_buttons:
        keyboard_buttons.extend(profile_buttons)

    # Agregar botón de volver al menú
    keyboard_buttons.append([{"text": "🔙 Volver al Menú", "callback_data": "profile:back"}])

    keyboard = create_inline_keyboard(keyboard_buttons)

    return summary, keyboard
