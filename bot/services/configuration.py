"""
Configuration Service - Creación unificada de recursos complejos.

Orquesta la creación de recursos relacionados (misiones con recompensas,
badges, etc.) en una sola transacción atómica.

FILOSOFÍA: Simple y directo. Sin abstracciones innecesarias.
"""
import logging
from typing import Dict, Optional, List
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import (
    Mission, MissionType, ObjectiveType,
    Reward, RewardType, RewardLimit,
    Badge, BadgeRarity,
    UserBadge
)

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Error en configuración. Causa rollback automático."""
    pass


class ConfigurationService:
    """
    Servicio para crear recursos complejos en una sola transacción.

    Métodos principales:
    - create_mission_complete() → Misión + Recompensa + Badge + Contenido
    - create_reward_complete() → Recompensa + Badge + Contenido

    Todo se crea en transacción atómica: todo o nada.

    Attributes:
        _session: AsyncSession para operaciones de BD
        _container: ServiceContainer para acceso a otros servicios
    """

    def __init__(self, session: AsyncSession, container):
        """
        Inicializa ConfigurationService.

        Args:
            session: Sesión de BD async
            container: ServiceContainer para acceso a otros servicios
        """
        self._session = session
        self._container = container
        self._logger = logging.getLogger(__name__)

    # ===== MISIÓN COMPLETA =====

    async def create_mission_complete(
        self,
        mission_data: Dict,
        reward_data: Optional[Dict] = None,
        badge_data: Optional[Dict] = None,
        content_data: Optional[Dict] = None
    ) -> Dict:
        """
        Crea misión con todos sus recursos relacionados.

        TODO en una transacción atómica. Si algo falla: rollback.

        Args:
            mission_data: Datos de la misión
                {
                    "name": "Primera Centena",
                    "description": "Alcanza 100 besitos",
                    "icon": "🎯",
                    "mission_type": "permanent",
                    "objective_type": "points",
                    "objective_value": 100,
                    "required_level": 1,
                    "is_vip_only": False
                }

            reward_data: Datos de recompensa (opcional)
                {
                    "name": "Badge de Centena",
                    "description": "Por alcanzar 100 besitos",
                    "icon": "🏆",
                    "reward_type": "badge",
                    "cost": 0,
                    "limit_type": "once",
                    "points_amount": 50
                }

            badge_data: Datos de badge (opcional)
                {
                    "name": "Centena",
                    "description": "Primera centena alcanzada",
                    "emoji": "🏆",
                    "rarity": "rare"
                }

            content_data: Datos de contenido (opcional)
                {
                    "content_id": "video_123",
                    "title": "Tutorial especial"
                }

        Returns:
            Dict con todos los recursos creados:
            {
                'mission': Mission,
                'reward': Reward (si se creó),
                'badge': Badge (si se creó)
            }

        Raises:
            ConfigurationError: Si algo falla (rollback automático)

        Example:
            >>> service = ConfigurationService(session, container)
            >>>
            >>> result = await service.create_mission_complete(
            ...     mission_data={
            ...         "name": "Primera Centena",
            ...         "description": "Alcanza 100 besitos",
            ...         "mission_type": "permanent",
            ...         "objective_type": "points",
            ...         "objective_value": 100
            ...     },
            ...     badge_data={
            ...         "name": "Centena",
            ...         "emoji": "🏆",
            ...         "rarity": "rare"
            ...     }
            ... )
            >>>
            >>> print(f"Misión: {result['mission'].name}")
            >>> print(f"Badge: {result['badge'].display_name}")
        """
        try:
            created = {}

            # 1. Crear badge si se especificó
            if badge_data:
                badge = await self._create_badge(badge_data)
                created['badge'] = badge
                self._logger.info(f"✅ Badge creado: {badge.name}")

            # 2. Crear recompensa vinculando badge y contenido
            if reward_data:
                # Vincular automáticamente badge si existe
                if 'badge' in created:
                    reward_data['badge_id'] = created['badge'].id

                # Vincular contenido si se proporciona
                if content_data:
                    reward_data['content_id'] = content_data.get('content_id')

                reward = await self._create_reward(reward_data)
                created['reward'] = reward
                self._logger.info(f"✅ Recompensa creada: {reward.name}")

            # 3. Crear misión vinculando recompensa
            if 'reward' in created:
                mission_data['reward_id'] = created['reward'].id

            mission = await self._create_mission(mission_data)
            created['mission'] = mission
            self._logger.info(f"✅ Misión creada: {mission.name}")

            await self._session.commit()

            self._logger.info(f"🎉 Configuración completa exitosa: {mission.name}")
            return created

        except Exception as e:
            await self._session.rollback()
            self._logger.error(
                f"❌ Error en create_mission_complete: {e}",
                exc_info=True
            )
            raise ConfigurationError(
                f"No se pudo completar la configuración: {str(e)}"
            ) from e

    # ===== RECOMPENSA COMPLETA =====

    async def create_reward_complete(
        self,
        reward_data: Dict,
        badge_data: Optional[Dict] = None,
        content_data: Optional[Dict] = None
    ) -> Dict:
        """
        Crea recompensa con badge y/o contenido.

        Similar a create_mission_complete pero solo para recompensa.

        Args:
            reward_data: Datos de la recompensa
            badge_data: Datos del badge (opcional)
            content_data: Datos del contenido (opcional)

        Returns:
            Dict con recursos creados:
            {
                'reward': Reward,
                'badge': Badge (si se creó)
            }

        Raises:
            ConfigurationError: Si algo falla
        """
        try:
            created = {}

            # 1. Badge
            if badge_data:
                badge = await self._create_badge(badge_data)
                created['badge'] = badge
                reward_data['badge_id'] = badge.id
                self._logger.info(f"✅ Badge creado: {badge.name}")

            # 2. Contenido
            if content_data:
                reward_data['content_id'] = content_data.get('content_id')

            # 3. Recompensa
            reward = await self._create_reward(reward_data)
            created['reward'] = reward
            self._logger.info(f"✅ Recompensa creada: {reward.name}")

            await self._session.commit()
            return created

        except Exception as e:
            await self._session.rollback()
            self._logger.error(
                f"❌ Error en create_reward_complete: {e}",
                exc_info=True
            )
            raise ConfigurationError(f"Error creando recompensa: {str(e)}") from e

    # ===== MÉTODOS PRIVADOS (creación de recursos individuales) =====

    async def _create_mission(self, data: Dict) -> Mission:
        """
        Crea misión en BD.

        Args:
            data: Diccionario con datos de la misión

        Returns:
            Instancia de Mission creada

        Raises:
            ValueError: Si datos inválidos
            ConfigurationError: Si error de BD
        """
        try:
            # Validaciones básicas
            if not data.get('name'):
                raise ValueError("Nombre de misión requerido")

            if not data.get('objective_value') or data['objective_value'] <= 0:
                raise ValueError("Valor objetivo debe ser positivo")

            # Crear instancia
            mission = Mission(
                name=data['name'],
                description=data.get('description', ''),
                icon=data.get('icon', '🎯'),
                mission_type=MissionType(data.get('mission_type', 'permanent')),
                objective_type=ObjectiveType(data.get('objective_type', 'points')),
                objective_value=data['objective_value'],
                reward_id=data.get('reward_id'),
                required_level=data.get('required_level', 1),
                is_vip_only=data.get('is_vip_only', False),
                is_active=data.get('is_active', True),
                mission_metadata=data.get('metadata')
            )

            self._session.add(mission)
            await self._session.flush()

            return mission

        except ValueError as e:
            raise ConfigurationError(f"Datos inválidos para misión: {str(e)}") from e
        except Exception as e:
            raise ConfigurationError(f"Error creando misión: {str(e)}") from e

    async def _create_reward(self, data: Dict) -> Reward:
        """
        Crea recompensa en BD.

        Args:
            data: Diccionario con datos de la recompensa

        Returns:
            Instancia de Reward creada

        Raises:
            ValueError: Si datos inválidos
            ConfigurationError: Si error de BD
        """
        try:
            # Validaciones básicas
            if not data.get('name'):
                raise ValueError("Nombre de recompensa requerido")

            if 'cost' not in data or data['cost'] < 0:
                raise ValueError("Costo debe ser >= 0")

            # Crear instancia
            reward = Reward(
                name=data['name'],
                description=data.get('description', ''),
                icon=data.get('icon', '🎁'),
                reward_type=RewardType(data.get('reward_type', 'badge')),
                cost=data['cost'],
                limit_type=RewardLimit(data.get('limit_type', 'once')),
                badge_id=data.get('badge_id'),
                content_id=data.get('content_id'),
                points_amount=data.get('points_amount', 0),
                required_level=data.get('required_level', 1),
                is_vip_only=data.get('is_vip_only', False),
                is_active=data.get('is_active', True),
                stock=data.get('stock'),
                reward_metadata=data.get('metadata')
            )

            self._session.add(reward)
            await self._session.flush()

            return reward

        except ValueError as e:
            raise ConfigurationError(f"Datos inválidos para recompensa: {str(e)}") from e
        except Exception as e:
            raise ConfigurationError(f"Error creando recompensa: {str(e)}") from e

    async def _create_badge(self, data: Dict) -> Badge:
        """
        Crea badge en BD.

        Args:
            data: Diccionario con datos del badge

        Returns:
            Instancia de Badge creada

        Raises:
            ValueError: Si datos inválidos
            ConfigurationError: Si error de BD
        """
        try:
            # Validaciones básicas
            if not data.get('name'):
                raise ValueError("Nombre de badge requerido")

            if not data.get('emoji'):
                raise ValueError("Emoji de badge requerido")

            # Verificar que el nombre sea único
            stmt = select(Badge).where(Badge.name == data['name'])
            result = await self._session.execute(stmt)
            if result.scalar_one_or_none():
                raise ValueError(f"Badge '{data['name']}' ya existe")

            # Crear instancia
            badge = Badge(
                name=data['name'],
                description=data.get('description', ''),
                emoji=data['emoji'],
                rarity=BadgeRarity(data.get('rarity', 'common')),
                is_active=data.get('is_active', True),
                is_secret=data.get('is_secret', False),
                badge_metadata=data.get('metadata')
            )

            self._session.add(badge)
            await self._session.flush()

            return badge

        except ValueError as e:
            raise ConfigurationError(f"Datos inválidos para badge: {str(e)}") from e
        except Exception as e:
            raise ConfigurationError(f"Error creando badge: {str(e)}") from e

    # ===== MÉTODOS DE CONSULTA =====

    async def get_existing_badges(self) -> List[Badge]:
        """
        Obtiene lista de badges existentes para reutilizar.

        Returns:
            Lista de badges disponibles
        """
        try:
            stmt = select(Badge).where(Badge.is_active == True).order_by(Badge.name)
            result = await self._session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            self._logger.error(f"Error obteniendo badges: {e}")
            return []

    async def get_existing_rewards(self) -> List[Reward]:
        """
        Obtiene lista de recompensas existentes.

        Returns:
            Lista de recompensas disponibles
        """
        try:
            stmt = select(Reward).where(Reward.is_active == True).order_by(Reward.name)
            result = await self._session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            self._logger.error(f"Error obteniendo recompensas: {e}")
            return []

    async def get_existing_missions(self) -> List[Mission]:
        """
        Obtiene lista de misiones existentes.

        Returns:
            Lista de misiones disponibles
        """
        try:
            stmt = select(Mission).where(Mission.is_active == True).order_by(Mission.name)
            result = await self._session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            self._logger.error(f"Error obteniendo misiones: {e}")
            return []

    async def get_badge_by_name(self, name: str) -> Optional[Badge]:
        """
        Obtiene un badge por nombre.

        Args:
            name: Nombre del badge

        Returns:
            Badge si existe, None si no
        """
        try:
            stmt = select(Badge).where(Badge.name == name)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            self._logger.error(f"Error obteniendo badge '{name}': {e}")
            return None
