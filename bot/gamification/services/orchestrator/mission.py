"""
Orquestador de creación de misiones.

Coordina creación de misiones con auto-creación de niveles
y recompensas en transacciones atómicas.
"""

from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from bot.gamification.services.mission import MissionService
from bot.gamification.services.level import LevelService
from bot.gamification.services.reward import RewardService
from bot.gamification.database.enums import MissionType, RewardType, BadgeRarity
from bot.gamification.utils.validators import (
    validate_mission_criteria,
    validate_reward_metadata
)

logger = logging.getLogger(__name__)


# Plantillas predefinidas
MISSION_TEMPLATES = {
    "welcome": {
        "mission_data": {
            "name": "Bienvenido al Sistema",
            "description": "Completa tu primera reacción",
            "mission_type": MissionType.ONE_TIME,
            "criteria": {"type": MissionType.ONE_TIME},
            "besitos_reward": 100,
            "repeatable": False
        },
        "auto_level_data": {
            "name": "Nuevo Usuario",
            "min_besitos": 0,
            "order": 1
        },
        "rewards_data": [
            {
                "name": "Primer Paso",
                "description": "Completaste tu primera misión",
                "reward_type": RewardType.BADGE,
                "metadata": {"icon": "🎯", "rarity": BadgeRarity.COMMON}
            }
        ]
    },

    "weekly_streak": {
        "mission_data": {
            "name": "Racha de 7 Días",
            "description": "Reacciona 7 días consecutivos",
            "mission_type": MissionType.STREAK,
            "criteria": {"type": MissionType.STREAK, "days": 7, "require_consecutive": True},
            "besitos_reward": 500,
            "repeatable": True
        }
    },

    "daily_reactor": {
        "mission_data": {
            "name": "Reactor Diario",
            "description": "Reacciona 5 veces hoy",
            "mission_type": MissionType.DAILY,
            "criteria": {"type": MissionType.DAILY, "count": 5},
            "besitos_reward": 200,
            "repeatable": True
        }
    }
}


class MissionOrchestrator:
    """Orquestador de creación de misiones."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.mission_service = MissionService(session)
        self.level_service = LevelService(session)
        self.reward_service = RewardService(session)

    async def create_mission_with_dependencies(
        self,
        mission_data: dict,
        auto_level_data: Optional[dict] = None,
        rewards_data: Optional[List[dict]] = None,
        created_by: int = 0
    ) -> dict:
        """
        Crea misión con dependencias en transacción atómica.

        Args:
            mission_data: {
                'name': str,
                'description': str,
                'mission_type': MissionType,
                'criteria': dict,
                'besitos_reward': int,
                'repeatable': bool
            }
            auto_level_data: {
                'name': str,
                'min_besitos': int,
                'order': int,
                'benefits': Optional[dict]
            }
            rewards_data: List[{
                'name': str,
                'description': str,
                'reward_type': RewardType,
                'cost_besitos': Optional[int],
                'metadata': dict
            }]
            created_by: ID del admin que crea

        Returns:
            {
                'mission': Mission,
                'created_level': Optional[Level],
                'created_rewards': List[Reward],
                'validation_errors': List[str]
            }
        """
        logger.info(f"Creating mission with dependencies: {mission_data.get('name')}")

        # Validar primero
        is_valid, errors = await self.validate_mission_creation(
            mission_data, auto_level_data, rewards_data
        )
        if not is_valid:
            logger.warning(f"Validation failed: {errors}")
            return {
                'mission': None,
                'created_level': None,
                'created_rewards': [],
                'validation_errors': errors
            }

        created_level = None
        created_rewards = []

        try:
            # Crear nivel si se especificó
            if auto_level_data:
                logger.debug(f"Creating auto level: {auto_level_data.get('name')}")
                created_level = await self.level_service.create_level(**auto_level_data)
                mission_data['auto_level_up_id'] = created_level.id
                logger.info(f"Created level: {created_level.name} (ID: {created_level.id})")

            # Crear recompensas si se especificaron
            if rewards_data:
                logger.debug(f"Creating {len(rewards_data)} rewards")
                for reward_data in rewards_data:
                    # Convertir 'metadata' a 'reward_metadata' si es necesario
                    reward_params = reward_data.copy()
                    if 'metadata' in reward_params:
                        reward_params['reward_metadata'] = reward_params.pop('metadata')

                    reward = await self.reward_service.create_reward(
                        **reward_params,
                        created_by=created_by
                    )
                    created_rewards.append(reward)
                    logger.info(f"Created reward: {reward.name} (ID: {reward.id})")

                # Vincular a misión
                mission_data['unlock_rewards'] = [r.id for r in created_rewards]

            # Crear misión
            logger.debug(f"Creating mission: {mission_data.get('name')}")
            mission = await self.mission_service.create_mission(
                **mission_data,
                created_by=created_by
            )

            logger.info(
                f"Mission created successfully: {mission.name} (ID: {mission.id}) "
                f"with {len(created_rewards)} rewards and "
                f"{'1 level' if created_level else 'no level'}"
            )

            # Commit implícito al salir del context manager de sesión

            return {
                'mission': mission,
                'created_level': created_level,
                'created_rewards': created_rewards,
                'validation_errors': []
            }

        except Exception as e:
            # Rollback automático
            logger.error(f"Failed to create mission: {e}", exc_info=True)
            raise

    async def validate_mission_creation(
        self,
        mission_data: dict,
        auto_level_data: Optional[dict] = None,
        rewards_data: Optional[List[dict]] = None
    ) -> tuple[bool, List[str]]:
        """
        Valida datos antes de crear.

        Verifica:
        - Criterios de misión válidos
        - Nombre de nivel no duplicado (si aplica)
        - Metadata de recompensas válida (si aplica)
        - Referencias cruzadas consistentes

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        # Validar campos requeridos en mission_data
        required_fields = ['name', 'description', 'mission_type', 'criteria', 'besitos_reward']
        for field in required_fields:
            if field not in mission_data:
                errors.append(f"Missing required field in mission_data: {field}")

        if errors:
            return False, errors

        # Validar criterios
        is_valid, error = validate_mission_criteria(
            mission_data['mission_type'],
            mission_data['criteria']
        )
        if not is_valid:
            errors.append(f"Invalid criteria: {error}")

        # Validar besitos_reward positivo
        if mission_data.get('besitos_reward', 0) <= 0:
            errors.append("besitos_reward must be > 0")

        # Validar nivel si existe
        if auto_level_data:
            # Verificar campos requeridos
            level_required = ['name', 'min_besitos', 'order']
            for field in level_required:
                if field not in auto_level_data:
                    errors.append(f"Missing required field in auto_level_data: {field}")

            if 'name' in auto_level_data:
                # Verificar nombre único
                existing = await self.level_service.get_all_levels()
                if any(l.name == auto_level_data['name'] for l in existing):
                    errors.append(f"Level name already exists: {auto_level_data['name']}")

        # Validar recompensas si existen
        if rewards_data:
            for idx, reward_data in enumerate(rewards_data):
                # Verificar campos requeridos
                reward_required = ['name', 'description', 'reward_type']
                for field in reward_required:
                    if field not in reward_data:
                        errors.append(f"Reward {idx}: Missing required field: {field}")
                        continue

                # Validar metadata si existe
                if 'metadata' in reward_data:
                    is_valid, error = validate_reward_metadata(
                        reward_data['reward_type'],
                        reward_data.get('metadata', {})
                    )
                    if not is_valid:
                        errors.append(f"Reward {idx}: {error}")

        return len(errors) == 0, errors

    async def create_from_template(
        self,
        template_name: str,
        customize: Optional[dict] = None,
        created_by: int = 0
    ) -> dict:
        """
        Crea misión desde plantilla predefinida.

        Templates:
        - "welcome": Misión de bienvenida (one_time, 100 besitos)
        - "weekly_streak": Racha de 7 días (500 besitos)
        - "daily_reactor": 5 reacciones diarias (200 besitos)

        Args:
            template_name: Nombre de plantilla
            customize: Overrides opcionales (ej: {'besitos_reward': 1000})
            created_by: ID del admin

        Returns:
            Resultado de create_mission_with_dependencies
        """
        if template_name not in MISSION_TEMPLATES:
            raise ValueError(f"Template not found: {template_name}")

        logger.info(f"Creating mission from template: {template_name}")

        # Deep copy de la plantilla
        import copy
        template = copy.deepcopy(MISSION_TEMPLATES[template_name])

        # Aplicar customizaciones
        if customize:
            if 'besitos_reward' in customize:
                template['mission_data']['besitos_reward'] = customize['besitos_reward']
            if 'name' in customize:
                template['mission_data']['name'] = customize['name']
            if 'description' in customize:
                template['mission_data']['description'] = customize['description']
            # ... otros overrides según necesidad

        return await self.create_mission_with_dependencies(
            mission_data=template.get('mission_data'),
            auto_level_data=template.get('auto_level_data'),
            rewards_data=template.get('rewards_data'),
            created_by=created_by
        )
