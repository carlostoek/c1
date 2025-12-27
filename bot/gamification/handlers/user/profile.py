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
        container = ServiceContainer(session, message.bot)

        summary = await gamification.user_gamification.get_profile_summary(
            message.from_user.id
        )

        # Verificar estado del regalo diario para mostrar indicador
        daily_gift_status = await gamification.daily_gift.get_daily_gift_status(
            message.from_user.id
        )

        # Texto del botón de regalo diario con indicador visual
        if daily_gift_status['can_claim'] and daily_gift_status['system_enabled']:
            daily_gift_text = "🎁 Regalo Diario ⭐"  # Indicador de disponible
        else:
            daily_gift_text = "🎁 Regalo Diario ✅"  # Indicador de reclamado

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

        # Agregar botón de volver al menú (solo cuando se accede desde /start)
        # Nota: Cuando se usa el comando /profile directamente, no se muestra el botón de volver
        # porque el usuario no vino desde /start

        keyboard = create_inline_keyboard(keyboard_buttons)

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
        container = ServiceContainer(session, callback.bot)

        summary = await gamification.user_gamification.get_profile_summary(
            callback.from_user.id
        )

        # Verificar estado del regalo diario para mostrar indicador
        daily_gift_status = await gamification.daily_gift.get_daily_gift_status(
            callback.from_user.id
        )

        # Texto del botón de regalo diario con indicador visual
        if daily_gift_status['can_claim'] and daily_gift_status['system_enabled']:
            daily_gift_text = "🎁 Regalo Diario ⭐"  # Indicador de disponible
        else:
            daily_gift_text = "🎁 Regalo Diario ✅"  # Indicador de reclamado

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

        keyboard = create_inline_keyboard(keyboard_buttons)

        await callback.message.edit_text(summary, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()

    except Exception as e:
        await callback.answer(f"❌ Error: {str(e)}", show_alert=True)
