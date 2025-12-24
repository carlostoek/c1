"""
Servicio de gestión de misiones.

Responsabilidades:
- CRUD de misiones
- Tracking de progreso por usuario
- Validación de criterios dinámicos
- Otorgamiento de recompensas
"""

from typing import Optional, List, Tuple
from datetime import datetime, UTC, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import json
import logging

from bot.gamification.database.models import (
    Mission, UserMission, UserStreak, Level, Reward
)
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
        """Crea nueva misión.

        Args:
            name: Nombre de la misión
            description: Descripción de la misión
            mission_type: Tipo de misión (ONE_TIME, DAILY, WEEKLY, STREAK)
            criteria: Dict con criterios de completación
            besitos_reward: Cantidad de besitos a otorgar
            auto_level_up_id: ID del nivel a otorgar (opcional)
            unlock_rewards: Lista de IDs de recompensas a desbloquear (opcional)
            repeatable: Si la misión es repetible
            created_by: ID del admin que creó la misión

        Returns:
            Mission creada
        """
        mission = Mission(
            name=name,
            description=description,
            mission_type=mission_type.value,
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

        logger.info(f"Created mission: {name} (type: {mission_type.value})")
        return mission

    async def update_mission(
        self,
        mission_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        criteria: Optional[dict] = None,
        besitos_reward: Optional[int] = None,
        active: Optional[bool] = None,
        repeatable: Optional[bool] = None
    ) -> Mission:
        """Actualiza misión existente.

        Args:
            mission_id: ID de la misión
            name: Nuevo nombre (opcional)
            description: Nueva descripción (opcional)
            criteria: Nuevos criterios (opcional)
            besitos_reward: Nueva recompensa (opcional)
            active: Nuevo estado activo (opcional)
            repeatable: Nuevo estado repetible (opcional)

        Returns:
            Mission actualizada

        Raises:
            ValueError: Si misión no existe
        """
        mission = await self.session.get(Mission, mission_id)
        if not mission:
            raise ValueError(f"Mission {mission_id} not found")

        if name is not None:
            mission.name = name
        if description is not None:
            mission.description = description
        if criteria is not None:
            mission.criteria = json.dumps(criteria)
        if besitos_reward is not None:
            mission.besitos_reward = besitos_reward
        if active is not None:
            mission.active = active
        if repeatable is not None:
            mission.repeatable = repeatable

        await self.session.commit()
        await self.session.refresh(mission)

        logger.info(f"Updated mission {mission_id}: {mission.name}")
        return mission

    async def delete_mission(self, mission_id: int) -> bool:
        """Soft-delete de misión (active=False).

        Args:
            mission_id: ID de la misión

        Returns:
            True si se eliminó correctamente
        """
        mission = await self.session.get(Mission, mission_id)
        if not mission:
            return False

        mission.active = False
        await self.session.commit()

        logger.info(f"Deleted mission {mission_id}: {mission.name}")
        return True

    async def get_all_missions(self, active_only: bool = True) -> List[Mission]:
        """Obtiene todas las misiones.

        Args:
            active_only: Si True, solo retorna misiones activas

        Returns:
            Lista de misiones
        """
        stmt = select(Mission)
        if active_only:
            stmt = stmt.where(Mission.active == True)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_mission_by_id(self, mission_id: int) -> Optional[Mission]:
        """Obtiene misión por ID.

        Args:
            mission_id: ID de la misión

        Returns:
            Mission o None si no existe
        """
        return await self.session.get(Mission, mission_id)

    # ========================================
    # USER MISSIONS
    # ========================================

    async def start_mission(self, user_id: int, mission_id: int) -> UserMission:
        """Inicia misión para usuario.

        Args:
            user_id: ID del usuario
            mission_id: ID de la misión

        Returns:
            UserMission creada

        Raises:
            ValueError: Si misión no existe, está inactiva o usuario ya la tiene activa
        """
        mission = await self.session.get(Mission, mission_id)
        if not mission or not mission.active:
            raise ValueError("Mission not found or inactive")

        # Verificar si ya tiene esta misión activa (si no es repeatable)
        if not mission.repeatable:
            stmt = select(UserMission).where(
                UserMission.user_id == user_id,
                UserMission.mission_id == mission_id,
                UserMission.status.in_([MissionStatus.IN_PROGRESS.value, MissionStatus.COMPLETED.value])
            )
            result = await self.session.execute(stmt)
            if result.scalar_one_or_none():
                raise ValueError("Mission already in progress or completed")

        user_mission = UserMission(
            user_id=user_id,
            mission_id=mission_id,
            status=MissionStatus.IN_PROGRESS.value,
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
        """Obtiene misiones de usuario.

        Args:
            user_id: ID del usuario
            status: Filtrar por estado (opcional)

        Returns:
            Lista de UserMission
        """
        stmt = select(UserMission).where(UserMission.user_id == user_id)
        if status:
            stmt = stmt.where(UserMission.status == status.value)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_available_missions(self, user_id: int) -> List[Mission]:
        """Obtiene misiones disponibles para usuario.

        Misiones que el usuario puede iniciar (no completadas o repeatables).

        Args:
            user_id: ID del usuario

        Returns:
            Lista de Mission disponibles
        """
        # Obtener misiones completadas no repetibles
        stmt_completed = select(UserMission.mission_id).where(
            UserMission.user_id == user_id,
            UserMission.status.in_([MissionStatus.COMPLETED.value, MissionStatus.CLAIMED.value])
        )
        result = await self.session.execute(stmt_completed)
        completed_ids = [row[0] for row in result]

        # Obtener misiones activas, excluyendo las completadas (si no son repetibles)
        stmt = select(Mission).where(Mission.active == True)
        result = await self.session.execute(stmt)
        all_missions = list(result.scalars().all())

        available = []
        for mission in all_missions:
            if mission.repeatable or mission.id not in completed_ids:
                available.append(mission)

        return available

    # ========================================
    # PROGRESO
    # ========================================

    async def on_user_reaction(
        self,
        user_id: int,
        emoji: str,
        reacted_at: datetime
    ):
        """Hook para actualizar progreso cuando usuario reacciona.

        Args:
            user_id: ID del usuario
            emoji: Emoji de la reacción
            reacted_at: Timestamp de la reacción

        Returns:
            Lista de tuplas (user_mission, mission) de las misiones completadas
        """
        # Obtener misiones IN_PROGRESS
        active_missions = await self.get_user_missions(
            user_id,
            status=MissionStatus.IN_PROGRESS
        )

        # Obtener racha del usuario (para misiones tipo STREAK)
        stmt = select(UserStreak).where(UserStreak.user_id == user_id)
        result = await self.session.execute(stmt)
        user_streak = result.scalar_one_or_none()

        completed_missions = []

        for user_mission in active_missions:
            mission = await self.session.get(Mission, user_mission.mission_id)

            completed = False

            # Actualizar según tipo
            if mission.mission_type == MissionType.STREAK.value:
                if user_streak:
                    completed = await self._update_streak_progress(user_mission, user_streak, mission)

            elif mission.mission_type == MissionType.DAILY.value:
                completed = await self._update_daily_progress(user_mission, emoji, reacted_at, mission)

            elif mission.mission_type == MissionType.WEEKLY.value:
                completed = await self._update_weekly_progress(user_mission, emoji, reacted_at, mission)

            if completed:
                completed_missions.append((user_mission, mission))

        await self.session.commit()
        return completed_missions

    async def _update_streak_progress(
        self,
        user_mission: UserMission,
        user_streak: UserStreak,
        mission: Mission
    ) -> bool:
        """Actualiza progreso de misión streak.

        Args:
            user_mission: UserMission a actualizar
            user_streak: Racha del usuario
            mission: Misión asociada

        Returns:
            True si se completó la misión
        """
        criteria = json.loads(mission.criteria)
        required_days = criteria.get('days', 7)

        progress = json.loads(user_mission.progress) if user_mission.progress else {}
        progress['days_completed'] = user_streak.current_streak
        if user_streak.last_reaction_date:
            progress['last_reaction_date'] = user_streak.last_reaction_date.isoformat()

        user_mission.progress = json.dumps(progress)

        if user_streak.current_streak >= required_days:
            user_mission.status = MissionStatus.COMPLETED.value
            user_mission.completed_at = datetime.now(UTC)
            logger.info(f"User {user_mission.user_id} completed STREAK mission {mission.id}")
            return True

        return False

    async def _update_daily_progress(
        self,
        user_mission: UserMission,
        emoji: str,
        reacted_at: datetime,
        mission: Mission
    ) -> bool:
        """Actualiza progreso de misión diaria.

        Args:
            user_mission: UserMission a actualizar
            emoji: Emoji de la reacción
            reacted_at: Timestamp de la reacción
            mission: Misión asociada

        Returns:
            True si se completó la misión
        """
        criteria = json.loads(mission.criteria)
        required_count = criteria.get('count', 5)
        specific_reaction = criteria.get('specific_reaction')

        # Si requiere emoji específico y no coincide, ignorar
        if specific_reaction and emoji != specific_reaction:
            return False

        progress = json.loads(user_mission.progress) if user_mission.progress else {
            'reactions_today': 0,
            'date': None
        }

        today = reacted_at.date().isoformat()

        # Si cambió el día, resetear
        if progress.get('date') != today:
            progress['reactions_today'] = 0
            progress['date'] = today

        progress['reactions_today'] += 1
        user_mission.progress = json.dumps(progress)

        if progress['reactions_today'] >= required_count:
            user_mission.status = MissionStatus.COMPLETED.value
            user_mission.completed_at = datetime.now(UTC)
            logger.info(f"User {user_mission.user_id} completed DAILY mission {mission.id}")
            return True

        return False

    async def _update_weekly_progress(
        self,
        user_mission: UserMission,
        emoji: str,
        reacted_at: datetime,
        mission: Mission
    ) -> bool:
        """Actualiza progreso de misión semanal.

        Args:
            user_mission: UserMission a actualizar
            emoji: Emoji de la reacción
            reacted_at: Timestamp de la reacción
            mission: Misión asociada

        Returns:
            True si se completó la misión
        """
        criteria = json.loads(mission.criteria)
        required_target = criteria.get('target', 50)
        specific_days = criteria.get('specific_days')  # [0, 1, 2, 3, 4, 5, 6] (0=Sunday)

        # Si requiere días específicos, verificar
        if specific_days and reacted_at.weekday() not in specific_days:
            return False

        progress = json.loads(user_mission.progress) if user_mission.progress else {
            'reactions_this_week': 0,
            'week_start': None
        }

        # Calcular inicio de semana (lunes)
        week_start = (reacted_at - timedelta(days=reacted_at.weekday())).date().isoformat()

        # Si cambió la semana, resetear
        if progress.get('week_start') != week_start:
            progress['reactions_this_week'] = 0
            progress['week_start'] = week_start

        progress['reactions_this_week'] += 1
        user_mission.progress = json.dumps(progress)

        if progress['reactions_this_week'] >= required_target:
            user_mission.status = MissionStatus.COMPLETED.value
            user_mission.completed_at = datetime.now(UTC)
            logger.info(f"User {user_mission.user_id} completed WEEKLY mission {mission.id}")
            return True

        return False

    async def update_progress(
        self,
        user_id: int,
        mission_id: int,
        new_data: dict
    ) -> UserMission:
        """Actualiza progreso de misión manualmente.

        Args:
            user_id: ID del usuario
            mission_id: ID de la misión
            new_data: Datos de progreso a actualizar

        Returns:
            UserMission actualizada

        Raises:
            ValueError: Si UserMission no existe
        """
        stmt = select(UserMission).where(
            UserMission.user_id == user_id,
            UserMission.mission_id == mission_id
        )
        result = await self.session.execute(stmt)
        user_mission = result.scalar_one_or_none()

        if not user_mission:
            raise ValueError("UserMission not found")

        # Merge con progreso existente
        progress = json.loads(user_mission.progress) if user_mission.progress else {}
        progress.update(new_data)
        user_mission.progress = json.dumps(progress)

        await self.session.commit()
        await self.session.refresh(user_mission)

        return user_mission

    async def check_completion(
        self,
        user_id: int,
        mission_id: int
    ) -> Tuple[bool, UserMission]:
        """Verifica si misión está completa según criterios.

        Args:
            user_id: ID del usuario
            mission_id: ID de la misión

        Returns:
            (is_complete, user_mission)

        Raises:
            ValueError: Si UserMission no existe
        """
        stmt = select(UserMission).where(
            UserMission.user_id == user_id,
            UserMission.mission_id == mission_id
        )
        result = await self.session.execute(stmt)
        user_mission = result.scalar_one_or_none()

        if not user_mission:
            raise ValueError("UserMission not found")

        is_complete = user_mission.status == MissionStatus.COMPLETED.value
        return is_complete, user_mission

    # ========================================
    # RECLAMAR RECOMPENSA
    # ========================================

    async def claim_reward(
        self,
        user_id: int,
        mission_id: int
    ) -> Tuple[bool, str, dict]:
        """Reclama recompensa de misión completada.

        Args:
            user_id: ID del usuario
            mission_id: ID de la misión

        Returns:
            (success, message, rewards_info)

            rewards_info = {
                'besitos': int,
                'level_up': Optional[Level],
                'unlocked_rewards': List[Reward]
            }
        """
        # Obtener user_mission
        stmt = select(UserMission).where(
            UserMission.user_id == user_id,
            UserMission.mission_id == mission_id
        )
        result = await self.session.execute(stmt)
        user_mission = result.scalar_one_or_none()

        if not user_mission:
            return False, "Mission not found", {}

        if user_mission.claimed_at:
            return False, "Reward already claimed", {}

        if user_mission.status != MissionStatus.COMPLETED.value:
            return False, "Mission not completed", {}

        # Obtener misión
        mission = await self.session.get(Mission, mission_id)

        rewards_info = {
            'besitos': 0,
            'level_up': None,
            'unlocked_rewards': []
        }

        # 1. Otorgar besitos
        besito_service = self.session.container.besito

        besitos_granted = await besito_service.grant_besitos(
            user_id=user_id,
            amount=mission.besitos_reward,
            transaction_type=TransactionType.MISSION_REWARD,
            description=f"Misión completada: {mission.name}",
            reference_id=user_mission.id
        )
        rewards_info['besitos'] = besitos_granted

        # 2. Auto level-up
        if mission.auto_level_up_id:
            await self.session.container.level.set_user_level(
                user_id,
                mission.auto_level_up_id
            )
            level = await self.session.get(Level, mission.auto_level_up_id)
            rewards_info['level_up'] = level

        # 3. Unlock rewards (si aplica)
        if mission.unlock_rewards:
            unlock_ids = json.loads(mission.unlock_rewards)
            for reward_id in unlock_ids:
                reward = await self.session.get(Reward, reward_id)
                if reward:
                    rewards_info['unlocked_rewards'].append(reward)

        # 4. Marcar como reclamada
        user_mission.status = MissionStatus.CLAIMED.value
        user_mission.claimed_at = datetime.now(UTC)
        await self.session.commit()

        logger.info(f"User {user_id} claimed mission {mission_id}: +{besitos_granted} besitos")

        return True, f"Recompensa reclamada: +{besitos_granted} besitos", rewards_info
