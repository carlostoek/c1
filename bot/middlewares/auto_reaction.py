"""
Auto Reaction Middleware - Reacciona automáticamente a TODOS los mensajes del usuario.

Cada vez que un usuario envía cualquier tipo de mensaje al bot (comando, respuesta, etc.),
el bot reacciona inmediatamente con ❤️.

Middleware global que se ejecuta para todos los mensajes.
"""
import logging
from typing import Any, Callable, Dict, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message

logger = logging.getLogger(__name__)


class AutoReactionMiddleware(BaseMiddleware):
    """
    Middleware que reacciona automáticamente a TODOS los mensajes con ❤️.

    Se aplica a nivel de mensaje (message.middleware).
    Ejecuta ANTES de cualquier handler.
    """

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        """
        Procesa el mensaje y reacciona automáticamente.

        Args:
            handler: Handler siguiente en la cadena
            event: Mensaje del usuario
            data: Datos contextuales

        Returns:
            Resultado del handler
        """
        # Auto-reaccionar AL INICIO con ❤️
        try:
            # Usar el método correcto de aiogram para reacciones
            from aiogram.types import ReactionTypeEmoji

            await event.bot.set_message_reaction(
                chat_id=event.chat.id,
                message_id=event.message_id,
                reaction=[ReactionTypeEmoji(emoji="❤️")],
                is_big=False
            )
            logger.debug(f"❤️ Reacción agregada al mensaje de {event.from_user.id}")
        except Exception as e:
            logger.debug(f"⚠️ No se pudo reaccionar al mensaje: {e}")

        # Continuar con el siguiente handler
        return await handler(event, data)
