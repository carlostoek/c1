"""
Orquestador de creación de recompensas.

Coordina creación de recompensas con unlock conditions
y creación masiva de badges.
"""

from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from bot.gamification.services.reward import RewardService
from bot.gamification.services.level import LevelService
from bot.gamification.database.enums import RewardType, BadgeRarity
from bot.gamification.utils.validators import (
    validate_reward_metadata,
    validate_unlock_conditions
)

logger = logging.getLogger(__name__)


# Plantillas predefinidas
REWARD_TEMPLATES = {
    "level_badges": {
        "badges_data": [
            {
                "name": "Novato",
                "description": "Alcanzaste el nivel 1",
                "icon": "🌱",
                "rarity": BadgeRarity.COMMON,
                "unlock_level_order": 1
            },
            {
                "name": "Regular",
                "description": "Alcanzaste el nivel 2",
                "icon": "⭐",
                "rarity": BadgeRarity.COMMON,
                "unlock_level_order": 2
            },
            {
                "name": "Entusiasta",
                "description": "Alcanzaste el nivel 3",
                "icon": "💫",
                "rarity": BadgeRarity.RARE,
                "unlock_level_order": 3
            },
            {
                "name": "Fanático",
                "description": "Alcanzaste el nivel 4",
                "icon": "🔥",
                "rarity": BadgeRarity.EPIC,
                "unlock_level_order": 4
            },
            {
                "name": "Leyenda",
                "description": "Alcanzaste el nivel 5",
                "icon": "👑",
                "rarity": BadgeRarity.LEGENDARY,
                "unlock_level_order": 5
            }
        ]
    },

    "welcome_pack": {
        "rewards_data": [
            {
                "name": "Badge de Bienvenida",
                "description": "Bienvenido al sistema",
                "reward_type": RewardType.BADGE,
                "metadata": {"icon": "🎉", "rarity": BadgeRarity.COMMON}
            },
            {
                "name": "Bonus de Inicio",
                "description": "100 besitos de regalo",
                "reward_type": RewardType.BESITOS,
                "metadata": {"amount": 100}
            }
        ]
    }
}


class RewardOrchestrator:
    """Orquestador de creación de recompensas."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.reward_service = RewardService(session)
        self.level_service = LevelService(session)

    async def create_reward_with_unlock_condition(
        self,
        reward_data: dict,
        unlock_mission_id: Optional[int] = None,
        unlock_level_id: Optional[int] = None,
        unlock_besitos: Optional[int] = None,
        created_by: int = 0
    ) -> dict:
        """
        Crea recompensa con unlock condition automática.

        Args:
            reward_data: {
                'name': str,
                'description': str,
                'reward_type': RewardType,
                'cost_besitos': Optional[int],
                'metadata': dict
            }
            unlock_mission_id: ID de misión requerida
            unlock_level_id: ID de nivel requerido
            unlock_besitos: Besitos mínimos requeridos
            created_by: ID del admin que crea

        Returns:
            {
                'reward': Reward,
                'unlock_condition': dict,
                'validation_errors': List[str]
            }
        """
        logger.info(f"Creating reward with unlock conditions: {reward_data.get('name')}")

        # Construir unlock_conditions
        conditions = []

        if unlock_mission_id:
            conditions.append({"type": "mission", "mission_id": unlock_mission_id})

        if unlock_level_id:
            conditions.append({"type": "level", "level_id": unlock_level_id})

        if unlock_besitos:
            conditions.append({"type": "besitos", "min_besitos": unlock_besitos})

        unlock_condition = None
        if len(conditions) == 1:
            unlock_condition = conditions[0]
        elif len(conditions) > 1:
            unlock_condition = {"type": "multiple", "conditions": conditions}

        # Validar unlock condition si existe
        if unlock_condition:
            is_valid, error = validate_unlock_conditions(unlock_condition)
            if not is_valid:
                logger.warning(f"Invalid unlock condition: {error}")
                return {
                    'reward': None,
                    'unlock_condition': None,
                    'validation_errors': [error]
                }

        # Validar metadata si existe
        if 'metadata' in reward_data:
            is_valid, error = validate_reward_metadata(
                reward_data['reward_type'],
                reward_data['metadata']
            )
            if not is_valid:
                logger.warning(f"Invalid reward metadata: {error}")
                return {
                    'reward': None,
                    'unlock_condition': None,
                    'validation_errors': [f"Invalid metadata: {error}"]
                }

        # Crear recompensa
        try:
            # Convertir 'metadata' a 'reward_metadata' si es necesario
            reward_params = reward_data.copy()
            if 'metadata' in reward_params:
                reward_params['reward_metadata'] = reward_params.pop('metadata')

            reward = await self.reward_service.create_reward(
                **reward_params,
                unlock_conditions=unlock_condition,
                created_by=created_by
            )

            logger.info(f"Created reward: {reward.name} (ID: {reward.id})")

            return {
                'reward': reward,
                'unlock_condition': unlock_condition,
                'validation_errors': []
            }

        except Exception as e:
            logger.error(f"Failed to create reward: {e}", exc_info=True)
            raise

    async def create_badge_set(
        self,
        badge_set_name: str,
        badges_data: List[dict],
        created_by: int = 0
    ) -> dict:
        """
        Crea set de badges relacionados.

        Args:
            badge_set_name: Nombre del set (para logging)
            badges_data: List[{
                'name': str,
                'description': str,
                'icon': str,
                'rarity': BadgeRarity,
                'unlock_level_order': Optional[int]
            }]
            created_by: ID del admin que crea

        Returns:
            {
                'created_badges': List[Reward],
                'failed': List[dict]  # {index, error}
            }
        """
        logger.info(f"Creating badge set '{badge_set_name}' with {len(badges_data)} badges")

        created_badges = []
        failed = []

        for idx, badge_data in enumerate(badges_data):
            try:
                # Resolver unlock_level_order a level_id si existe
                unlock_level_id = None
                if 'unlock_level_order' in badge_data:
                    order = badge_data.pop('unlock_level_order')
                    levels = await self.level_service.get_all_levels()
                    level = next((l for l in levels if l.order == order), None)
                    if level:
                        unlock_level_id = level.id
                    else:
                        logger.warning(f"Level with order {order} not found for badge {badge_data['name']}")

                # Crear badge
                unlock_conditions = None
                if unlock_level_id:
                    unlock_conditions = {"type": "level", "level_id": unlock_level_id}

                reward, badge = await self.reward_service.create_badge(
                    name=badge_data['name'],
                    description=badge_data['description'],
                    icon=badge_data['icon'],
                    rarity=badge_data['rarity'],
                    unlock_conditions=unlock_conditions,
                    created_by=created_by
                )

                created_badges.append(reward)
                logger.info(f"Created badge {idx+1}/{len(badges_data)}: {reward.name}")

            except Exception as e:
                failed.append({'index': idx, 'error': str(e), 'name': badge_data.get('name', 'Unknown')})
                logger.error(f"Failed to create badge {idx} ({badge_data.get('name')}): {e}")

        logger.info(f"Badge set creation completed: {len(created_badges)} created, {len(failed)} failed")

        return {
            'created_badges': created_badges,
            'failed': failed
        }

    async def create_from_template(
        self,
        template_name: str,
        customize: Optional[dict] = None,
        created_by: int = 0
    ) -> dict:
        """
        Crea recompensa(s) desde plantilla.

        Templates:
        - "level_badges": Set de 5 badges por nivel
        - "welcome_pack": Pack de bienvenida (badge + besitos)

        Args:
            template_name: Nombre de plantilla
            customize: Overrides opcionales
            created_by: ID del admin

        Returns:
            Resultado según tipo de plantilla
        """
        if template_name not in REWARD_TEMPLATES:
            raise ValueError(f"Template not found: {template_name}")

        logger.info(f"Creating rewards from template: {template_name}")

        template = REWARD_TEMPLATES[template_name]

        # Template de badges
        if 'badges_data' in template:
            return await self.create_badge_set(
                badge_set_name=template_name,
                badges_data=template['badges_data'],
                created_by=created_by
            )

        # Template de multiple rewards
        if 'rewards_data' in template:
            created_rewards = []
            failed = []

            for idx, reward_data in enumerate(template['rewards_data']):
                try:
                    # Convertir 'metadata' a 'reward_metadata'
                    reward_params = reward_data.copy()
                    if 'metadata' in reward_params:
                        reward_params['reward_metadata'] = reward_params.pop('metadata')

                    reward = await self.reward_service.create_reward(
                        **reward_params,
                        created_by=created_by
                    )

                    created_rewards.append(reward)
                    logger.info(f"Created reward {idx+1}/{len(template['rewards_data'])}: {reward.name}")

                except Exception as e:
                    failed.append({'index': idx, 'error': str(e), 'name': reward_data.get('name', 'Unknown')})
                    logger.error(f"Failed to create reward {idx}: {e}")

            return {
                'created_rewards': created_rewards,
                'failed': failed
            }

        return {}
