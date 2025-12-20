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

from bot.gamification.database.models import UserGamification, BesitoTransaction
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
        commit: bool = True
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
            commit: Si se debe hacer commit de la sesión

        Returns:
            int: Balance total de besitos después de la operación

        Raises:
            InvalidTransactionError: Si amount <= 0
        """
        if amount <= 0:
            raise InvalidTransactionError(f"Amount debe ser positivo, recibido: {amount}")

        # Asegurar existencia del usuario (crea si no existe)
        await self._ensure_user_exists(user_id, commit=False)

        # Obtener balance antes de la operación para auditoría
        old_balance = await self.get_balance(user_id)

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
            # This case can happen if the user was created in the same transaction
            # but the session has not been flushed. We can't easily recover from this
            # without more complex logic, so we raise an error.
            raise UserNotFoundError(user_id)

        # Calcular nuevo balance
        expected_new_balance = old_balance + amount

        # Registrar transacción
        await self._create_transaction(
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            description=description,
            reference_id=reference_id,
            balance_after=expected_new_balance
        )

        if commit:
            await self.session.commit()

        # Obtener nuevo balance para verificación
        actual_new_balance = await self.get_balance(user_id)

        # Verificar integridad
        if actual_new_balance != expected_new_balance:
            logger.error(
                f"Balance inconsistency for user {user_id}: "
                f"expected {expected_new_balance}, got {actual_new_balance}"
            )

        logger.info(
            f"Granted {amount} besitos to user {user_id}: {description} "
            f"(new balance: {actual_new_balance})"
        )

        return actual_new_balance

    async def spend_besitos(
        self,
        user_id: int,
        amount: int,
        transaction_type: TransactionType,
        description: str,
        reference_id: Optional[int] = None,
        commit: bool = True
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
            commit: Si se debe hacer commit de la sesión

        Returns:
            int: Balance restante después de la operación

        Raises:
            InvalidTransactionError: Si amount <= 0
            InsufficientBesitosError: Si no hay saldo suficiente
        """
        if amount <= 0:
            raise InvalidTransactionError(f"Amount debe ser positivo, recibido: {amount}")

        # Asegurar existencia del usuario
        await self._ensure_user_exists(user_id, commit=False)

        # Validar saldo antes de operar
        current_balance = await self.get_balance(user_id)
        if current_balance < amount:
            raise InsufficientBesitosError(
                user_id=user_id,
                amount_needed=amount,
                current_balance=current_balance
            )

        # Obtener balance antes de la operación para auditoría
        old_balance = await self.get_balance(user_id)

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

        # Calcular nuevo balance
        expected_new_balance = old_balance - amount

        # Registrar transacción
        await self._create_transaction(
            user_id=user_id,
            amount=-amount,  # Negativo para gastos
            transaction_type=transaction_type,
            description=description,
            reference_id=reference_id,
            balance_after=expected_new_balance
        )

        if commit:
            await self.session.commit()

        # Obtener nuevo balance para verificación
        actual_new_balance = await self.get_balance(user_id)

        # Verificar integridad
        if actual_new_balance != expected_new_balance:
            logger.error(
                f"Balance inconsistency for user {user_id}: "
                f"expected {expected_new_balance}, got {actual_new_balance}"
            )

        logger.info(
            f"Spent {amount} besitos from user {user_id}: {description} "
            f"(new balance: {actual_new_balance})"
        )

        return actual_new_balance

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

        Args:
            user_id: ID del usuario
            limit: Límite de transacciones a devolver
            transaction_type: Tipo específico de transacción a filtrar

        Returns:
            List[dict]: Lista de transacciones con sus detalles
        """
        # Call the new method with offset 0 to maintain backward compatibility
        return await self.get_transaction_history_with_offset(user_id, limit=limit, offset=0, transaction_type=transaction_type)

    async def get_transaction_history_with_offset(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        transaction_type: Optional[TransactionType] = None
    ) -> List[dict]:
        """
        Obtiene historial de transacciones de un usuario con paginación.

        Args:
            user_id: ID del usuario
            limit: Límite de transacciones a devolver
            offset: Desplazamiento para paginación
            transaction_type: Tipo específico de transacción a filtrar

        Returns:
            List[dict]: Lista de transacciones con sus detalles
        """
        stmt = (
            select(BesitoTransaction)
            .where(BesitoTransaction.user_id == user_id)
        )

        if transaction_type:
            stmt = stmt.where(BesitoTransaction.transaction_type == transaction_type)

        stmt = stmt.order_by(BesitoTransaction.created_at.desc()).offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        transactions = result.scalars().all()

        return [
            {
                'id': t.id,
                'user_id': t.user_id,
                'amount': t.amount,
                'transaction_type': t.transaction_type,
                'description': t.description,
                'reference_id': t.reference_id,
                'balance_after': t.balance_after,
                'created_at': t.created_at
            }
            for t in transactions
        ]

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
        await self._ensure_user_exists(from_user_id, commit=False)
        await self._ensure_user_exists(to_user_id, commit=False)

        from_balance = await self.get_balance(from_user_id)
        if from_balance < amount:
            raise InsufficientBesitosError(
                user_id=from_user_id,
                amount_needed=amount,
                current_balance=from_balance
            )

        # Obtener balances antes de la operación para auditoría
        from_old_balance = await self.get_balance(from_user_id)
        to_old_balance = await self.get_balance(to_user_id)

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

            # Calcular nuevos balances esperados
            from_expected_new_balance = from_old_balance - amount
            to_expected_new_balance = to_old_balance + amount

            # Registrar transacciones
            await self._create_transaction(
                user_id=from_user_id,
                amount=-amount,
                transaction_type=TransactionType.PURCHASE,  # Transferencia
                description=f"{description} (transfer to user {to_user_id})",
                reference_id=to_user_id,
                balance_after=from_expected_new_balance
            )

            await self._create_transaction(
                user_id=to_user_id,
                amount=amount,
                transaction_type=TransactionType.MISSION_REWARD,  # Transferencia
                description=f"{description} (transfer from user {from_user_id})",
                reference_id=from_user_id,
                balance_after=to_expected_new_balance
            )

            # Confirmar ambas operaciones
            await self.session.commit()

            # Obtener nuevos balances para verificación
            from_actual_new_balance = await self.get_balance(from_user_id)
            to_actual_new_balance = await self.get_balance(to_user_id)

            # Verificar integridad
            if from_actual_new_balance != from_expected_new_balance:
                logger.error(
                    f"Balance inconsistency for sender {from_user_id}: "
                    f"expected {from_expected_new_balance}, got {from_actual_new_balance}"
                )

            if to_actual_new_balance != to_expected_new_balance:
                logger.error(
                    f"Balance inconsistency for receiver {to_user_id}: "
                    f"expected {to_expected_new_balance}, got {to_actual_new_balance}"
                )

            logger.info(
                f"Transferred {amount} besitos from {from_user_id} to {to_user_id} "
                f"(from: {from_actual_new_balance}, to: {to_actual_new_balance})"
            )

            return from_actual_new_balance, to_actual_new_balance

        except Exception as e:
            # Rollback automático si falla cualquier parte
            await self.session.rollback()
            logger.error(f"Transfer failed from {from_user_id} to {to_user_id}: {str(e)}")
            raise

    async def get_transaction_history(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        transaction_type: Optional[TransactionType] = None
    ) -> List[dict]:
        """
        Obtiene historial de transacciones de un usuario.

        Args:
            user_id: ID del usuario
            limit: Límite de transacciones a devolver
            offset: Desplazamiento para paginación
            transaction_type: Tipo específico de transacción a filtrar

        Returns:
            List[dict]: Lista de transacciones con sus detalles
        """
        stmt = (
            select(BesitoTransaction)
            .where(BesitoTransaction.user_id == user_id)
        )

        if transaction_type:
            stmt = stmt.where(BesitoTransaction.transaction_type == transaction_type)

        stmt = stmt.order_by(BesitoTransaction.created_at.desc()).offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        transactions = result.scalars().all()

        return [
            {
                'id': t.id,
                'user_id': t.user_id,
                'amount': t.amount,
                'transaction_type': t.transaction_type,
                'description': t.description,
                'reference_id': t.reference_id,
                'balance_after': t.balance_after,
                'created_at': t.created_at
            }
            for t in transactions
        ]

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

    async def _ensure_user_exists(self, user_id: int, commit: bool = True) -> UserGamification:
        """
        Asegura que exista un perfil de gamificación para el usuario.
        Crea uno si no existe.

        Args:
            user_id: ID del usuario
            commit: Si se debe hacer commit de la sesión

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
            if commit:
                await self.session.commit()

        return user_gamification

    async def _create_transaction(
        self,
        user_id: int,
        amount: int,
        transaction_type: TransactionType,
        description: str,
        reference_id: Optional[int] = None,
        balance_after: Optional[int] = None
    ) -> None:
        """
        Crea un registro de transacción en la base de datos.

        Args:
            user_id: ID del usuario
            amount: Cantidad de besitos (+ para ganancia, - para gasto)
            transaction_type: Tipo de transacción
            description: Descripción
            reference_id: ID de referencia
            balance_after: Balance después de la transacción
        """
        if balance_after is None:
            # Si no se proporciona balance_after, calcularlo (solo para operaciones de gasto simple)
            current_balance = await self.get_balance(user_id)
            balance_after = current_balance

        transaction = BesitoTransaction(
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            description=description,
            reference_id=reference_id,
            balance_after=balance_after,
            created_at=datetime.now(UTC)
        )
        self.session.add(transaction)

        logger.debug(
            f"Transaction created: user={user_id}, amount={amount}, "
            f"type={transaction_type}, balance_after={balance_after}, desc={description}, ref={reference_id}"
        )