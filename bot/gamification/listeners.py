"""
Gamification Listeners - Event listeners para gamificación.

Escucha eventos del Event Bus y otorga recompensas automáticamente.
"""
import logging
from datetime import datetime

from bot.events import (
    event_bus,
    subscribe,
    UserStartedBotEvent,
    UserJoinedVIPEvent,
    UserJoinedFreeChannelEvent,
    MessageReactedEvent,
    UserReferredEvent
)
from bot.database import get_session

logger = logging.getLogger(__name__)


class GamificationListeners:
    """
    Listeners de gamificación.

    Esta clase agrupa todos los event listeners que otorgan
    Besitos y recompensas automáticamente.
    """

    @staticmethod
    def register_all():
        """Registra todos los listeners del sistema."""
        logger.info("🎮 Registrando listeners de gamificación...")

        # Los decoradores @subscribe ya registran automáticamente
        # Esta función es solo para logging

        logger.info("✅ Listeners de gamificación registrados")


# ===== LISTENER: USER STARTED BOT =====

@subscribe(UserStartedBotEvent)
async def on_user_started_bot(event: UserStartedBotEvent):
    """
    Otorga Besitos de bienvenida cuando un usuario inicia el bot.

    Args:
        event: UserStartedBotEvent
    """
    # Solo dar Besitos si es usuario nuevo
    if not event.is_new:
        logger.debug(f"👋 Usuario {event.user_id} no es nuevo, skip reward")
        return

    logger.info(f"👋 Nuevo usuario: {event.user_id}, otorgando Besitos de bienvenida")

    async with get_session() as session:
        from aiogram import Bot
        from bot.config import settings
        from bot.services.container import ServiceContainer

        bot = Bot(token=settings.bot_token)
        container = ServiceContainer(session, bot)

        try:
            # Otorgar Besitos de bienvenida
            amount, ranked_up, new_rank = await container.gamification.award_besitos(
                user_id=event.user_id,
                action="user_started"
            )

            # Verificar badges
            new_badges = await container.gamification.check_and_unlock_badges(event.user_id)

            # Crear RewardBatch (aunque sea solo Besitos)
            batch = await container.notifications.create_reward_batch(
                user_id=event.user_id,
                action="¡Bienvenido/a al bot!"
            )

            batch.add_besitos(amount, "Regalo de bienvenida")

            if ranked_up:
                batch.add_rank_up("", new_rank)

            for badge_id in new_badges:
                badge_def = container.gamification.config.get_badge_definition(badge_id)
                if badge_def:
                    batch.add_badge(f"{badge_def.icon} {badge_def.name}", badge_def.description)

            # Enviar notificación unificada
            await container.notifications.send_reward_batch(batch)

            logger.info(f"✅ Recompensas de bienvenida enviadas: User {event.user_id}")

        except Exception as e:
            logger.error(f"❌ Error en listener user_started: {e}", exc_info=True)
        finally:
            await bot.session.close()


# ===== LISTENER: JOINED VIP =====

@subscribe(UserJoinedVIPEvent)
async def on_user_joined_vip(event: UserJoinedVIPEvent):
    """
    Otorga Besitos cuando un usuario activa VIP.

    Args:
        event: UserJoinedVIPEvent
    """
    logger.info(f"⭐ Usuario {event.user_id} activó VIP, otorgando Besitos")

    async with get_session() as session:
        from aiogram import Bot
        from bot.config import settings
        from bot.services.container import ServiceContainer

        bot = Bot(token=settings.bot_token)
        container = ServiceContainer(session, bot)

        try:
            # Otorgar Besitos VIP
            amount, ranked_up, new_rank = await container.gamification.award_besitos(
                user_id=event.user_id,
                action="joined_vip"
            )

            # Verificar badges (incluyendo badge de VIP)
            new_badges = await container.gamification.check_and_unlock_badges(event.user_id)

            # Crear RewardBatch
            batch = await container.notifications.create_reward_batch(
                user_id=event.user_id,
                action=f"¡Activaste tu suscripción VIP! ({event.plan_name})"
            )

            batch.add_besitos(amount, "Bono VIP")

            if ranked_up:
                batch.add_rank_up("Novato" if new_rank == "Bronce" else "", new_rank)

            for badge_id in new_badges:
                badge_def = container.gamification.config.get_badge_definition(badge_id)
                if badge_def:
                    batch.add_badge(f"{badge_def.icon} {badge_def.name}", badge_def.description)

            # Enviar
            await container.notifications.send_reward_batch(batch)

            logger.info(f"✅ Recompensas VIP enviadas: User {event.user_id}")

        except Exception as e:
            logger.error(f"❌ Error en listener joined_vip: {e}", exc_info=True)
        finally:
            await bot.session.close()


# ===== LISTENER: JOINED FREE CHANNEL =====

@subscribe(UserJoinedFreeChannelEvent)
async def on_user_joined_free_channel(event: UserJoinedFreeChannelEvent):
    """
    Otorga Besitos cuando un usuario ingresa al canal Free.

    Args:
        event: UserJoinedFreeChannelEvent
    """
    logger.info(f"🆓 Usuario {event.user_id} ingresó a canal Free, otorgando Besitos")

    async with get_session() as session:
        from aiogram import Bot
        from bot.config import settings
        from bot.services.container import ServiceContainer

        bot = Bot(token=settings.bot_token)
        container = ServiceContainer(session, bot)

        try:
            # Otorgar Besitos
            amount, ranked_up, new_rank = await container.gamification.award_besitos(
                user_id=event.user_id,
                action="joined_free_channel"
            )

            # Verificar badges
            new_badges = await container.gamification.check_and_unlock_badges(event.user_id)

            # Crear RewardBatch
            batch = await container.notifications.create_reward_batch(
                user_id=event.user_id,
                action="¡Ingresaste al canal Free!"
            )

            batch.add_besitos(amount, "Bono de ingreso")

            if ranked_up:
                batch.add_rank_up("", new_rank)

            for badge_id in new_badges:
                badge_def = container.gamification.config.get_badge_definition(badge_id)
                if badge_def:
                    batch.add_badge(f"{badge_def.icon} {badge_def.name}", badge_def.description)

            # Enviar
            await container.notifications.send_reward_batch(batch)

            logger.info(f"✅ Recompensas Free enviadas: User {event.user_id}")

        except Exception as e:
            logger.error(f"❌ Error en listener joined_free: {e}", exc_info=True)
        finally:
            await bot.session.close()


# ===== LISTENER: MESSAGE REACTED =====

@subscribe(MessageReactedEvent)
async def on_message_reacted(event: MessageReactedEvent):
    """
    Otorga Besitos cuando un usuario reacciona a un mensaje.

    Args:
        event: MessageReactedEvent
    """
    logger.info(
        f"❤️ Usuario {event.user_id} reaccionó ({event.reaction_type}) "
        f"al mensaje {event.message_id}"
    )

    async with get_session() as session:
        from aiogram import Bot
        from bot.config import settings
        from bot.services.container import ServiceContainer

        bot = Bot(token=settings.bot_token)
        container = ServiceContainer(session, bot)

        try:
            # Verificar rate limiting
            can_react = await container.gamification.can_react_to_message(event.user_id)

            if not can_react:
                logger.debug(f"⚠️ Usuario {event.user_id} en rate limit, no otorgar Besitos")
                return

            # Registrar reacción
            await container.gamification.record_reaction(event.user_id)

            # Otorgar Besitos base
            amount, ranked_up, new_rank = await container.gamification.award_besitos(
                user_id=event.user_id,
                action="message_reacted"
            )

            # Bonus si es primera reacción del día
            progress = await container.gamification.get_or_create_progress(event.user_id)

            bonus_amount = 0
            if progress.reactions_today == 1:  # Acaba de ser la primera
                bonus_amount, _, _ = await container.gamification.award_besitos(
                    user_id=event.user_id,
                    action="first_reaction_of_day"
                )

            # Verificar badges
            new_badges = await container.gamification.check_and_unlock_badges(event.user_id)

            # Crear RewardBatch
            batch = await container.notifications.create_reward_batch(
                user_id=event.user_id,
                action=f"Reaccionaste con {event.reaction_type}"
            )

            total_besitos = amount + bonus_amount
            reason = "Reacción" + (" (primera del día)" if bonus_amount > 0 else "")
            batch.add_besitos(total_besitos, reason)

            if ranked_up:
                batch.add_rank_up("", new_rank)

            for badge_id in new_badges:
                badge_def = container.gamification.config.get_badge_definition(badge_id)
                if badge_def:
                    batch.add_badge(f"{badge_def.icon} {badge_def.name}", badge_def.description)

            # Enviar
            await container.notifications.send_reward_batch(batch)

            logger.info(
                f"✅ Recompensas de reacción enviadas: User {event.user_id} | "
                f"Besitos: {total_besitos}"
            )

        except Exception as e:
            logger.error(f"❌ Error en listener message_reacted: {e}", exc_info=True)
        finally:
            await bot.session.close()


# ===== LISTENER: USER REFERRED =====

@subscribe(UserReferredEvent)
async def on_user_referred(event: UserReferredEvent):
    """
    Otorga Besitos cuando un usuario refiere a otro.

    Args:
        event: UserReferredEvent
    """
    logger.info(
        f"👥 Usuario {event.referrer_id} refirió a {event.referred_id}, "
        f"otorgando Besitos"
    )

    async with get_session() as session:
        from aiogram import Bot
        from bot.config import settings
        from bot.services.container import ServiceContainer

        bot = Bot(token=settings.bot_token)
        container = ServiceContainer(session, bot)

        try:
            # Otorgar Besitos al referrer
            amount, ranked_up, new_rank = await container.gamification.award_besitos(
                user_id=event.referrer_id,
                action="referral_success"
            )

            # Verificar badges
            new_badges = await container.gamification.check_and_unlock_badges(event.referrer_id)

            # Crear RewardBatch
            batch = await container.notifications.create_reward_batch(
                user_id=event.referrer_id,
                action="¡Tu amigo/a se unió usando tu link!"
            )

            batch.add_besitos(amount, "Referido exitoso")

            if ranked_up:
                batch.add_rank_up("", new_rank)

            for badge_id in new_badges:
                badge_def = container.gamification.config.get_badge_definition(badge_id)
                if badge_def:
                    batch.add_badge(f"{badge_def.icon} {badge_def.name}", badge_def.description)

            # Enviar
            await container.notifications.send_reward_batch(batch)

            logger.info(f"✅ Recompensas de referral enviadas: User {event.referrer_id}")

        except Exception as e:
            logger.error(f"❌ Error en listener user_referred: {e}", exc_info=True)
        finally:
            await bot.session.close()
