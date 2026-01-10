"""
Teaser Handlers - Muestra teasers para contenido bloqueado por onboarding.

Cuando un usuario intenta acceder a funcionalidades que requieren onboarding:
1. Verifica si completó onboarding
2. Si NO: Muestra teaser atractivo + CTA para hacer onboarding
3. Si SÍ: Redirige a funcionalidad real
"""
import logging

from aiogram import F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.handlers.user.start import user_router
from bot.narrative.services.container import NarrativeContainer
from bot.services.container import ServiceContainer
from bot.services.lucien_voice import LucienVoiceService
from bot.utils.keyboards import create_inline_keyboard

logger = logging.getLogger(__name__)


@user_router.callback_query(F.data == "user:profile")
async def callback_user_profile_teaser(callback: CallbackQuery, session: AsyncSession):
    """
    Handler teaser para Mi Perfil.

    Si usuario NO completó onboarding → Muestra teaser + CTA
    Si completó onboarding → Muestra perfil real (TODO)
    """
    user_id = callback.from_user.id
    logger.info(f"📊 Usuario {user_id} accediendo a Mi Perfil")

    narrative = NarrativeContainer(session, callback.bot)
    container = ServiceContainer(session, callback.bot)

    # Verificar onboarding
    completed_onboarding = await narrative.onboarding.has_completed_onboarding(user_id)

    if not completed_onboarding:
        # Mostrar TEASER + CTA
        lucien = LucienVoiceService()

        text = (
            "📊 <b>Centro de Perfil</b>\n\n"
            "🌟 <i>Descubre tu progreso, logros y estadísticas personales</i>\n\n"
            "<b>✨ Lo que encontrarás aquí:</b>\n"
            "• 📈 Progreso en la narrativa\n"
            "• 🏆 Logros desbloqueados\n"
            "• 💋 Besitos acumulados\n"
            "• 🎯 Estadísticas de participación\n"
            "• 👑 Nivel de suscripción\n\n"
            "─────────────────────\n\n"
            "🔒 <b>Esta área está protegida</b>\n\n"
            f"{await lucien.get_message('onboarding_teaser_profile')}\n\n"
            "💫 <i>Completa el tutorial para desbloquear tu perfil personalizado</i>"
        )

        keyboard = create_inline_keyboard([
            [{"text": "📖 Iniciar Tutorial", "callback_data": "onboard:start"}],
            [{"text": "⭐ ¡Hazte VIP!", "callback_data": "user:vip_access"}],
            [{"text": "🔙 Volver", "callback_data": "profile:back"}]
        ])

        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
        return

    # TODO: Mostrar perfil real (cuando se implemente)
    text = (
        "📊 <b>Mi Perfil</b>\n\n"
        "Tu perfil está siendo preparado...\n\n"
        "<i>Próximamente verás aquí todas tus estadísticas y logros.</i>"
    )

    keyboard = create_inline_keyboard([
        [{"text": "🔙 Volver", "callback_data": "profile:back"}]
    ])

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@user_router.callback_query(F.data == "games:main")
async def callback_games_main_teaser(callback: CallbackQuery, session: AsyncSession):
    """
    Handler teaser para Juegos.

    Si usuario NO completó onboarding → Muestra teaser + CTA
    Si completó onboarding → Muestra juegos disponibles (TODO)
    """
    user_id = callback.from_user.id
    logger.info(f"🎮 Usuario {user_id} accediendo a Juegos")

    narrative = NarrativeContainer(session, callback.bot)
    container = ServiceContainer(session, callback.bot)

    # Verificar onboarding
    completed_onboarding = await narrative.onboarding.has_completed_onboarding(user_id)

    if not completed_onboarding:
        # Mostrar TEASER + CTA
        lucien = LucienVoiceService()

        text = (
            "🎮 <b>Zona de Juegos</b>\n\n"
            "🎲 <i>Diviértete mientras ganas besitos y desbloqueas contenido exclusivo</i>\n\n"
            "<b>🎯 Juegos disponibles:</b>\n"
            "• 🎰 Ruleta de Besitos\n"
            "• 🃏 Memoria Seductora\n"
            "• 🎲 Dado del Deseo\n"
            "• 💎 Piedra, Papel, Tijera VIP\n\n"
            "─────────────────────\n\n"
            "🔒 <b>Los juegos están bloqueados</b>\n\n"
            f"{await lucien.get_message('onboarding_teaser_games')}\n\n"
            "💫 <i>Completa el tutorial para comenzar a jugar y ganar</i>"
        )

        keyboard = create_inline_keyboard([
            [{"text": "📖 Iniciar Tutorial", "callback_data": "onboard:start"}],
            [{"text": "⭐ ¡Hazte VIP!", "callback_data": "user:vip_access"}],
            [{"text": "🔙 Volver", "callback_data": "profile:back"}]
        ])

        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
        return

    # TODO: Mostrar juegos reales (cuando se implementen)
    text = (
        "🎮 <b>Zona de Juegos</b>\n\n"
        "Los juegos están siendo preparados...\n\n"
        "<i>Próximamente encontrarás aquí entretenimiento exclusivo.</i>"
    )

    keyboard = create_inline_keyboard([
        [{"text": "🔙 Volver", "callback_data": "profile:back"}]
    ])

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()
