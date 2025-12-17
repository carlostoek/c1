"""
Rewards Service - Gestión de catálogo y canjes de recompensas.

Responsabilidades:
- Obtener recompensas disponibles para usuarios
- Validar si un usuario puede canjear una recompensa
- Ejecutar canjes (deducir puntos, entregar recompensa, registrar histórico)
- Consultar histórico de canjes
- Entregar contenido de recompensas según tipo

Características:
- Soporte para múltiples tipos de recompensa (badge, content, points, role, custom)
- Límites de canje (once, daily, weekly, unlimited)
- Requisitos de nivel y VIP
- Stock configurable
- Validación atómica de canjes
"""
import logging
from typing import List, Optional, Tuple, Dict
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import Reward, UserReward, RewardLimit, RewardType

logger = logging.getLogger(__name__)


class RewardsService:
    """
    Servicio de gestión de recompensas canjeables por puntos.

    Métodos principales:
    - get_available_rewards(): Obtiene recompensas disponibles para usuario
    - can_redeem(): Valida si puede canjear una recompensa
    - redeem_reward(): Ejecuta el canje
    - get_user_rewards(): Obtiene histórico de canjes
    """

    def __init__(self, session: AsyncSession, container=None):
        """
        Inicializa el servicio.

        Args:
            session: Sesión de base de datos
            container: ServiceContainer (para acceso a otros servicios)
        """
        self.session = session
        self.container = container
        self._logger = logging.getLogger(__name__)

    # ===== CATÁLOGO =====

    async def get_available_rewards(
        self,
        user_id: int,
        reward_type: Optional[RewardType] = None
    ) -> List[Reward]:
        """
        Obtiene recompensas disponibles para un usuario.

        Filtra por:
        - Nivel requerido
        - Requisito VIP
        - Stock disponible
        - Actividad de la recompensa

        Args:
            user_id: ID del usuario
            reward_type: Tipo específico a filtrar (opcional)

        Returns:
            Lista de Reward disponibles
        """
        try:
            # Obtener nivel del usuario
            level = 1
            is_vip = False
            if self.container:
                try:
                    level = await self.container.levels.get_user_level(user_id)
                except Exception:
                    level = 1
                # TODO: Verificar VIP cuando esté disponible

            # Query base
            query = select(Reward).where(
                and_(
                    Reward.is_active == True,
                    Reward.required_level <= level
                )
            )

            # Filtrar por tipo si se especifica
            if reward_type:
                query = query.where(Reward.reward_type == reward_type)

            # Filtrar si no es VIP
            if not is_vip:
                query = query.where(Reward.is_vip_only == False)

            result = await self.session.execute(query)
            rewards = list(result.scalars().all())

            # Filtrar por stock
            available = [r for r in rewards if r.is_available]

            self._logger.debug(
                f"Recompensas disponibles para user {user_id}: {len(available)}"
            )
            return available

        except Exception as e:
            self._logger.error(f"Error getting available rewards: {e}", exc_info=True)
            return []

    # ===== VALIDACIÓN =====

    async def can_redeem(
        self,
        user_id: int,
        reward_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida si un usuario puede canjear una recompensa.

        Verifica:
        - Recompensa existe y está activa
        - Stock disponible
        - Nivel requerido
        - VIP (si aplica)
        - Saldo suficiente
        - Límites de canje

        Args:
            user_id: ID del usuario
            reward_id: ID de la recompensa

        Returns:
            (puede_canjear, mensaje_error)
        """
        try:
            # Obtener recompensa
            result = await self.session.execute(
                select(Reward).where(Reward.id == reward_id)
            )
            reward = result.scalar_one_or_none()

            if not reward:
                return False, "Recompensa no encontrada"

            if not reward.is_active:
                return False, "Recompensa no disponible"

            # Stock
            if reward.stock is not None and reward.stock <= 0:
                return False, "Sin stock disponible"

            # Nivel
            if self.container:
                try:
                    level = await self.container.levels.get_user_level(user_id)
                    if level < reward.required_level:
                        return False, f"Requiere nivel {reward.required_level}"
                except Exception:
                    pass

            # VIP (cuando esté disponible)
            if reward.is_vip_only:
                # TODO: Verificar VIP del usuario
                pass

            # Saldo
            if self.container:
                try:
                    balance = await self.container.points.get_user_balance(user_id)
                    if balance < reward.cost:
                        return (
                            False,
                            f"Saldo insuficiente (necesitas {reward.cost} 💋)"
                        )
                except Exception as e:
                    self._logger.error(f"Error checking balance: {e}")
                    return False, "Error al verificar saldo"

            # Límites
            if reward.limit_type != RewardLimit.UNLIMITED:
                can_redeem_limit = await self._check_redeem_limit(
                    user_id, reward_id, reward.limit_type
                )
                if not can_redeem_limit:
                    limit_names = {
                        RewardLimit.ONCE: "Ya canjeaste esta recompensa",
                        RewardLimit.DAILY: "Ya canjeaste hoy, vuelve mañana",
                        RewardLimit.WEEKLY: "Ya canjeaste esta semana",
                    }
                    return False, limit_names.get(reward.limit_type, "Límite alcanzado")

            return True, None

        except Exception as e:
            self._logger.error(f"Error validating redeem: {e}", exc_info=True)
            return False, "Error al validar"

    async def _check_redeem_limit(
        self,
        user_id: int,
        reward_id: int,
        limit_type: RewardLimit
    ) -> bool:
        """
        Verifica si el usuario respeta los límites de canje.

        Args:
            user_id: ID del usuario
            reward_id: ID de la recompensa
            limit_type: Tipo de límite

        Returns:
            True si puede canjear, False si ya alcanzó el límite
        """
        try:
            now = datetime.now(timezone.utc)

            query = select(UserReward).where(
                and_(
                    UserReward.user_id == user_id,
                    UserReward.reward_id == reward_id
                )
            )

            # ONCE: Verificar si existe alguno
            if limit_type == RewardLimit.ONCE:
                result = await self.session.execute(query)
                existing = result.scalar_one_or_none()
                return existing is None

            # DAILY: Verificar si canjeó hoy
            if limit_type == RewardLimit.DAILY:
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                daily_query = query.where(UserReward.redeemed_at >= today_start)
                result = await self.session.execute(daily_query)
                existing = result.scalar_one_or_none()
                return existing is None

            # WEEKLY: Verificar si canjeó esta semana
            if limit_type == RewardLimit.WEEKLY:
                week_start = now.date() - timedelta(days=now.weekday())
                week_start_dt = datetime.combine(
                    week_start, datetime.min.time()
                ).replace(tzinfo=timezone.utc)
                weekly_query = query.where(UserReward.redeemed_at >= week_start_dt)
                result = await self.session.execute(weekly_query)
                existing = result.scalar_one_or_none()
                return existing is None

            return True

        except Exception as e:
            self._logger.error(f"Error checking limit: {e}", exc_info=True)
            return False

    # ===== CANJE =====

    async def redeem_reward(
        self,
        user_id: int,
        reward_id: int
    ) -> Tuple[bool, Optional[str], Optional[UserReward]]:
        """
        Ejecuta el canje de una recompensa.

        Proceso atómico:
        1. Validar que puede canjear
        2. Obtener recompensa
        3. Deducir puntos
        4. Crear registro UserReward
        5. Actualizar stock
        6. Entregar contenido
        7. Commit

        Args:
            user_id: ID del usuario
            reward_id: ID de la recompensa

        Returns:
            (éxito, mensaje, user_reward)
        """
        try:
            # Validar
            can_redeem, error = await self.can_redeem(user_id, reward_id)
            if not can_redeem:
                return False, error, None

            # Obtener recompensa
            result = await self.session.execute(
                select(Reward).where(Reward.id == reward_id)
            )
            reward = result.scalar_one_or_none()

            if not reward:
                return False, "Recompensa no encontrada", None

            # Transacción atómica
            try:
                async with self.session.begin_nested():
                    # 1. Deducir puntos
                    if self.container:
                        success = await self.container.points.deduct_points(
                            user_id=user_id,
                            amount=reward.cost,
                            reason=f"Canje: {reward.name}",
                            metadata={"reward_id": reward.id}
                        )

                        if not success:
                            return False, "Error al deducir puntos", None

                    # 2. Crear UserReward
                    user_reward = UserReward(
                        user_id=user_id,
                        reward_id=reward_id,
                        cost_paid=reward.cost
                    )
                    self.session.add(user_reward)
                    await self.session.flush()

                    # 3. Actualizar stock
                    if reward.stock is not None:
                        reward.stock -= 1

                    # 4. Entregar recompensa
                    await self._deliver_reward_content(user_id, reward, user_reward)

                    await self.session.commit()

                self._logger.info(
                    f"Reward redeemed: user={user_id}, reward={reward.name}, "
                    f"cost={reward.cost}"
                )

                return True, f"✅ Canjeaste: {reward.display_name}", user_reward

            except Exception as e:
                await self.session.rollback()
                self._logger.error(f"Transaction error: {e}", exc_info=True)
                return False, "Error al procesar el canje", None

        except Exception as e:
            self._logger.error(f"Error redeeming reward: {e}", exc_info=True)
            return False, "Error inesperado", None

    async def _deliver_reward_content(
        self,
        user_id: int,
        reward: Reward,
        user_reward: UserReward
    ):
        """
        Entrega el contenido específico de la recompensa.

        Según el tipo:
        - BADGE: Asigna badge al usuario
        - POINTS: Otorga puntos extra
        - CONTENT: Desbloquea contenido
        - ROLE/CUSTOM: Extensible

        Args:
            user_id: ID del usuario
            reward: Objeto Reward
            user_reward: Objeto UserReward (para marcar entregado)
        """
        try:
            # BADGE: Asignar badge
            if reward.reward_type == RewardType.BADGE and reward.badge_id:
                if self.container:
                    try:
                        await self.container.badges.assign_badge(
                            user_id=user_id,
                            badge_id=reward.badge_id,
                            source="reward"
                        )
                        self._logger.info(
                            f"Assigned badge {reward.badge_id} to user {user_id}"
                        )
                    except Exception as e:
                        self._logger.error(f"Error assigning badge: {e}")

            # POINTS: Otorgar puntos extra
            if reward.reward_type == RewardType.POINTS and reward.points_amount > 0:
                if self.container:
                    try:
                        await self.container.points.award_points(
                            user_id=user_id,
                            amount=reward.points_amount,
                            reason=f"Recompensa: {reward.name}",
                            apply_multipliers=False
                        )
                        self._logger.info(
                            f"Awarded {reward.points_amount} points to user {user_id}"
                        )
                    except Exception as e:
                        self._logger.error(f"Error awarding points: {e}")

            # CONTENT: Desbloquear (implementación futura)
            if reward.reward_type == RewardType.CONTENT and reward.content_id:
                self._logger.info(f"Unlocked content {reward.content_id} for {user_id}")

            # Marcar como entregado
            user_reward.is_delivered = True
            user_reward.delivered_at = datetime.now(timezone.utc)

        except Exception as e:
            self._logger.error(f"Error delivering reward content: {e}", exc_info=True)

    # ===== HISTÓRICO =====

    async def get_user_rewards(
        self,
        user_id: int,
        limit: int = 20
    ) -> List[UserReward]:
        """
        Obtiene el histórico de canjes de un usuario.

        Args:
            user_id: ID del usuario
            limit: Cantidad máxima de registros

        Returns:
            Lista de UserReward (más recientes primero)
        """
        try:
            result = await self.session.execute(
                select(UserReward)
                .where(UserReward.user_id == user_id)
                .order_by(UserReward.redeemed_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())

        except Exception as e:
            self._logger.error(f"Error getting user rewards: {e}", exc_info=True)
            return []

    # ===== ADMIN =====

    async def create_reward(
        self,
        name: str,
        description: str,
        icon: str,
        reward_type: RewardType,
        cost: int,
        limit_type: RewardLimit = RewardLimit.ONCE,
        required_level: int = 1,
        is_vip_only: bool = False,
        badge_id: Optional[int] = None,
        points_amount: int = 0,
        stock: Optional[int] = None,
        reward_metadata: Optional[Dict] = None
    ) -> Optional[Reward]:
        """
        Crea una nueva recompensa (admin).

        Args:
            name: Nombre de la recompensa
            description: Descripción
            icon: Emoji
            reward_type: Tipo de recompensa
            cost: Costo en besitos
            limit_type: Límite de canje
            required_level: Nivel mínimo
            is_vip_only: Solo para VIP
            badge_id: ID del badge (si aplica)
            points_amount: Cantidad de puntos (si es POINTS)
            stock: Stock disponible
            reward_metadata: Datos adicionales

        Returns:
            Reward creado o None si error
        """
        try:
            reward = Reward(
                name=name,
                description=description,
                icon=icon,
                reward_type=reward_type,
                cost=cost,
                limit_type=limit_type,
                required_level=required_level,
                is_vip_only=is_vip_only,
                badge_id=badge_id,
                points_amount=points_amount,
                stock=stock,
                reward_metadata=reward_metadata
            )
            self.session.add(reward)
            await self.session.flush()

            self._logger.info(f"Created reward: {reward.name} (id={reward.id})")
            return reward

        except Exception as e:
            self._logger.error(f"Error creating reward: {e}", exc_info=True)
            raise

    async def toggle_reward(self, reward_id: int, active: bool) -> Optional[Reward]:
        """
        Activa o desactiva una recompensa.

        Args:
            reward_id: ID de la recompensa
            active: True para activar, False para desactivar

        Returns:
            Reward actualizado o None
        """
        try:
            result = await self.session.execute(
                select(Reward).where(Reward.id == reward_id)
            )
            reward = result.scalar_one_or_none()

            if not reward:
                return None

            reward.is_active = active
            await self.session.flush()

            self._logger.info(f"Toggled reward {reward_id}: active={active}")
            return reward

        except Exception as e:
            self._logger.error(f"Error toggling reward: {e}", exc_info=True)
            return None
