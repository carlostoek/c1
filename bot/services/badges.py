"""
BadgesService - Gestión de insignias del sistema de gamificación.

Responsabilidades:
- Asignación de badges a usuarios
- Consulta de colecciones personales
- Catálogo completo de badges
- Verificación de posesión
"""
import logging
from typing import List, Optional, Dict

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import Badge, UserBadge, BadgeRarity

logger = logging.getLogger(__name__)


class BadgesService:
    """
    Servicio de gestión de insignias.

    Métodos principales:
    - assign_badge(): Otorgar badge a usuario
    - get_user_badges(): Obtener colección del usuario
    - get_badge_by_id(): Obtener badge específico
    - has_badge(): Verificar si usuario tiene badge
    - get_all_badges(): Obtener catálogo completo
    - count_user_badges(): Contar badges del usuario
    """

    def __init__(self, session: AsyncSession, container=None):
        """
        Inicializa el servicio.

        Args:
            session: AsyncSession para operaciones de BD
            container: ServiceContainer para acceso a otros servicios
        """
        self._session = session
        self._container = container
        self._logger = logging.getLogger(__name__)

    # ===== ASIGNACIÓN =====

    async def assign_badge(
        self,
        user_id: int,
        badge_id: int,
        source: Optional[str] = None
    ) -> Optional[UserBadge]:
        """
        Otorga un badge a un usuario.

        Solo asigna si el usuario no posee el badge y está activo.

        Args:
            user_id: ID del usuario
            badge_id: ID del badge
            source: Origen del badge (mission/reward/achievement/etc)

        Returns:
            UserBadge creado o None si ya lo tiene o no existe

        Raises:
            Captura excepciones internamente
        """
        try:
            # Verificar si ya lo tiene
            has_it = await self.has_badge(user_id, badge_id)
            if has_it:
                self._logger.debug(
                    f"User {user_id} already has badge {badge_id}"
                )
                return None

            # Verificar que badge existe y está activo
            badge = await self.get_badge_by_id(badge_id)
            if not badge or not badge.is_active:
                self._logger.warning(
                    f"Badge {badge_id} not found or inactive"
                )
                return None

            # Crear UserBadge
            user_badge = UserBadge(
                user_id=user_id,
                badge_id=badge_id,
                source=source
            )
            self._session.add(user_badge)
            await self._session.flush()
            await self._session.commit()
            await self._session.refresh(user_badge)

            self._logger.info(
                f"Badge assigned: user={user_id}, badge={badge.name}, "
                f"source={source}"
            )

            return user_badge

        except Exception as e:
            await self._session.rollback()
            self._logger.error(f"Error assigning badge: {e}", exc_info=True)
            return None

    async def revoke_badge(self, user_id: int, badge_id: int) -> bool:
        """
        Revoca un badge de un usuario.

        Args:
            user_id: ID del usuario
            badge_id: ID del badge

        Returns:
            True si fue revocado, False si no lo tenía o hubo error
        """
        try:
            stmt = select(UserBadge).where(
                and_(
                    UserBadge.user_id == user_id,
                    UserBadge.badge_id == badge_id
                )
            )
            result = await self._session.execute(stmt)
            user_badge = result.scalar_one_or_none()

            if user_badge is None:
                return False

            await self._session.delete(user_badge)
            await self._session.commit()
            self._logger.info(
                f"Badge revoked: user={user_id}, badge_id={badge_id}"
            )
            return True

        except Exception as e:
            await self._session.rollback()
            self._logger.error(f"Error revoking badge: {e}", exc_info=True)
            return False

    # ===== CONSULTAS =====

    async def has_badge(self, user_id: int, badge_id: int) -> bool:
        """
        Verifica si un usuario posee un badge.

        Args:
            user_id: ID del usuario
            badge_id: ID del badge

        Returns:
            True si lo tiene, False si no o si hay error
        """
        try:
            stmt = select(UserBadge).where(
                and_(
                    UserBadge.user_id == user_id,
                    UserBadge.badge_id == badge_id
                )
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            self._logger.error(f"Error checking badge: {e}", exc_info=True)
            return False

    async def get_user_badges(
        self,
        user_id: int,
        rarity: Optional[BadgeRarity] = None
    ) -> List[UserBadge]:
        """
        Obtiene badges del usuario.

        Retorna ordenados por rareza (legendario primero) y fecha de obtención.

        Args:
            user_id: ID del usuario
            rarity: Filtrar por rareza específica (opcional)

        Returns:
            Lista de UserBadge ordenada
        """
        try:
            stmt = select(UserBadge).where(
                UserBadge.user_id == user_id
            )
            result = await self._session.execute(stmt)
            user_badges = result.scalars().all()

            # Filtrar por rareza si se especifica
            if rarity:
                user_badges = [
                    ub for ub in user_badges
                    if ub.badge.rarity == rarity
                ]

            # Ordenar por rareza (legendario primero) y fecha (más reciente primero)
            rarity_order = {
                BadgeRarity.LEGENDARY: 0,
                BadgeRarity.EPIC: 1,
                BadgeRarity.RARE: 2,
                BadgeRarity.COMMON: 3
            }

            user_badges = sorted(
                user_badges,
                key=lambda ub: (
                    rarity_order.get(ub.badge.rarity, 4),
                    -ub.earned_at.timestamp()
                )
            )

            return user_badges

        except Exception as e:
            self._logger.error(
                f"Error getting user badges: {e}", exc_info=True
            )
            return []

    async def get_badge_by_id(self, badge_id: int) -> Optional[Badge]:
        """
        Obtiene un badge por su ID.

        Args:
            badge_id: ID del badge

        Returns:
            Badge o None si no existe
        """
        try:
            stmt = select(Badge).where(Badge.id == badge_id)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            self._logger.error(f"Error getting badge: {e}", exc_info=True)
            return None

    async def get_badge_by_name(self, name: str) -> Optional[Badge]:
        """
        Obtiene un badge por su nombre.

        Args:
            name: Nombre del badge

        Returns:
            Badge o None si no existe
        """
        try:
            stmt = select(Badge).where(Badge.name == name)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            self._logger.error(
                f"Error getting badge by name: {e}", exc_info=True
            )
            return None

    async def get_all_badges(
        self,
        include_secret: bool = False,
        include_inactive: bool = False
    ) -> List[Badge]:
        """
        Obtiene el catálogo completo de badges.

        Retorna ordenados por rareza (legendario primero).

        Args:
            include_secret: Incluir badges secretos
            include_inactive: Incluir badges inactivos

        Returns:
            Lista de Badge ordenada
        """
        try:
            stmt = select(Badge)

            if not include_inactive:
                stmt = stmt.where(Badge.is_active == True)

            if not include_secret:
                stmt = stmt.where(Badge.is_secret == False)

            result = await self._session.execute(stmt)
            badges = result.scalars().all()

            # Ordenar por rareza (legendario primero)
            rarity_order = {
                BadgeRarity.LEGENDARY: 0,
                BadgeRarity.EPIC: 1,
                BadgeRarity.RARE: 2,
                BadgeRarity.COMMON: 3
            }

            badges = sorted(
                badges,
                key=lambda b: rarity_order.get(b.rarity, 4)
            )

            return badges

        except Exception as e:
            self._logger.error(f"Error getting badges: {e}", exc_info=True)
            return []

    async def count_user_badges(
        self,
        user_id: int,
        rarity: Optional[BadgeRarity] = None
    ) -> int:
        """
        Cuenta la cantidad de badges del usuario.

        Args:
            user_id: ID del usuario
            rarity: Contar solo de una rareza específica (opcional)

        Returns:
            Cantidad de badges
        """
        try:
            badges = await self.get_user_badges(user_id, rarity)
            return len(badges)
        except Exception as e:
            self._logger.error(
                f"Error counting badges: {e}", exc_info=True
            )
            return 0

    async def get_badges_by_rarity(
        self,
        user_id: int,
        rarity: BadgeRarity
    ) -> List[UserBadge]:
        """
        Obtiene badges de una rareza específica.

        Args:
            user_id: ID del usuario
            rarity: Rareza a filtrar

        Returns:
            Lista de UserBadge de esa rareza
        """
        return await self.get_user_badges(user_id, rarity)

    # ===== ADMIN =====

    async def create_badge(
        self,
        name: str,
        description: str,
        emoji: str,
        rarity: BadgeRarity = BadgeRarity.COMMON,
        is_secret: bool = False,
        metadata: Optional[Dict] = None
    ) -> Optional[Badge]:
        """
        Crea un nuevo badge (operación admin).

        Args:
            name: Nombre único del badge
            description: Descripción
            emoji: Emoji representativo
            rarity: Rareza del badge
            is_secret: Si está oculto hasta obtenerlo
            metadata: Información adicional en JSON

        Returns:
            Badge creado o None si hay error

        Raises:
            Captura excepciones internamente
        """
        try:
            badge = Badge(
                name=name,
                description=description,
                emoji=emoji,
                rarity=rarity,
                is_secret=is_secret,
                badge_metadata=metadata,
                is_active=True
            )
            self._session.add(badge)
            await self._session.flush()
            await self._session.commit()
            await self._session.refresh(badge)

            self._logger.info(f"Badge created: {name} ({rarity.value})")
            return badge

        except Exception as e:
            await self._session.rollback()
            self._logger.error(f"Error creating badge: {e}", exc_info=True)
            return None

    async def toggle_badge_active(
        self,
        badge_id: int,
        active: bool
    ) -> Optional[Badge]:
        """
        Activa o desactiva un badge.

        Args:
            badge_id: ID del badge
            active: Nuevo estado

        Returns:
            Badge actualizado o None si hay error
        """
        try:
            badge = await self.get_badge_by_id(badge_id)
            if not badge:
                return None

            badge.is_active = active
            self._session.add(badge)
            await self._session.commit()
            await self._session.refresh(badge)

            self._logger.info(
                f"Badge {'activated' if active else 'deactivated'}: "
                f"{badge.name}"
            )
            return badge

        except Exception as e:
            await self._session.rollback()
            self._logger.error(
                f"Error toggling badge: {e}", exc_info=True
            )
            return None
