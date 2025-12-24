# PROMPT G6.1: Sistema de Plantillas de Configuración

---

## ROL

Ingeniero de Software Senior especializado en sistemas de plantillas y configuraciones predefinidas.

---

## TAREA

Implementa el sistema de plantillas en `bot/gamification/utils/templates.py` con plantillas predefinidas de sistemas completos de gamificación y comando para aplicarlas.

---

## CONTEXTO

### Objetivo

Permitir que admins apliquen configuraciones completas predefinidas con un solo comando, evitando configurar manualmente misiones, niveles y recompensas.

### Arquitectura
```
bot/gamification/utils/
├── templates.py          # ← ESTE ARCHIVO
└── validators.py
```

---

## RESPONSABILIDADES

### 1. Definición de Plantillas

```python
SYSTEM_TEMPLATES = {
    "starter": {
        "name": "Sistema Inicial",
        "description": "Configuración básica para comenzar",
        "components": {
            "levels": [...],
            "missions": [...],
            "rewards": [...]
        }
    },
    "engagement": {...},
    "progression": {...}
}
```

### 2. Aplicador de Plantillas

```python
async def apply_template(
    template_name: str,
    session: AsyncSession,
    created_by: int
) -> dict:
    """
    Aplica plantilla completa.
    
    Returns:
        {
            'created_missions': List[Mission],
            'created_levels': List[Level],
            'created_rewards': List[Reward],
            'summary': str
        }
    """
```

### 3. Comando Admin

```python
# Handler en bot/gamification/handlers/admin/templates.py

@router.callback_query(F.data == "gamif:templates")
async def show_templates(callback: CallbackQuery):
    """Lista plantillas disponibles."""

@router.callback_query(F.data.startswith("gamif:template:apply:"))
async def apply_template_handler(callback: CallbackQuery):
    """Aplica plantilla seleccionada."""
```

---

## PLANTILLAS PREDEFINIDAS

### Starter Pack
```python
{
    "levels": [
        {"name": "Novato", "min_besitos": 0, "order": 1},
        {"name": "Regular", "min_besitos": 500, "order": 2},
        {"name": "Entusiasta", "min_besitos": 2000, "order": 3}
    ],
    "missions": [
        {
            "name": "Bienvenido",
            "type": "one_time",
            "criteria": {"type": "one_time"},
            "besitos_reward": 100,
            "auto_level_id": 1
        }
    ],
    "rewards": [
        {
            "name": "Primer Paso",
            "type": "badge",
            "metadata": {"icon": "🎯", "rarity": "common"},
            "unlock_level_id": 1
        }
    ]
}
```

### Engagement System
```python
{
    "missions": [
        {
            "name": "Reactor Diario",
            "type": "daily",
            "criteria": {"type": "daily", "count": 5},
            "besitos_reward": 200,
            "repeatable": True
        },
        {
            "name": "Racha Semanal",
            "type": "streak",
            "criteria": {"type": "streak", "days": 7},
            "besitos_reward": 500,
            "repeatable": True
        }
    ]
}
```

### Progression System
```python
{
    "levels": [
        {"name": "Novato", "min_besitos": 0, "order": 1},
        {"name": "Aprendiz", "min_besitos": 500, "order": 2},
        {"name": "Regular", "min_besitos": 1500, "order": 3},
        {"name": "Entusiasta", "min_besitos": 3500, "order": 4},
        {"name": "Fanático", "min_besitos": 7000, "order": 5},
        {"name": "Leyenda", "min_besitos": 15000, "order": 6}
    ],
    "rewards": [
        # Badge por cada nivel
    ]
}
```

---

## FORMATO DE SALIDA

```python
# bot/gamification/utils/templates.py

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
```

---

## HANDLER

```python
# bot/gamification/handlers/admin/templates.py

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.admin import IsAdmin
from bot.gamification.utils.templates import list_templates, apply_template

router = Router()
router.callback_query.filter(IsAdmin())


@router.callback_query(F.data == "gamif:missions:templates")
async def show_templates(callback: CallbackQuery):
    """Muestra plantillas disponibles."""
    templates = list_templates()
    
    keyboard_buttons = []
    for template in templates:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{template['name']} ({template['missions_count']} misiones)",
                callback_data=f"gamif:template:apply:{template['key']}"
            )
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Volver", callback_data="gamif:admin:missions")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(
        "📄 <b>Plantillas Predefinidas</b>\n\n"
        "Selecciona una plantilla para aplicar:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("gamif:template:apply:"))
async def apply_template_handler(
    callback: CallbackQuery,
    session: AsyncSession
):
    """Aplica plantilla seleccionada."""
    template_name = callback.data.split(":")[-1]
    
    await callback.message.edit_text("⚙️ Aplicando plantilla...")
    
    try:
        result = await apply_template(
            template_name,
            session,
            created_by=callback.from_user.id
        )
        
        await callback.message.edit_text(
            result['summary'],
            parse_mode="HTML"
        )
    
    except Exception as e:
        await callback.message.edit_text(f"❌ Error: {e}")
    
    await callback.answer()
```

---

## VALIDACIÓN

- ✅ 3 plantillas predefinidas completas
- ✅ Aplicación transaccional
- ✅ Handler con menú de selección
- ✅ Resumen detallado post-aplicación
- ✅ Rollback automático en errores

---

**ENTREGABLES:** 
- `templates.py` (sistema de plantillas)
- `templates.py` handler (menú y aplicación)
