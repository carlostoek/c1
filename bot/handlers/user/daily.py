"""
Daily Login Handler - Manejo de regalos diarios.
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.container import ServiceContainer

logger = logging.getLogger(__name__)

daily_router = Router()


@daily_router.callback_query(F.data == "daily:claim")
async def callback_claim_daily(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Handler para reclamar regalo diario.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    user_id = callback.from_user.id
    logger.info(f"🎁 Usuario {user_id} reclamando regalo diario")

    container = ServiceContainer(session, callback.bot)

    try:
        # Intentar reclamar
        besitos, streak_days, is_new_record = await container.gamification.claim_daily_login(
            user_id=user_id
        )

        # Verificar badges (por si desbloqueó badge de streak)
        new_badges = await container.gamification.check_and_unlock_badges(user_id)

        # Verificar rank up
        progress = await container.gamification.get_or_create_progress(user_id)

        # Crear RewardBatch
        batch = await container.notifications.create_reward_batch(
            user_id=user_id,
            action="¡Regalo Diario Reclamado!"
        )

        # Besitos con descripción de racha
        streak_desc = f"Racha de {streak_days} día{'s' if streak_days != 1 else ''} 🔥"
        batch.add_besitos(besitos, streak_desc)

        # Badges desbloqueados
        for badge_id in new_badges:
            badge_def = container.gamification.config.get_badge_definition(badge_id)
            if badge_def:
                batch.add_badge(f"{badge_def.icon} {badge_def.name}", badge_def.description)

        # Si es nuevo récord, agregar mención especial
        if is_new_record:
            batch.add_custom("🏆", f"¡Nuevo récord personal: {streak_days} días!", "")

        # Enviar RewardBatch
        await container.notifications.send_reward_batch(batch)

        await callback.answer("✅ Regalo diario reclamado", show_alert=False)

        logger.info(
            f"✅ Daily login reclamado: User {user_id} | "
            f"Besitos: {besitos} | Streak: {streak_days}"
        )

    except ValueError as e:
        # Ya reclamó hoy
        await callback.answer(
            "⚠️ Ya reclamaste tu regalo diario hoy. ¡Vuelve mañana!",
            show_alert=True
        )
        logger.debug(f"⚠️ Usuario {user_id} ya reclamó hoy")

    except Exception as e:
        logger.error(f"❌ Error en daily login: {e}", exc_info=True)
        await callback.answer(
            "❌ Error al reclamar regalo. Intenta más tarde.",
            show_alert=True
        )
