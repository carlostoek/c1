"""
Servicio de gestión de reacciones.

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
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from bot.gamification.database.models import (
    Reaction, 
    UserReaction, 
    UserStreak,
    UserGamification,
    GamificationConfig as DBConfig
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
        """Crea nueva reacción en catálogo."""
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
        """Actualiza una reacción existente."""
        reaction = await self.session.get(Reaction, reaction_id)
        if not reaction:
            return None
        
        if besitos_value is not None:
            reaction.besitos_value = besitos_value
        if active is not None:
            reaction.active = active
        
        await self.session.commit()
        await self.session.refresh(reaction)
        
        logger.info(f"Updated reaction {reaction_id}: {reaction.emoji} ({reaction.besitos_value} besitos, active: {reaction.active})")
        return reaction
    
    async def delete_reaction(self, reaction_id: int) -> bool:
        """Elimina una reacción del catálogo."""
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
        """Obtiene todas las reacciones."""
        stmt = select(Reaction)
        if active_only:
            stmt = stmt.where(Reaction.active == True)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_reaction_by_emoji(
        self, 
        emoji: str
    ) -> Optional[Reaction]:
        """Busca reacción por emoji."""
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
        message_id: int,
        reacted_at: Optional[datetime] = None
    ) -> Tuple[bool, str, int]:
        """
        Registra reacción de usuario y otorga besitos.

        Returns:
            (success, message, besitos_granted)
        """
        try:
            current_time = reacted_at or datetime.now(UTC)

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
                reacted_at=current_time
            )
            self.session.add(user_reaction)
            
            # 5. Otorgar besitos (se commitea dentro de este servicio)
            from bot.gamification.services.container import gamification_container
            besitos_granted = await gamification_container.besito.grant_besitos(
                user_id=user_id,
                amount=reaction.besitos_value,
                transaction_type=TransactionType.REACTION,
                description=f"Reacción {emoji} en canal {channel_id}",
                reference_id=user_reaction.id,
                commit=False
            )

            # 6. Actualizar racha
            streak = await self._update_user_streak(user_id, current_time)
            
            await self.session.commit()

            logger.info(
                f"User {user_id} reacted with {emoji}: "
                f"+{besitos_granted} besitos, streak: {streak.current_streak if streak else 'N/A'}"
            )

            return True, f"+{besitos_granted} besitos (racha: {streak.current_streak if streak else 0})", besitos_granted

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error recording reaction for user {user_id}: {str(e)}", exc_info=True)
            return False, "Error al procesar la reacción", 0
    
    # ========================================
    # VALIDACIONES
    # ========================================
    
    async def _has_reacted_to_message(
        self, 
        user_id: int, 
        message_id: int
    ) -> bool:
        """Verifica si usuario ya reaccionó a este mensaje."""
        stmt = select(func.count()).select_from(UserReaction).where(
            UserReaction.user_id == user_id,
            UserReaction.message_id == message_id
        )
        result = await self.session.execute(stmt)
        count = result.scalar()
        return count > 0
    
    async def _check_daily_limit(self, user_id: int) -> Tuple[bool, int]:
        """Verifica límite diario de besitos."""
        # Obtener la configuración de la base de datos
        config = await self.session.get(DBConfig, 1)
        if not config or config.max_besitos_per_day is None:
            return True, 0  # Sin límite

        max_daily = config.max_besitos_per_day
        if max_daily <= 0:
            return True, 0  # Sin límite

        # Contar besitos de hoy
        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

        stmt = select(func.coalesce(func.sum(Reaction.besitos_value), 0)).join(
            UserReaction, Reaction.id == UserReaction.reaction_id
        ).where(
            UserReaction.user_id == user_id,
            UserReaction.reacted_at >= today_start
        )
        result = await self.session.execute(stmt)
        besitos_today = result.scalar()

        can_react = besitos_today < max_daily
        return can_react, besitos_today
    
    # ========================================
    # RACHAS
    # ========================================
    
    async def _update_user_streak(self, user_id: int, reacted_at: datetime) -> UserStreak:
        """Actualiza la racha del usuario de forma atómica."""
        streak = await self._get_or_create_streak(user_id)

        today = reacted_at.date()
        last_date = streak.last_reaction_date.date() if streak.last_reaction_date else None

        if last_date is None:
            streak.current_streak = 1
        elif last_date == today:
            pass  # No change if already reacted today
        elif last_date == today - timedelta(days=1):
            streak.current_streak += 1
        else:
            streak.current_streak = 1

        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak

        streak.last_reaction_date = reacted_at
        
        return streak

    async def _get_or_create_streak(self, user_id: int) -> UserStreak:
        """
        Obtiene la racha de un usuario, o la crea si no existe.
        Usa SELECT ... FOR UPDATE para prevenir race conditions.
        """
        async with self.session.begin_nested():
            stmt = select(UserStreak).where(UserStreak.user_id == user_id).with_for_update()
            result = await self.session.execute(stmt)
            streak = result.scalar_one_or_none()

            if not streak:
                streak = UserStreak(user_id=user_id)
                self.session.add(streak)
        
        return streak

    
    async def get_user_streak(self, user_id: int) -> Optional[UserStreak]:
        """Obtiene racha actual del usuario."""
        try:
            stmt = select(UserStreak).where(UserStreak.user_id == user_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting streak for user {user_id}: {str(e)}", exc_info=True)
            return None
    
    # ========================================
    # ESTADÍSTICAS
    # ========================================
    
    async def get_user_reactions(
        self,
        user_id: int,
        limit: int = 50,
        channel_id: Optional[int] = None
    ) -> List[UserReaction]:
        """Obtiene historial de reacciones del usuario."""
        try:
            stmt = select(UserReaction).where(UserReaction.user_id == user_id)

            if channel_id:
                stmt = stmt.where(UserReaction.channel_id == channel_id)

            stmt = stmt.order_by(UserReaction.reacted_at.desc()).limit(limit)

            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting reactions for user {user_id}: {str(e)}", exc_info=True)
            return []
    
    async def get_reaction_stats(self, user_id: int) -> dict:
        """Obtiene estadísticas de reacciones del usuario."""
        try:
            # Contar total reacciones
            total_reactions_stmt = select(func.count()).select_from(UserReaction).where(
                UserReaction.user_id == user_id
            )
            result = await self.session.execute(total_reactions_stmt)
            total_reactions = result.scalar()

            # Contar reacciones por emoji
            emoji_stats_stmt = select(
                Reaction.emoji,
                func.count().label('count')
            ).join(
                UserReaction, Reaction.id == UserReaction.reaction_id
            ).where(
                UserReaction.user_id == user_id
            ).group_by(Reaction.emoji)

            emoji_result = await self.session.execute(emoji_stats_stmt)
            emoji_rows = emoji_result.all()
            reactions_by_emoji = {row.emoji: row.count for row in emoji_rows}

            # Calcular total besitos de reacciones
            besitos_stmt = select(func.coalesce(func.sum(Reaction.besitos_value), 0)).join(
                UserReaction, Reaction.id == UserReaction.reaction_id
            ).where(
                UserReaction.user_id == user_id
            )
            besitos_result = await self.session.execute(besitos_stmt)
            total_besitos_from_reactions = besitos_result.scalar()

            # Canal favorito (más reacciones)
            channel_stats_stmt = select(
                UserReaction.channel_id,
                func.count().label('count')
            ).where(
                UserReaction.user_id == user_id
            ).group_by(UserReaction.channel_id).order_by(
                func.count().desc()
            ).limit(1)

            channel_result = await self.session.execute(channel_stats_stmt)
            favorite_channel_row = channel_result.first()
            favorite_channel = favorite_channel_row[0] if favorite_channel_row else None

            return {
                'total_reactions': total_reactions,
                'reactions_by_emoji': reactions_by_emoji,
                'total_besitos_from_reactions': total_besitos_from_reactions,
                'favorite_channel': favorite_channel
            }
        except Exception as e:
            logger.error(f"Error getting reaction stats for user {user_id}: {str(e)}", exc_info=True)
            return {
                'total_reactions': 0,
                'reactions_by_emoji': {},
                'total_besitos_from_reactions': 0,
                'favorite_channel': None
            }