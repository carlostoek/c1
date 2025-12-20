"""
Orquestador maestro de configuración.

Coordina MissionOrchestrator y RewardOrchestrator para
crear sistemas completos de gamificación.
"""

from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import copy

from bot.gamification.services.orchestrator.mission import MissionOrchestrator
from bot.gamification.services.orchestrator.reward import RewardOrchestrator
from bot.gamification.database.enums import MissionType, RewardType, BadgeRarity

logger = logging.getLogger(__name__)


class ConfigurationOrchestrator:
    """Orquestador maestro de configuración."""

    # Plantillas de sistema completo
    SYSTEM_TEMPLATES = {
        "starter_pack": {
            "description": "Sistema inicial para nuevos canales",
            "missions": [
                {
                    "name": "Bienvenido",
                    "mission_type": MissionType.ONE_TIME.value,
                    "criteria": {"type": "one_time"},
                    "besitos_reward": 100,
                    "auto_level": {
                        "name": "Novato",
                        "min_besitos": 0,
                        "order": 1
                    },
                    "rewards": [
                        {
                            "name": "Primer Paso",
                            "reward_type": RewardType.BADGE.value,
                            "metadata": {"icon": "🎯", "rarity": BadgeRarity.COMMON.value}
                        }
                    ]
                }
            ],
            "additional_levels": [
                {"name": "Regular", "min_besitos": 500, "order": 2},
                {"name": "Entusiasta", "min_besitos": 2000, "order": 3}
            ],
            "level_badges": True  # Crear badge por cada nivel
        },

        "engagement_system": {
            "description": "Misiones para engagement diario/semanal",
            "missions": [
                {
                    "name": "Reactor Diario",
                    "mission_type": MissionType.DAILY.value,
                    "criteria": {"type": "daily", "count": 5},
                    "besitos_reward": 200,
                    "repeatable": True
                },
                {
                    "name": "Racha Semanal",
                    "mission_type": MissionType.STREAK.value,
                    "criteria": {"type": "streak", "days": 7},
                    "besitos_reward": 500,
                    "repeatable": True,
                    "rewards": [
                        {
                            "name": "Racha de Fuego",
                            "reward_type": RewardType.BADGE.value,
                            "metadata": {"icon": "🔥", "rarity": BadgeRarity.RARE.value}
                        }
                    ]
                }
            ]
        },

        "progression_system": {
            "description": "Sistema de progresión por niveles",
            "missions": [
                {
                    "name": "Racha de 7 Días",
                    "mission_type": MissionType.STREAK.value,
                    "criteria": {"type": "streak", "days": 7, "require_consecutive": True},
                    "besitos_reward": 500,
                    "repeatable": False,
                    "auto_level": {
                        "name": "Fanático Dedicado",
                        "min_besitos": 1000,
                        "order": 3
                    }
                },
                {
                    "name": "Reactor Activo",
                    "mission_type": MissionType.WEEKLY.value,
                    "criteria": {"type": "weekly", "target": 50},
                    "besitos_reward": 300,
                    "repeatable": True
                }
            ],
            "level_badges": True
        }
    }

    def __init__(self, session: AsyncSession):
        self.session = session
        self.mission_orchestrator = MissionOrchestrator(session)
        self.reward_orchestrator = RewardOrchestrator(session)
    
    async def create_complete_mission_system(
        self,
        config: dict,
        created_by: int = 0
    ) -> dict:
        """Crea sistema completo en transacción atómica."""
        # Validar primero
        is_valid, errors = await self.validate_complete_config(config)
        if not is_valid:
            return {'validation_errors': errors}
        
        try:
            # Delegar a mission_orchestrator
            result = await self.mission_orchestrator.create_mission_with_dependencies(
                mission_data=config['mission'],
                auto_level_data=config.get('auto_level'),
                rewards_data=config.get('rewards'),
                created_by=created_by
            )
            
            # Generar resumen
            result['summary'] = self.generate_summary(result)
            
            logger.info(f"Created complete mission system: {config['mission']['name']}")
            return result
        
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to create system: {e}")
            raise
    
    async def validate_complete_config(self, config: dict) -> tuple[bool, List[str]]:
        """Valida configuración completa."""
        errors = []
        
        # Validar que misión existe
        if 'mission' not in config:
            errors.append("Missing mission configuration")
            return False, errors
        
        # Delegar validaciones específicas a mission_orchestrator
        is_valid, mission_errors = await self.mission_orchestrator.validate_mission_creation(
            mission_data=config['mission'],
            auto_level_data=config.get('auto_level'),
            rewards_data=config.get('rewards')
        )
        
        if not is_valid:
            errors.extend(mission_errors)
        
        # Validación de coherencia: besitos de misión vs nivel
        if config.get('auto_level'):
            mission_besitos = config['mission'].get('besitos_reward', 0)
            level_min = config['auto_level'].get('min_besitos', 0)
            
            if mission_besitos < level_min:
                errors.append(
                    f"Mission reward ({mission_besitos}) is less than level requirement ({level_min})"
                )
        
        return len(errors) == 0, errors
    
    def generate_summary(self, result: dict) -> str:
        """Genera resumen formateado."""
        mission = result.get('mission')
        level = result.get('created_level')
        rewards = result.get('created_rewards', [])
        
        summary = "🎉 <b>CONFIGURACIÓN COMPLETA</b>\n\n"
        
        if mission:
            summary += f"✅ Misión creada: \"{mission.name}\"\n"
        
        if level:
            summary += f"✅ Nivel creado: \"{level.name}\" ({level.min_besitos} besitos)\n"
        
        if rewards:
            summary += f"✅ Recompensas creadas:\n"
            for reward in rewards:
                if reward.reward_type == RewardType.BADGE:
                    icon = "🏆"
                elif reward.reward_type == RewardType.BESITOS:
                    icon = "💰"
                else:
                    icon = "🎁"
                summary += f"   • {icon} {reward.name}\n"
        
        summary += "\n<b>Los usuarios ahora pueden:</b>\n"
        if mission:
            summary += f"• Completar la misión y obtener {mission.besitos_reward} besitos\n"
        if level:
            summary += f"• Subir al nivel \"{level.name}\"\n"
        if rewards:
            summary += f"• Desbloquear {len(rewards)} recompensa(s)\n"
        
        return summary
    
    async def apply_system_template(
        self,
        template_name: str,
        created_by: int = 0
    ) -> dict:
        """Aplica plantilla de sistema completo."""
        if template_name not in self.SYSTEM_TEMPLATES:
            raise ValueError(f"Template not found: {template_name}")

        template = copy.deepcopy(self.SYSTEM_TEMPLATES[template_name])
        
        missions_created = []
        levels_created = []
        rewards_created = []
        
        # Crear misiones del template
        for mission_config in template.get('missions', []):
            config = {
                'mission': {
                    'name': mission_config['name'],
                    'mission_type': mission_config['mission_type'],
                    'criteria': mission_config['criteria'],
                    'besitos_reward': mission_config['besitos_reward'],
                    'repeatable': mission_config.get('repeatable', False),
                    'description': mission_config.get('description', f"Misión: {mission_config['name']}")
                }
            }

            if 'auto_level' in mission_config:
                config['auto_level'] = mission_config['auto_level']

            if 'rewards' in mission_config:
                # Ensure rewards have descriptions
                rewards_with_descriptions = []
                for reward in mission_config['rewards']:
                    reward_copy = reward.copy()
                    if 'description' not in reward_copy:
                        reward_copy['description'] = f"Recompensa: {reward_copy['name']}"
                    rewards_with_descriptions.append(reward_copy)
                config['rewards'] = rewards_with_descriptions

            result = await self.create_complete_mission_system(
                config=config,
                created_by=created_by
            )

            if result.get('mission'):
                missions_created.append(result['mission'])
            if result.get('created_level'):
                levels_created.append(result['created_level'])
            if result.get('created_rewards'):
                rewards_created.extend(result['created_rewards'])
        
        # Crear niveles adicionales si existen
        if template.get('additional_levels'):
            from bot.gamification.services.level import LevelService
            level_service = LevelService(self.session)
            
            for level_data in template['additional_levels']:
                level = await level_service.create_level(**level_data)
                levels_created.append(level)
                await self.session.flush()  # Ensure level ID is available
        
        # Crear badges por nivel si aplica
        if template.get('level_badges'):
            for level in levels_created:
                badge_result = await self.reward_orchestrator.create_reward_with_unlock_condition(
                    reward_data={
                        'name': f"Badge {level.name}",
                        'description': f"Alcanzaste el nivel {level.name}",
                        'reward_type': RewardType.BADGE,
                        'metadata': {'icon': '⭐', 'rarity': BadgeRarity.COMMON.value}
                    },
                    unlock_level_id=level.id,
                    created_by=created_by
                )
                if badge_result.get('reward'):
                    rewards_created.append(badge_result['reward'])
        
        summary = f"""✅ Plantilla aplicada: {template_name}

📋 Creado:
• {len(missions_created)} misión(es)
• {len(levels_created)} nivel(es)
• {len(rewards_created)} recompensa(s)
"""
        
        return {
            'missions_created': missions_created,
            'levels_created': levels_created,
            'rewards_created': rewards_created,
            'summary': summary
        }