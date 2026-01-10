"""
InterestService - Servicio de gesti\u00f3n de intereses de usuarios.

Permite registrar y gestionar intereses de usuarios en productos comerciales,
y facilita el seguimiento por parte de admins.
"""
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.database.models_menu import UserInterest
from bot.database.models import User

logger = logging.getLogger(__name__)


class InterestService:
    """
    Servicio de gesti\u00f3n de intereses de usuarios.

    Responsabilidades:
    - Registrar inter\u00e9s de usuario en producto
    - Obtener intereses pendientes para admin
    - Marcar intereses como contactados/convertidos/rechazados
    - Obtener historial de intereses por usuario
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio.

        Args:
            session: Sesi\u00f3n async de SQLAlchemy
        """
        self._session = session

    async def register_interest(
        self,
        user_id: int,
        product_type: str,
        product_key: str
    ) -> UserInterest:
        """
        Registra el inter\u00e9s de un usuario en un producto.

        Args:
            user_id: ID del usuario
            product_type: Tipo de producto ('set', 'personalizado', 'vip', 'premium', 'mapa_deseo')
            product_key: Clave espec\u00edfica del producto

        Returns:
            UserInterest creado

        Raises:
            ValueError: Si el usuario no existe
        """
        # Verificar que el usuario existe
        stmt = select(User).where(User.user_id == user_id)
        result = await self._session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError(f"Usuario {user_id} no existe")

        # Verificar si ya existe un inter\u00e9s reciente para este producto
        existing = await self._get_recent_interest(user_id, product_type, product_key)

        if existing and existing.status == "pending":
            logger.info(
                f"Usuario {user_id} ya tiene inter\u00e9s pendiente en "
                f"{product_type}:{product_key}, retornando existente"
            )
            return existing

        # Crear nuevo registro de inter\u00e9s
        interest = UserInterest(
            user_id=user_id,
            product_type=product_type,
            product_key=product_key,
            status="pending",
            created_at=datetime.utcnow()
        )

        self._session.add(interest)
        await self._session.flush()
        await self._session.refresh(interest)

        logger.info(
            f"\u2728 Inter\u00e9s registrado: user={user_id}, "
            f"product={product_type}:{product_key}, id={interest.id}"
        )

        return interest

    async def _get_recent_interest(
        self,
        user_id: int,
        product_type: str,
        product_key: str
    ) -> Optional[UserInterest]:
        """
        Busca un inter\u00e9s reciente (menos de 24h) del mismo producto.

        Args:
            user_id: ID del usuario
            product_type: Tipo de producto
            product_key: Clave del producto

        Returns:
            UserInterest si existe, None si no
        """
        stmt = (
            select(UserInterest)
            .where(
                and_(
                    UserInterest.user_id == user_id,
                    UserInterest.product_type == product_type,
                    UserInterest.product_key == product_key
                )
            )
            .order_by(UserInterest.created_at.desc())
            .limit(1)
        )

        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_pending_interests(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[UserInterest]:
        """
        Obtiene intereses pendientes ordenados por fecha.

        Args:
            limit: N\u00famero m\u00e1ximo de resultados
            offset: Offset para paginaci\u00f3n

        Returns:
            Lista de UserInterest con status='pending'
        """
        stmt = (
            select(UserInterest)
            .options(selectinload(UserInterest.user))  # Cargar usuario
            .where(UserInterest.status == "pending")
            .order_by(UserInterest.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self._session.execute(stmt)
        interests = list(result.scalars().all())

        logger.debug(
            f"Intereses pendientes obtenidos: {len(interests)} "
            f"(limit={limit}, offset={offset})"
        )

        return interests

    async def get_user_interests(
        self,
        user_id: int,
        status: Optional[str] = None
    ) -> List[UserInterest]:
        """
        Obtiene todos los intereses de un usuario.

        Args:
            user_id: ID del usuario
            status: Filtrar por status (None = todos)

        Returns:
            Lista de UserInterest del usuario
        """
        stmt = (
            select(UserInterest)
            .where(UserInterest.user_id == user_id)
        )

        if status:
            stmt = stmt.where(UserInterest.status == status)

        stmt = stmt.order_by(UserInterest.created_at.desc())

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def mark_as_contacted(
        self,
        interest_id: int,
        admin_id: int,
        notes: Optional[str] = None
    ) -> Optional[UserInterest]:
        """
        Marca un inter\u00e9s como contactado por admin.

        Args:
            interest_id: ID del inter\u00e9s
            admin_id: ID del admin que contact\u00f3
            notes: Notas opcionales del admin

        Returns:
            UserInterest actualizado o None si no existe
        """
        interest = await self.get_interest_by_id(interest_id)
        if not interest:
            logger.warning(f"Inter\u00e9s {interest_id} no existe")
            return None

        interest.status = "contacted"
        interest.contacted_at = datetime.utcnow()
        interest.contacted_by = admin_id

        if notes:
            interest.notes = notes

        await self._session.flush()
        await self._session.refresh(interest)

        logger.info(
            f"\u2705 Inter\u00e9s {interest_id} marcado como contactado por admin {admin_id}"
        )

        return interest

    async def mark_as_converted(
        self,
        interest_id: int,
        admin_id: int,
        notes: Optional[str] = None
    ) -> Optional[UserInterest]:
        """
        Marca un inter\u00e9s como convertido (usuario compr\u00f3/acept\u00f3).

        Args:
            interest_id: ID del inter\u00e9s
            admin_id: ID del admin
            notes: Notas opcionales

        Returns:
            UserInterest actualizado o None si no existe
        """
        interest = await self.get_interest_by_id(interest_id)
        if not interest:
            logger.warning(f"Inter\u00e9s {interest_id} no existe")
            return None

        interest.status = "converted"

        if not interest.contacted_at:
            interest.contacted_at = datetime.utcnow()

        if not interest.contacted_by:
            interest.contacted_by = admin_id

        if notes:
            interest.notes = notes

        await self._session.flush()
        await self._session.refresh(interest)

        logger.info(
            f"\ud83c\udf89 Inter\u00e9s {interest_id} marcado como convertido"
        )

        return interest

    async def mark_as_rejected(
        self,
        interest_id: int,
        admin_id: int,
        notes: Optional[str] = None
    ) -> Optional[UserInterest]:
        """
        Marca un inter\u00e9s como rechazado.

        Args:
            interest_id: ID del inter\u00e9s
            admin_id: ID del admin
            notes: Notas (raz\u00f3n del rechazo)

        Returns:
            UserInterest actualizado o None si no existe
        """
        interest = await self.get_interest_by_id(interest_id)
        if not interest:
            logger.warning(f"Inter\u00e9s {interest_id} no existe")
            return None

        interest.status = "rejected"

        if not interest.contacted_at:
            interest.contacted_at = datetime.utcnow()

        if not interest.contacted_by:
            interest.contacted_by = admin_id

        if notes:
            interest.notes = notes

        await self._session.flush()
        await self._session.refresh(interest)

        logger.info(
            f"\u274c Inter\u00e9s {interest_id} marcado como rechazado"
        )

        return interest

    async def get_interest_by_id(
        self,
        interest_id: int,
        load_user: bool = True
    ) -> Optional[UserInterest]:
        """
        Obtiene un inter\u00e9s por ID.

        Args:
            interest_id: ID del inter\u00e9s
            load_user: Si True, carga relaci\u00f3n con usuario

        Returns:
            UserInterest o None si no existe
        """
        stmt = select(UserInterest).where(UserInterest.id == interest_id)

        if load_user:
            stmt = stmt.options(selectinload(UserInterest.user))

        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_interests_by_product(
        self,
        product_type: str,
        product_key: Optional[str] = None
    ) -> List[UserInterest]:
        """
        Obtiene intereses por tipo y/o clave de producto.

        Args:
            product_type: Tipo de producto
            product_key: Clave espec\u00edfica (None = todos del tipo)

        Returns:
            Lista de UserInterest
        """
        stmt = (
            select(UserInterest)
            .options(selectinload(UserInterest.user))
            .where(UserInterest.product_type == product_type)
        )

        if product_key:
            stmt = stmt.where(UserInterest.product_key == product_key)

        stmt = stmt.order_by(UserInterest.created_at.desc())

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_interest_stats(self) -> dict:
        """
        Obtiene estad\u00edsticas de intereses.

        Returns:
            Dict con estad\u00edsticas por status
        """
        from sqlalchemy import func

        stmt = (
            select(
                UserInterest.status,
                func.count(UserInterest.id).label("count")
            )
            .group_by(UserInterest.status)
        )

        result = await self._session.execute(stmt)
        stats = {row[0]: row[1] for row in result.all()}

        logger.debug(f"Stats de intereses: {stats}")

        return stats
