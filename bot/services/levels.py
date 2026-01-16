"""
Level Service - Gestión de niveles de usuario.

Maneja:
- CRUD de niveles
- Nivel actual de usuarios
- Verificación de level-up
"""
import logging
from typing import Tuple, Optional

from sqlalchemy import select, and_
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
        """
        # Obtener puntos del usuario
        result = await self._session.execute(
            select(UserPoints).where(UserPoints.user_id == user_id)
        )
        points = result.scalar_one_or_none()

        if points is None or points.balance == 0:
            return None

        # Buscar el nivel más alto con min_points <= user_points
        result = await self._session.execute(
            select(UserLevel)
            .where(
                and_(
                    UserLevel.active == True,
                    UserLevel.min_points_required <= points.balance
                )
            )
            .order_by(UserLevel.min_points_required.desc())
            .limit(1)
        )

        return result.scalar_one_or_none()

    async def check_level_up(self, user_id: int) -> Tuple[bool, Optional[UserLevel]]:
        """
        Verifica si un usuario subió de nivel.

        Args:
            user_id: ID del usuario

        Returns:
            Tuple[bool, UserLevel]: (subió_de_nivel, nuevo_nivel)
        """
        current_level = await self.get_user_level(user_id)

        if current_level is None:
            return False, None

        # Obtener puntos para verificar el nivel registrado
        result = await self._session.execute(
            select(UserPoints).where(UserPoints.user_id == user_id)
        )
        points = result.scalar_one_or_none()

        if points is None:
            return False, None

        # Si el nivel actual es mayor que el registrado, hubo level-up
        # (Este método es simple, una implementación más compleja
        #  podría guardar last_level_id en UserPoints)

        # Por ahora, retornamos True si tiene nivel
        # En el futuro se podría comparar con last_level_id
        return True, current_level
