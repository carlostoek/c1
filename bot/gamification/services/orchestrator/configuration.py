"""
Orquestador maestro de configuración.

Coordina MissionOrchestrator y RewardOrchestrator para
crear sistemas completos de gamificación.
"""

from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from bot.gamification.services.orchestrator.mission import MissionOrchestrator
from bot.gamification.services.orchestrator.reward import RewardOrchestrator
from bot.gamification.database.enums import MissionType, RewardType

logger = logging.getLogger(__name__)


SYSTEM_TEMPLATES = {
    "starter_pack": {
        "description": "Sistema inicial para nuevos canales",
        "missions": [
            {
                "name": "Bienvenido",
                "description": "Completa tu primera interacción",
                "mission_type": MissionType.ONE_TIME,
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
                        "description": "Badge por primera interacción",
                        "reward_type": RewardType.BADGE,
                        "metadata": {"icon": "🎯", "rarity": "common"}
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
                "description": "Reacciona 5 veces en un día",
                "mission_type": MissionType.DAILY,
                "criteria": {"type": "daily", "count": 5},
                "besitos_reward": 200,
                "repeatable": True
            },
            {
                "name": "Racha Semanal",
                "description": "Mantén una racha de 7 días",
                "mission_type": MissionType.STREAK,
                "criteria": {"type": "streak", "days": 7},
                "besitos_reward": 500,
                "repeatable": True,
                "rewards": [
                    {
                        "name": "Racha de Fuego",
                        "description": "Badge por racha semanal",
                        "reward_type": RewardType.BADGE,
                        "metadata": {"icon": "🔥", "rarity": "rare"}
                    }
                ]
            }
        ]
    }
}


class ConfigurationOrchestrator:
    """Orquestador maestro de configuración."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.mission_orchestrator = MissionOrchestrator(session)
        self.reward_orchestrator = RewardOrchestrator(session)

    async def create_complete_mission_system(
        self,
        config: dict,
        created_by: int = 0
    ) -> dict:
        """
        Crea sistema completo en transacción atómica.

        Args:
            config: {
                'mission': {
                    'name': str,
                    'description': str,
                    'mission_type': MissionType,
                    'criteria': dict,
                    'besitos_reward': int
                },
                'auto_level': Optional[{
                    'name': str,
                    'min_besitos': int,
                    'order': int
                }],
                'rewards': Optional[List[{
                    'name': str,
                    'description': str,
                    'reward_type': RewardType,
                    'metadata': dict
                }]]
            }
            created_by: ID del usuario que crea (admin)

        Returns:
            {
                'mission': Mission,
                'created_level': Optional[Level],
                'created_rewards': List[Reward],
                'summary': str,  # Resumen formateado
                'validation_errors': List[str]
            }
        """
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
            logger.error(f"Failed to create system: {e}")
            raise

    async def validate_complete_config(self, config: dict) -> tuple[bool, List[str]]:
        """
        Valida configuración completa con dependencias cruzadas.

        Verifica:
        - Criterios de misión válidos
        - Orden de nivel no conflictivo
        - Nombre de nivel único
        - Metadata de recompensas válida
        - Coherencia entre besitos de misión y min_besitos de nivel

        Returns:
            (is_valid, error_messages)
        """
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
        """
        Genera resumen formateado de lo creado.

        Example output:
            🎉 CONFIGURACIÓN COMPLETA

            ✅ Misión creada: "Racha de 7 días"
            ✅ Nivel creado: "Fanático Dedicado" (1000 besitos)
            ✅ Recompensas creadas:
               • 🏆 Badge: "Maestro de la Racha"
               • 🎁 Bonus: 500 besitos extra

            Los usuarios ahora pueden:
            • Completar la misión reaccionando 7 días seguidos
            • Subir al nivel "Fanático Dedicado"
            • Desbloquear 2 recompensas
        """
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
                icon = "🏆" if reward.reward_type == RewardType.BADGE else "🎁"
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
        """
        Aplica plantilla de sistema completo.

        Templates disponibles:
        - "starter_pack": Sistema inicial (bienvenida + 3 niveles + badges)
        - "engagement_system": Misiones diarias/semanales + recompensas

        Returns:
            {
                'missions_created': List[Mission],
                'levels_created': List[Level],
                'rewards_created': List[Reward],
                'summary': str
            }
        """
        if template_name not in SYSTEM_TEMPLATES:
            raise ValueError(f"Template not found: {template_name}")

        template = SYSTEM_TEMPLATES[template_name]

        missions_created = []
        levels_created = []
        rewards_created = []

        # Crear misiones del template
        for mission_config in template.get('missions', []):
            result = await self.create_complete_mission_system(
                config={
                    'mission': {
                        'name': mission_config['name'],
                        'description': mission_config.get('description', ''),
                        'mission_type': mission_config['mission_type'],
                        'criteria': mission_config['criteria'],
                        'besitos_reward': mission_config['besitos_reward'],
                        'repeatable': mission_config.get('repeatable', False)
                    },
                    'auto_level': mission_config.get('auto_level'),
                    'rewards': mission_config.get('rewards')
                },
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

        # Crear badges por nivel si aplica
        if template.get('level_badges'):
            for level in levels_created:
                badge_result = await self.reward_orchestrator.create_reward_with_unlock_condition(
                    reward_data={
                        'name': f"Badge {level.name}",
                        'description': f"Alcanzaste el nivel {level.name}",
                        'reward_type': RewardType.BADGE,
                        'metadata': {'icon': '⭐', 'rarity': 'common'}
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

        logger.info(f"Applied system template: {template_name}")

        return {
            'missions_created': missions_created,
            'levels_created': levels_created,
            'rewards_created': rewards_created,
            'summary': summary
        }
