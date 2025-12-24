# PROMPT G3.3: RewardOrchestrator - Creación Orquestada de Recompensas

---

## ROL

Actúa como Ingeniero de Software Senior especializado en patrones de orquestación y gestión de recompensas complejas.

---

## TAREA

Implementa `RewardOrchestrator` en `bot/gamification/services/orchestrator/reward.py` que coordina la creación de recompensas con unlock conditions vinculadas a misiones/niveles en transacciones atómicas.

---

## CONTEXTO

### Arquitectura
```
bot/gamification/services/orchestrator/
├── mission.py         # Ya existe
├── reward.py          # ← ESTE ARCHIVO
└── configuration.py   # G3.4
```

---

## RESPONSABILIDADES

### 1. Creación de Recompensa con Unlock Condition

```python
async def create_reward_with_unlock_condition(
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
    
    Returns:
        {
            'reward': Reward,
            'unlock_condition': dict,
            'validation_errors': List[str]
        }
    
    Construye unlock_conditions según parámetros:
    - Si unlock_mission_id: {"type": "mission", "mission_id": X}
    - Si unlock_level_id: {"type": "level", "level_id": X}
    - Si unlock_besitos: {"type": "besitos", "min_besitos": X}
    - Si múltiples: {"type": "multiple", "conditions": [...]}
    """
```

### 2. Creación Masiva de Badges

```python
async def create_badge_set(
    badge_set_name: str,
    badges_data: List[dict],
    created_by: int = 0
) -> dict:
    """
    Crea set de badges relacionados (ej: niveles 1-5).
    
    Args:
        badge_set_name: Nombre del set (para logging)
        badges_data: List[{
            'name': str,
            'description': str,
            'icon': str,
            'rarity': BadgeRarity,
            'unlock_level_id': Optional[int]
        }]
    
    Returns:
        {
            'created_badges': List[Reward],
            'failed': List[dict]  # {index, error}
        }
    
    Útil para crear badges de progresión por nivel.
    """
```

### 3. Plantillas de Recompensas

```python
async def create_from_template(
    template_name: str,
    customize: Optional[dict] = None,
    created_by: int = 0
) -> dict:
    """
    Crea recompensa desde plantilla.
    
    Templates:
    - "level_badges": Set de 5 badges por nivel
    - "streak_badges": Badges por rachas (7d, 14d, 30d)
    - "welcome_pack": Pack de bienvenida (badge + besitos)
    """
```

---

## PLANTILLAS

```python
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
```

---

## FORMATO DE SALIDA

```python
# bot/gamification/services/orchestrator/reward.py

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


REWARD_TEMPLATES = {
    # ... templates
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
        """Crea recompensa con unlock condition."""
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
        
        # Validar
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
            
            return {
                'reward': reward,
                'unlock_condition': unlock_condition,
                'validation_errors': []
            }
        
        except Exception as e:
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
                # Resolver unlock_level_order a level_id si existe
                unlock_level_id = None
                if 'unlock_level_order' in badge_data:
                    order = badge_data.pop('unlock_level_order')
                    levels = await self.level_service.get_all_levels()
                    level = next((l for l in levels if l.order == order), None)
                    if level:
                        unlock_level_id = level.id
                
                # Crear badge
                reward, badge = await self.reward_service.create_badge(
                    name=badge_data['name'],
                    description=badge_data['description'],
                    icon=badge_data['icon'],
                    rarity=badge_data['rarity'],
                    unlock_conditions={"type": "level", "level_id": unlock_level_id} if unlock_level_id else None,
                    created_by=created_by
                )
                
                created_badges.append(reward)
                logger.info(f"Created badge {idx+1}/{len(badges_data)}: {reward.name}")
            
            except Exception as e:
                failed.append({'index': idx, 'error': str(e)})
                logger.error(f"Failed to create badge {idx}: {e}")
        
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
        if template_name not in REWARD_TEMPLATES:
            raise ValueError(f"Template not found: {template_name}")
        
        template = REWARD_TEMPLATES[template_name]
        
        if 'badges_data' in template:
            return await self.create_badge_set(
                badge_set_name=template_name,
                badges_data=template['badges_data'],
                created_by=created_by
            )
        
        # Otros tipos de templates...
        return {}
```

---

## INTEGRACIÓN

```python
# bot/gamification/services/container.py

@property
def reward_orchestrator(self) -> RewardOrchestrator:
    if self._reward_orchestrator is None:
        self._reward_orchestrator = RewardOrchestrator(self._session)
    return self._reward_orchestrator
```

---

## VALIDACIÓN

- ✅ Construcción automática de unlock conditions
- ✅ Creación masiva de badges
- ✅ Plantillas predefinidas
- ✅ Manejo de errores parciales (batch)
- ✅ Validaciones previas

---

**ENTREGABLE:** Archivo `reward.py` con orquestación de recompensas.
