"""
Servicio de gestión de economía de besitos.

Responsabilidades:
- Otorgar y deducir besitos de forma atómica
- Prevenir race conditions con operaciones UPDATE ... SET col = col + delta
- Auditoría de transacciones (pendiente de implementación de modelo)
- Validación de saldos
- Leaderboards y estadísticas
"""

from typing import Optional, List
from sqlalchemy import select, update, func, desc
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, UTC
import logging

from bot.gamification.database.models import UserGamification
from bot.gamification.database.enums import TransactionType

logger = logging.getLogger(__name__)


# Excepciones custom
class InsufficientBesitosError(Exception):
    """Se lanza cuando usuario intenta gastar más besitos de los disponibles"""
    def __init__(self, user_id: int, amount_needed: int, current_balance: int):
        self.user_id = user_id
        self.amount_needed = amount_needed
        self.current_balance = current_balance
        super().__init__(
            f"Usuario {user_id} necesita {amount_needed} besitos "
            f"pero solo tiene {current_balance}"
        )


class UserNotFoundError(Exception):
    """Se lanza cuando se intenta operar sobre un usuario que no existe"""
    def __init__(self, user_id: int):
        self.user_id = user_id
        super().__init__(f"Usuario {user_id} no encontrado")


class InvalidTransactionError(Exception):
    """Se lanza cuando una transacción es inválida por lógica de negocio"""
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Transacción inválida: {reason}")


class BesitoService:
    """
    Servicio de gestión de economía de besitos.

    Características:
    - Operaciones atómicas para prevenir race conditions
    - Validación de saldo antes de gastar
    - Creación automática de perfiles de usuario
    - Auditoría de transacciones (cuando se implemente el modelo)
    - Leaderboards
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def grant_besitos(
        self,
        user_id: int,
        amount: int,
        transaction_type: TransactionType,
        description: str,
        reference_id: Optional[int] = None,
        allow_negative: bool = False
    ) -> int:
        """
        Otorga besitos a un usuario.

        Implementa operación atómica para prevenir race conditions:
        UPDATE user_gamification SET total_besitos = total_besitos + amount

        Args:
            user_id: ID del usuario
            amount: Cantidad de besitos a otorgar (debe ser positivo)
            transaction_type: Tipo de transacción
            description: Descripción de la operación
            reference_id: ID de referencia (ej: mission_id)
            allow_negative: Si permite saldos negativos (para admins)

        Returns:
            int: Balance total de besitos después de la operación

        Raises:
            InvalidTransactionError: Si amount <= 0
        """
        if amount <= 0:
            raise InvalidTransactionError(f"Amount debe ser positivo, recibido: {amount}")

        # Asegurar existencia del usuario (crea si no existe)
        await self._ensure_user_exists(user_id)

        # Operación atómica: UPDATE ... SET col = col + delta
        stmt = (
            update(UserGamification)
            .where(UserGamification.user_id == user_id)
            .values(
                total_besitos=UserGamification.total_besitos + amount,
                besitos_earned=UserGamification.besitos_earned + amount,
                updated_at=datetime.now(UTC)
            )
        )
        result = await self.session.execute(stmt)

        if result.rowcount == 0:
            raise UserNotFoundError(user_id)

        # Confirmar transacción
        await self.session.commit()

        # Obtener nuevo balance
        new_balance = await self.get_balance(user_id)

        # Registrar transacción si existe el modelo (esto se implementará cuando se cree la tabla)
        await self._create_transaction(
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            description=description,
            reference_id=reference_id
        )

        logger.info(
            f"Granted {amount} besitos to user {user_id}: {description} "
            f"(new balance: {new_balance})"
        )

        return new_balance

    async def spend_besitos(
        self,
        user_id: int,
        amount: int,
        transaction_type: TransactionType,
        description: str,
        reference_id: Optional[int] = None,
        allow_negative: bool = False
    ) -> int:
        """
        Deduce besitos de un usuario.

        Valida saldo suficiente antes de la operación. Implementa operación atómica:
        UPDATE user_gamification SET total_besitos = total_besitos - amount

        Args:
            user_id: ID del usuario
            amount: Cantidad de besitos a deducir (debe ser positivo)
            transaction_type: Tipo de transacción
            description: Descripción de la operación
            reference_id: ID de referencia (ej: reward_id)
            allow_negative: Si permite saldos negativos (para admins)

        Returns:
            int: Balance restante después de la operación

        Raises:
            InvalidTransactionError: Si amount <= 0
            InsufficientBesitosError: Si no hay saldo suficiente
        """
        if amount <= 0:
            raise InvalidTransactionError(f"Amount debe ser positivo, recibido: {amount}")

        # Asegurar existencia del usuario
        await self._ensure_user_exists(user_id)

        # Validar saldo antes de operar
        current_balance = await self.get_balance(user_id)
        if not allow_negative and current_balance < amount:
            raise InsufficientBesitosError(
                user_id=user_id,
                amount_needed=amount,
                current_balance=current_balance
            )

        # Operación atómica: UPDATE ... SET col = col - delta
        stmt = (
            update(UserGamification)
            .where(UserGamification.user_id == user_id)
            .values(
                total_besitos=UserGamification.total_besitos - amount,
                besitos_spent=UserGamification.besitos_spent + amount,
                updated_at=datetime.now(UTC)
            )
        )
        result = await self.session.execute(stmt)

        if result.rowcount == 0:
            raise UserNotFoundError(user_id)

        # Confirmar transacción
        await self.session.commit()

        # Obtener nuevo balance
        new_balance = await self.get_balance(user_id)

        # Registrar transacción si existe el modelo
        await self._create_transaction(
            user_id=user_id,
            amount=-amount,  # Negativo para gastos
            transaction_type=transaction_type,
            description=description,
            reference_id=reference_id
        )

        logger.info(
            f"Spent {amount} besitos from user {user_id}: {description} "
            f"(new balance: {new_balance})"
        )

        return new_balance

    async def get_balance(self, user_id: int) -> int:
        """
        Obtiene el balance actual de besitos de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            int: Balance actual de besitos (0 si no existe el usuario)
        """
        stmt = select(UserGamification.total_besitos).where(
            UserGamification.user_id == user_id
        )
        result = await self.session.execute(stmt)
        balance = result.scalar()

        return balance if balance is not None else 0

    async def get_transaction_history(
        self,
        user_id: int,
        limit: int = 50,
        transaction_type: Optional[TransactionType] = None
    ) -> List[dict]:
        """
        Obtiene historial de transacciones de un usuario.

        NOTA: Actualmente devuelve historial simulado basado en los cambios de balance
        ya que el modelo BesitoTransaction aún no está implementado.

        Args:
            user_id: ID del usuario
            limit: Límite de transacciones a devolver
            transaction_type: Tipo específico de transacción a filtrar

        Returns:
            List[dict]: Lista de transacciones (simuladas por ahora)
        """
        # Temporal: Devolver información basada en el historial de UserGamification
        # Cuando se implemente BesitoTransaction, esta función usará esa tabla
        logger.warning("get_transaction_history: Modelo BesitoTransaction no implementado aún")
        return []

    async def transfer_besitos(
        self,
        from_user_id: int,
        to_user_id: int,
        amount: int,
        description: str
    ) -> tuple[int, int]:
        """
        Transfiere besitos entre usuarios.

        Operación atómica en una sola transacción: ambos usuarios se actualizan
        en la misma operación para prevenir race conditions.

        Args:
            from_user_id: ID del usuario que envía
            to_user_id: ID del usuario que recibe
            amount: Cantidad a transferir
            description: Descripción de la transferencia

        Returns:
            tuple[int, int]: (nuevo balance del emisor, nuevo balance del receptor)

        Raises:
            InvalidTransactionError: Si amount <= 0
            InsufficientBesitosError: Si from_user no tiene saldo suficiente
        """
        if amount <= 0:
            raise InvalidTransactionError(f"Amount debe ser positivo, recibido: {amount}")

        # Validar que ambos usuarios existan y el emisor tenga saldo
        await self._ensure_user_exists(from_user_id)
        await self._ensure_user_exists(to_user_id)

        from_balance = await self.get_balance(from_user_id)
        if from_balance < amount:
            raise InsufficientBesitosError(
                user_id=from_user_id,
                amount_needed=amount,
                current_balance=from_balance
            )

        try:
            # Operación atómica: ambas actualizaciones en la misma transacción
            # Gastar del emisor
            spend_stmt = (
                update(UserGamification)
                .where(UserGamification.user_id == from_user_id)
                .values(
                    total_besitos=UserGamification.total_besitos - amount,
                    besitos_spent=UserGamification.besitos_spent + amount,
                    updated_at=datetime.now(UTC)
                )
            )
            await self.session.execute(spend_stmt)

            # Otorgar al receptor
            grant_stmt = (
                update(UserGamification)
                .where(UserGamification.user_id == to_user_id)
                .values(
                    total_besitos=UserGamification.total_besitos + amount,
                    besitos_earned=UserGamification.besitos_earned + amount,
                    updated_at=datetime.now(UTC)
                )
            )
            await self.session.execute(grant_stmt)

            # Confirmar ambas operaciones
            await self.session.commit()

            # Obtener nuevos balances
            from_new_balance = await self.get_balance(from_user_id)
            to_new_balance = await self.get_balance(to_user_id)

            # Registrar transacciones
            await self._create_transaction(
                user_id=from_user_id,
                amount=-amount,
                transaction_type=TransactionType.PURCHASE,  # Transferencia
                description=f"{description} (transfer to user {to_user_id})",
                reference_id=to_user_id
            )

            await self._create_transaction(
                user_id=to_user_id,
                amount=amount,
                transaction_type=TransactionType.MISSION_REWARD,  # Transferencia
                description=f"{description} (transfer from user {from_user_id})",
                reference_id=from_user_id
            )

            logger.info(
                f"Transferred {amount} besitos from {from_user_id} to {to_user_id} "
                f"(from: {from_new_balance}, to: {to_new_balance})"
            )

            return from_new_balance, to_new_balance

        except Exception as e:
            # Rollback automático si falla cualquier parte
            await self.session.rollback()
            logger.error(f"Transfer failed from {from_user_id} to {to_user_id}: {str(e)}")
            raise

    async def get_leaderboard(self, limit: int = 10) -> List[dict]:
        """
        Obtiene el leaderboard de usuarios por total de besitos.

        Args:
            limit: Número de usuarios a devolver

        Returns:
            List[dict]: Lista de diccionarios con user_id y total_besitos
        """
        stmt = (
            select(UserGamification.user_id, UserGamification.total_besitos)
            .order_by(desc(UserGamification.total_besitos))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        rows = result.all()

        return [
            {"user_id": row.user_id, "total_besitos": row.total_besitos}
            for row in rows
        ]

    async def _ensure_user_exists(self, user_id: int) -> UserGamification:
        """
        Asegura que exista un perfil de gamificación para el usuario.
        Crea uno si no existe.

        Args:
            user_id: ID del usuario

        Returns:
            UserGamification: Instancia del perfil existente o recién creado
        """
        user_gamification = await self.session.get(UserGamification, user_id)
        if not user_gamification:
            user_gamification = UserGamification(
                user_id=user_id,
                total_besitos=0,
                besitos_earned=0,
                besitos_spent=0
            )
            self.session.add(user_gamification)
            await self.session.commit()

        return user_gamification

    async def _create_transaction(
        self,
        user_id: int,
        amount: int,
        transaction_type: TransactionType,
        description: str,
        reference_id: Optional[int] = None
    ) -> None:
        """
        Crea un registro de transacción (simulado por ahora).

        NOTA: Esta función está preparada para usar BesitoTransaction cuando
        se implemente el modelo. Por ahora, solo hace logging.

        Args:
            user_id: ID del usuario
            amount: Cantidad de besitos (+ para ganancia, - para gasto)
            transaction_type: Tipo de transacción
            description: Descripción
            reference_id: ID de referencia
        """
        # Simular creación de transacción - pendiente de modelo BesitoTransaction
        logger.debug(
            f"Transaction record: user={user_id}, amount={amount}, "
            f"type={transaction_type}, desc={description}, ref={reference_id}"
        )
        # Aquí se creará un BesitoTransaction cuando se implemente el modelo