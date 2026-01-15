"""
Points Service - Gestión de puntos ("besitos") en el sistema de gamificación.

Maneja:
- Balance de puntos de usuarios
- Otorgamiento y gasto de puntos
- Regalo diario
- Leaderboard
- Historial de transacciones
"""
import logging
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Union

from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot

from bot.database.gamification_models import (
    UserPoints, PointsTransaction, GamificationConfig
)
from bot.database.enums import TransactionType
from bot.database.models import User

logger = logging.getLogger(__name__)


class PointsService:
    """
    Servicio para gestión de puntos (besitos).

    Responsabilidades:
    - Otorgar puntos por reacciones, regalos diarios, misiones
    - Gastos de puntos en compras
    - Regalo diario con cooldown de 24h
    - Leaderboard de usuarios
    - Historial de transacciones

    Attributes:
        _session: Sesión de base de datos SQLAlchemy
        _bot: Instancia del bot de Telegram
    """

    def __init__(self, session: AsyncSession, bot: Bot):
        """
        Inicializa el PointsService.

        Args:
            session: Sesión de base de datos SQLAlchemy
            bot: Instancia del bot de Telegram
        """
        self._session = session
        self._bot = bot

    def _normalize_transaction_type(self, transaction_type: Union[TransactionType, str]) -> TransactionType:
        """
        Normaliza el tipo de transacción a enum.

        Args:
            transaction_type: TransactionType enum o string

        Returns:
            TransactionType: Enum normalizado
        """
        if isinstance(transaction_type, str):
            return TransactionType(transaction_type)
        return transaction_type

    # ===== CONFIGURACIÓN =====

    async def _get_config(self) -> GamificationConfig:
        """
        Obtiene la configuración de gamificación.

        Returns:
            GamificationConfig: Configuración global (singleton id=1)
        """
        result = await self._session.execute(
            select(GamificationConfig).where(GamificationConfig.id == 1)
        )
        config = result.scalar_one_or_none()

        if config is None:
            # Crear configuración por defecto si no existe
            config = GamificationConfig(
                points_per_reaction=1,
                daily_gift_points=5,
                streak_multiplier=1.5,
                default_reaction_emojis=["👍", "❤️", "🔥", "🎉", "💯"]
            )
            self._session.add(config)
            await self._session.commit()
            logger.info("✅ GamificationConfig creado por defecto")

        return config

    # ===== GETTERS =====

    async def get_balance(self, user_id: int) -> Optional[UserPoints]:
        """
        Obtiene el balance de puntos de un usuario.

        Args:
            user_id: ID del usuario en Telegram

        Returns:
            UserPoints o None si no existe
        """
        result = await self._session.execute(
            select(UserPoints).where(UserPoints.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create_points(self, user_id: int) -> UserPoints:
        """
        Obtiene o crea el balance de puntos de un usuario.

        Args:
            user_id: ID del usuario en Telegram

        Returns:
            UserPoints: Balance del usuario (creado si no existía)
        """
        points = await self.get_balance(user_id)

        if points is None:
            points = UserPoints(
                user_id=user_id,
                balance=0,
                total_earned=0,
                total_spent=0,
                current_streak=0,
                max_streak=0
            )
            self._session.add(points)
            await self._session.commit()
            await self._session.refresh(points)
            logger.debug(f"🎁 UserPoints creado para user {user_id}")

        return points

    # ===== TRANSACCIONES =====

    async def award_points(
        self,
        user_id: int,
        amount: int,
        transaction_type: Union[TransactionType, str],
        description: str,
        reference_id: Optional[int] = None
    ) -> PointsTransaction:
        """
        Otorga puntos a un usuario.

        Args:
            user_id: ID del usuario
            amount: Cantidad de puntos (debe ser positivo)
            transaction_type: Tipo de transacción (enum o string)
            description: Descripción de la transacción
            reference_id: ID de referencia (opcional)

        Returns:
            PointsTransaction: Transacción creada

        Raises:
            ValueError: Si amount es negativo o cero
        """
        if amount <= 0:
            raise ValueError("Amount debe ser positivo")

        # Normalizar transaction_type
        transaction_type = self._normalize_transaction_type(transaction_type)

        # Obtener o crear balance
        points = await self.get_or_create_points(user_id)

        # Actualizar balance
        points.balance += amount
        points.total_earned += amount
        points.updated_at = datetime.utcnow()

        # Crear transacción
        transaction = PointsTransaction(
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            reference_id=reference_id,
            description=description
        )

        self._session.add(transaction)
        await self._session.commit()
        await self._session.refresh(transaction)

        logger.info(
            f"💰 +{amount} puntos para user {user_id} "
            f"({transaction_type.value}): {description}"
        )

        return transaction

    async def spend_points(
        self,
        user_id: int,
        amount: int,
        transaction_type: Union[TransactionType, str],
        description: str,
        reference_id: Optional[int] = None
    ) -> Tuple[bool, str]:
        """
        Gasta puntos de un usuario.

        Args:
            user_id: ID del usuario
            amount: Cantidad de puntos (debe ser positivo)
            transaction_type: Tipo de transacción (enum o string)
            description: Descripción del gasto
            reference_id: ID de referencia (opcional)

        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        if amount <= 0:
            return False, "Amount debe ser positivo"

        # Normalizar transaction_type
        transaction_type = self._normalize_transaction_type(transaction_type)

        # Obtener balance
        points = await self.get_balance(user_id)

        if points is None:
            return False, "Usuario no tiene balance de puntos"

        # Verificar fondos suficientes
        if not points.has_enough_points(amount):
            return False, f"Puntos insuficientes (tienes: {points.balance}, necesitas: {amount})"

        # Actualizar balance
        points.balance -= amount
        points.total_spent += amount
        points.updated_at = datetime.utcnow()

        # Crear transacción (amount negativo para gasto)
        transaction = PointsTransaction(
            user_id=user_id,
            amount=-amount,  # Negativo = gasto
            transaction_type=transaction_type,
            reference_id=reference_id,
            description=description
        )

        self._session.add(transaction)
        await self._session.commit()

        logger.info(
            f"💸 -{amount} puntos de user {user_id} "
            f"({transaction_type.value}): {description}"
        )

        return True, f"Gastaste {amount} puntos"

    async def has_enough_points(self, user_id: int, amount: int) -> bool:
        """
        Verifica si un usuario tiene suficientes puntos.

        Args:
            user_id: ID del usuario
            amount: Cantidad de puntos necesaria

        Returns:
            bool: True si tiene suficientes puntos
        """
        points = await self.get_balance(user_id)
        if points is None:
            return False
        return points.has_enough_points(amount)

    # ===== REGALO DIARIO =====

    async def can_claim_daily_gift(self, user_id: int) -> bool:
        """
        Verifica si un usuario puede reclamar el regalo diario.

        Args:
            user_id: ID del usuario

        Returns:
            bool: True si puede reclamar
        """
        points = await self.get_balance(user_id)
        if points is None:
            return True  # Primer regalo

        return points.can_claim_daily_gift()

    async def claim_daily_gift(self, user_id: int) -> Tuple[bool, int, str]:
        """
        Reclama el regalo diario.

        Args:
            user_id: ID del usuario

        Returns:
            Tuple[bool, int, str]: (éxito, puntos_otorgados, mensaje)
        """
        # Verificar si puede reclamar
        if not await self.can_claim_daily_gift(user_id):
            points = await self.get_balance(user_id)
            if points and points.last_daily_gift:
                # Calcular tiempo restante
                time_since = datetime.utcnow() - points.last_daily_gift
                hours_left = 24 - int(time_since.total_seconds() / 3600)
                return False, 0, f"Debes esperar {hours_left}h para el próximo regalo"

        # Obtener config
        config = await self._get_config()
        gift_amount = config.daily_gift_points

        # Otorgar puntos
        await self.award_points(
            user_id=user_id,
            amount=gift_amount,
            transaction_type=TransactionType.DAILY_GIFT,
            description="🎁 Regalo diario"
        )

        # Actualizar last_daily_gift
        points = await self.get_or_create_points(user_id)
        points.last_daily_gift = datetime.utcnow()
        await self._session.commit()

        logger.info(f"🎁 User {user_id} reclamó regalo diario: {gift_amount} puntos")

        return True, gift_amount, f"¡Recibiste {gift_amount} puntos de regalo!"

    # ===== HISTORIAL =====

    async def get_transaction_history(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> List[PointsTransaction]:
        """
        Obtiene el historial de transacciones de un usuario.

        Args:
            user_id: ID del usuario
            limit: Máximo de resultados
            offset: Desplazamiento (para paginación)

        Returns:
            List[PointsTransaction]: Lista de transacciones
        """
        result = await self._session.execute(
            select(PointsTransaction)
            .where(PointsTransaction.user_id == user_id)
            .order_by(desc(PointsTransaction.created_at))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    # ===== LEADERBOARD =====

    async def get_leaderboard(self, limit: int = 10) -> List[Tuple[int, UserPoints]]:
        """
        Obtiene el leaderboard de usuarios por balance.

        Args:
            limit: Máximo de resultados

        Returns:
            List[Tuple[int, UserPoints]]: Lista de (posición, UserPoints)
        """
        result = await self._session.execute(
            select(UserPoints)
            .where(UserPoints.balance > 0)
            .order_by(desc(UserPoints.balance))
            .limit(limit)
        )
        points_list = list(result.scalars().all())

        # Agregar posición
        return [(i + 1, points) for i, points in enumerate(points_list)]

    async def get_user_leaderboard_position(self, user_id: int) -> Optional[int]:
        """
        Obtiene la posición de un usuario en el leaderboard.

        Args:
            user_id: ID del usuario

        Returns:
            int o None: Posición (1-indexed) o None si no está en ranking
        """
        points = await self.get_balance(user_id)
        if points is None or points.balance == 0:
            return None

        # Contar usuarios con mayor balance
        result = await self._session.execute(
            select(func.count(UserPoints.user_id))
            .where(UserPoints.balance > points.balance)
        )
        count = result.scalar()

        return count + 1  # Posición 1-indexed

    # ===== ESTADÍSTICAS =====

    async def get_total_points_issued(self) -> int:
        """
        Obtiene el total de puntos emitidos en el sistema.

        Returns:
            int: Total de puntos en circulación
        """
        result = await self._session.execute(
            select(func.sum(UserPoints.balance))
        )
        total = result.scalar()
        return total if total is not None else 0

    async def get_top_earners(self, limit: int = 10) -> List[UserPoints]:
        """
        Obtiene los usuarios que más puntos han ganado históricamente.

        Args:
            limit: Máximo de resultados

        Returns:
            List[UserPoints]: Lista ordenada por total_earned
        """
        result = await self._session.execute(
            select(UserPoints)
            .order_by(desc(UserPoints.total_earned))
            .limit(limit)
        )
        return list(result.scalars().all())

    # ===== ADMIN =====

    async def admin_grant_points(
        self,
        admin_id: int,
        target_user_id: int,
        amount: int,
        description: str
    ) -> Tuple[bool, str]:
        """
        Otorga puntos manualmente (función de admin).

        Args:
            admin_id: ID del admin que otorga los puntos
            target_user_id: ID del usuario que recibe los puntos
            amount: Cantidad de puntos
            description: Descripción del motivo

        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        try:
            await self.award_points(
                user_id=target_user_id,
                amount=amount,
                transaction_type=TransactionType.ADMIN_GRANT,
                description=f"[Admin {admin_id}] {description}"
            )

            logger.info(f"👑 Admin {admin_id} otorgó {amount} puntos a user {target_user_id}")
            return True, f"Otorgados {amount} puntos al usuario"

        except Exception as e:
            logger.error(f"Error otorgando puntos admin: {e}", exc_info=True)
            return False, f"Error: {str(e)}"

    async def admin_set_balance(
        self,
        admin_id: int,
        target_user_id: int,
        new_balance: int
    ) -> Tuple[bool, str]:
        """
        Establece directamente el balance de un usuario (función de admin).

        Args:
            admin_id: ID del admin
            target_user_id: ID del usuario
            new_balance: Nuevo balance

        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        try:
            points = await self.get_or_create_points(target_user_id)
            old_balance = points.balance
            points.balance = new_balance
            points.updated_at = datetime.utcnow()

            # Crear transacción de ajuste
            diff = new_balance - old_balance
            transaction = PointsTransaction(
                user_id=target_user_id,
                amount=diff,
                transaction_type=TransactionType.ADMIN_GRANT,
                description=f"[Admin {admin_id}] Ajuste manual: {old_balance} → {new_balance}"
            )
            self._session.add(transaction)
            await self._session.commit()

            logger.info(
                f"👑 Admin {admin_id} ajustó balance de user {target_user_id}: "
                f"{old_balance} → {new_balance}"
            )

            return True, f"Balance ajustado: {old_balance} → {new_balance}"

        except Exception as e:
            logger.error(f"Error ajustando balance: {e}", exc_info=True)
            return False, f"Error: {str(e)}"
