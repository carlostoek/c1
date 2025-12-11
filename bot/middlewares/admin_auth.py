"""
Admin Auth Middleware - Valida que el usuario tenga permisos de admin.

Se aplica a handlers que requieren permisos administrativos.
Si el usuario no es admin, responde con mensaje de error y no ejecuta el handler.
"""
import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from config import Config

logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    """Verifica si un usuario es administrador.

    Args:
        user_id: ID de usuario de Telegram a verificar

    Returns:
        True si el usuario es administrador, False en caso contrario
    """
    return Config.is_admin(user_id)


class AdminAuthMiddleware(BaseMiddleware):
    """
    Middleware que valida permisos de administrador.

    Uso:
        # En el router de admin:
        admin_router.message.middleware(AdminAuthMiddleware())
        admin_router.callback_query.middleware(AdminAuthMiddleware())

    Si el usuario no es admin:
    - Envía mensaje de error
    - No ejecuta el handler
    - Loguea el intento
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Ejecuta el middleware.

        Args:
            handler: Handler a ejecutar si pasa validación
            event: Evento de Telegram (Message, CallbackQuery, etc)
            data: Data del handler (incluye bot, session, etc)

        Returns:
            Resultado del handler si es admin, None si no
        """
        # Extraer user del event
        user = None

        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user

        if user is None:
            # No se pudo extraer usuario (edge case raro)
            logger.warning("⚠️ No se pudo extraer usuario del evento")
            return await handler(event, data)

        # Verificar si es admin
        if not Config.is_admin(user.id):
            # Usuario no es admin
            logger.warning(
                f"🚫 Acceso denegado: user {user.id} (@{user.username or 'sin username'}) "
                f"intentó acceder a handler admin"
            )

            # Enviar mensaje de error
            error_message = (
                "🚫 <b>Acceso Denegado</b>\n\n"
                "Este comando es solo para administradores."
            )

            if isinstance(event, Message):
                await event.answer(error_message, parse_mode="HTML")
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    "🚫 Acceso denegado: solo administradores",
                    show_alert=True
                )

            # No ejecutar handler
            return None

        # Usuario es admin: ejecutar handler normalmente
        logger.debug(f"✅ Admin verificado: user {user.id}")
        return await handler(event, data)
