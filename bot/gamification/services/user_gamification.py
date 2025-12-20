"""
Servicio de perfil de usuario (fachada).

Responsabilidades:
- Agregar datos de múltiples servicios
- Proveer API unificada para UI
- Inicialización de usuarios nuevos
- Resúmenes formateados
"""

from typing import Optional
from datetime import datetime, UTC
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from bot.gamification.database.models import UserGamification, Level, UserStreak
from bot.gamification.database.enums import MissionStatus

logger = logging.getLogger(__name__)


class UserGamificationService:
    """Servicio de perfil de usuario (fachada)."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        # Acceso a otros servicios via container
        from bot.gamification.services.container import gamification_container
        self.container = gamification_container
    
    # ========================================
    # INICIALIZACIÓN
    # ========================================
    
    async def ensure_user_exists(self, user_id: int) -> UserGamification:
        """Crea UserGamification si no existe."""
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
        """Inicializa usuario nuevo completamente."""
        try:
            # Crear perfil base
            user_gamif = await self.ensure_user_exists(user_id)
            
            # Crear racha si no existe
            streak = await self.session.get(UserStreak, user_id)
            if not streak:
                streak = UserStreak(
                    user_id=user_id,
                    current_streak=0,
                    longest_streak=0,
                    last_reaction_date=None
                )
                self.session.add(streak)
                await self.session.commit()
            
            logger.info(f"Initialized new user {user_id}")
            
            # Retornar perfil completo
            return await self.get_user_profile(user_id)
        except Exception as e:
            logger.error(f"Error initializing user {user_id}: {str(e)}", exc_info=True)
            raise
    
    # ========================================
    # PERFIL COMPLETO
    # ========================================
    
    async def get_user_profile(self, user_id: int) -> dict:
        """Retorna perfil completo."""
        try:
            # Obtener datos de múltiples servicios
            user_gamif = await self.ensure_user_exists(user_id)
            
            # Nivel y progresión
            level_progress = await self.container.level.get_user_level_progress(user_id)
            
            # Racha
            streak = await self.container.reaction.get_user_streak(user_id)
            
            # Misiones
            active_missions = await self.container.mission.get_user_missions(
                user_id, 
                status=MissionStatus.IN_PROGRESS
            )
            completed_missions = await self.container.mission.get_user_missions(
                user_id,
                status=MissionStatus.CLAIMED
            )
            available_missions = await self.container.mission.get_available_missions(user_id)
            
            # Recompensas
            user_rewards = await self.container.reward.get_user_rewards(user_id)
            user_badges = await self.container.reward.get_user_badges(user_id)
            displayed_badges = [b for b, ub in user_badges if ub.displayed]
            
            # Estadísticas de reacciones
            reaction_stats = await self.container.reaction.get_reaction_stats(user_id)
            
            # Agregar todo
            return {
                'user_id': user_id,
                'besitos': {
                    'total': user_gamif.total_besitos,
                    'earned': user_gamif.besitos_earned,
                    'spent': user_gamif.besitos_spent
                },
                'level': level_progress,
                'streak': {
                    'current': streak.current_streak if streak else 0,
                    'longest': streak.longest_streak if streak else 0,
                    'last_reaction_date': streak.last_reaction_date if streak else None
                },
                'missions': {
                    'in_progress': active_missions,
                    'completed': completed_missions,
                    'available_count': len(available_missions)
                },
                'rewards': {
                    'total_obtained': len(user_rewards),
                    'badges': [b for b, _ in user_badges],
                    'displayed_badges': displayed_badges
                },
                'stats': reaction_stats
            }
        except Exception as e:
            logger.error(f"Error getting user profile {user_id}: {str(e)}", exc_info=True)
            raise
    
    # ========================================
    # RESÚMENES
    # ========================================
    
    async def get_profile_summary(self, user_id: int) -> str:
        """Genera resumen formateado."""
        try:
            profile = await self.get_user_profile(user_id)
            
            # Formatear
            level_name = profile['level']['current'].name if profile['level']['current'] else 'Sin nivel'
            progress = profile['level']['progress_percentage']
            besitos_to_next = profile['level']['besitos_to_next']
            
            summary = f"""👤 <b>Perfil de Usuario</b>

💰 Besitos: <b>{profile['besitos']['total']:,}</b>
⭐ Nivel: <b>{level_name}</b> ({progress:.0f}% al siguiente)"""
            
            if besitos_to_next is not None:
                summary += f" ({besitos_to_next} más para subir)"
            
            summary += f"""
🔥 Racha: <b>{profile['streak']['current']}</b> días (récord: {profile['streak']['longest']})

📋 Misiones: {len(profile['missions']['in_progress'])} activas, {len(profile['missions']['completed'])} completadas
🏆 Recompensas: {profile['rewards']['total_obtained']} obtenidas
"""
            
            # Badges mostrados
            if profile['rewards']['displayed_badges']:
                summary += "\n<b>Badges mostrados:</b>\n"
                for badge in profile['rewards']['displayed_badges']:
                    summary += f"{badge.icon} {badge.name}\n"
            
            return summary
        except Exception as e:
            logger.error(f"Error getting profile summary {user_id}: {str(e)}", exc_info=True)
            return f"Error al cargar perfil: {str(e)}"
    
    async def get_leaderboard_position(self, user_id: int) -> dict:
        """Posición en leaderboards."""
        try:
            user = await self.session.get(UserGamification, user_id)
            if not user:
                return {}
            
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
        except Exception as e:
            logger.error(f"Error getting leaderboard position {user_id}: {str(e)}", exc_info=True)
            return {}
    
    # ========================================
    # ESTADÍSTICAS
    # ========================================
    
    async def get_user_stats(self, user_id: int) -> dict:
        """Estadísticas detalladas."""
        try:
            profile = await self.get_user_profile(user_id)
            
            # Obtener datos de reacciones
            reactions = await self.container.reaction.get_user_reactions(user_id, limit=1000)
            total_reactions = len(reactions)
            
            # Contar por emoji
            emoji_counts = {}
            for reaction in reactions:
                emoji = reaction.reaction.emoji
                emoji_counts[emoji] = emoji_counts.get(emoji, 0) + 1
            
            # Contar por canal
            channel_counts = {}
            for reaction in reactions:
                channel_id = reaction.channel_id
                channel_counts[channel_id] = channel_counts.get(channel_id, 0) + 1
            
            # Calcular promedio por día
            if profile['stats']['total_reactions'] > 0:
                # Utilizamos el total de reacciones del profile, ya que incluye información de los stats
                if profile['streak']['last_reaction_date']:
                    days_active = (datetime.now(UTC) - profile['streak']['last_reaction_date']).days + 1
                    avg_per_day = profile['stats']['total_reactions'] / max(1, days_active)
                else:
                    avg_per_day = profile['stats']['total_reactions']  # Si no hay reacción reciente, usar total
            else:
                avg_per_day = 0
            
            # Calcular estadísticas de misiónes
            missions_completed = len(profile['missions']['completed'])
            missions_in_progress = len(profile['missions']['in_progress'])
            total_missions = missions_completed + missions_in_progress
            completion_rate = (missions_completed / max(1, total_missions)) * 100 if total_missions > 0 else 0
            
            # Determinar tipo favorito de misión (si hay misiones completadas)
            mission_types = {}
            if profile['missions']['completed']:
                for mission in profile['missions']['completed']:
                    mission_record = await self.session.get(Mission, mission.mission_id)
                    if mission_record:
                        m_type = mission_record.mission_type
                        mission_types[m_type] = mission_types.get(m_type, 0) + 1
                
                favorite_type = max(mission_types, key=mission_types.get) if mission_types else "N/A"
            else:
                favorite_type = "N/A"
            
            # Calcular días activos
            days_active = len(set(r.reacted_at.date() for r in reactions)) if reactions else 0
            
            return {
                'reactions': {
                    'total': total_reactions,
                    'by_emoji': emoji_counts,
                    'by_channel': channel_counts,
                    'avg_per_day': avg_per_day
                },
                'besitos': {
                    'total_earned': profile['besitos']['earned'],
                    'total_spent': profile['besitos']['spent'],
                    'from_reactions': sum(profile['stats'].get('reactions_by_emoji', {}).values()),  # Aproximación
                    'balance': profile['besitos']['total']
                },
                'missions': {
                    'total_completed': missions_completed,
                    'completion_rate': completion_rate,
                    'favorite_type': favorite_type
                },
                'activity': {
                    'first_seen': profile.get('streak', {}).get('last_reaction_date'),
                    'last_active': max((r.reacted_at for r in reactions), default=None) if reactions else None,
                    'active_days': days_active
                }
            }
        except Exception as e:
            logger.error(f"Error getting user stats {user_id}: {str(e)}", exc_info=True)
            raise

# Importar Mission aquí para evitar problemas de circular imports
from bot.gamification.database.models import Mission