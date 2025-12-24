"""
Servicio de perfil de usuario (fachada).

Responsabilidades:
- Agregar datos de múltiples servicios
- Proveer API unificada para UI
- Inicialización de usuarios nuevos
- Resúmenes formateados
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, UTC
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import json

from bot.gamification.database.models import (
    UserGamification, Level, UserStreak, UserMission,
    UserReaction, Reaction
)
from bot.gamification.database.enums import MissionStatus, TransactionType

logger = logging.getLogger(__name__)


class UserGamificationService:
    """Servicio de perfil de usuario (fachada)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ========================================
    # INICIALIZACIÓN
    # ========================================

    async def ensure_user_exists(self, user_id: int) -> UserGamification:
        """Crea UserGamification si no existe.

        Args:
            user_id: ID del usuario

        Returns:
            UserGamification del usuario
        """
        user = await self.session.get(UserGamification, user_id)

        if not user:
            # Obtener nivel inicial (order=1)
            stmt = select(Level).where(Level.active == True).order_by(Level.order.asc()).limit(1)
            result = await self.session.execute(stmt)
            initial_level = result.scalar_one_or_none()

            user = UserGamification(
                user_id=user_id,
                total_besitos=0,
                besitos_earned=0,
                besitos_spent=0,
                current_level_id=initial_level.id if initial_level else None,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)

            logger.info(f"Created UserGamification for user {user_id}")

        return user

    async def initialize_new_user(
        self,
        user_id: int,
        username: Optional[str] = None
    ) -> dict:
        """Inicializa usuario nuevo completamente.

        Args:
            user_id: ID del usuario
            username: Username opcional del usuario

        Returns:
            Perfil completo del usuario
        """
        # Crear perfil base
        user_gamif = await self.ensure_user_exists(user_id)

        # Verificar si ya tiene streak
        streak = await self.session.get(UserStreak, user_id)
        if not streak:
            # Crear racha
            streak = UserStreak(user_id=user_id)
            self.session.add(streak)
            await self.session.commit()

        logger.info(f"Initialized new user {user_id}")

        # Retornar perfil completo
        return await self.get_user_profile(user_id)

    # ========================================
    # PERFIL COMPLETO
    # ========================================

    async def get_user_profile(self, user_id: int) -> dict:
        """Retorna perfil completo de gamificación.

        Args:
            user_id: ID del usuario

        Returns:
            Diccionario con perfil completo
        """
        # Asegurar que usuario existe
        user_gamif = await self.ensure_user_exists(user_id)

        # Obtener nivel y progresión
        level_progress = await self._get_level_progress(user_id)

        # Obtener racha
        streak_info = await self._get_streak_info(user_id)

        # Obtener misiones
        missions_info = await self._get_missions_info(user_id)

        # Obtener recompensas
        rewards_info = await self._get_rewards_info(user_id)

        # Estadísticas de reacciones
        reaction_stats = await self._get_reaction_stats(user_id)

        return {
            'user_id': user_id,
            'besitos': {
                'total': user_gamif.total_besitos,
                'earned': user_gamif.besitos_earned,
                'spent': user_gamif.besitos_spent
            },
            'level': level_progress,
            'streak': streak_info,
            'missions': missions_info,
            'rewards': rewards_info,
            'stats': reaction_stats
        }

    async def _get_level_progress(self, user_id: int) -> dict:
        """Obtiene progreso de nivel del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Diccionario con información de nivel
        """
        user_gamif = await self.session.get(UserGamification, user_id)
        if not user_gamif or not user_gamif.current_level_id:
            return {
                'current': None,
                'next': None,
                'progress_percentage': 0.0,
                'besitos_to_next': None
            }

        # Obtener nivel actual
        current_level = await self.session.get(Level, user_gamif.current_level_id)

        # Obtener siguiente nivel
        stmt = (
            select(Level)
            .where(Level.active == True)
            .where(Level.order == current_level.order + 1)
        )
        result = await self.session.execute(stmt)
        next_level = result.scalar_one_or_none()

        # Calcular progreso
        progress_percentage = 0.0
        besitos_to_next = None

        if next_level:
            besitos_in_level = user_gamif.total_besitos - current_level.min_besitos
            besitos_needed = next_level.min_besitos - current_level.min_besitos
            progress_percentage = (besitos_in_level / besitos_needed * 100) if besitos_needed > 0 else 0
            besitos_to_next = next_level.min_besitos - user_gamif.total_besitos

        return {
            'current': current_level,
            'next': next_level,
            'progress_percentage': max(0, min(100, progress_percentage)),
            'besitos_to_next': besitos_to_next if besitos_to_next and besitos_to_next > 0 else None
        }

    async def _get_streak_info(self, user_id: int) -> dict:
        """Obtiene información de racha del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Diccionario con información de racha
        """
        streak = await self.session.get(UserStreak, user_id)
        if not streak:
            return {
                'current': 0,
                'longest': 0,
                'last_reaction_date': None
            }

        return {
            'current': streak.current_streak,
            'longest': streak.longest_streak,
            'last_reaction_date': streak.last_reaction_date
        }

    async def _get_missions_info(self, user_id: int) -> dict:
        """Obtiene información de misiones del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Diccionario con información de misiones
        """
        # Misiones en progreso
        stmt = select(UserMission).where(
            UserMission.user_id == user_id,
            UserMission.status == MissionStatus.IN_PROGRESS.value
        )
        result = await self.session.execute(stmt)
        in_progress = list(result.scalars().all())

        # Misiones completadas
        stmt = select(UserMission).where(
            UserMission.user_id == user_id,
            UserMission.status == MissionStatus.CLAIMED.value
        )
        result = await self.session.execute(stmt)
        completed = list(result.scalars().all())

        # Contar misiones disponibles (esto requeriría MissionService)
        # Por ahora, retornamos 0
        available_count = 0

        return {
            'in_progress': in_progress,
            'completed': completed,
            'available_count': available_count
        }

    async def _get_rewards_info(self, user_id: int) -> dict:
        """Obtiene información de recompensas del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Diccionario con información de recompensas
        """
        from bot.gamification.database.models import UserReward, UserBadge, Badge, Reward

        # Total de recompensas obtenidas
        stmt = select(func.count()).select_from(UserReward).where(
            UserReward.user_id == user_id
        )
        result = await self.session.execute(stmt)
        total_obtained = result.scalar()

        # Badges del usuario
        stmt = (
            select(Badge, UserBadge)
            .join(UserReward, UserReward.id == UserBadge.id)
            .join(Reward, Reward.id == Badge.id)
            .where(UserReward.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        badges_data = list(result.all())

        badges = [badge for badge, _ in badges_data]
        displayed_badges = [badge for badge, user_badge in badges_data if user_badge.displayed]

        return {
            'total_obtained': total_obtained,
            'badges': badges,
            'displayed_badges': displayed_badges
        }

    async def _get_reaction_stats(self, user_id: int) -> dict:
        """Obtiene estadísticas de reacciones del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Diccionario con estadísticas de reacciones
        """
        # Total de reacciones
        stmt = select(func.count()).select_from(UserReaction).where(
            UserReaction.user_id == user_id
        )
        result = await self.session.execute(stmt)
        total_reactions = result.scalar()

        # Emoji favorito (más usado) - requiere join con Reaction
        stmt = (
            select(Reaction.emoji, func.count(UserReaction.id).label('count'))
            .join(UserReaction, UserReaction.reaction_id == Reaction.id)
            .where(UserReaction.user_id == user_id)
            .group_by(Reaction.emoji)
            .order_by(func.count(UserReaction.id).desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        favorite_data = result.first()
        favorite_emoji = favorite_data[0] if favorite_data else None

        # Días activos (días únicos con reacciones)
        stmt = select(func.count(func.distinct(func.date(UserReaction.reacted_at)))).select_from(
            UserReaction
        ).where(UserReaction.user_id == user_id)
        result = await self.session.execute(stmt)
        days_active = result.scalar()

        return {
            'total_reactions': total_reactions,
            'favorite_emoji': favorite_emoji,
            'days_active': days_active
        }

    # ========================================
    # RESÚMENES
    # ========================================

    async def get_profile_summary(self, user_id: int) -> str:
        """Genera resumen formateado para Telegram.

        Args:
            user_id: ID del usuario

        Returns:
            Texto HTML formateado para Telegram
        """
        profile = await self.get_user_profile(user_id)

        # Formatear nivel
        level_name = profile['level']['current'].name if profile['level']['current'] else 'Sin nivel'
        progress = profile['level']['progress_percentage']

        summary = f"""👤 <b>Perfil de Usuario</b>

💰 Besitos: <b>{profile['besitos']['total']:,}</b>
⭐ Nivel: <b>{level_name}</b> ({progress:.0f}% al siguiente)
🔥 Racha: <b>{profile['streak']['current']}</b> días (récord: {profile['streak']['longest']})

📋 Misiones: {len(profile['missions']['in_progress'])} activas, {len(profile['missions']['completed'])} completadas
🏆 Recompensas: {profile['rewards']['total_obtained']} obtenidas
"""

        # Badges mostrados
        if profile['rewards']['displayed_badges']:
            from bot.gamification.database.models import Reward
            summary += "\n<b>Badges mostrados:</b>\n"
            for badge in profile['rewards']['displayed_badges']:
                # Badge solo tiene icon, necesitamos el Reward para el nombre
                reward = await self.session.get(Reward, badge.id)
                reward_name = reward.name if reward else "Badge"
                summary += f"{badge.icon} {reward_name}\n"

        return summary

    async def get_leaderboard_position(self, user_id: int) -> dict:
        """Obtiene posición del usuario en leaderboards.

        Args:
            user_id: ID del usuario

        Returns:
            Diccionario con posiciones en rankings
        """
        user = await self.session.get(UserGamification, user_id)
        if not user:
            return {
                'besitos_rank': 0,
                'total_users': 0
            }

        # Contar usuarios con más besitos
        stmt = select(func.count()).select_from(UserGamification).where(
            UserGamification.total_besitos > user.total_besitos
        )
        result = await self.session.execute(stmt)
        besitos_rank = result.scalar() + 1

        # Total de usuarios
        stmt = select(func.count()).select_from(UserGamification)
        result = await self.session.execute(stmt)
        total_users = result.scalar()

        return {
            'besitos_rank': besitos_rank,
            'total_users': total_users
        }

    # ========================================
    # ESTADÍSTICAS
    # ========================================

    async def get_user_stats(self, user_id: int) -> dict:
        """Obtiene estadísticas detalladas del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Diccionario con estadísticas detalladas
        """
        user_gamif = await self.ensure_user_exists(user_id)

        # Estadísticas de reacciones
        reactions_stats = await self._get_detailed_reaction_stats(user_id)

        # Estadísticas de besitos
        besitos_stats = await self._get_detailed_besitos_stats(user_id)

        # Estadísticas de misiones
        missions_stats = await self._get_detailed_missions_stats(user_id)

        # Estadísticas de actividad
        activity_stats = await self._get_activity_stats(user_id)

        return {
            'reactions': reactions_stats,
            'besitos': besitos_stats,
            'missions': missions_stats,
            'activity': activity_stats
        }

    async def _get_detailed_reaction_stats(self, user_id: int) -> dict:
        """Estadísticas detalladas de reacciones.

        Args:
            user_id: ID del usuario

        Returns:
            Diccionario con stats de reacciones
        """
        # Total
        stmt = select(func.count()).select_from(UserReaction).where(
            UserReaction.user_id == user_id
        )
        result = await self.session.execute(stmt)
        total = result.scalar()

        # Por emoji (join con Reaction)
        stmt = (
            select(Reaction.emoji, func.count(UserReaction.id).label('count'))
            .join(UserReaction, UserReaction.reaction_id == Reaction.id)
            .where(UserReaction.user_id == user_id)
            .group_by(Reaction.emoji)
        )
        result = await self.session.execute(stmt)
        by_emoji = {row[0]: row[1] for row in result.all()}

        # Por canal
        stmt = (
            select(UserReaction.channel_id, func.count(UserReaction.id).label('count'))
            .where(UserReaction.user_id == user_id)
            .group_by(UserReaction.channel_id)
        )
        result = await self.session.execute(stmt)
        by_channel = {row[0]: row[1] for row in result.all()}

        # Promedio por día
        stmt = select(func.count(func.distinct(func.date(UserReaction.reacted_at)))).select_from(
            UserReaction
        ).where(UserReaction.user_id == user_id)
        result = await self.session.execute(stmt)
        days_with_reactions = result.scalar()

        avg_per_day = total / days_with_reactions if days_with_reactions > 0 else 0

        return {
            'total': total,
            'by_emoji': by_emoji,
            'by_channel': by_channel,
            'avg_per_day': round(avg_per_day, 2)
        }

    async def _get_detailed_besitos_stats(self, user_id: int) -> dict:
        """Estadísticas detalladas de besitos.

        Args:
            user_id: ID del usuario

        Returns:
            Diccionario con stats de besitos
        """
        user_gamif = await self.session.get(UserGamification, user_id)

        # Sin modelo BesitoTransaction, retornamos solo totales
        # Los detalles por tipo requerirían tracking adicional
        return {
            'total_earned': user_gamif.besitos_earned if user_gamif else 0,
            'total_spent': user_gamif.besitos_spent if user_gamif else 0,
            'from_reactions': 0,  # Requiere BesitoTransaction
            'from_missions': 0    # Requiere BesitoTransaction
        }

    async def _get_detailed_missions_stats(self, user_id: int) -> dict:
        """Estadísticas detalladas de misiones.

        Args:
            user_id: ID del usuario

        Returns:
            Diccionario con stats de misiones
        """
        # Total completadas
        stmt = select(func.count()).select_from(UserMission).where(
            UserMission.user_id == user_id,
            UserMission.status == MissionStatus.CLAIMED.value
        )
        result = await self.session.execute(stmt)
        total_completed = result.scalar()

        # Total iniciadas
        stmt = select(func.count()).select_from(UserMission).where(
            UserMission.user_id == user_id
        )
        result = await self.session.execute(stmt)
        total_started = result.scalar()

        # Tasa de completitud
        completion_rate = (total_completed / total_started * 100) if total_started > 0 else 0

        return {
            'total_completed': total_completed,
            'completion_rate': round(completion_rate, 2),
            'favorite_type': None  # Requiere join con Mission
        }

    async def _get_activity_stats(self, user_id: int) -> dict:
        """Estadísticas de actividad del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Diccionario con stats de actividad
        """
        user_gamif = await self.session.get(UserGamification, user_id)

        # Primera reacción
        stmt = (
            select(func.min(UserReaction.reacted_at))
            .where(UserReaction.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        first_seen = result.scalar()

        # Última reacción
        stmt = (
            select(func.max(UserReaction.reacted_at))
            .where(UserReaction.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        last_active = result.scalar()

        # Días desde el inicio
        days_since_start = 0
        if first_seen:
            # Asegurar que first_seen sea timezone-aware
            if first_seen.tzinfo is None:
                first_seen = first_seen.replace(tzinfo=UTC)
            days_since_start = (datetime.now(UTC) - first_seen).days

        # Días activos
        stmt = select(func.count(func.distinct(func.date(UserReaction.reacted_at)))).select_from(
            UserReaction
        ).where(UserReaction.user_id == user_id)
        result = await self.session.execute(stmt)
        active_days = result.scalar()

        return {
            'first_seen': first_seen,
            'last_active': last_active,
            'days_since_start': days_since_start,
            'active_days': active_days
        }
