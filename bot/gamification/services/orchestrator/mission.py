"""
Orquestador de creación de misiones.

Coordina creación de misiones con auto-creación de niveles
y recompensas en transacciones atómicas.
"""

from typing import Optional, List, Dict, Any
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


class MissionOrchestrator:
    """Orquestador de creación de misiones."""

    # Plantillas predefinidas
    MISSION_TEMPLATES = {
        "welcome": {
            "mission_data": {
                "name": "Bienvenido al Sistema",
                "description": "Completa tu primera reacción",
                "mission_type": MissionType.ONE_TIME,
                "criteria": {"type": "one_time"},
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
                    "metadata": {"icon": "🎯", "rarity": BadgeRarity.COMMON.value}
                }
            ]
        },

        "weekly_streak": {
            "mission_data": {
                "name": "Racha de 7 Días",
                "description": "Reacciona 7 días consecutivos",
                "mission_type": MissionType.STREAK,
                "criteria": {"type": "streak", "days": 7, "require_consecutive": True},
                "besitos_reward": 500,
                "repeatable": True
            }
        },

        "daily_reactor": {
            "mission_data": {
                "name": "Reactor Diario",
                "description": "Reacciona 5 veces hoy",
                "mission_type": MissionType.DAILY,
                "criteria": {"type": "daily", "count": 5},
                "besitos_reward": 200,
                "repeatable": True
            }
        }
    }

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
        """Crea misión con dependencias en transacción atómica."""
        # Validar primero
        is_valid, errors = await self.validate_mission_creation(
            mission_data, auto_level_data, rewards_data
        )
        if not is_valid:
            return {'validation_errors': errors}
        
        created_level = None
        created_rewards = []
        
        try:
            # Crear nivel si se especificó
            if auto_level_data:
                created_level = await self.level_service.create_level(**auto_level_data)
                mission_data['auto_level_up_id'] = created_level.id
                # Commit after creating level to ensure ID is available
                await self.session.flush()
        
            # Crear recompensas si se especificaron
            if rewards_data:
                for reward_data in rewards_data:
                    reward = await self.reward_service.create_reward(
                        **reward_data,
                        created_by=created_by
                    )
                    created_rewards.append(reward)
                    # Flush after each reward to get IDs
                    await self.session.flush()
                
                # Vincular a misión
                mission_data['unlock_rewards'] = [r.id for r in created_rewards]
        
            # Crear misión
            mission = await self.mission_service.create_mission(
                **mission_data,
                created_by=created_by
            )
            
            # Commit implícito al salir del context manager de sesión
            await self.session.commit()
            
            return {
                'mission': mission,
                'created_level': created_level,
                'created_rewards': created_rewards,
                'validation_errors': []
            }
        
        except Exception as e:
            # Rollback automático
            await self.session.rollback()
            logger.error(f"Failed to create mission: {e}")
            raise
    
    async def validate_mission_creation(
        self,
        mission_data: dict,
        auto_level_data: Optional[dict] = None,
        rewards_data: Optional[List[dict]] = None
    ) -> tuple[bool, List[str]]:
        """Valida datos antes de crear."""
        errors = []
        
        # Validar campos obligatorios de misión
        required_mission_fields = ['name', 'description', 'mission_type', 'criteria', 'besitos_reward']
        for field in required_mission_fields:
            if field not in mission_data:
                errors.append(f"Missing required mission field: {field}")
        
        # Validar criterios
        if 'mission_type' in mission_data and 'criteria' in mission_data:
            is_valid, error = validate_mission_criteria(
                mission_data['mission_type'],
                mission_data['criteria']
            )
            if not is_valid:
                errors.append(f"Invalid criteria: {error}")
        
        # Validar nivel si existe
        if auto_level_data:
            # Verificar campos obligatorios
            required_level_fields = ['name', 'min_besitos', 'order']
            for field in required_level_fields:
                if field not in auto_level_data:
                    errors.append(f"Missing required level field: {field}")
            
            # Verificar nombre único
            existing_levels = await self.level_service.get_all_levels()
            if any(l.name == auto_level_data['name'] for l in existing_levels):
                errors.append(f"Level name already exists: {auto_level_data['name']}")
        
        # Validar recompensas si existen
        if rewards_data:
            for idx, reward_data in enumerate(rewards_data):
                # Verificar campos obligatorios
                required_reward_fields = ['name', 'description', 'reward_type', 'metadata']
                for field in required_reward_fields:
                    if field not in reward_data:
                        errors.append(f"Reward {idx}: Missing required field: {field}")
                
                if 'reward_type' in reward_data and 'metadata' in reward_data:
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
        """Crea misión desde plantilla."""
        if template_name not in self.MISSION_TEMPLATES:
            raise ValueError(f"Template not found: {template_name}")

        template = self.MISSION_TEMPLATES[template_name].copy()
        
        # Aplicar customizaciones
        if customize:
            # Deep copy to avoid modifying the template
            import copy
            template = copy.deepcopy(template)
            
            if 'besitos_reward' in customize:
                template['mission_data']['besitos_reward'] = customize['besitos_reward']
            if 'name' in customize:
                template['mission_data']['name'] = customize['name']
            if 'description' in customize:
                template['mission_data']['description'] = customize['description']
            # Add other customizable fields as needed
        
        return await self.create_mission_with_dependencies(
            mission_data=template.get('mission_data'),
            auto_level_data=template.get('auto_level_data'),
            rewards_data=template.get('rewards_data'),
            created_by=created_by
        )