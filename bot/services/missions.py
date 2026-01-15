"""
Mission Service - Gestión de misiones de gamificación.

Maneja:
- CRUD de misiones
- Progreso de usuarios en misiones
- Recompensas de misiones

NOTE: Implementación básica para SPRINT 1.
SPRINT 4 completará la funcionalidad completa.
"""
import logging
from typing import List, Tuple, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.database.gamification_models import Mission, UserMissionProgress
from bot.database.enums import MissionType

logger = logging.getLogger(__name__)


class MissionService:
    """
    Servicio para gestión de misiones.

    Attributes:
        _session: Sesión de base de datos SQLAlchemy
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el MissionService.

        Args:
            session: Sesión de base de datos SQLAlchemy
        """
        self._session = session

    # ===== MISIONES =====

    async def get_active_missions(self) -> List[Mission]:
        """
        Obtiene todas las misiones activas.

        Returns:
            List[Mission]: Lista de misiones
        """
        result = await self._session.execute(
            select(Mission)
            .where(Mission.active == True)
        )
        return list(result.scalars().all())

    async def get_mission(self, mission_id: int) -> Optional[Mission]:
        """
        Obtiene una misión por ID.

        Args:
            mission_id: ID de la misión

        Returns:
            Mission o None si no existe
        """
        result = await self._session.execute(
            select(Mission).where(Mission.id == mission_id)
        )
        return result.scalar_one_or_none()

    # ===== PROGRESO =====

    async def get_user_missions(self, user_id: int) -> List[dict]:
        """
        Obtiene misiones con progreso de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            List[dict]: Lista de {mission, progress}

        NOTE: Implementación completa en SPRINT 4
        """
        # TODO: Implementar:
        # - Obtener misiones activas
        # - Para cada misión, buscar progreso del usuario
        # - Retornar lista con ambos
        return []

    # ===== ACTUALIZACIÓN DE PROGRESO =====

    async def update_progress(
        self,
        user_id: int,
        mission_type: MissionType,
        increment: int = 1
    ) -> List[Mission]:
        """
        Actualiza el progreso del usuario en misiones de un tipo.

        Args:
            user_id: ID del usuario
            mission_type: Tipo de misión
            increment: Cantidad a incrementar

        Returns:
            List[Mission]: Misiones completadas

        NOTE: Implementación completa en SPRINT 4
        """
        # TODO: Implementar:
        # - Buscar misiones activas del tipo
        # - Para cada una, buscar/crear progreso
        # - Incrementar current_value
        # - Verificar si completó (current_value >= target_value)
        # - Retornar misiones completadas
        return []

    # ===== RECOMPENSAS =====

    async def claim_reward(
        self,
        user_id: int,
        mission_id: int
    ) -> Tuple[bool, str]:
        """
        Reclama la recompensa de una misión completada.

        Args:
            user_id: ID del usuario
            mission_id: ID de la misión

        Returns:
            Tuple[bool, str]: (éxito, mensaje)

        NOTE: Implementación completa en SPRINT 4
        """
        # TODO: Implementar:
        # - Verificar que misión está completada
        # - Verificar que recompensa no ha sido reclamada
        # - Entregar recompensa (puntos, badge, o media_set)
        # - Marcar reward_claimed = True
        return False, "Implementación pendiente (SPRINT 4)"
