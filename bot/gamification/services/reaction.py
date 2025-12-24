"""Servicio de gestión de reacciones.

Responsabilidades:
- CRUD de catálogo de reacciones
- Registro de reacciones de usuarios
- Otorgamiento de besitos por reacciones
- Actualización de rachas
- Anti-spam y validaciones
"""

from typing import Optional, List, Tuple
from datetime import datetime, UTC, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from bot.gamification.database.models import (
    Reaction,
    UserReaction,
    UserStreak,
    UserGamification
)
from bot.gamification.database.enums import TransactionType

logger = logging.getLogger(__name__)


class ReactionService:
    """Servicio de gestión de reacciones y rachas."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ========================================
    # CATÁLOGO DE REACCIONES
    # ========================================

    async def create_reaction(
        self,
        emoji: str,
        besitos_value: int = 1
    ) -> Reaction:
        """Crea nueva reacción en catálogo.

        Args:
            emoji: Emoji de la reacción
            besitos_value: Besitos que otorga

        Returns:
            Reacción creada
        """
        reaction = Reaction(
            emoji=emoji,
            besitos_value=besitos_value,
            active=True
        )
        self.session.add(reaction)
        await self.session.commit()
        await self.session.refresh(reaction)

        logger.info(f"Created reaction: {emoji} ({besitos_value} besitos)")
        return reaction

    async def update_reaction(
        self,
        reaction_id: int,
        besitos_value: Optional[int] = None,
        active: Optional[bool] = None
    ) -> Optional[Reaction]:
        """Actualiza una reacción existente.

        Args:
            reaction_id: ID de la reacción
            besitos_value: Nuevo valor de besitos
            active: Nuevo estado activo/inactivo

        Returns:
            Reacción actualizada o None si no existe
        """
        reaction = await self.session.get(Reaction, reaction_id)
        if not reaction:
            logger.warning(f"Reaction {reaction_id} not found")
            return None

        if besitos_value is not None:
            reaction.besitos_value = besitos_value
        if active is not None:
            reaction.active = active

        await self.session.commit()
        await self.session.refresh(reaction)

        logger.info(f"Updated reaction {reaction_id}: {reaction.emoji}")
        return reaction

    async def delete_reaction(self, reaction_id: int) -> bool:
        """Elimina una reacción del catálogo.

        Args:
            reaction_id: ID de la reacción

        Returns:
            True si se eliminó, False si no existía
        """
        reaction = await self.session.get(Reaction, reaction_id)
        if not reaction:
            return False

        await self.session.delete(reaction)
        await self.session.commit()

        logger.info(f"Deleted reaction {reaction_id}: {reaction.emoji}")
        return True

    async def get_all_reactions(
        self,
        active_only: bool = True
    ) -> List[Reaction]:
        """Obtiene todas las reacciones.

        Args:
            active_only: Solo reacciones activas

        Returns:
            Lista de reacciones
        """
        stmt = select(Reaction)
        if active_only:
            stmt = stmt.where(Reaction.active == True)

        stmt = stmt.order_by(Reaction.emoji)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_reaction_by_emoji(
        self,
        emoji: str
    ) -> Optional[Reaction]:
        """Busca reacción por emoji.

        Args:
            emoji: Emoji a buscar

        Returns:
            Reacción o None si no existe
        """
        stmt = select(Reaction).where(Reaction.emoji == emoji)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ========================================
    # REGISTRO DE REACCIONES
    # ========================================

    async def record_reaction(
        self,
        user_id: int,
        emoji: str,
        channel_id: int,
        message_id: int
    ) -> Tuple[bool, str, int]:
        """Registra reacción de usuario y otorga besitos.

        Args:
            user_id: ID del usuario
            emoji: Emoji de la reacción
            channel_id: ID del canal
            message_id: ID del mensaje

        Returns:
            (success, message, besitos_granted)
        """
        # 1. Validar que reacción existe y está activa
        reaction = await self.get_reaction_by_emoji(emoji)
        if not reaction or not reaction.active:
            return False, f"Reacción {emoji} no configurada o inactiva", 0

        # 2. Validar anti-spam: no reaccionar dos veces al mismo mensaje
        if await self._has_reacted_to_message(user_id, message_id):
            return False, "Ya reaccionaste a este mensaje", 0

        # 3. Validar límite diario
        can_react, besitos_today = await self._check_daily_limit(user_id)
        if not can_react:
            return False, f"Límite diario alcanzado ({besitos_today} besitos)", 0

        # 4. Crear registro de reacción
        user_reaction = UserReaction(
            user_id=user_id,
            reaction_id=reaction.id,
            channel_id=channel_id,
            message_id=message_id,
            reacted_at=datetime.now(UTC)
        )
        self.session.add(user_reaction)
        await self.session.commit()
        await self.session.refresh(user_reaction)

        # 5. Otorgar besitos
        besitos_granted = await self.session.container.besito.grant_besitos(
            user_id=user_id,
            amount=reaction.besitos_value,
            transaction_type=TransactionType.REACTION,
            description=f"Reacción {emoji} en canal",
            reference_id=user_reaction.id
        )

        # 6. Actualizar racha
        streak = await self._update_user_streak(user_id)

        logger.info(
            f"User {user_id} reacted with {emoji}: "
            f"+{besitos_granted} besitos, streak: {streak.current_streak}"
        )

        return True, f"+{besitos_granted} besitos (racha: {streak.current_streak})", besitos_granted

    # ========================================
    # VALIDACIONES
    # ========================================

    async def _has_reacted_to_message(
        self,
        user_id: int,
        message_id: int
    ) -> bool:
        """Verifica si usuario ya reaccionó a este mensaje.

        Args:
            user_id: ID del usuario
            message_id: ID del mensaje

        Returns:
            True si ya reaccionó
        """
        stmt = select(func.count()).select_from(UserReaction).where(
            UserReaction.user_id == user_id,
            UserReaction.message_id == message_id
        )
        result = await self.session.execute(stmt)
        count = result.scalar()
        return count > 0

    async def _check_daily_limit(self, user_id: int) -> Tuple[bool, int]:
        """Verifica límite diario de besitos.

        Args:
            user_id: ID del usuario

        Returns:
            (can_react, besitos_earned_today)
        """
        from bot.gamification.config import GamificationConfig

        max_daily = GamificationConfig.MAX_BESITOS_PER_DAY
        if max_daily is None or max_daily <= 0:
            return True, 0  # Sin límite

        # Contar besitos de hoy desde reacciones
        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

        stmt = select(func.coalesce(func.sum(Reaction.besitos_value), 0)).select_from(
            UserReaction
        ).join(
            Reaction
        ).where(
            UserReaction.user_id == user_id,
            UserReaction.reacted_at >= today_start
        )
        result = await self.session.execute(stmt)
        besitos_today = result.scalar() or 0

        can_react = besitos_today < max_daily
        return can_react, besitos_today

    # ========================================
    # RACHAS
    # ========================================

    async def _update_user_streak(self, user_id: int) -> UserStreak:
        """Actualiza racha del usuario.

        Lógica:
        1. Obtener UserStreak (crear si no existe)
        2. Comparar last_reaction_date con hoy
        3. Si es consecutivo → current_streak += 1
        4. Si saltó días → current_streak = 1
        5. Si current_streak > longest_streak → actualizar récord
        6. Actualizar last_reaction_date

        Args:
            user_id: ID del usuario

        Returns:
            UserStreak actualizado
        """
        # Obtener o crear streak
        streak = await self._get_or_create_streak(user_id)

        today = datetime.now(UTC).date()
        last_date = streak.last_reaction_date.date() if streak.last_reaction_date else None

        if last_date is None:
            # Primera reacción
            streak.current_streak = 1
        elif last_date == today:
            # Ya reaccionó hoy, no modificar streak
            pass
        elif last_date == today - timedelta(days=1):
            # Día consecutivo
            streak.current_streak += 1
        else:
            # Rompió racha
            streak.current_streak = 1

        # Actualizar récord
        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak

        streak.last_reaction_date = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(streak)

        return streak

    async def _get_or_create_streak(self, user_id: int) -> UserStreak:
        """Obtiene o crea racha del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            UserStreak del usuario
        """
        stmt = select(UserStreak).where(UserStreak.user_id == user_id)
        result = await self.session.execute(stmt)
        streak = result.scalar_one_or_none()

        if not streak:
            streak = UserStreak(user_id=user_id)
            self.session.add(streak)
            await self.session.commit()
            await self.session.refresh(streak)
            logger.info(f"Created UserStreak for user {user_id}")

        return streak

    async def get_user_streak(self, user_id: int) -> Optional[UserStreak]:
        """Obtiene racha actual del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            UserStreak o None
        """
        stmt = select(UserStreak).where(UserStreak.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ========================================
    # ESTADÍSTICAS
    # ========================================

    async def get_user_reactions(
        self,
        user_id: int,
        limit: int = 50,
        channel_id: Optional[int] = None
    ) -> List[UserReaction]:
        """Obtiene historial de reacciones del usuario.

        Args:
            user_id: ID del usuario
            limit: Límite de resultados
            channel_id: Filtrar por canal (opcional)

        Returns:
            Lista de reacciones del usuario
        """
        stmt = select(UserReaction).where(UserReaction.user_id == user_id)

        if channel_id is not None:
            stmt = stmt.where(UserReaction.channel_id == channel_id)

        stmt = stmt.order_by(UserReaction.reacted_at.desc()).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_reaction_stats(self, user_id: int) -> dict:
        """Obtiene estadísticas de reacciones del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Diccionario con estadísticas
        """
        # Total de reacciones
        stmt_total = select(func.count()).select_from(UserReaction).where(
            UserReaction.user_id == user_id
        )
        result_total = await self.session.execute(stmt_total)
        total_reactions = result_total.scalar() or 0

        # Reacciones por emoji
        stmt_by_emoji = select(
            Reaction.emoji,
            func.count(UserReaction.id).label('count')
        ).select_from(UserReaction).join(
            Reaction
        ).where(
            UserReaction.user_id == user_id
        ).group_by(Reaction.emoji)

        result_by_emoji = await self.session.execute(stmt_by_emoji)
        reactions_by_emoji = {row.emoji: row.count for row in result_by_emoji}

        # Total besitos de reacciones
        stmt_besitos = select(
            func.coalesce(func.sum(Reaction.besitos_value), 0)
        ).select_from(UserReaction).join(
            Reaction
        ).where(
            UserReaction.user_id == user_id
        )
        result_besitos = await self.session.execute(stmt_besitos)
        total_besitos_from_reactions = result_besitos.scalar() or 0

        # Canal favorito (con más reacciones)
        stmt_channel = select(
            UserReaction.channel_id,
            func.count(UserReaction.id).label('count')
        ).where(
            UserReaction.user_id == user_id
        ).group_by(
            UserReaction.channel_id
        ).order_by(
            func.count(UserReaction.id).desc()
        ).limit(1)

        result_channel = await self.session.execute(stmt_channel)
        channel_row = result_channel.first()
        favorite_channel = channel_row.channel_id if channel_row else None

        return {
            'total_reactions': total_reactions,
            'reactions_by_emoji': reactions_by_emoji,
            'total_besitos_from_reactions': total_besitos_from_reactions,
            'favorite_channel': favorite_channel
        }
