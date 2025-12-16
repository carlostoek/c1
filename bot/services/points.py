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
