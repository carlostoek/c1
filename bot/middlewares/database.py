"""
Database Middleware - Inyecta sesión de base de datos en handlers.

Proporciona una sesión de SQLAlchemy a cada handler automáticamente.
"""
import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram.exceptions import TelegramNetworkError, TelegramBadRequest

from bot.database import get_session
from bot.gamification.services import GamificationContainer, set_container

logger = logging.getLogger(__name__)


def get_db_session():
    """Obtiene una sesión de base de datos para su uso en handlers.

    Returns:
        Context manager para una sesión de base de datos
    """
    return get_session()


class DatabaseMiddleware(BaseMiddleware):
    """
    Middleware que inyecta sesión de base de datos y containers de servicios.

    Uso:
        dispatcher.update.middleware(DatabaseMiddleware())

    El handler recibe automáticamente:
        async def handler(message: Message, session: AsyncSession, gamification: GamificationContainer):
            # session y gamification están disponibles
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
        Crea GamificationContainer y lo inyecta en data["gamification"].
        El handler puede acceder a ellos como parámetros.

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

            # Crear y configurar GamificationContainer
            gamif_container = GamificationContainer(session)
            set_container(gamif_container)  # Establecer como instancia global
            data["gamification"] = gamif_container

            try:
                # Ejecutar handler
                return await handler(event, data)
            except (TelegramNetworkError, TelegramBadRequest) as e:
                # Errores de red/Telegram - loguear como WARNING (no son errores del handler)
                logger.warning(
                    f"⚠️ Error de Telegram en handler: {type(e).__name__}: {e}"
                )
                raise
            except Exception as e:
                # Otros errores - loguear como ERROR
                logger.error(f"❌ Error en handler con sesión DB: {e}", exc_info=True)
                raise
