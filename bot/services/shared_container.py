"""Shared container para inyección de dependencias compartida entre módulos.

Este archivo permite que el módulo de gamificación y el sistema core compartan
servicios y recursos sin crear dependencias circulares.
"""

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from aiogram import Bot
    from bot.gamification.services.container import GamificationContainer


class SharedContainer:
    """Contenedor compartido de servicios entre módulos."""

    _instance: Optional["SharedContainer"] = None
    _gamification_container: Optional["GamificationContainer"] = None

    def __init__(self):
        """Inicializa el contenedor compartido."""
        self._gamification_container = None

    @classmethod
    def get_instance(cls) -> "SharedContainer":
        """Obtiene la instancia singleton del contenedor compartido."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def gamification(self) -> "GamificationContainer":
        """Accede al contenedor de gamificación de forma lazy."""
        if self._gamification_container is None:
            from bot.gamification.services.container import GamificationContainer
            self._gamification_container = GamificationContainer()
        return self._gamification_container

    async def initialize_gamification(self, session: "AsyncSession", bot: "Bot") -> None:
        """Inicializa el contenedor de gamificación con dependencias.

        Args:
            session: Sesión de base de datos async
            bot: Instancia del bot de Aiogram
        """
        from bot.gamification.services.container import GamificationContainer
        self._gamification_container = GamificationContainer(session, bot)


# Instancia global del contenedor compartido
shared_container = SharedContainer.get_instance()
