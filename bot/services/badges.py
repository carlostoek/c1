"""
Badge Service - Gestión de badges/insignias.

Maneja:
- CRUD de badges
- Otorgar badges a usuarios
- Consultar badges de usuarios

NOTE: Implementación básica para SPRINT 1.
SPRINT 3 completará la funcionalidad completa.
"""
import logging
from typing import List, Tuple, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.gamification_models import Badge, UserBadge
from bot.database.enums import BadgeRarity

logger = logging.getLogger(__name__)


class BadgeService:
    """
    Servicio para gestión de badges.

    Attributes:
        _session: Sesión de base de datos SQLAlchemy
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el BadgeService.

        Args:
            session: Sesión de base de datos SQLAlchemy
        """
        self._session = session

    # ===== CRUD BADGES =====

    async def get_all_badges(self, active_only: bool = True) -> List[Badge]:
        """
        Obtiene todos los badges.

        Args:
            active_only: Solo badges activos

        Returns:
            List[Badge]: Lista de badges
        """
        query = select(Badge)

        if active_only:
            query = query.where(Badge.active == True)

        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_badge(self, badge_id: int) -> Optional[Badge]:
        """
        Obtiene un badge por ID.

        Args:
            badge_id: ID del badge

        Returns:
            Badge o None si no existe
        """
        result = await self._session.execute(
            select(Badge).where(Badge.id == badge_id)
        )
        return result.scalar_one_or_none()

    # ===== USER BADGES =====

    async def get_user_badges(self, user_id: int) -> List[UserBadge]:
        """
        Obtiene badges desbloqueados por un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            List[UserBadge]: Lista de badges desbloqueados
        """
        result = await self._session.execute(
            select(UserBadge)
            .where(UserBadge.user_id == user_id)
            .order_by(UserBadge.unlocked_at.desc())
        )
        return list(result.scalars().all())

    async def has_badge(self, user_id: int, badge_id: int) -> bool:
        """
        Verifica si un usuario tiene un badge.

        Args:
            user_id: ID del usuario
            badge_id: ID del badge

        Returns:
            bool: True si tiene el badge
        """
        result = await self._session.execute(
            select(UserBadge)
            .where(
                UserBadge.user_id == user_id,
                UserBadge.badge_id == badge_id
            )
        )
        return result.scalar_one_or_none() is not None

    # ===== OTORGAR BADGES =====

    async def award_badge(
        self,
        user_id: int,
        badge_id: int
    ) -> Tuple[bool, str]:
        """
        Otorga un badge a un usuario.

        Args:
            user_id: ID del usuario
            badge_id: ID del badge a otorgar

        Returns:
            Tuple[bool, str]: (éxito, mensaje)

        NOTE: Implementación completa en SPRINT 3
        """
        # TODO: Implementar:
        # - Verificar que badge existe
        # - Verificar que no lo tiene
        # - Crear UserBadge
        # - Notificar usuario
        return False, "Implementación pendiente (SPRINT 3)"
