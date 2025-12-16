"""
Points Service - Servicio central de gestión de puntos.

Gestiona:
- Otorgamiento de puntos (besitos)
- Deducción de puntos
- Consultas de saldo
- Histórico de transacciones
- Cálculo de multiplicadores
- Integración con otros servicios

Este es el servicio CORE del módulo de gamificación.
"""
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Tuple

from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import (
    User,
    UserProgress,
    PointTransaction,
    TransactionType
)

logger = logging.getLogger(__name__)


class PointsService:
    """
    Servicio de gestión de puntos (besitos).

    Responsabilidades:
    - Otorgar puntos por acciones
    - Restar puntos por canjes
    - Calcular multiplicadores
    - Mantener histórico de transacciones
    - Consultar saldo y estadísticas

    Este servicio NO escucha eventos directamente.
    Los handlers llaman a los métodos según sea necesario.
    """

    def __init__(self, session: AsyncSession, bot=None):
        """
        Inicializa el servicio de puntos.

        Args:
            session: Sesión de base de datos async
            bot: Instancia del bot (opcional, para futuras integraciones)
        """
        self.session = session
        self.bot = bot

        # Configuración de multiplicadores base
        # Estos pueden ser sobrescritos por configuración dinámica
        self.VIP_MULTIPLIER = 1.5  # VIP gana 50% más
        self.DEFAULT_MULTIPLIER = 1.0

    # ===== MÉTODOS DE GESTIÓN DE USERPROGRESS =====

    async def get_or_create_progress(
        self,
        user_id: int
    ) -> Optional[UserProgress]:
        """
        Obtiene el UserProgress de un usuario o lo crea si no existe.

        Este método asegura que cada usuario tenga su registro de progreso.
        Se llama automáticamente en operaciones de puntos.

        Args:
            user_id: ID del usuario

        Returns:
            UserProgress del usuario, o None si hay error

        Example:
            >>> progress = await service.get_or_create_progress(123)
            >>> print(progress.besitos_balance)
            0
        """
        try:
            # Intentar obtener progress existente
            result = await self.session.execute(
                select(UserProgress).where(UserProgress.user_id == user_id)
            )
            progress = result.scalar_one_or_none()

            if progress:
                logger.debug(f"UserProgress encontrado para user {user_id}")
                return progress

            # No existe, crear nuevo
            logger.info(f"Creando UserProgress para user {user_id}")

            # Verificar que el usuario existe
            user_result = await self.session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = user_result.scalar_one_or_none()

            if not user:
                logger.warning(f"Usuario {user_id} no existe, no se puede crear progress")
                return None

            # Crear nuevo UserProgress
            progress = UserProgress(
                user_id=user_id,
                besitos_balance=0,
                current_level=1,
                total_points_earned=0,
                total_points_spent=0
            )

            self.session.add(progress)
            await self.session.commit()
            await self.session.refresh(progress)

            logger.info(f"✅ UserProgress creado para user {user_id}")
            return progress

        except Exception as e:
            logger.error(
                f"❌ Error obteniendo/creando progress para user {user_id}: {e}",
                exc_info=True
            )
            await self.session.rollback()
            return None

    async def get_user_progress(
        self,
        user_id: int
    ) -> Optional[UserProgress]:
        """
        Obtiene el UserProgress de un usuario (sin crear si no existe).

        Args:
            user_id: ID del usuario

        Returns:
            UserProgress del usuario, o None si no existe
        """
        try:
            result = await self.session.execute(
                select(UserProgress).where(UserProgress.user_id == user_id)
            )
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(
                f"❌ Error obteniendo progress de user {user_id}: {e}",
                exc_info=True
            )
            return None

    async def get_user_balance(
        self,
        user_id: int
    ) -> int:
        """
        Obtiene el saldo actual de besitos de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Saldo de besitos (0 si no tiene progress)

        Example:
            >>> balance = await service.get_user_balance(123)
            >>> print(f"Saldo: {balance} 💋")
            Saldo: 150 💋
        """
        progress = await self.get_user_progress(user_id)

        if not progress:
            logger.debug(f"User {user_id} no tiene progress, saldo=0")
            return 0

        return progress.besitos_balance

    async def get_user_level(
        self,
        user_id: int
    ) -> int:
        """
        Obtiene el nivel actual de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Nivel actual (1 si no tiene progress)
        """
        progress = await self.get_user_progress(user_id)

        if not progress:
            logger.debug(f"User {user_id} no tiene progress, nivel=1")
            return 1

        return progress.current_level

    async def update_level(
        self,
        user_id: int,
        new_level: int
    ) -> bool:
        """
        Actualiza el nivel de un usuario.

        NOTA: Este método es llamado por el LevelsService,
        no debe ser llamado directamente por handlers.

        Args:
            user_id: ID del usuario
            new_level: Nuevo nivel a asignar

        Returns:
            True si se actualizó, False si hubo error
        """
        try:
            progress = await self.get_or_create_progress(user_id)

            if not progress:
                return False

            old_level = progress.current_level
            progress.current_level = new_level

            await self.session.commit()

            logger.info(
                f"📊 Nivel actualizado: user {user_id} "
                f"{old_level} → {new_level}"
            )

            return True

        except Exception as e:
            logger.error(
                f"❌ Error actualizando nivel de user {user_id}: {e}",
                exc_info=True
            )
            await self.session.rollback()
            return False

    # ===== MÉTODOS DE CONSULTA DE ESTADÍSTICAS =====

    async def get_user_stats(
        self,
        user_id: int
    ) -> Optional[Dict]:
        """
        Obtiene estadísticas completas de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Dict con estadísticas o None si no existe

        Example:
            >>> stats = await service.get_user_stats(123)
            >>> print(stats)
            {
                'balance': 150,
                'level': 3,
                'total_earned': 500,
                'total_spent': 350,
                'net_points': 150,
                'transaction_count': 25
            }
        """
        try:
            progress = await self.get_user_progress(user_id)

            if not progress:
                return None

            # Contar transacciones
            count_result = await self.session.execute(
                select(func.count(PointTransaction.id))
                .where(PointTransaction.user_id == user_id)
            )
            transaction_count = count_result.scalar()

            stats = {
                "balance": progress.besitos_balance,
                "level": progress.current_level,
                "total_earned": progress.total_points_earned,
                "total_spent": progress.total_points_spent,
                "net_points": progress.net_points,
                "transaction_count": transaction_count,
                "created_at": progress.created_at,
                "updated_at": progress.updated_at
            }

            logger.debug(f"Estadísticas de user {user_id}: {stats}")
            return stats

        except Exception as e:
            logger.error(
                f"❌ Error obteniendo stats de user {user_id}: {e}",
                exc_info=True
            )
            return None

    async def user_exists(
        self,
        user_id: int
    ) -> bool:
        """
        Verifica si un usuario existe en el sistema.

        Args:
            user_id: ID del usuario

        Returns:
            True si existe, False si no
        """
        try:
            result = await self.session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = result.scalar_one_or_none()
            return user is not None

        except Exception as e:
            logger.error(
                f"❌ Error verificando existencia de user {user_id}: {e}",
                exc_info=True
            )
            return False

    # ===== MÉTODOS DE OTORGAMIENTO Y DEDUCCIÓN DE PUNTOS =====

    async def award_points(
        self,
        user_id: int,
        amount: int,
        reason: str,
        multiplier: float = 1.0,
        metadata: Optional[Dict] = None
    ) -> Tuple[bool, Optional[int]]:
        """
        Otorga puntos a un usuario.

        Crea una transacción EARNED y actualiza el saldo.

        Args:
            user_id: ID del usuario
            amount: Cantidad base de puntos (antes de multiplicador)
            reason: Razón del otorgamiento
            multiplier: Multiplicador a aplicar (default: 1.0)
            metadata: Datos adicionales de contexto (opcional)

        Returns:
            Tuple (éxito: bool, saldo_final: int o None)

        Example:
            >>> success, new_balance = await service.award_points(
            ...     user_id=123,
            ...     amount=10,
            ...     reason="Reacción a mensaje",
            ...     multiplier=1.5,
            ...     metadata={"emoji": "❤️", "message_id": 456}
            ... )
            >>> if success:
            ...     print(f"Nuevo saldo: {new_balance}")
        """
        try:
            # Obtener o crear progress
            progress = await self.get_or_create_progress(user_id)
            if not progress:
                logger.error(f"No se pudo obtener/crear progress para user {user_id}")
                return (False, None)

            # Calcular puntos finales con multiplicador
            final_amount = int(amount * multiplier)

            # Actualizar saldo
            progress.besitos_balance += final_amount
            progress.total_points_earned += final_amount

            # Crear transacción
            transaction = PointTransaction(
                user_id=user_id,
                amount=final_amount,
                transaction_type=TransactionType.EARNED,
                reason=reason,
                transaction_metadata=metadata or {},
                balance_after=progress.besitos_balance
            )

            self.session.add(transaction)
            await self.session.commit()

            logger.info(
                f"🎁 Puntos otorgados: user {user_id} "
                f"+{final_amount} ({amount}×{multiplier}), saldo={progress.besitos_balance}"
            )

            return (True, progress.besitos_balance)

        except Exception as e:
            logger.error(
                f"❌ Error otorgando puntos a user {user_id}: {e}",
                exc_info=True
            )
            await self.session.rollback()
            return (False, None)

    async def deduct_points(
        self,
        user_id: int,
        amount: int,
        reason: str,
        metadata: Optional[Dict] = None
    ) -> Tuple[bool, Optional[int]]:
        """
        Deduce puntos de un usuario.

        Crea una transacción SPENT y actualiza el saldo.

        Args:
            user_id: ID del usuario
            amount: Cantidad de puntos a deducir (positiva)
            reason: Razón de la deducción
            metadata: Datos adicionales de contexto (opcional)

        Returns:
            Tuple (éxito: bool, saldo_final: int o None)

        Raises:
            No lanza excepción, retorna (False, None) si falla

        Example:
            >>> success, new_balance = await service.deduct_points(
            ...     user_id=123,
            ...     amount=50,
            ...     reason="Canje de badge",
            ...     metadata={"badge_id": 5, "badge_name": "Oro"}
            ... )
        """
        try:
            # Obtener progress (debe existir para deducir)
            progress = await self.get_user_progress(user_id)
            if not progress:
                logger.warning(f"User {user_id} no tiene progress, no se puede deducir")
                return (False, None)

            # Verificar saldo suficiente
            if progress.besitos_balance < amount:
                logger.warning(
                    f"Saldo insuficiente: user {user_id} "
                    f"tiene {progress.besitos_balance}, quiere deducir {amount}"
                )
                return (False, progress.besitos_balance)

            # Actualizar saldo
            progress.besitos_balance -= amount
            progress.total_points_spent += amount

            # Crear transacción (amount negativo)
            transaction = PointTransaction(
                user_id=user_id,
                amount=-amount,
                transaction_type=TransactionType.SPENT,
                reason=reason,
                transaction_metadata=metadata or {},
                balance_after=progress.besitos_balance
            )

            self.session.add(transaction)
            await self.session.commit()

            logger.info(
                f"💸 Puntos deducidos: user {user_id} "
                f"-{amount}, saldo={progress.besitos_balance}"
            )

            return (True, progress.besitos_balance)

        except Exception as e:
            logger.error(
                f"❌ Error deduciendo puntos de user {user_id}: {e}",
                exc_info=True
            )
            await self.session.rollback()
            return (False, None)

    # ===== MÉTODOS DE MULTIPLICADORES =====

    def get_vip_multiplier(self, is_vip: bool) -> float:
        """
        Obtiene el multiplicador por estado VIP.

        Args:
            is_vip: Si el usuario es VIP

        Returns:
            Multiplicador (1.5 si VIP, 1.0 si no)
        """
        return self.VIP_MULTIPLIER if is_vip else self.DEFAULT_MULTIPLIER

    def get_level_multiplier(self, level: int) -> float:
        """
        Obtiene el multiplicador por nivel del usuario.

        La fórmula: 1.0 + (nivel - 1) * 0.1
        - Nivel 1: 1.0x
        - Nivel 2: 1.1x
        - Nivel 3: 1.2x
        - Nivel 10: 1.9x

        Args:
            level: Nivel del usuario

        Returns:
            Multiplicador basado en nivel
        """
        if level < 1:
            level = 1
        return 1.0 + (level - 1) * 0.1

    async def calculate_multiplier(
        self,
        user_id: int,
        is_vip: bool = False
    ) -> float:
        """
        Calcula el multiplicador total para un usuario.

        Combina multiplicadores de:
        - Estado VIP
        - Nivel actual

        Fórmula: VIP_multiplier × level_multiplier

        Args:
            user_id: ID del usuario
            is_vip: Si el usuario es VIP

        Returns:
            Multiplicador total

        Example:
            >>> multiplier = await service.calculate_multiplier(123, is_vip=True)
            >>> print(f"Multiplicador total: {multiplier}x")
            Multiplicador total: 1.8x
        """
        try:
            # Obtener nivel
            level = await self.get_user_level(user_id)

            # Calcular multiplicadores
            vip_mult = self.get_vip_multiplier(is_vip)
            level_mult = self.get_level_multiplier(level)

            # Multiplicador total
            total_mult = vip_mult * level_mult

            logger.debug(
                f"Multiplicador: user {user_id} "
                f"VIP={vip_mult}x × Nivel={level_mult}x = {total_mult}x"
            )

            return total_mult

        except Exception as e:
            logger.error(
                f"❌ Error calculando multiplicador para user {user_id}: {e}",
                exc_info=True
            )
            return 1.0

    # ===== MÉTODOS DE HISTÓRICO =====

    async def get_point_history(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """
        Obtiene el histórico de transacciones de un usuario.

        Retorna las transacciones más recientes primero.

        Args:
            user_id: ID del usuario
            limit: Máximo número de transacciones (default: 50)
            offset: Número de transacciones a saltar (default: 0)

        Returns:
            Lista de dicts con transacciones (vacía si no hay)

        Example:
            >>> history = await service.get_point_history(123, limit=10)
            >>> for tx in history:
            ...     print(f"{tx['reason']}: {tx['amount']:+d}")
        """
        try:
            result = await self.session.execute(
                select(PointTransaction)
                .where(PointTransaction.user_id == user_id)
                .order_by(desc(PointTransaction.created_at))
                .limit(limit)
                .offset(offset)
            )

            transactions = result.scalars().all()

            history = [
                {
                    "id": tx.id,
                    "amount": tx.amount,
                    "type": tx.transaction_type.value,
                    "reason": tx.reason,
                    "balance_after": tx.balance_after,
                    "metadata": tx.transaction_metadata,
                    "created_at": tx.created_at,
                    "is_credit": tx.is_credit,
                    "is_debit": tx.is_debit
                }
                for tx in transactions
            ]

            logger.debug(f"Histórico obtenido: user {user_id}, {len(history)} transacciones")
            return history

        except Exception as e:
            logger.error(
                f"❌ Error obteniendo histórico de user {user_id}: {e}",
                exc_info=True
            )
            return []

    async def get_recent_transactions(
        self,
        user_id: int,
        days: int = 7
    ) -> List[Dict]:
        """
        Obtiene transacciones recientes de los últimos N días.

        Args:
            user_id: ID del usuario
            days: Número de días hacia atrás (default: 7)

        Returns:
            Lista de transacciones recientes

        Example:
            >>> recent = await service.get_recent_transactions(123, days=30)
            >>> earned = sum(tx['amount'] for tx in recent if tx['is_credit'])
            >>> spent = sum(abs(tx['amount']) for tx in recent if tx['is_debit'])
            >>> print(f"Ganados: {earned}, Gastados: {spent}")
        """
        try:
            from datetime import timedelta

            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

            result = await self.session.execute(
                select(PointTransaction)
                .where(
                    (PointTransaction.user_id == user_id) &
                    (PointTransaction.created_at >= cutoff_date)
                )
                .order_by(desc(PointTransaction.created_at))
            )

            transactions = result.scalars().all()

            recent = [
                {
                    "amount": tx.amount,
                    "type": tx.transaction_type.value,
                    "reason": tx.reason,
                    "created_at": tx.created_at,
                    "is_credit": tx.is_credit
                }
                for tx in transactions
            ]

            logger.debug(
                f"Transacciones recientes: user {user_id}, "
                f"últimos {days} días, {len(recent)} registros"
            )
            return recent

        except Exception as e:
            logger.error(
                f"❌ Error obteniendo transacciones recientes de user {user_id}: {e}",
                exc_info=True
            )
            return []

    async def can_afford(
        self,
        user_id: int,
        amount: int
    ) -> bool:
        """
        Verifica si un usuario puede pagar una cantidad de puntos.

        Args:
            user_id: ID del usuario
            amount: Cantidad requerida

        Returns:
            True si tiene suficientes puntos, False si no
        """
        balance = await self.get_user_balance(user_id)
        return balance >= amount

    # ===== MÉTODOS DE HISTÓRICO Y CONSULTAS AVANZADAS =====

    async def get_point_history_by_type(
        self,
        user_id: int,
        limit: int = 10,
        transaction_type: Optional[TransactionType] = None
    ) -> List[PointTransaction]:
        """
        Obtiene el histórico de transacciones de un usuario.

        Args:
            user_id: ID del usuario
            limit: Cantidad máxima de transacciones a retornar
            transaction_type: Filtrar por tipo (opcional)

        Returns:
            Lista de transacciones, ordenadas por fecha desc (más reciente primero)

        Example:
            >>> history = await service.get_point_history_by_type(123, limit=5)
            >>> for tx in history:
            ...     print(f"{tx.created_at}: {tx.amount} - {tx.reason}")
        """
        try:
            query = select(PointTransaction).where(
                PointTransaction.user_id == user_id
            )

            # Filtrar por tipo si se especifica
            if transaction_type:
                query = query.where(
                    PointTransaction.transaction_type == transaction_type
                )

            # Ordenar por fecha desc y limitar
            query = query.order_by(desc(PointTransaction.created_at)).limit(limit)

            result = await self.session.execute(query)
            transactions = result.scalars().all()

            logger.debug(
                f"Histórico obtenido: user {user_id}, "
                f"{len(transactions)} transacciones"
            )

            return list(transactions)

        except Exception as e:
            logger.error(
                f"❌ Error obteniendo histórico de user {user_id}: {e}",
                exc_info=True
            )
            return []

    async def get_earned_history(
        self,
        user_id: int,
        limit: int = 10
    ) -> List[PointTransaction]:
        """
        Obtiene histórico de puntos GANADOS de un usuario.

        Args:
            user_id: ID del usuario
            limit: Cantidad máxima

        Returns:
            Lista de transacciones EARNED
        """
        return await self.get_point_history_by_type(
            user_id=user_id,
            limit=limit,
            transaction_type=TransactionType.EARNED
        )

    async def get_spent_history(
        self,
        user_id: int,
        limit: int = 10
    ) -> List[PointTransaction]:
        """
        Obtiene histórico de puntos GASTADOS de un usuario.

        Args:
            user_id: ID del usuario
            limit: Cantidad máxima

        Returns:
            Lista de transacciones SPENT
        """
        return await self.get_point_history_by_type(
            user_id=user_id,
            limit=limit,
            transaction_type=TransactionType.SPENT
        )

    async def get_transaction_by_id(
        self,
        transaction_id: int
    ) -> Optional[PointTransaction]:
        """
        Obtiene una transacción específica por ID.

        Args:
            transaction_id: ID de la transacción

        Returns:
            PointTransaction o None si no existe
        """
        try:
            result = await self.session.execute(
                select(PointTransaction).where(
                    PointTransaction.id == transaction_id
                )
            )
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(
                f"❌ Error obteniendo transacción {transaction_id}: {e}",
                exc_info=True
            )
            return None

    async def count_user_transactions(
        self,
        user_id: int,
        transaction_type: Optional[TransactionType] = None
    ) -> int:
        """
        Cuenta el total de transacciones de un usuario.

        Args:
            user_id: ID del usuario
            transaction_type: Filtrar por tipo (opcional)

        Returns:
            Cantidad de transacciones
        """
        try:
            query = select(func.count(PointTransaction.id)).where(
                PointTransaction.user_id == user_id
            )

            if transaction_type:
                query = query.where(
                    PointTransaction.transaction_type == transaction_type
                )

            result = await self.session.execute(query)
            count = result.scalar()

            return count or 0

        except Exception as e:
            logger.error(
                f"❌ Error contando transacciones de user {user_id}: {e}",
                exc_info=True
            )
            return 0

    async def get_total_points_in_system(self) -> int:
        """
        Calcula el total de puntos en circulación en todo el sistema.

        Returns:
            Suma de todos los balances de usuarios
        """
        try:
            result = await self.session.execute(
                select(func.sum(UserProgress.besitos_balance))
            )
            total = result.scalar()

            return total or 0

        except Exception as e:
            logger.error(
                f"❌ Error calculando puntos totales del sistema: {e}",
                exc_info=True
            )
            return 0

    async def get_richest_users(
        self,
        limit: int = 10
    ) -> List[Tuple[int, int, int]]:
        """
        Obtiene los usuarios con más besitos.

        Args:
            limit: Cantidad de usuarios a retornar

        Returns:
            Lista de tuplas (user_id, balance, level)

        Example:
            >>> top = await service.get_richest_users(5)
            >>> for user_id, balance, level in top:
            ...     print(f"User {user_id}: {balance} 💋 (Nivel {level})")
        """
        try:
            result = await self.session.execute(
                select(
                    UserProgress.user_id,
                    UserProgress.besitos_balance,
                    UserProgress.current_level
                )
                .order_by(desc(UserProgress.besitos_balance))
                .limit(limit)
            )

            users = result.all()
            return users

        except Exception as e:
            logger.error(
                f"❌ Error obteniendo usuarios más ricos: {e}",
                exc_info=True
            )
            return []
