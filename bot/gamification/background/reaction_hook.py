"""
Hook de eventos de reacción para gamificación.

Integra reacciones de Telegram con sistema de gamificación.
"""

from datetime import datetime, UTC
from aiogram import Router
from aiogram.types import MessageReactionUpdated
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from bot.gamification.services.container import GamificationContainer
from bot.services.container import ServiceContainer
from bot.middlewares import DatabaseMiddleware, GamificationMiddleware

logger = logging.getLogger(__name__)
router = Router(name="reaction_hook")

# Aplicar middlewares (debe estar en este orden: Database primero, Gamification después)
router.message_reaction.middleware(DatabaseMiddleware())
router.message_reaction.middleware(GamificationMiddleware())


@router.message_reaction()
async def on_reaction_event(
    update: MessageReactionUpdated,
    session: AsyncSession,
    gamification: GamificationContainer
):
    """Procesa evento de reacción."""

    # Obtener datos
    user_id = update.user.id if update.user else None
    chat_id = update.chat.id
    message_id = update.message_id

    if not user_id:
        return

    # Validar que sea canal configurado
    # Note: This validation needs to be handled differently since we don't have the full service container
    # For now, we'll implement validation that doesn't require ServiceContainer
    is_valid = await is_valid_reaction(update, session, gamification)
    if not is_valid:
        return
    
    # Obtener emojis añadidos
    new_reactions = update.new_reaction
    if not new_reactions:
        return
    
    # Procesar cada emoji
    for reaction in new_reactions:
        if hasattr(reaction, 'emoji'):
            emoji = reaction.emoji
            
            try:
                # Registrar reacción
                success, message, besitos = await gamification.reaction.record_reaction(
                    user_id=user_id,
                    emoji=emoji,
                    message_id=message_id,
                    channel_id=chat_id,
                    reacted_at=datetime.now(UTC)
                )
                
                if success:
                    logger.info(f"Reaction recorded: User {user_id} {emoji} (+{besitos} besitos)")
                    
                    # Auto level-up
                    changed, old_level, new_level = await gamification.level.check_and_apply_level_up(user_id)
                    if changed:
                        logger.info(f"Level-up: User {user_id} → {new_level.name}")
                    
                    # Actualizar progreso de misiones
                    await gamification.mission.on_user_reaction(
                        user_id=user_id,
                        emoji=emoji,
                        reacted_at=datetime.now(UTC)
                    )
                else:
                    logger.warning(f"Reaction failed: User {user_id} - {message}")
            
            except Exception as e:
                logger.error(f"Error processing reaction: {e}")


async def is_valid_reaction(
    update: MessageReactionUpdated,
    session: AsyncSession,
    gamification: GamificationContainer
) -> bool:
    """Valida que reacción sea procesable."""

    # We need to access channel and subscription services
    # This requires importing the main ServiceContainer directly
    from bot.services.container import ServiceContainer
    from aiogram import Bot

    # We need to get the bot instance somehow.
    # For now, let's implement a different approach by using direct database queries
    # to check if the channel is one of our configured channels.

    # For now, we'll use a direct database query approach
    # Import the required model
    from bot.database.models import Channel

    stmt = select(Channel).where(Channel.chat_id == update.chat.id)
    result = await session.execute(stmt)
    channel = result.scalar_one_or_none()

    if not channel:
        return False

    # For VIP channels, we should check if user has access
    # This requires another query to check access status
    if channel.is_vip:
        from bot.database.models import VipSubscription
        from datetime import datetime, UTC

        current_time = datetime.now(UTC)

        # Check if user has an active VIP subscription
        sub_stmt = select(VipSubscription).where(
            VipSubscription.user_id == update.user.id,
            VipSubscription.ends_at > current_time,
            VipSubscription.active == True
        )
        sub_result = await session.execute(sub_stmt)
        subscription = sub_result.scalar_one_or_none()

        if not subscription:
            return False

    return True