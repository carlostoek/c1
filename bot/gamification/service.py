"""
Gamification Service - Servicio principal de gamificación.

Maneja:
- Otorgar Besitos
- Verificar y desbloquear badges
- Actualizar rangos
- Daily login
"""
import logging
from datetime import datetime, date, timedelta
from typing import Optional, List, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import (
    UserProgress,
    UserBadge,
    DailyStreak,
    BesitosTransaction
)
from bot.gamification.config import GamificationConfig
from bot.events import event_bus, PointsAwardedEvent, BadgeUnlockedEvent, RankUpEvent

logger = logging.getLogger(__name__)


class GamificationService:
    """Servicio de gamificación."""

    def __init__(self, session: AsyncSession):
        """Inicializa el servicio."""
        self.session = session
        self.config = GamificationConfig

    async def get_or_create_progress(self, user_id: int) -> UserProgress:
        """
        Obtiene o crea el progreso de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            UserProgress del usuario
        """
        result = await self.session.execute(
            select(UserProgress).where(UserProgress.user_id == user_id)
        )
        progress = result.scalar_one_or_none()

        if not progress:
            # Crear progreso nuevo
            progress = UserProgress(
                user_id=user_id,
                total_besitos=0,
                current_rank="Novato",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.session.add(progress)

            # Crear daily streak
            streak = DailyStreak(user_id=user_id)
            self.session.add(streak)

            await self.session.commit()
            await self.session.refresh(progress)

            logger.info(f"✅ Progreso creado para user {user_id}")

        return progress

    async def award_besitos(
        self,
        user_id: int,
        action: str,
        custom_amount: Optional[int] = None,
        custom_reason: Optional[str] = None
    ) -> Tuple[int, bool, Optional[str]]:
        """
        Otorga Besitos a un usuario.

        Args:
            user_id: ID del usuario
            action: Acción que genera la recompensa (del config)
            custom_amount: Cantidad personalizada (opcional)
            custom_reason: Razón personalizada (opcional)

        Returns:
            Tuple[int, bool, Optional[str]]:
                - Cantidad otorgada
                - Si hubo rank up
                - Nuevo rango (si hubo cambio)

        Examples:
            >>> amount, ranked_up, new_rank = await service.award_besitos(
            ...     user_id=123,
            ...     action="message_reacted"
            ... )
        """
        # Obtener progreso
        progress = await self.get_or_create_progress(user_id)

        # Obtener reward del config
        if custom_amount is not None:
            amount = custom_amount
            reason = custom_reason or action
        else:
            reward = self.config.get_reward(action)
            if not reward:
                logger.warning(f"⚠️ Acción sin recompensa: {action}")
                return 0, False, None
            amount = reward.amount
            reason = reward.description

        # Guardar rango anterior
        old_rank = progress.current_rank
        old_besitos = progress.total_besitos

        # Otorgar Besitos
        progress.total_besitos += amount
        progress.updated_at = datetime.utcnow()

        # Verificar cambio de rango
        new_rank_obj = self.config.get_rank_for_besitos(progress.total_besitos)
        ranked_up = new_rank_obj.name != old_rank

        if ranked_up:
            progress.current_rank = new_rank_obj.name
            logger.info(
                f"⭐ Rank up: User {user_id} | {old_rank} → {new_rank_obj.name}"
            )

        # Guardar transacción
        transaction = BesitosTransaction(
            user_id=user_id,
            amount=amount,
            reason=reason,
            created_at=datetime.utcnow()
        )
        self.session.add(transaction)

        await self.session.commit()
        await self.session.refresh(progress)

        logger.info(
            f"💋 Besitos otorgados: User {user_id} | +{amount} | "
            f"Total: {progress.total_besitos} | Razón: {reason}"
        )

        # Emitir evento de puntos
        event_bus.publish(PointsAwardedEvent(
            user_id=user_id,
            points=amount,
            reason=reason,
            source_event=action
        ))

        # Emitir evento de rank up si aplica
        if ranked_up:
            event_bus.publish(RankUpEvent(
                user_id=user_id,
                old_rank=old_rank,
                new_rank=new_rank_obj.name,
                total_points=progress.total_besitos
            ))

        return amount, ranked_up, new_rank_obj.name if ranked_up else None

    async def check_and_unlock_badges(self, user_id: int) -> List[str]:
        """
        Verifica y desbloquea badges que el usuario haya ganado.

        Args:
            user_id: ID del usuario

        Returns:
            Lista de IDs de badges desbloqueados (nuevos)
        """
        progress = await self.get_or_create_progress(user_id)

        # Obtener badges ya desbloqueados
        unlocked_badge_ids = {badge.badge_id for badge in progress.badges}

        # Verificar cada badge del config
        new_badges = []

        for badge_def in self.config.BADGES:
            # Si ya lo tiene, skip
            if badge_def.id in unlocked_badge_ids:
                continue

            # Verificar requisito
            meets_requirement = await self._check_badge_requirement(
                user_id,
                progress,
                badge_def
            )

            if meets_requirement:
                # Desbloquear badge
                user_badge = UserBadge(
                    user_id=user_id,
                    badge_id=badge_def.id,
                    unlocked_at=datetime.utcnow()
                )
                self.session.add(user_badge)
                new_badges.append(badge_def.id)

                logger.info(
                    f"🏆 Badge desbloqueado: User {user_id} | {badge_def.name}"
                )

                # Emitir evento
                event_bus.publish(BadgeUnlockedEvent(
                    user_id=user_id,
                    badge_id=badge_def.id,
                    badge_name=badge_def.name
                ))

        if new_badges:
            await self.session.commit()

        return new_badges

    async def _check_badge_requirement(
        self,
        user_id: int,
        progress: UserProgress,
        badge_def
    ) -> bool:
        """Verifica si se cumple el requisito de un badge."""
        req_type = badge_def.requirement_type
        req_value = badge_def.requirement_value

        if req_type == "total_besitos":
            return progress.total_besitos >= req_value

        elif req_type == "total_reactions":
            return progress.total_reactions >= req_value

        elif req_type == "daily_streak":
            if progress.daily_streak:
                return progress.daily_streak.current_streak >= req_value
            return False

        elif req_type == "vip_active":
            # Verificar si tiene VIP activo
            from bot.database.models import User, VIPSubscriber
            from bot.database.enums import UserRole

            result = await self.session.execute(
                select(VIPSubscriber).where(VIPSubscriber.user_id == user_id)
            )
            vip = result.scalar_one_or_none()
            return vip is not None and vip.status == "active" and not vip.is_expired()

        return False

    async def claim_daily_login(
        self,
        user_id: int
    ) -> Tuple[int, int, bool]:
        """
        Reclama el regalo diario.

        Args:
            user_id: ID del usuario

        Returns:
            Tuple[int, int, bool]:
                - Besitos ganados
                - Días de racha actual
                - Si es nuevo récord

        Raises:
            ValueError: Si ya reclamó hoy
        """
        progress = await self.get_or_create_progress(user_id)

        # Obtener o crear streak
        if not progress.daily_streak:
            streak = DailyStreak(user_id=user_id)
            self.session.add(streak)
            await self.session.flush()
        else:
            streak = progress.daily_streak

        today = date.today()

        # Verificar si ya reclamó hoy
        if streak.last_login_date == today:
            raise ValueError("Ya reclamaste tu regalo diario hoy")

        # Actualizar streak
        if streak.last_login_date == today - timedelta(days=1):
            # Login consecutivo
            streak.current_streak += 1
        elif streak.last_login_date is None or streak.last_login_date < today - timedelta(days=1):
            # Se rompió la racha o es primer login
            streak.current_streak = 1

        streak.last_login_date = today
        streak.total_logins += 1

        # Verificar nuevo récord
        is_new_record = streak.current_streak > streak.longest_streak
        if is_new_record:
            streak.longest_streak = streak.current_streak

        # Calcular Besitos
        base_reward = self.config.get_reward("daily_login_base").amount
        streak_bonus = self.config.get_reward("daily_login_streak_bonus").amount
        streak_bonus_total = (streak.current_streak - 1) * streak_bonus

        total_besitos = base_reward + streak_bonus_total

        # Otorgar Besitos
        await self.award_besitos(
            user_id=user_id,
            action="daily_login",
            custom_amount=total_besitos,
            custom_reason=f"Regalo diario (racha de {streak.current_streak} días)"
        )

        await self.session.commit()

        logger.info(
            f"🎁 Daily login: User {user_id} | Racha: {streak.current_streak} | "
            f"Besitos: {total_besitos}"
        )

        return total_besitos, streak.current_streak, is_new_record

    async def can_react_to_message(self, user_id: int) -> bool:
        """
        Verifica si el usuario puede reaccionar a un mensaje (rate limiting).

        Args:
            user_id: ID del usuario

        Returns:
            True si puede reaccionar, False si no
        """
        progress = await self.get_or_create_progress(user_id)

        # Verificar límite diario
        if progress.reactions_today >= self.config.MAX_REACTIONS_PER_DAY:
            return False

        # Verificar tiempo mínimo entre reacciones
        if progress.last_reaction_at:
            seconds_since_last = (datetime.utcnow() - progress.last_reaction_at).total_seconds()
            if seconds_since_last < self.config.MIN_SECONDS_BETWEEN_REACTIONS:
                return False

        return True

    async def record_reaction(self, user_id: int):
        """
        Registra una reacción del usuario.

        Args:
            user_id: ID del usuario
        """
        progress = await self.get_or_create_progress(user_id)

        progress.total_reactions += 1
        progress.reactions_today += 1
        progress.last_reaction_at = datetime.utcnow()
        progress.updated_at = datetime.utcnow()

        await self.session.commit()
