"""
Database Middleware - Inyecta sesión de base de datos en handlers.

Proporciona una sesión de SQLAlchemy a cada handler automáticamente.
"""
import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.database import get_session

logger = logging.getLogger(__name__)


def get_db_session():
    """Obtiene una sesión de base de datos para su uso en handlers.

    Returns:
        Context manager para una sesión de base de datos
    """
    return get_session()


class DatabaseMiddleware(BaseMiddleware):
    """
    Middleware que inyecta sesión de base de datos.

    Uso:
        dispatcher.update.middleware(DatabaseMiddleware())

    El handler recibe automáticamente:
        async def handler(message: Message, session: AsyncSession):
            # session está disponible
            pass
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Ejecuta el middleware.

        Crea una sesión de base de datos y la inyecta en data["session"].
        El handler puede acceder a ella como parámetro.

        Args:
            handler: Handler a ejecutar
            event: Evento de Telegram
            data: Data del handler

        Returns:
            Resultado del handler
        """
        # Crear sesión y ejecutar handler dentro del contexto
        async with get_session() as session:
            # Inyectar sesión en data
            data["session"] = session

            try:
                # Ejecutar handler
                return await handler(event, data)
            except Exception as e:
                # Loguear error pero dejar que se propague
                logger.error(f"❌ Error en handler con sesión DB: {e}", exc_info=True)
                raise
