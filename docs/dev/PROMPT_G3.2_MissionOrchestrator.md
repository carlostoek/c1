# PROMPT G3.2: MissionOrchestrator - Creación Orquestada de Misiones

---

## ROL

Actúa como Ingeniero de Software Senior especializado en patrones de orquestación, transacciones atómicas y workflows complejos.

---

## TAREA

Implementa `MissionOrchestrator` en `bot/gamification/services/orchestrator/mission.py` que coordina la creación de misiones con auto-creación de niveles y recompensas relacionadas en una sola transacción atómica.

---

## CONTEXTO

### Problema que Resuelve

Sin orquestador, el admin debe:
1. Crear nivel manualmente
2. Crear recompensa manualmente
3. Crear misión manualmente
4. Vincular IDs entre ellos

**Con orquestador:** El admin define todo en un wizard, el orquestador crea todo en una transacción.

### Arquitectura
```
bot/gamification/services/orchestrator/
├── __init__.py
├── mission.py         # ← ESTE ARCHIVO
├── reward.py          # G3.3
└── configuration.py   # G3.4
```

---

## RESPONSABILIDADES

### 1. Creación Orquestada de Misión

```python
async def create_mission_with_dependencies(
    mission_data: dict,
    auto_level_data: Optional[dict] = None,
    rewards_data: Optional[List[dict]] = None,
    created_by: int = 0
) -> dict:
    """
    Crea misión con auto-creación de dependencias.
    
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
        } (si se especifica, se crea nivel y vincula)
        
        rewards_data: List[{
            'name': str,
            'description': str,
            'reward_type': RewardType,
            'cost_besitos': Optional[int],
            'metadata': dict
        }] (se crean y vinculan a unlock_rewards)
    
    Returns:
        {
            'mission': Mission,
            'created_level': Optional[Level],
            'created_rewards': List[Reward],
            'validation_errors': List[str]
        }
    
    Flujo:
    1. Validar todos los datos con validators
    2. BEGIN TRANSACTION
    3. Crear nivel si auto_level_data
    4. Crear recompensas si rewards_data
    5. Crear misión con IDs vinculados
    6. COMMIT o ROLLBACK si falla
    """
```

### 2. Validación Previa

```python
async def validate_mission_creation(
    mission_data: dict,
    auto_level_data: Optional[dict] = None,
    rewards_data: Optional[List[dict]] = None
) -> tuple[bool, List[str]]:
    """
    Valida todos los datos antes de crear.
    
    Verifica:
    - Criterios de misión válidos
    - Nombre de nivel no duplicado (si aplica)
    - Metadata de recompensas válida (si aplica)
    - Referencias cruzadas consistentes
    
    Returns:
        (is_valid, error_messages)
    """
```

### 3. Plantillas Predefinidas

```python
async def create_from_template(
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
    """
```

---

## TRANSACCIONES ATÓMICAS

```python
async def create_mission_with_dependencies(...):
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
        
        # Crear recompensas si se especificaron
        if rewards_data:
            for reward_data in rewards_data:
                reward = await self.reward_service.create_reward(
                    **reward_data,
                    created_by=created_by
                )
                created_rewards.append(reward)
            
            # Vincular a misión
            mission_data['unlock_rewards'] = [r.id for r in created_rewards]
        
        # Crear misión
        mission = await self.mission_service.create_mission(
            **mission_data,
            created_by=created_by
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
        logger.error(f"Failed to create mission: {e}")
        raise
```

---

## PLANTILLAS

```python
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
                "metadata": {"icon": "🎯", "rarity": BadgeRarity.COMMON}
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
```

---

## FORMATO DE SALIDA

```python
# bot/gamification/services/orchestrator/mission.py

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
    # ... templates aquí
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
        """Crea misión con dependencias en transacción atómica."""
        # Implementar lógica descrita arriba
        pass
    
    async def validate_mission_creation(
        self,
        mission_data: dict,
        auto_level_data: Optional[dict] = None,
        rewards_data: Optional[List[dict]] = None
    ) -> tuple[bool, List[str]]:
        """Valida datos antes de crear."""
        errors = []
        
        # Validar criterios
        is_valid, error = validate_mission_criteria(
            mission_data['mission_type'],
            mission_data['criteria']
        )
        if not is_valid:
            errors.append(f"Invalid criteria: {error}")
        
        # Validar nivel si existe
        if auto_level_data:
            # Verificar nombre único
            existing = await self.level_service.get_all_levels()
            if any(l.name == auto_level_data['name'] for l in existing):
                errors.append(f"Level name already exists: {auto_level_data['name']}")
        
        # Validar recompensas si existen
        if rewards_data:
            for idx, reward_data in enumerate(rewards_data):
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
        if template_name not in MISSION_TEMPLATES:
            raise ValueError(f"Template not found: {template_name}")
        
        template = MISSION_TEMPLATES[template_name].copy()
        
        # Aplicar customizaciones
        if customize:
            if 'besitos_reward' in customize:
                template['mission_data']['besitos_reward'] = customize['besitos_reward']
            # ... otros overrides
        
        return await self.create_mission_with_dependencies(
            mission_data=template.get('mission_data'),
            auto_level_data=template.get('auto_level_data'),
            rewards_data=template.get('rewards_data'),
            created_by=created_by
        )
```

---

## INTEGRACIÓN

```python
# bot/gamification/services/container.py

from bot.gamification.services.orchestrator.mission import MissionOrchestrator

@property
def mission_orchestrator(self) -> MissionOrchestrator:
    if self._mission_orchestrator is None:
        self._mission_orchestrator = MissionOrchestrator(self._session)
    return self._mission_orchestrator
```

---

## VALIDACIÓN

- ✅ Transacciones atómicas (todo o nada)
- ✅ Validación previa completa
- ✅ Auto-creación de niveles y recompensas
- ✅ Plantillas predefinidas
- ✅ Rollback automático en errores
- ✅ Logging de operaciones

---

**ENTREGABLE:** Archivo `mission.py` completo con orquestación transaccional.
