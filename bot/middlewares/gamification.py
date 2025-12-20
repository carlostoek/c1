"""
Gamification Middleware - Inyecta contenedores de servicios de gamificación en handlers.

Proporciona los contenedores de servicios de gamificación a cada handler automáticamente.
"""
import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.gamification.services.container import GamificationContainer

logger = logging.getLogger(__name__)


class GamificationMiddleware(BaseMiddleware):
    """
    Middleware que inyecta contenedores de servicios de gamificación.

    Uso:
        router.message.middleware(GamificationMiddleware())

    El handler recibe automáticamente:
        async def handler(message: Message, gamification: GamificationContainer):
            # gamification está disponible
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

        Crea contenedores de servicios de gamificación y los inyecta en data.
        El handler puede acceder a ellos como parámetros.

        Args:
            handler: Handler a ejecutar
            event: Evento de Telegram
            data: Data del handler

        Returns:
            Resultado del handler
        """
        # Obtener la sesión de la data (debe haber sido inyectada previamente por DatabaseMiddleware)
        session = data.get("session")
        if session is None:
            logger.error("GamificationMiddleware requiere que DatabaseMiddleware esté registrado antes")
            raise RuntimeError("Session no encontrada en data. DatabaseMiddleware debe estar registrado antes de GamificationMiddleware")

        # Crear contenedor de gamificación
        gamification = GamificationContainer(session)

        # Inyectar contenedores en data
        data["gamification"] = gamification

        try:
            # Ejecutar handler
            return await handler(event, data)
        except Exception as e:
            # Loguear errores
            logger.error(f"Error en handler con gamificación: {e}", exc_info=True)
            raise