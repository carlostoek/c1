"""
Reactions Handler - Manejo de reacciones inline.
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.gamification.reactions import ReactionSystem
from bot.events import event_bus, MessageReactedEvent

logger = logging.getLogger(__name__)

reactions_router = Router()


@reactions_router.callback_query(F.data.startswith("react:"))
async def callback_reaction(
    callback: CallbackQuery,
    session: AsyncSession
):
    """
    Handler para reacciones inline.

    Args:
        callback: Callback query
        session: Sesión de BD
    """
    user_id = callback.from_user.id

    try:
        # Parsear callback
        reaction_type, message_id, channel_id = ReactionSystem.parse_reaction_callback(
            callback.data
        )

        logger.info(
            f"❤️ Reacción: User {user_id} | Tipo: {reaction_type} | "
            f"Message: {message_id} | Channel: {channel_id}"
        )

        # Emitir evento (el listener otorgará Besitos)
        await event_bus.publish(MessageReactedEvent(
            user_id=user_id,
            message_id=message_id,
            channel_id=channel_id,
            reaction_type=reaction_type,
            is_first_reaction=True
        ))

        # Responder al usuario
        await callback.answer(
            f"¡Gracias por reaccionar! 💋",
            show_alert=False
        )

    except ValueError as e:
        logger.error(f"❌ Callback inválido: {callback.data} - {e}")
        await callback.answer("❌ Error", show_alert=False)

    except Exception as e:
        logger.error(f"❌ Error en reacción: {e}", exc_info=True)
        await callback.answer("❌ Error al procesar reacción", show_alert=False)
