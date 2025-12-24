"""
Sistema de plantillas de configuración predefinidas.
"""

from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from bot.gamification.services.level import LevelService
from bot.gamification.services.mission import MissionService
from bot.gamification.services.reward import RewardService
from bot.gamification.database.enums import MissionType, RewardType, BadgeRarity

logger = logging.getLogger(__name__)


SYSTEM_TEMPLATES = {
    "starter": {
        "name": "Sistema Inicial",
        "description": "3 niveles + misión de bienvenida + badge",
        "components": {
            "levels": [
                {"name": "Novato", "min_besitos": 0, "order": 1},
                {"name": "Regular", "min_besitos": 500, "order": 2},
                {"name": "Entusiasta", "min_besitos": 2000, "order": 3}
            ],
            "missions": [
                {
                    "name": "Bienvenido",
                    "description": "Completa tu primera reacción",
                    "mission_type": MissionType.ONE_TIME,
                    "criteria": {"type": "one_time"},
                    "besitos_reward": 100,
                    "repeatable": False
                }
            ],
            "rewards": [
                {
                    "name": "Primer Paso",
                    "description": "Completaste tu primera misión",
                    "reward_type": RewardType.BADGE,
                    "metadata": {"icon": "🎯", "rarity": BadgeRarity.COMMON}
                }
            ]
        }
    },

    "engagement": {
        "name": "Sistema de Engagement",
        "description": "Misiones diarias/semanales para engagement",
        "components": {
            "missions": [
                {
                    "name": "Reactor Diario",
                    "description": "Reacciona 5 veces hoy",
                    "mission_type": MissionType.DAILY,
                    "criteria": {"type": "daily", "count": 5},
                    "besitos_reward": 200,
                    "repeatable": True
                },
                {
                    "name": "Racha de 7 Días",
                    "description": "Reacciona 7 días consecutivos",
                    "mission_type": MissionType.STREAK,
                    "criteria": {"type": "streak", "days": 7, "require_consecutive": True},
                    "besitos_reward": 500,
                    "repeatable": True
                }
            ],
            "rewards": [
                {
                    "name": "Racha de Fuego",
                    "description": "Mantuviste racha de 7 días",
                    "reward_type": RewardType.BADGE,
                    "metadata": {"icon": "🔥", "rarity": BadgeRarity.RARE}
                }
            ]
        }
    },

    "progression": {
        "name": "Sistema de Progresión",
        "description": "6 niveles con badges por nivel",
        "components": {
            "levels": [
                {"name": "Novato", "min_besitos": 0, "order": 1},
                {"name": "Aprendiz", "min_besitos": 500, "order": 2},
                {"name": "Regular", "min_besitos": 1500, "order": 3},
                {"name": "Entusiasta", "min_besitos": 3500, "order": 4},
                {"name": "Fanático", "min_besitos": 7000, "order": 5},
                {"name": "Leyenda", "min_besitos": 15000, "order": 6}
            ]
        }
    }
}


async def apply_template(
    template_name: str,
    session: AsyncSession,
    created_by: int = 0
) -> dict:
    """Aplica plantilla de sistema completo."""

    if template_name not in SYSTEM_TEMPLATES:
        raise ValueError(f"Template not found: {template_name}")

    template = SYSTEM_TEMPLATES[template_name]
    components = template["components"]

    created_levels = []
    created_missions = []
    created_rewards = []

    level_service = LevelService(session)
    mission_service = MissionService(session)
    reward_service = RewardService(session)

    try:
        # Crear niveles
        if "levels" in components:
            for level_data in components["levels"]:
                level = await level_service.create_level(**level_data)
                created_levels.append(level)
                logger.info(f"Created level: {level.name}")

        # Crear misiones
        if "missions" in components:
            for mission_data in components["missions"]:
                mission = await mission_service.create_mission(
                    **mission_data,
                    created_by=created_by
                )
                created_missions.append(mission)
                logger.info(f"Created mission: {mission.name}")

        # Crear recompensas
        if "rewards" in components:
            for reward_data in components["rewards"]:
                if reward_data["reward_type"] == RewardType.BADGE:
                    reward, _ = await reward_service.create_badge(
                        name=reward_data["name"],
                        description=reward_data["description"],
                        icon=reward_data["metadata"]["icon"],
                        rarity=reward_data["metadata"]["rarity"],
                        created_by=created_by
                    )
                else:
                    reward = await reward_service.create_reward(
                        **reward_data,
                        created_by=created_by
                    )
                created_rewards.append(reward)
                logger.info(f"Created reward: {reward.name}")

        # Crear badges por nivel si es progression system
        if template_name == "progression":
            for level in created_levels:
                badge, _ = await reward_service.create_badge(
                    name=f"Badge {level.name}",
                    description=f"Alcanzaste el nivel {level.name}",
                    icon="⭐",
                    rarity=BadgeRarity.COMMON,
                    unlock_conditions={"type": "level", "level_id": level.id},
                    created_by=created_by
                )
                created_rewards.append(badge)

        await session.commit()

        summary = f"""✅ <b>Plantilla Aplicada: {template['name']}</b>

<b>Creado:</b>
• {len(created_levels)} nivel(es)
• {len(created_missions)} misión(es)
• {len(created_rewards)} recompensa(s)

{template['description']}
"""

        return {
            'created_levels': created_levels,
            'created_missions': created_missions,
            'created_rewards': created_rewards,
            'summary': summary
        }

    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to apply template: {e}")
        raise


def get_template_info(template_name: str) -> dict:
    """Obtiene información de plantilla."""
    if template_name not in SYSTEM_TEMPLATES:
        return None

    template = SYSTEM_TEMPLATES[template_name]
    components = template["components"]

    return {
        'name': template['name'],
        'description': template['description'],
        'levels_count': len(components.get('levels', [])),
        'missions_count': len(components.get('missions', [])),
        'rewards_count': len(components.get('rewards', []))
    }


def list_templates() -> List[dict]:
    """Lista todas las plantillas disponibles."""
    return [
        {
            'key': key,
            **get_template_info(key)
        }
        for key in SYSTEM_TEMPLATES.keys()
    ]
