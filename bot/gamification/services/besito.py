"""Servicio de gestión de economía de besitos.

Responsabilidades:
- Otorgar besitos a usuarios
- Deducir besitos (compras, penalizaciones)
- Consultar balance
- Auditoría de transacciones
"""

from typing import Optional
from datetime import datetime, UTC
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from bot.gamification.database.models import UserGamification
from bot.gamification.database.enums import TransactionType

logger = logging.getLogger(__name__)


class BesitoService:
    """Servicio de gestión de besitos (economía)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def grant_besitos(
        self,
        user_id: int,
        amount: int,
        transaction_type: TransactionType,
        description: str = "",
        reference_id: Optional[int] = None
    ) -> int:
        """Otorga besitos a un usuario.

        Args:
            user_id: ID del usuario
            amount: Cantidad de besitos a otorgar
            transaction_type: Tipo de transacción
            description: Descripción opcional
            reference_id: ID de referencia (ej: UserReaction.id)

        Returns:
            Cantidad de besitos otorgados
        """
        if amount <= 0:
            logger.warning(f"Attempted to grant {amount} besitos to user {user_id}")
            return 0

        # Obtener o crear perfil de gamificación
        user_gamif = await self._get_or_create_user_gamification(user_id)

        # Actualizar balances
        user_gamif.total_besitos += amount
        user_gamif.besitos_earned += amount

        await self.session.commit()
        await self.session.refresh(user_gamif)

        logger.info(
            f"Granted {amount} besitos to user {user_id} "
            f"({transaction_type.value}). New balance: {user_gamif.total_besitos}"
        )

        return amount

    async def deduct_besitos(
        self,
        user_id: int,
        amount: int,
        transaction_type: TransactionType,
        description: str = "",
        reference_id: Optional[int] = None
    ) -> tuple[bool, str, int]:
        """Deduce besitos de un usuario.

        Args:
            user_id: ID del usuario
            amount: Cantidad a deducir
            transaction_type: Tipo de transacción
            description: Descripción
            reference_id: ID de referencia

        Returns:
            (success, message, new_balance)
        """
        if amount <= 0:
            return False, "Cantidad inválida", 0

        user_gamif = await self._get_or_create_user_gamification(user_id)

        if user_gamif.total_besitos < amount:
            return False, f"Besitos insuficientes ({user_gamif.total_besitos})", user_gamif.total_besitos

        # Deducir
        user_gamif.total_besitos -= amount
        user_gamif.besitos_spent += amount

        await self.session.commit()
        await self.session.refresh(user_gamif)

        logger.info(
            f"Deducted {amount} besitos from user {user_id} "
            f"({transaction_type.value}). New balance: {user_gamif.total_besitos}"
        )

        return True, f"Deducidos {amount} besitos", user_gamif.total_besitos

    async def get_balance(self, user_id: int) -> int:
        """Obtiene balance actual de besitos del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Balance actual de besitos
        """
        user_gamif = await self._get_or_create_user_gamification(user_id)
        return user_gamif.total_besitos

    async def _get_or_create_user_gamification(self, user_id: int) -> UserGamification:
        """Obtiene o crea perfil de gamificación del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            UserGamification del usuario
        """
        stmt = select(UserGamification).where(UserGamification.user_id == user_id)
        result = await self.session.execute(stmt)
        user_gamif = result.scalar_one_or_none()

        if not user_gamif:
            user_gamif = UserGamification(user_id=user_id)
            self.session.add(user_gamif)
            await self.session.commit()
            await self.session.refresh(user_gamif)
            logger.info(f"Created UserGamification for user {user_id}")

        return user_gamif
