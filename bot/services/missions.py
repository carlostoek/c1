"""
Missions Service - Gestión de misiones y progreso de usuarios.

Responsabilidades:
- Obtener misiones disponibles para usuario
- Tracking automático de progreso
- Reset de misiones temporales (daily, weekly)
- Entrega de recompensas al completar
- Validación de requisitos (nivel, VIP)

Características:
- Daily: Se resetean cada 24 horas
- Weekly: Se resetean cada lunes
- Permanent: Una sola vez (achievements)
"""
import logging
from typing import List, Optional, Dict
from datetime import datetime, timezone

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import Mission, UserMission, MissionType, ObjectiveType

logger = logging.getLogger(__name__)


class MissionsService:
    """
    Servicio de gestión de misiones.

    Métodos principales:
    - get_active_missions(): Misiones disponibles para usuario
    - get_user_missions(): Progreso del usuario
    - update_progress(): Incrementar progreso automáticamente
    - check_completion(): Verificar si completó
    - reset_expired_missions(): Reset automático para background task
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

    # ===== CONSULTAS DE MISIONES =====

    async def get_active_missions(
        self,
        user_id: int,
        mission_type: Optional[MissionType] = None
    ) -> List[Mission]:
        """
        Obtiene misiones activas disponibles para el usuario.

        Filtra por:
        - is_active = True
        - Nivel del usuario >= required_level
        - VIP si es requerido

        Args:
            user_id: ID del usuario
            mission_type: Tipo específico a filtrar (opcional)

        Returns:
            Lista de Mission disponibles
        """
        try:
            # Obtener nivel y VIP del usuario
            level = 1
            is_vip = False

            if self.container:
                try:
                    level = await self.container.levels.get_user_level(user_id)
                except Exception:
                    level = 1
                # TODO: Verificar is_vip del usuario cuando esté disponible

            # Query base
            query = select(Mission).where(
                and_(
                    Mission.is_active == True,
                    Mission.required_level <= level
                )
            )

            # Filtrar por tipo si se especifica
            if mission_type:
                query = query.where(Mission.mission_type == mission_type)

            # Filtrar si no es VIP
            if not is_vip:
                query = query.where(Mission.is_vip_only == False)

            result = await self.session.execute(query)
            missions = list(result.scalars().all())

            self._logger.debug(f"Found {len(missions)} active missions for user {user_id}")
            return missions

        except Exception as e:
            self._logger.error(f"Error getting active missions: {e}", exc_info=True)
            return []

    async def get_user_missions(
        self,
        user_id: int,
        include_completed: bool = False
    ) -> List[UserMission]:
        """
        Obtiene progreso de misiones del usuario.

        Args:
            user_id: ID del usuario
            include_completed: Incluir misiones completadas

        Returns:
            Lista de UserMission
        """
        try:
            query = select(UserMission).where(UserMission.user_id == user_id)

            if not include_completed:
                query = query.where(UserMission.is_completed == False)

            result = await self.session.execute(query)
            user_missions = list(result.scalars().all())

            return user_missions

        except Exception as e:
            self._logger.error(f"Error getting user missions: {e}", exc_info=True)
            return []

    async def get_or_create_user_mission(
        self,
        user_id: int,
        mission_id: int
    ) -> Optional[UserMission]:
        """
        Obtiene o crea UserMission para tracking de progreso.

        Si no existe, lo crea automáticamente en la BD.

        Args:
            user_id: ID del usuario
            mission_id: ID de la misión

        Returns:
            UserMission creado/obtenido o None
        """
        try:
            # Buscar existente
            result = await self.session.execute(
                select(UserMission).where(
                    and_(
                        UserMission.user_id == user_id,
                        UserMission.mission_id == mission_id
                    )
                )
            )
            user_mission = result.scalar_one_or_none()

            if user_mission:
                return user_mission

            # Crear nuevo
            user_mission = UserMission(
                user_id=user_id,
                mission_id=mission_id,
                current_progress=0,
                is_completed=False
            )
            self.session.add(user_mission)
            await self.session.flush()

            self._logger.info(f"Created UserMission: user={user_id}, mission={mission_id}")
            return user_mission

        except Exception as e:
            self._logger.error(f"Error creating UserMission: {e}", exc_info=True)
            return None

    # ===== ACTUALIZACIÓN DE PROGRESO =====

    async def update_progress(
        self,
        user_id: int,
        objective_type: ObjectiveType,
        amount: int = 1
    ) -> List[UserMission]:
        """
        Actualiza progreso de misiones según el tipo de objetivo.

        Se llama automáticamente cuando:
        - Usuario gana puntos → ObjectiveType.POINTS
        - Usuario hace reacción → ObjectiveType.REACTIONS
        - Usuario sube de nivel → ObjectiveType.LEVEL

        Args:
            user_id: ID del usuario
            objective_type: Tipo de objetivo (POINTS, REACTIONS, LEVEL, CUSTOM)
            amount: Cantidad a incrementar

        Returns:
            Lista de UserMissions actualizadas

        Example:
            >>> # Usuario gana 10 puntos
            >>> updated = await service.update_progress(123, ObjectiveType.POINTS, 10)
            >>>
            >>> # Usuario hace una reacción
            >>> updated = await service.update_progress(123, ObjectiveType.REACTIONS, 1)
        """
        try:
            # Obtener misiones activas del tipo correcto
            result = await self.session.execute(
                select(Mission).where(
                    and_(
                        Mission.is_active == True,
                        Mission.objective_type == objective_type
                    )
                )
            )
            missions = list(result.scalars().all())

            updated = []

            for mission in missions:
                # Obtener o crear UserMission
                user_mission = await self.get_or_create_user_mission(user_id, mission.id)

                if not user_mission or user_mission.is_completed:
                    continue

                # Reset si es necesario
                now = datetime.now(timezone.utc)
                if user_mission.should_reset(now):
                    await self._reset_user_mission(user_mission, now)

                # Actualizar progreso
                user_mission.current_progress += amount

                # Verificar completado
                if user_mission.current_progress >= mission.objective_value:
                    await self._complete_mission(user_mission, now)

                updated.append(user_mission)

            if updated:
                await self.session.commit()

            self._logger.debug(
                f"Updated progress for user {user_id}: "
                f"{objective_type.value} +{amount} ({len(updated)} missions)"
            )

            return updated

        except Exception as e:
            await self.session.rollback()
            self._logger.error(f"Error updating progress: {e}", exc_info=True)
            return []

    async def _complete_mission(
        self,
        user_mission: UserMission,
        now: datetime
    ):
        """
        Marca misión como completada y entrega recompensa.

        Args:
            user_mission: UserMission a completar
            now: Datetime actual
        """
        user_mission.is_completed = True
        user_mission.completed_at = now

        # Entregar recompensa si existe
        if user_mission.mission.reward_id and self.container:
            try:
                reward = user_mission.mission.reward
                if not reward or not reward.is_active:
                    self._logger.warning(
                        f"Reward {user_mission.mission.reward_id} not available"
                    )
                    return

                # Entregar según tipo de recompensa
                if reward.reward_type == "badge":
                    if reward.badge_id:
                        await self.container.badges.assign_badge(
                            user_id=user_mission.user_id,
                            badge_id=reward.badge_id,
                            source="mission"
                        )
                        self._logger.info(
                            f"Badge reward delivered: user={user_mission.user_id}, "
                            f"badge={reward.badge_id}, mission={user_mission.mission.name}"
                        )

                elif reward.reward_type == "points":
                    if reward.points_amount > 0:
                        await self.container.points.add_points(
                            user_id=user_mission.user_id,
                            points=reward.points_amount,
                            reason=f"Mission reward: {user_mission.mission.name}"
                        )
                        self._logger.info(
                            f"Points reward delivered: user={user_mission.user_id}, "
                            f"points={reward.points_amount}, mission={user_mission.mission.name}"
                        )

                else:
                    self._logger.debug(
                        f"Reward type {reward.reward_type} not yet implemented"
                    )

                self._logger.info(
                    f"Mission completed: user={user_mission.user_id}, "
                    f"mission={user_mission.mission.name}, reward={reward.name}"
                )
            except Exception as e:
                self._logger.error(f"Error delivering reward: {e}", exc_info=True)

    async def _reset_user_mission(
        self,
        user_mission: UserMission,
        now: datetime
    ):
        """
        Resetea progreso de misión temporal.

        Args:
            user_mission: UserMission a resetear
            now: Datetime actual
        """
        user_mission.current_progress = 0
        user_mission.is_completed = False
        user_mission.completed_at = None
        user_mission.last_reset_at = now

        self._logger.info(
            f"Reset mission: user={user_mission.user_id}, "
            f"mission={user_mission.mission.name}"
        )

    # ===== RESET AUTOMÁTICO =====

    async def reset_expired_missions(self) -> int:
        """
        Resetea todas las misiones temporales expiradas.

        Llamar periódicamente vía cron job (ej: cada hora) para
        resetear misiones daily y weekly cuando corresponda.

        Returns:
            Cantidad de misiones reseteadas
        """
        try:
            now = datetime.now(timezone.utc)

            # Obtener todas las UserMissions activas (no completadas)
            result = await self.session.execute(
                select(UserMission).where(
                    UserMission.is_completed == False
                )
            )
            user_missions = list(result.scalars().all())

            reset_count = 0

            for um in user_missions:
                if um.should_reset(now):
                    await self._reset_user_mission(um, now)
                    reset_count += 1

            if reset_count > 0:
                await self.session.commit()

            self._logger.info(f"Reset {reset_count} expired missions")
            return reset_count

        except Exception as e:
            await self.session.rollback()
            self._logger.error(f"Error resetting missions: {e}", exc_info=True)
            return 0

    # ===== ADMIN =====

    async def create_mission(
        self,
        name: str,
        description: str,
        icon: str,
        mission_type: MissionType,
        objective_type: ObjectiveType,
        objective_value: int,
        reward_id: Optional[int] = None,
        required_level: int = 1,
        is_vip_only: bool = False,
        mission_metadata: Optional[Dict] = None
    ) -> Optional[Mission]:
        """
        Crea nueva misión (admin).

        Args:
            name: Nombre de la misión
            description: Descripción
            icon: Emoji
            mission_type: Tipo (daily, weekly, permanent)
            objective_type: Tipo de objetivo
            objective_value: Valor objetivo
            reward_id: ID de recompensa (opcional)
            required_level: Nivel mínimo
            is_vip_only: Solo para VIP
            mission_metadata: Datos adicionales

        Returns:
            Mission creada o None
        """
        try:
            mission = Mission(
                name=name,
                description=description,
                icon=icon,
                mission_type=mission_type,
                objective_type=objective_type,
                objective_value=objective_value,
                reward_id=reward_id,
                required_level=required_level,
                is_vip_only=is_vip_only,
                mission_metadata=mission_metadata
            )
            self.session.add(mission)
            await self.session.flush()

            self._logger.info(f"Created mission: {mission.name} (id={mission.id})")
            return mission

        except Exception as e:
            self._logger.error(f"Error creating mission: {e}", exc_info=True)
            raise

    async def toggle_mission(self, mission_id: int, active: bool) -> Optional[Mission]:
        """
        Activa o desactiva una misión.

        Args:
            mission_id: ID de la misión
            active: True para activar, False para desactivar

        Returns:
            Mission actualizada o None
        """
        try:
            result = await self.session.execute(
                select(Mission).where(Mission.id == mission_id)
            )
            mission = result.scalar_one_or_none()

            if not mission:
                return None

            mission.is_active = active
            await self.session.flush()

            self._logger.info(f"Toggled mission {mission_id}: active={active}")
            return mission

        except Exception as e:
            self._logger.error(f"Error toggling mission: {e}", exc_info=True)
            return None
