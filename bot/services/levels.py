"""
Level Service - Gestión de niveles de usuario.

Maneja:
- CRUD de niveles
- Nivel actual de usuarios
- Verificación de level-up

NOTE: Implementación básica para SPRINT 1.
SPRINT 3 completará la funcionalidad completa.
"""
import logging
from typing import Tuple, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.gamification_models import UserLevel, UserPoints

logger = logging.getLogger(__name__)


class LevelService:
    """
    Servicio para gestión de niveles de usuario.

    Attributes:
        _session: Sesión de base de datos SQLAlchemy
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el LevelService.

        Args:
            session: Sesión de base de datos SQLAlchemy
        """
        self._session = session

    # ===== CRUD LEVELS =====

    async def get_all_levels(self) -> List[UserLevel]:
        """
        Obtiene todos los niveles.

        Returns:
            List[UserLevel]: Lista ordenada de niveles
        """
        result = await self._session.execute(
            select(UserLevel)
            .where(UserLevel.active == True)
            .order_by(UserLevel.min_points_required)
        )
        return list(result.scalars().all())

    async def get_level(self, level_id: int) -> Optional[UserLevel]:
        """
        Obtiene un nivel por ID.

        Args:
            level_id: ID del nivel

        Returns:
            UserLevel o None si no existe
        """
        result = await self._session.execute(
            select(UserLevel).where(UserLevel.id == level_id)
        )
        return result.scalar_one_or_none()

    # ===== USER LEVELS =====

    async def get_user_level(self, user_id: int) -> Optional[UserLevel]:
        """
        Obtiene el nivel actual de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            UserLevel o None si no tiene puntos

        NOTE: Implementación completa en SPRINT 3
        """
        # TODO: Implementar:
        # - Obtener puntos del usuario
        # - Buscar el nivel más alto con min_points <= user_points
        return None

    async def check_level_up(self, user_id: int) -> Tuple[bool, Optional[UserLevel]]:
        """
        Verifica si un usuario subió de nivel.

        Args:
            user_id: ID del usuario

        Returns:
            Tuple[bool, UserLevel]: (subió_de_nivel, nuevo_nivel)

        NOTE: Implementación completa en SPRINT 3
        """
        # TODO: Implementar:
        # - Obtener puntos actuales
        # - Buscar nivel correspondiente
        # - Comparar con último nivel registrado
        return False, None
