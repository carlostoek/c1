"""
Typing Indicator Middleware - Envía typing indicator ANTES de responder.

Cada vez que el bot va a procesar un mensaje/update del usuario y posiblemente responder,
envía la acción "typing" para mostrar que está escribiendo.

Middleware global que se ejecuta para todos los mensajes y callbacks.
"""
import logging
from typing import Any, Callable, Dict, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update

logger = logging.getLogger(__name__)


class TypingIndicatorMiddleware(BaseMiddleware):
    """
    Middleware que envía typing indicator AUTOMÁTICAMENTE a TODOS los updates.

    Se aplica a nivel de mensaje y callback query.
    Ejecuta ANTES de cualquier handler.
    """

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        """
        Procesa el evento y envía typing indicator.

        Args:
            handler: Handler siguiente en la cadena
            event: Evento (Message o CallbackQuery)
            data: Datos contextuales

        Returns:
            Resultado del handler
        """
        chat_id = None
        bot = data.get("bot") if "bot" in data else None

        # Obtener chat_id y bot según el tipo de evento
        if isinstance(event, Message):
            chat_id = event.chat.id
            if not bot:
                bot = event.bot
        elif isinstance(event, CallbackQuery):
            chat_id = event.message.chat.id if event.message else None
            if not bot:
                bot = event.bot

        # Enviar typing indicator AL INICIO
        if chat_id and bot:
            try:
                await bot.send_chat_action(
                    chat_id=chat_id,
                    action="typing"
                )
                logger.debug(f"⏳ Typing indicator enviado a chat {chat_id}")
            except Exception as e:
                logger.debug(f"⚠️ No se pudo enviar typing indicator: {e}")

        # Continuar con el siguiente handler
        return await handler(event, data)
