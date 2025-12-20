"""
Servicio de gestión de misiones.

Responsabilidades:
- CRUD de misiones
- Tracking de progreso por usuario
- Validación de criterios dinámicos
- Otorgamiento de recompensas
"""

from typing import Optional, List, Tuple
from datetime import datetime, UTC, date, timedelta
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
import json
import logging

from bot.gamification.database.models import Mission, UserMission, UserStreak, Level
from bot.gamification.database.enums import MissionType, MissionStatus, TransactionType

logger = logging.getLogger(__name__)


class MissionService:
    """Servicio de gestión de misiones y progreso."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # ========================================
    # CRUD MISIONES
    # ========================================
    
    async def create_mission(
        self,
        name: str,
        description: str,
        mission_type: MissionType,
        criteria: dict,
        besitos_reward: int,
        auto_level_up_id: Optional[int] = None,
        unlock_rewards: Optional[List[int]] = None,
        repeatable: bool = False,
        created_by: int = 0
    ) -> Mission:
        """Crea nueva misión."""
        mission = Mission(
            name=name,
            description=description,
            mission_type=mission_type,
            criteria=json.dumps(criteria),
            besitos_reward=besitos_reward,
            auto_level_up_id=auto_level_up_id,
            unlock_rewards=json.dumps(unlock_rewards) if unlock_rewards else None,
            active=True,
            repeatable=repeatable,
            created_by=created_by
        )
        self.session.add(mission)
        await self.session.commit()
        await self.session.refresh(mission)
        
        logger.info(f"Created mission: {name} (type: {mission_type})")
        return mission
    
    async def update_mission(self, mission_id: int, **kwargs) -> Optional[Mission]:
        """Actualiza una misión existente."""
        mission = await self.session.get(Mission, mission_id)
        if not mission:
            return None
        
        # Permitir actualizar todos los campos válidos
        update_fields = [
            'name', 'description', 'mission_type', 'criteria', 'besitos_reward',
            'auto_level_up_id', 'unlock_rewards', 'active', 'repeatable'
        ]
        
        for key, value in kwargs.items():
            if key in update_fields:
                if key in ['criteria', 'unlock_rewards'] and value is not None:
                    # Convertir a JSON si es necesario
                    setattr(mission, key, json.dumps(value) if isinstance(value, dict) else json.dumps(value))
                else:
                    setattr(mission, key, value)
        
        await self.session.commit()
        await self.session.refresh(mission)
        
        logger.info(f"Updated mission {mission_id}: {mission.name}")
        return mission
    
    async def delete_mission(self, mission_id: int) -> bool:
        """Soft-delete (active=False) de una misión."""
        mission = await self.session.get(Mission, mission_id)
        if not mission:
            return False
        
        mission.active = False
        await self.session.commit()
        
        logger.info(f"Soft-deleted mission {mission_id}: {mission.name}")
        return True
    
    async def get_all_missions(self, active_only: bool = True) -> List[Mission]:
        """Obtiene todas las misiones."""
        stmt = select(Mission)
        if active_only:
            stmt = stmt.where(Mission.active == True)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_mission_by_id(self, mission_id: int) -> Optional[Mission]:
        """Obtiene una misión por ID."""
        stmt = select(Mission).where(Mission.id == mission_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    # ========================================
    # USER MISSIONS
    # ========================================
    
    async def start_mission(self, user_id: int, mission_id: int) -> UserMission:
        """Inicia misión para usuario."""
        mission = await self.session.get(Mission, mission_id)
        if not mission or not mission.active:
            raise ValueError("Mission not found or inactive")
        
        # Verificar si ya tiene esta misión activa (si no es repeatable)
        if not mission.repeatable:
            stmt = select(UserMission).where(
                UserMission.user_id == user_id,
                UserMission.mission_id == mission_id,
                UserMission.status.in_([MissionStatus.IN_PROGRESS, MissionStatus.COMPLETED])
            )
            result = await self.session.execute(stmt)
            if result.scalar_one_or_none():
                raise ValueError("Mission already in progress or completed")
        
        user_mission = UserMission(
            user_id=user_id,
            mission_id=mission_id,
            status=MissionStatus.IN_PROGRESS,
            progress=json.dumps({}),
            started_at=datetime.now(UTC)
        )
        self.session.add(user_mission)
        await self.session.commit()
        await self.session.refresh(user_mission)
        
        logger.info(f"User {user_id} started mission {mission_id}")
        return user_mission
    
    async def get_user_missions(
        self,
        user_id: int,
        status: Optional[MissionStatus] = None
    ) -> List[UserMission]:
        """Obtiene misiones de usuario."""
        stmt = select(UserMission).where(UserMission.user_id == user_id)
        if status:
            stmt = stmt.where(UserMission.status == status)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_available_missions(self, user_id: int) -> List[Mission]:
        """Misiones que usuario puede iniciar (no completadas o repeatables)."""
        # Obtener misiones activas
        stmt = select(Mission).where(Mission.active == True)
        result = await self.session.execute(stmt)
        all_active_missions = result.scalars().all()
        
        # Obtener misiones del usuario que ya completó o está en progreso
        stmt = select(UserMission).where(
            UserMission.user_id == user_id,
            UserMission.status.in_([MissionStatus.IN_PROGRESS, MissionStatus.COMPLETED])
        )
        result = await self.session.execute(stmt)
        user_missions = result.scalars().all()
        
        # Filtrar misiones disponibles
        available_missions = []
        for mission in all_active_missions:
            # Buscar si el usuario ya tiene esta misión
            user_mission = next((um for um in user_missions if um.mission_id == mission.id), None)
            if not user_mission:
                # No tiene la misión, está disponible
                available_missions.append(mission)
            elif mission.repeatable:
                # Tiene la misión pero es repetible, está disponible
                available_missions.append(mission)
        
        return available_missions
    
    # ========================================
    # PROGRESO
    # ========================================
    
    async def update_progress(
        self,
        user_id: int,
        mission_id: int,
        new_data: dict
    ) -> UserMission:
        """Actualiza progreso de misión."""
        stmt = select(UserMission).where(
            UserMission.user_id == user_id,
            UserMission.mission_id == mission_id
        )
        result = await self.session.execute(stmt)
        user_mission = result.scalar_one_or_none()
        
        if not user_mission:
            raise ValueError(f"UserMission not found for user {user_id}, mission {mission_id}")
        
        # Combinar datos existentes con nuevos
        current_progress = json.loads(user_mission.progress) if user_mission.progress else {}
        current_progress.update(new_data)
        
        user_mission.progress = json.dumps(current_progress)
        await self.session.commit()
        await self.session.refresh(user_mission)
        
        logger.debug(f"Updated progress for user {user_id}, mission {mission_id}: {current_progress}")
        return user_mission
    
    async def check_completion(
        self,
        user_id: int,
        mission_id: int
    ) -> tuple[bool, UserMission]:
        """Verifica si misión está completa según criterios."""
        stmt = select(UserMission).where(
            UserMission.user_id == user_id,
            UserMission.mission_id == mission_id
        )
        result = await self.session.execute(stmt)
        user_mission = result.scalar_one_or_none()
        
        if not user_mission:
            return False, user_mission
        
        # Obtener misión base
        mission = await self.session.get(Mission, mission_id)
        if not mission:
            return False, user_mission
        
        # Parsear criterios
        criteria = json.loads(mission.criteria)
        progress = json.loads(user_mission.progress) if user_mission.progress else {}
        
        is_complete = False
        
        # Verificar según tipo de misión
        if mission.mission_type == MissionType.ONE_TIME:
            # Una misión simple, completada cuando está en estado COMPLETED
            is_complete = user_mission.status == MissionStatus.COMPLETED
        
        elif mission.mission_type == MissionType.STREAK:
            required_days = criteria.get('days', 0)
            days_completed = progress.get('days_completed', 0)
            is_complete = days_completed >= required_days
        
        elif mission.mission_type == MissionType.DAILY:
            required_count = criteria.get('count', 0)
            reactions_today = progress.get('reactions_today', 0)
            is_complete = reactions_today >= required_count
        
        elif mission.mission_type == MissionType.WEEKLY:
            required_target = criteria.get('target', 0)
            reactions_this_week = progress.get('reactions_this_week', 0)
            is_complete = reactions_this_week >= required_target
        
        # Si está completa y no lo estaba, actualizar estado
        if is_complete and user_mission.status != MissionStatus.COMPLETED:
            user_mission.status = MissionStatus.COMPLETED
            user_mission.completed_at = datetime.now(UTC)
            await self.session.commit()
            await self.session.refresh(user_mission)
            logger.info(f"Mission {mission_id} completed for user {user_id}")
        
        return is_complete, user_mission
    
    async def on_user_reaction(
        self,
        user_id: int,
        emoji: str,
        reacted_at: datetime
    ):
        """Hook para actualizar progreso cuando usuario reacciona."""
        try:
            # Obtener misiones IN_PROGRESS activas del usuario
            stmt = select(UserMission).join(Mission).where(
                UserMission.user_id == user_id,
                UserMission.status == MissionStatus.IN_PROGRESS,
                Mission.active == True
            )
            result = await self.session.execute(stmt)
            active_user_missions = result.scalars().all()
            
            # Obtener racha del usuario (para misiones tipo STREAK)
            from bot.gamification.services.container import gamification_container
            user_streak = await gamification_container.reaction.get_user_streak(user_id)
            
            completed_missions = []
            
            for user_mission in active_user_missions:
                mission = await self.session.get(Mission, user_mission.mission_id)
                
                # Actualizar progreso según tipo de misión
                if mission.mission_type == MissionType.STREAK:
                    if user_streak:
                        completed = await self._update_streak_progress(user_mission, user_streak, reacted_at)
                        if completed:
                            completed_missions.append(user_mission.id)
                
                elif mission.mission_type == MissionType.DAILY:
                    completed = await self._update_daily_progress(user_mission, emoji, reacted_at)
                    if completed:
                        completed_missions.append(user_mission.id)
                
                elif mission.mission_type == MissionType.WEEKLY:
                    completed = await self._update_weekly_progress(user_mission, emoji, reacted_at)
                    if completed:
                        completed_missions.append(user_mission.id)
                
                # Para ONE_TIME misiones, puede haber alguna lógica específica
                elif mission.mission_type == MissionType.ONE_TIME:
                    completed = await self._update_one_time_progress(user_mission, reacted_at)
                    if completed:
                        completed_missions.append(user_mission.id)
            
            await self.session.commit()
            
            if completed_missions:
                logger.info(f"User {user_id} completed missions: {completed_missions}")
        
        except Exception as e:
            logger.error(f"Error in on_user_reaction for user {user_id}: {str(e)}", exc_info=True)
            # No lanzar error para no afectar la experiencia principal del usuario
    
    async def _update_streak_progress(
        self,
        user_mission: UserMission,
        user_streak: UserStreak,
        reacted_at: datetime
    ) -> bool:
        """Actualiza progreso de misión streak."""
        try:
            criteria = json.loads(user_mission.mission.criteria)
            required_days = criteria.get('days', 0)
            
            # Actualizar el progreso con información actual de streak
            progress = json.loads(user_mission.progress) if user_mission.progress else {}
            progress['days_completed'] = user_streak.current_streak
            progress['last_reaction_date'] = user_streak.last_reaction_date.isoformat() if user_streak.last_reaction_date else None
            
            user_mission.progress = json.dumps(progress)
            
            # Comprobar si completó la misión
            is_completed = user_streak.current_streak >= required_days
            
            if is_completed and user_mission.status != MissionStatus.COMPLETED:
                user_mission.status = MissionStatus.COMPLETED
                user_mission.completed_at = datetime.now(UTC)
                logger.info(f"Streak mission {user_mission.mission_id} completed for user {user_mission.user_id}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error updating streak progress: {str(e)}", exc_info=True)
            return False
    
    async def _update_daily_progress(
        self,
        user_mission: UserMission,
        emoji: str,
        reacted_at: datetime
    ) -> bool:
        """Actualiza progreso de misión daily."""
        try:
            criteria = json.loads(user_mission.mission.criteria)
            required_count = criteria.get('count', 0)
            specific_reaction = criteria.get('specific_reaction')
            
            # Si requiere emoji específico y no coincide, ignorar
            if specific_reaction and emoji != specific_reaction:
                return False
            
            progress = json.loads(user_mission.progress) if user_mission.progress else {
                'reactions_today': 0,
                'date': None
            }
            
            today = reacted_at.date().isoformat()
            
            # Si es un nuevo día, resetear contador
            if progress.get('date') != today:
                progress['reactions_today'] = 0
                progress['date'] = today
            
            # Incrementar contador
            progress['reactions_today'] += 1
            user_mission.progress = json.dumps(progress)
            
            # Comprobar si completó la misión
            is_completed = progress['reactions_today'] >= required_count
            
            if is_completed and user_mission.status != MissionStatus.COMPLETED:
                user_mission.status = MissionStatus.COMPLETED
                user_mission.completed_at = datetime.now(UTC)
                logger.info(f"Daily mission {user_mission.mission_id} completed for user {user_mission.user_id}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error updating daily progress: {str(e)}", exc_info=True)
            return False
    
    async def _update_weekly_progress(
        self,
        user_mission: UserMission,
        emoji: str,
        reacted_at: datetime
    ) -> bool:
        """Actualiza progreso de misión weekly."""
        try:
            criteria = json.loads(user_mission.mission.criteria)
            required_target = criteria.get('target', 0)
            specific_reaction = criteria.get('specific_reaction')  # Puede ser None para cualquier reacción
            specific_days = set(criteria.get('specific_days', []))  # [1, 3, 5] -> lunes, miércoles, viernes
            
            # Si requiere emoji específico y no coincide, ignorar
            if specific_reaction and emoji != specific_reaction:
                return False
            
            # Verificar si el día coincide con los días específicos (si hay restricción)
            if specific_days:
                day_of_week = reacted_at.weekday()  # 0=lunes, 6=domingo
                if (day_of_week + 1) % 7 not in specific_days:  # Convertir a formato 0=domingo, 1=lunes...
                    return False
            
            progress = json.loads(user_mission.progress) if user_mission.progress else {
                'reactions_this_week': 0,
                'week_start': None,
                'week_end': None
            }
            
            # Calcular inicio de semana (lunes)
            week_start = (reacted_at.date() - timedelta(days=reacted_at.weekday())).isoformat()
            
            # Si es una nueva semana, resetear
            if progress.get('week_start') != week_start:
                progress['reactions_this_week'] = 0
                progress['week_start'] = week_start
                # Calcular fin de semana
                week_end = (reacted_at.date() + timedelta(days=6 - reacted_at.weekday())).isoformat()
                progress['week_end'] = week_end
            
            # Incrementar contador
            progress['reactions_this_week'] += 1
            user_mission.progress = json.dumps(progress)
            
            # Comprobar si completó la misión
            is_completed = progress['reactions_this_week'] >= required_target
            
            if is_completed and user_mission.status != MissionStatus.COMPLETED:
                user_mission.status = MissionStatus.COMPLETED
                user_mission.completed_at = datetime.now(UTC)
                logger.info(f"Weekly mission {user_mission.mission_id} completed for user {user_mission.user_id}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error updating weekly progress: {str(e)}", exc_info=True)
            return False
    
    async def _update_one_time_progress(
        self,
        user_mission: UserMission,
        reacted_at: datetime
    ) -> bool:
        """Actualiza progreso de misión one_time (si aplica)."""
        try:
            # Para misiones one_time que dependen de reacciones, marcar como completada
            # Solo si no está ya completada
            if user_mission.status != MissionStatus.COMPLETED:
                user_mission.status = MissionStatus.COMPLETED
                user_mission.completed_at = datetime.now(UTC)
                logger.info(f"One-time mission {user_mission.mission_id} completed for user {user_mission.user_id}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error updating one-time progress: {str(e)}", exc_info=True)
            return False
    
    # ========================================
    # ESTADÍSTICAS DE MISIÓN
    # ========================================

    async def get_mission_stats(self, mission_id: int) -> dict:
        """Obtiene estadísticas de uso de una misión."""
        # Obtener misión
        mission = await self.session.get(Mission, mission_id)
        if not mission:
            return {
                'active_users': 0,
                'completed_count': 0,
                'completion_rate': 0.0,
                'total_distributed_besitos': 0,
                'error': 'Mission not found'
            }

        # Contar usuarios con misión in_progress
        active_stmt = select(func.count()).select_from(UserMission).where(
            UserMission.mission_id == mission_id,
            UserMission.status == MissionStatus.IN_PROGRESS
        )
        result = await self.session.execute(active_stmt)
        active_users = result.scalar() or 0

        # Contar usuarios que completaron la misión
        completed_stmt = select(func.count()).select_from(UserMission).where(
            UserMission.mission_id == mission_id,
            UserMission.status == MissionStatus.COMPLETED
        )
        result = await self.session.execute(completed_stmt)
        completed_count = result.scalar() or 0

        # Total que han iniciado la misión
        started_stmt = select(func.count()).select_from(UserMission).where(
            UserMission.mission_id == mission_id
        )
        result = await self.session.execute(started_stmt)
        started_count = result.scalar() or 0

        # Tasa de completación
        completion_rate = (completed_count / started_count * 100) if started_count > 0 else 0.0

        # Besitos totales distribuidos (solo de misiones reclamadas)
        claimed_stmt = select(func.sum(Mission.besitos_reward)).join(
            UserMission, UserMission.mission_id == Mission.id
        ).where(
            Mission.id == mission_id,
            UserMission.status == MissionStatus.CLAIMED
        )
        result = await self.session.execute(claimed_stmt)
        total_distributed_besitos = result.scalar() or 0

        return {
            'active_users': active_users,
            'completed_count': completed_count,
            'completion_rate': round(completion_rate, 2),
            'total_distributed_besitos': total_distributed_besitos
        }

    # ========================================
    # RECLAMAR RECOMPENSA
    # ========================================

    async def claim_reward(
        self,
        user_id: int,
        mission_id: int
    ) -> tuple[bool, str, dict]:
        """Reclama recompensa de misión completada."""
        try:
            # Obtener user_mission
            stmt = select(UserMission).where(
                UserMission.user_id == user_id,
                UserMission.mission_id == mission_id
            )
            result = await self.session.execute(stmt)
            user_mission = result.scalar_one_or_none()

            if not user_mission:
                return False, "Mission not found", {}

            if user_mission.status != MissionStatus.COMPLETED:
                return False, "Mission not completed", {}

            if user_mission.claimed_at:
                return False, "Reward already claimed", {}

            # Obtener misión
            mission = await self.session.get(Mission, mission_id)
            if not mission:
                return False, "Mission not found", {}

            rewards_info = {
                'besitos': 0,
                'level_up': None,
                'unlocked_rewards': []
            }

            # 1. Otorgar besitos
            from bot.gamification.services.container import gamification_container
            besitos_granted = await gamification_container.besito.grant_besitos(
                user_id=user_id,
                amount=mission.besitos_reward,
                transaction_type=TransactionType.MISSION_REWARD,
                description=f"Misión completada: {mission.name}",
                reference_id=user_mission.id
            )
            rewards_info['besitos'] = besitos_granted

            # 2. Auto level-up (si aplica)
            if mission.auto_level_up_id:
                level_updated = await gamification_container.level.set_user_level(
                    user_id,
                    mission.auto_level_up_id
                )
                if level_updated:
                    level = await self.session.get(Level, mission.auto_level_up_id)
                    rewards_info['level_up'] = level

            # 3. No implementado: Unlock rewards - se implementará cuando se tenga el sistema de recompensas
            # TODO: Integrar con RewardService cuando exista

            # 4. Marcar como reclamada
            user_mission.status = MissionStatus.CLAIMED
            user_mission.claimed_at = datetime.now(UTC)
            await self.session.commit()

            logger.info(f"User {user_id} claimed mission {mission_id}: +{besitos_granted} besitos")

            return True, f"Recompensa reclamada: +{besitos_granted} besitos", rewards_info

        except Exception as e:
            logger.error(f"Error claiming reward for user {user_id}, mission {mission_id}: {str(e)}", exc_info=True)
            return False, f"Error al reclamar recompensa: {str(e)}", {}