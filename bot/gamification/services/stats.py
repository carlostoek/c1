"""
Servicio de estadísticas y métricas del sistema de gamificación.
"""

from datetime import datetime, timedelta, UTC
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List

from bot.gamification.database.models import (
    UserGamification, UserMission, UserReward, UserReaction,
    UserStreak, Mission, Level
)
from bot.gamification.database.enums import MissionStatus

import logging
logger = logging.getLogger(__name__)


class StatsService:
    """Servicio de estadísticas del sistema."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_system_overview(self) -> dict:
        """Métricas generales del sistema."""
        # Total usuarios
        stmt = select(func.count()).select_from(UserGamification)
        total_users = (await self.session.execute(stmt)).scalar()
        
        # Usuarios activos últimos 7 días
        week_ago = datetime.now(UTC) - timedelta(days=7)
        stmt = select(func.count()).select_from(UserReaction).where(
            UserReaction.reacted_at >= week_ago
        ).distinct(UserReaction.user_id)
        active_7d = (await self.session.execute(stmt)).scalar()
        
        # Total besitos distribuidos
        stmt = select(func.sum(UserGamification.besitos_earned))
        total_besitos = (await self.session.execute(stmt)).scalar() or 0
        
        # Misiones y recompensas
        stmt = select(func.count()).select_from(Mission).where(Mission.active == True)
        total_missions = (await self.session.execute(stmt)).scalar()
        
        stmt = select(func.count()).select_from(UserMission).where(
            UserMission.status == MissionStatus.CLAIMED
        )
        missions_completed = (await self.session.execute(stmt)).scalar()
        
        stmt = select(func.count()).select_from(UserReward)
        rewards_claimed = (await self.session.execute(stmt)).scalar()
        
        return {
            'total_users': total_users,
            'active_users_7d': active_7d,
            'total_besitos_distributed': total_besitos,
            'total_missions': total_missions,
            'missions_completed': missions_completed,
            'rewards_claimed': rewards_claimed
        }
    
    async def get_user_distribution(self) -> dict:
        """Distribución de usuarios por nivel."""
        # Por nivel
        stmt = (
            select(Level.name, func.count(UserGamification.user_id))
            .join(UserGamification, UserGamification.current_level_id == Level.id)
            .group_by(Level.name)
        )
        result = await self.session.execute(stmt)
        by_level = {name: count for name, count in result}
        
        # Top 10
        stmt = (
            select(UserGamification, Level.name)
            .join(Level, UserGamification.current_level_id == Level.id)
            .order_by(UserGamification.total_besitos.desc())
            .limit(10)
        )
        result = await self.session.execute(stmt)
        top_users = [
            {
                'user_id': ug.user_id,
                'besitos': ug.total_besitos,
                'level_name': level_name
            }
            for ug, level_name in result
        ]
        
        # Promedio
        stmt = select(func.avg(UserGamification.total_besitos))
        avg_besitos = (await self.session.execute(stmt)).scalar() or 0
        
        return {
            'by_level': by_level,
            'top_users': top_users,
            'avg_besitos': round(avg_besitos, 2)
        }
    
    async def get_mission_stats(self) -> dict:
        """Estadísticas de misiones."""
        # Total starts
        stmt = select(func.count()).select_from(UserMission)
        total_starts = (await self.session.execute(stmt)).scalar()
        
        # Completions
        stmt = select(func.count()).select_from(UserMission).where(
            UserMission.status.in_([MissionStatus.COMPLETED, MissionStatus.CLAIMED])
        )
        total_completions = (await self.session.execute(stmt)).scalar()
        
        # Rate
        completion_rate = (total_completions / total_starts * 100) if total_starts > 0 else 0
        
        # Por tipo
        stmt = (
            select(Mission.mission_type, func.count(UserMission.id))
            .join(UserMission)
            .where(UserMission.status == MissionStatus.CLAIMED)
            .group_by(Mission.mission_type)
        )
        result = await self.session.execute(stmt)
        by_type = {mtype: count for mtype, count in result}
        
        # Top misiones
        stmt = (
            select(Mission.name, func.count(UserMission.id))
            .join(UserMission)
            .where(UserMission.status == MissionStatus.CLAIMED)
            .group_by(Mission.id, Mission.name)
            .order_by(func.count(UserMission.id).desc())
            .limit(5)
        )
        result = await self.session.execute(stmt)
        top_missions = [
            {'mission_name': name, 'completions': count}
            for name, count in result
        ]
        
        return {
            'total_starts': total_starts,
            'total_completions': total_completions,
            'completion_rate': round(completion_rate, 2),
            'by_type': by_type,
            'top_missions': top_missions
        }
    
    async def get_engagement_stats(self) -> dict:
        """Estadísticas de engagement."""
        # Total reacciones
        stmt = select(func.count()).select_from(UserReaction)
        total_reactions = (await self.session.execute(stmt)).scalar()
        
        # Últimos 7 días
        week_ago = datetime.now(UTC) - timedelta(days=7)
        stmt = select(func.count()).select_from(UserReaction).where(
            UserReaction.reacted_at >= week_ago
        )
        reactions_7d = (await self.session.execute(stmt)).scalar()
        
        # Promedio por usuario
        stmt = select(func.count(UserGamification.user_id))
        total_users = (await self.session.execute(stmt)).scalar()
        avg_reactions = (total_reactions / total_users) if total_users > 0 else 0
        
        # Top emojis
        stmt = (
            select(UserReaction.emoji, func.count(UserReaction.id))
            .group_by(UserReaction.emoji)
            .order_by(func.count(UserReaction.id).desc())
            .limit(5)
        )
        result = await self.session.execute(stmt)
        top_emojis = {emoji: count for emoji, count in result}
        
        # Rachas activas
        stmt = select(func.count()).select_from(UserStreak).where(
            UserStreak.current_streak > 0
        )
        active_streaks = (await self.session.execute(stmt)).scalar()
        
        # Racha más larga
        stmt = select(func.max(UserStreak.longest_streak))
        longest_streak = (await self.session.execute(stmt)).scalar() or 0
        
        return {
            'total_reactions': total_reactions,
            'reactions_7d': reactions_7d,
            'avg_reactions_per_user': round(avg_reactions, 2),
            'top_emojis': top_emojis,
            'active_streaks': active_streaks,
            'longest_streak': longest_streak
        }
    
    async def get_timeline_stats(self, days: int = 30) -> dict:
        """Estadísticas por día."""
        from_date = datetime.now(UTC) - timedelta(days=days)
        
        # Reacciones diarias
        stmt = (
            select(
                func.date(UserReaction.reacted_at).label('date'),
                func.count(UserReaction.id).label('count')
            )
            .where(UserReaction.reacted_at >= from_date)
            .group_by(func.date(UserReaction.reacted_at))
            .order_by(func.date(UserReaction.reacted_at))
        )
        result = await self.session.execute(stmt)
        daily_reactions = [
            {'date': str(row.date), 'count': row.count}
            for row in result
        ]
        
        # Completions diarias
        stmt = (
            select(
                func.date(UserMission.completed_at).label('date'),
                func.count(UserMission.id).label('count')
            )
            .where(UserMission.completed_at >= from_date)
            .where(UserMission.status.in_([MissionStatus.COMPLETED, MissionStatus.CLAIMED]))
            .group_by(func.date(UserMission.completed_at))
            .order_by(func.date(UserMission.completed_at))
        )
        result = await self.session.execute(stmt)
        daily_completions = [
            {'date': str(row.date), 'count': row.count}
            for row in result
        ]
        
        # Besitos diarios (sum of besitos earned)
        # Note: We'll estimate based on missions completed since direct tracking is complex
        # For now, we'll focus on mission completions and reactions
        
        return {
            'daily_reactions': daily_reactions,
            'daily_completions': daily_completions
        }