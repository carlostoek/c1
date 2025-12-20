"""
Orquestador de creación de recompensas.

Coordina creación de recompensas con unlock conditions
y creación masiva de badges.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import copy

from bot.gamification.services.reward import RewardService
from bot.gamification.services.level import LevelService
from bot.gamification.services.mission import MissionService
from bot.gamification.database.enums import RewardType, BadgeRarity
from bot.gamification.utils.validators import (
    validate_reward_metadata,
    validate_unlock_conditions
)

logger = logging.getLogger(__name__)


class RewardOrchestrator:
    """Orquestador de creación de recompensas."""

    # Templates predefinidos
    REWARD_TEMPLATES = {
        "level_badges": {
            "badges_data": [
                {
                    "name": "Novato",
                    "description": "Alcanzaste el nivel 1",
                    "icon": "🌱",
                    "rarity": BadgeRarity.COMMON.value,
                    "unlock_level_order": 1
                },
                {
                    "name": "Regular",
                    "description": "Alcanzaste el nivel 2",
                    "icon": "⭐",
                    "rarity": BadgeRarity.COMMON.value,
                    "unlock_level_order": 2
                },
                {
                    "name": "Entusiasta",
                    "description": "Alcanzaste el nivel 3",
                    "icon": "💫",
                    "rarity": BadgeRarity.RARE.value,
                    "unlock_level_order": 3
                },
                {
                    "name": "Fanático",
                    "description": "Alcanzaste el nivel 4",
                    "icon": "🔥",
                    "rarity": BadgeRarity.EPIC.value,
                    "unlock_level_order": 4
                },
                {
                    "name": "Leyenda",
                    "description": "Alcanzaste el nivel 5",
                    "icon": "👑",
                    "rarity": BadgeRarity.LEGENDARY.value,
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
                    "metadata": {"icon": "🎉", "rarity": BadgeRarity.COMMON.value}
                },
                {
                    "name": "Bonus de Inicio",
                    "description": "100 besitos de regalo",
                    "reward_type": RewardType.BESITOS,
                    "metadata": {"amount": 100}
                }
            ]
        },

        "streak_badges": {
            "badges_data": [
                {
                    "name": "Racha de 7 Días",
                    "description": "Completaste una racha de 7 días",
                    "icon": "7️⃣",
                    "rarity": BadgeRarity.COMMON.value,
                    "unlock_mission_name": "7_day_streak"
                },
                {
                    "name": "Racha de 14 Días",
                    "description": "Completaste una racha de 14 días",
                    "icon": "1️⃣4️⃣",
                    "rarity": BadgeRarity.RARE.value,
                    "unlock_mission_name": "14_day_streak"
                },
                {
                    "name": "Racha de 30 Días",
                    "description": "Completaste una racha de 30 días",
                    "icon": "3️⃣0️⃣",
                    "rarity": BadgeRarity.EPIC.value,
                    "unlock_mission_name": "30_day_streak"
                }
            ]
        }
    }

    def __init__(self, session: AsyncSession):
        self.session = session
        self.reward_service = RewardService(session)
        self.level_service = LevelService(session)
        self.mission_service = MissionService(session)
    
    async def create_reward_with_unlock_condition(
        self,
        reward_data: dict,
        unlock_mission_id: Optional[int] = None,
        unlock_level_id: Optional[int] = None,
        unlock_besitos: Optional[int] = None,
        created_by: int = 0
    ) -> dict:
        """Crea recompensa con unlock condition."""
        # Validar los datos de la recompensa
        is_valid, error = validate_reward_metadata(
            reward_data['reward_type'],
            reward_data.get('metadata', {})
        )
        if not is_valid:
            return {'validation_errors': [f"Invalid reward metadata: {error}"]}
        
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
        
        # Validar unlock_condition si existe
        if unlock_condition:
            is_valid, error = validate_unlock_conditions(unlock_condition)
            if not is_valid:
                return {'validation_errors': [error]}
        
        # Crear recompensa
        try:
            reward = await self.reward_service.create_reward(
                **reward_data,
                unlock_conditions=unlock_condition,
                created_by=created_by
            )
            
            await self.session.commit()
            
            return {
                'reward': reward,
                'unlock_condition': unlock_condition,
                'validation_errors': []
            }
        
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create reward: {e}")
            raise
    
    async def create_badge_set(
        self,
        badge_set_name: str,
        badges_data: List[dict],
        created_by: int = 0
    ) -> dict:
        """Crea set de badges."""
        created_badges = []
        failed = []
        
        for idx, badge_data in enumerate(badges_data):
            try:
                # Validar campos obligatorios
                required_fields = ['name', 'description', 'icon', 'rarity']
                for field in required_fields:
                    if field not in badge_data:
                        raise ValueError(f"Missing required field: {field}")
                
                # Resolver unlock_level_order a level_id si existe
                unlock_condition = None
                if 'unlock_level_order' in badge_data:
                    order = badge_data.pop('unlock_level_order')
                    levels = await self.level_service.get_all_levels()
                    level = next((l for l in levels if l.order == order), None)
                    if level:
                        unlock_condition = {"type": "level", "level_id": level.id}
                
                # Crear badge
                reward_data = {
                    'name': badge_data['name'],
                    'description': badge_data['description'],
                    'reward_type': RewardType.BADGE,
                    'metadata': {
                        'icon': badge_data['icon'],
                        'rarity': badge_data['rarity']
                    },
                    'created_by': created_by
                }
                
                if unlock_condition:
                    reward_data['unlock_conditions'] = unlock_condition
                
                reward = await self.reward_service.create_reward(**reward_data)
                created_badges.append(reward)
                logger.info(f"Created badge {idx+1}/{len(badges_data)}: {reward.name}")
            
            except Exception as e:
                failed.append({'index': idx, 'error': str(e), 'data': badge_data})
                logger.error(f"Failed to create badge {idx}: {e}")
                # Rollback any partial changes for this badge
                await self.session.rollback()
        
        if len(failed) == 0:
            # Commit only if no failures occurred
            try:
                await self.session.commit()
            except:
                pass  # Commit may fail if session was already rolled back due to errors
        
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
        """Crea desde plantilla."""
        if template_name not in self.REWARD_TEMPLATES:
            raise ValueError(f"Template not found: {template_name}")

        # Hacer una copia profunda para evitar modificar la plantilla original
        template = copy.deepcopy(self.REWARD_TEMPLATES[template_name])
        
        # Aplicar personalizaciones
        if customize:
            if 'badges_data' in template and 'badges_data' in customize:
                # Combinar datos personalizados con los de la plantilla
                for i, custom_badge in enumerate(customize['badges_data']):
                    if i < len(template['badges_data']):
                        template['badges_data'][i].update(custom_badge)
            elif 'rewards_data' in template and 'rewards_data' in customize:
                for i, custom_reward in enumerate(customize['rewards_data']):
                    if i < len(template['rewards_data']):
                        template['rewards_data'][i].update(custom_reward)
        
        if 'badges_data' in template:
            return await self.create_badge_set(
                badge_set_name=template_name,
                badges_data=template['badges_data'],
                created_by=created_by
            )
        elif 'rewards_data' in template:
            created_rewards = []
            failed = []
            
            for idx, reward_data in enumerate(template['rewards_data']):
                try:
                    reward = await self.reward_service.create_reward(
                        **reward_data,
                        created_by=created_by
                    )
                    created_rewards.append(reward)
                except Exception as e:
                    failed.append({'index': idx, 'error': str(e), 'data': reward_data})
                    # Rollback any partial changes for this reward
                    await self.session.rollback()
            
            if len(failed) == 0:
                # Commit only if no failures occurred
                try:
                    await self.session.commit()
                except:
                    pass  # Commit may fail if session was already rolled back due to errors
            
            return {
                'created_rewards': created_rewards,
                'failed': failed
            }
        
        return {'created_rewards': [], 'failed': [], 'message': f'No data in template {template_name}'}