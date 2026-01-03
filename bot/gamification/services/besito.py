"""Servicio de gestión de economía de besitos.

Responsabilidades:
- Otorgar besitos a usuarios
- Deducir besitos (compras, penalizaciones)
- Consultar balance
- Auditoría de transacciones
"""

from typing import Optional, List
from datetime import datetime, UTC
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from bot.gamification.database.models import UserGamification, BesitoTransaction
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

        # Crear registro de transacción
        transaction = BesitoTransaction(
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type.value,
            description=description or f"Besitos otorgados ({transaction_type.value})",
            reference_id=reference_id,
            balance_after=user_gamif.total_besitos,
            created_at=datetime.now(UTC)
        )
        self.session.add(transaction)

        await self.session.commit()
        await self.session.refresh(user_gamif)

        logger.info(
            f"Granted {amount} besitos to user {user_id} "
            f"({transaction_type.value}). New balance: {user_gamif.total_besitos}"
        )

        # Verificar y aplicar level-up automático
        try:
            from bot.gamification.services.level import LevelService
            level_service = LevelService(self.session)
            changed, old_level, new_level = await level_service.check_and_apply_level_up(user_id)

            if changed:
                logger.info(
                    f"✨ Auto level-up triggered: User {user_id} "
                    f"{old_level.name if old_level else 'None'} → {new_level.name}"
                )

                # Notificar level-up
                try:
                    from bot.gamification.services.container import get_container
                    container = get_container()
                    await container.notifications.notify_level_up(
                        user_id, old_level, new_level
                    )
                except RuntimeError:
                    # Container no inicializado (ej: en tests)
                    logger.warning("Container not available for level-up notification")
                except Exception as e:
                    logger.error(f"Could not send level-up notification: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Error checking level-up for user {user_id}: {e}", exc_info=True)

        # Verificar y otorgar recompensas automáticas desbloqueadas
        try:
            from bot.gamification.services.reward import RewardService
            reward_service = RewardService(self.session)
            granted = await reward_service.check_and_grant_unlocked_rewards(user_id)

            if granted:
                for reward, msg in granted:
                    logger.info(
                        f"Auto-unlocked reward '{reward.name}' "
                        f"for user {user_id} after reaching {user_gamif.total_besitos} besitos"
                    )

                # Intentar notificar usando el container global
                try:
                    from bot.gamification.services.container import get_container
                    container = get_container()
                    logger.info(f"📢 Attempting to send notifications for {len(granted)} rewards")

                    for reward, _ in granted:
                        logger.info(f"📢 Sending notification for reward: {reward.name}")
                        await container.notifications.notify_reward_unlocked(
                            user_id, reward
                        )
                        logger.info(f"✅ Notification sent successfully for reward: {reward.name}")

                except RuntimeError as e:
                    # Container no inicializado (ej: en tests)
                    logger.warning(f"❌ Container not available for notifications: {e}")
                except Exception as e:
                    logger.error(f"❌ Could not send reward notification: {e}", exc_info=True)

        except Exception as e:
            logger.error(
                f"Error checking/granting auto-unlock rewards for user {user_id}: {e}",
                exc_info=True
            )

        # Verificar y notificar milestone de besitos totales
        try:
            from bot.gamification.config.economy import EconomyConfig
            if EconomyConfig.is_milestone(user_gamif.total_besitos):
                try:
                    from bot.gamification.services.container import get_container
                    container = get_container()
                    await container.notifications.notify_besitos_milestone(
                        user_id, int(user_gamif.total_besitos)
                    )
                except RuntimeError:
                    # Container no inicializado (ej: en tests)
                    logger.warning("Container not available for besitos milestone notification")
                except Exception as e:
                    logger.error(f"Could not send besitos milestone notification: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Error checking besitos milestone for user {user_id}: {e}", exc_info=True)

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

        # Crear registro de transacción (amount negativo)
        transaction = BesitoTransaction(
            user_id=user_id,
            amount=-amount,  # Negativo para indicar gasto
            transaction_type=transaction_type.value,
            description=description or f"Besitos gastados ({transaction_type.value})",
            reference_id=reference_id,
            balance_after=user_gamif.total_besitos,
            created_at=datetime.now(UTC)
        )
        self.session.add(transaction)

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

    # ========================================
    # HISTORIAL DE TRANSACCIONES
    # ========================================

    async def get_transaction_history(
        self,
        user_id: int,
        transaction_type: Optional[TransactionType] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[BesitoTransaction]:
        """Obtiene historial de transacciones del usuario.

        Args:
            user_id: ID del usuario
            transaction_type: Filtrar por tipo (opcional)
            limit: Cantidad máxima de resultados
            offset: Offset para paginación

        Returns:
            Lista de BesitoTransaction ordenadas por fecha DESC
        """
        stmt = select(BesitoTransaction).where(BesitoTransaction.user_id == user_id)

        if transaction_type:
            stmt = stmt.where(BesitoTransaction.transaction_type == transaction_type.value)

        stmt = stmt.order_by(BesitoTransaction.created_at.desc())
        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_transaction_stats(self, user_id: int) -> dict:
        """Obtiene estadísticas de transacciones del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Dict con estadísticas:
            {
                'total_earned': int,
                'total_spent': int,
                'total_transactions': int,
                'by_type': {
                    'reaction': {'count': int, 'total': int},
                    'purchase': {'count': int, 'total': int},
                    ...
                }
            }
        """
        # Total ganado (transacciones positivas)
        stmt_earned = select(
            func.coalesce(func.sum(BesitoTransaction.amount), 0)
        ).where(
            BesitoTransaction.user_id == user_id,
            BesitoTransaction.amount > 0
        )
        result_earned = await self.session.execute(stmt_earned)
        total_earned = result_earned.scalar() or 0

        # Total gastado (transacciones negativas, valor absoluto)
        stmt_spent = select(
            func.coalesce(func.sum(BesitoTransaction.amount), 0)
        ).where(
            BesitoTransaction.user_id == user_id,
            BesitoTransaction.amount < 0
        )
        result_spent = await self.session.execute(stmt_spent)
        total_spent = abs(result_spent.scalar() or 0)

        # Total de transacciones
        stmt_count = select(
            func.count()
        ).select_from(BesitoTransaction).where(
            BesitoTransaction.user_id == user_id
        )
        result_count = await self.session.execute(stmt_count)
        total_transactions = result_count.scalar() or 0

        # Por tipo
        stmt_by_type = select(
            BesitoTransaction.transaction_type,
            func.count(BesitoTransaction.id).label('count'),
            func.sum(BesitoTransaction.amount).label('total')
        ).where(
            BesitoTransaction.user_id == user_id
        ).group_by(BesitoTransaction.transaction_type)

        result_by_type = await self.session.execute(stmt_by_type)
        by_type = {}
        for row in result_by_type:
            by_type[row.transaction_type] = {
                'count': row.count,
                'total': row.total or 0
            }

        return {
            'total_earned': total_earned,
            'total_spent': total_spent,
            'total_transactions': total_transactions,
            'by_type': by_type
        }

    async def get_total_transactions_count(
        self,
        user_id: int,
        transaction_type: Optional[TransactionType] = None
    ) -> int:
        """Obtiene total de transacciones para paginación.

        Args:
            user_id: ID del usuario
            transaction_type: Filtrar por tipo (opcional)

        Returns:
            Total de transacciones
        """
        stmt = select(func.count()).select_from(BesitoTransaction).where(
            BesitoTransaction.user_id == user_id
        )

        if transaction_type:
            stmt = stmt.where(BesitoTransaction.transaction_type == transaction_type.value)

        result = await self.session.execute(stmt)
        return result.scalar() or 0
