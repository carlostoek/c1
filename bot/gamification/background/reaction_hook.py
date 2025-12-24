"""
Hook de eventos de reacción para gamificación.

Integra reacciones de Telegram con sistema de gamificación.
"""

from datetime import datetime, UTC
from aiogram import Router, Bot
from aiogram.types import MessageReactionUpdated
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from bot.gamification.services.container import GamificationContainer

logger = logging.getLogger(__name__)
router = Router(name="gamification_reactions")


@router.message_reaction()
async def on_reaction_event(
    update: MessageReactionUpdated,
    session: AsyncSession,
    bot: Bot
):
    """
    Procesa evento de reacción.

    Flujo:
    1. Validar que haya usuario y reacciones nuevas
    2. Obtener emoji(s) añadidos
    3. Llamar reaction_service.record_reaction()
    4. Verificar auto level-up
    5. Actualizar progreso de misiones

    Args:
        update: Evento de reacción de Telegram
        session: Sesión de base de datos
    """

    # Obtener datos básicos
    user_id = update.user.id if update.user else None

    if not user_id:
        logger.debug("Reaction without user_id, skipping")
        return

    chat_id = update.chat.id
    message_id = update.message_id

    # Obtener reacciones nuevas
    new_reactions = update.new_reaction
    if not new_reactions:
        logger.debug(f"No new reactions for user {user_id}")
        return

    # Crear container de gamificación
    gamification = GamificationContainer(session, bot)

    # Procesar cada emoji añadido
    for reaction in new_reactions:
        # Verificar que sea una reacción de emoji (no custom emoji)
        if hasattr(reaction, 'emoji') and reaction.emoji:
            emoji = reaction.emoji

            try:
                # Registrar reacción en el sistema de gamificación
                success, message, besitos = await gamification.reaction.record_reaction(
                    user_id=user_id,
                    emoji=emoji,
                    channel_id=chat_id,
                    message_id=message_id
                )

                if success:
                    logger.info(
                        f"Reaction recorded: User {user_id} reacted with {emoji} "
                        f"(+{besitos} besitos) in chat {chat_id}"
                    )

                    # Verificar y aplicar level-up automático
                    changed, old_level, new_level = await gamification.level.check_and_apply_level_up(
                        user_id
                    )
                    if changed:
                        logger.info(
                            f"Auto level-up triggered: User {user_id} "
                            f"{old_level.name} → {new_level.name}"
                        )
                        # Notificar level-up
                        await gamification.notifications.notify_level_up(
                            user_id, old_level, new_level
                        )

                    # Actualizar progreso de misiones
                    completed_missions = await gamification.mission.on_user_reaction(
                        user_id=user_id,
                        emoji=emoji,
                        reacted_at=update.date
                    )

                    # Notificar misiones completadas
                    if completed_missions:
                        logger.info(
                            f"Missions completed: User {user_id} "
                            f"({len(completed_missions)} mission(s) completed)"
                        )

                        for user_mission, mission in completed_missions:
                            await gamification.notifications.notify_mission_completed(
                                user_id, mission
                            )

                else:
                    logger.warning(
                        f"Reaction not recorded: User {user_id} {emoji} - {message}"
                    )

            except Exception as e:
                logger.error(
                    f"Error processing reaction: User {user_id} {emoji} - {e}",
                    exc_info=True
                )
                # Continue processing other reactions even if one fails


async def is_valid_reaction(update: MessageReactionUpdated) -> bool:
    """
    Valida que reacción sea procesable.

    Validaciones básicas:
    - Usuario existe
    - Hay reacciones nuevas
    - Es una reacción de emoji (no custom)

    Args:
        update: Evento de reacción

    Returns:
        True si la reacción es válida, False si no
    """
    # Verificar usuario
    if not update.user or not update.user.id:
        return False

    # Verificar que haya reacciones nuevas
    if not update.new_reaction:
        return False

    # Verificar que al menos una sea emoji (no custom)
    has_emoji = any(
        hasattr(reaction, 'emoji') and reaction.emoji
        for reaction in update.new_reaction
    )

    return has_emoji
