# PROMPT G3.1: Validadores - Criterios y Metadata

---

## ROL

Actúa como Ingeniero de Software Senior especializado en validación de datos, schemas dinámicos y type safety en Python.

---

## TAREA

Implementa validadores en `bot/gamification/utils/validators.py` para validar criterios JSON de misiones, metadata de recompensas y otros datos dinámicos del sistema.

---

## CONTEXTO

### Arquitectura
```
bot/gamification/utils/
├── validators.py      # ← ESTE ARCHIVO
├── formatters.py
└── __init__.py
```

### Problema a Resolver

Los modelos usan campos JSON (como `Mission.criteria`, `Reward.metadata`) almacenados como strings. Sin validación, errores de formato/tipos solo se descubren en runtime cuando el servicio intenta parsear el JSON.

**Objetivo:** Validar estructura y tipos ANTES de guardar en BD.

---

## VALIDADORES REQUERIDOS

### 1. Validador de Criterios de Misión

```python
def validate_mission_criteria(
    mission_type: MissionType,
    criteria: dict
) -> tuple[bool, str]:
    """
    Valida criterios según tipo de misión.
    
    Returns:
        (is_valid, error_message)
    """
```

**Reglas por tipo:**

**STREAK:**
```python
Required: type, days
Optional: require_consecutive
Types: days (int > 0)
Example: {"type": "streak", "days": 7, "require_consecutive": true}
```

**DAILY:**
```python
Required: type, count
Optional: specific_reaction
Types: count (int > 0), specific_reaction (str emoji o null)
Example: {"type": "daily", "count": 5, "specific_reaction": "❤️"}
```

**WEEKLY:**
```python
Required: type, target
Optional: specific_days
Types: target (int > 0), specific_days (list[int 0-6] o null)
Example: {"type": "weekly", "target": 50, "specific_days": [1,3,5]}
```

**ONE_TIME:**
```python
Required: type
Example: {"type": "one_time"}
```

### 2. Validador de Metadata de Recompensa

```python
def validate_reward_metadata(
    reward_type: RewardType,
    metadata: dict
) -> tuple[bool, str]:
    """Valida metadata según tipo de recompensa."""
```

**Reglas por tipo:**

**BADGE:**
```python
Required: icon, rarity
Types: icon (str emoji), rarity (BadgeRarity value)
Example: {"icon": "🏆", "rarity": "epic"}
```

**PERMISSION:**
```python
Required: permission_key
Optional: duration_days
Types: permission_key (str), duration_days (int > 0 o null)
Example: {"permission_key": "custom_emoji", "duration_days": 30}
```

**BESITOS:**
```python
Required: amount
Types: amount (int > 0)
Example: {"amount": 500}
```

### 3. Validador de Unlock Conditions

```python
def validate_unlock_conditions(conditions: dict) -> tuple[bool, str]:
    """Valida condiciones de desbloqueo."""
```

**Tipos soportados:**
- `mission`: Requiere `mission_id` (int)
- `level`: Requiere `level_id` (int)
- `besitos`: Requiere `min_besitos` (int > 0)
- `multiple`: Requiere `conditions` (list[dict])

### 4. Validador de Emojis

```python
def is_valid_emoji(emoji: str) -> bool:
    """Valida que string sea un emoji válido."""
```

Usar biblioteca `emoji` o regex simple.

### 5. Validador de Progreso de Misión

```python
def validate_mission_progress(
    mission_type: MissionType,
    progress: dict
) -> tuple[bool, str]:
    """Valida estructura de progreso según tipo de misión."""
```

---

## HELPERS

```python
def validate_json_structure(
    data: dict,
    required_fields: List[str],
    optional_fields: List[str] = None,
    field_types: dict = None
) -> tuple[bool, str]:
    """
    Validador genérico de estructura JSON.
    
    Args:
        data: Dict a validar
        required_fields: Campos obligatorios
        optional_fields: Campos opcionales permitidos
        field_types: Dict con tipos esperados {field: type}
    
    Returns:
        (is_valid, error_message)
    """
```

---

## FORMATO DE SALIDA

```python
# bot/gamification/utils/validators.py

"""
Validadores para datos dinámicos del módulo de gamificación.

Valida:
- Criterios de misiones (JSON)
- Metadata de recompensas (JSON)
- Unlock conditions (JSON)
- Emojis
"""

from typing import List, Dict, Tuple
import re

from bot.gamification.database.enums import (
    MissionType, RewardType, BadgeRarity
)


# ========================================
# HELPERS
# ========================================

def validate_json_structure(
    data: dict,
    required_fields: List[str],
    optional_fields: List[str] = None,
    field_types: Dict[str, type] = None
) -> Tuple[bool, str]:
    """Validador genérico de estructura JSON."""
    if not isinstance(data, dict):
        return False, "Data must be a dictionary"
    
    # Verificar campos requeridos
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
    
    # Verificar tipos si se especificaron
    if field_types:
        for field, expected_type in field_types.items():
            if field in data and data[field] is not None:
                if not isinstance(data[field], expected_type):
                    return False, f"Field '{field}' must be {expected_type.__name__}"
    
    # Verificar campos no permitidos
    if optional_fields is not None:
        allowed = set(required_fields + optional_fields)
        extra = set(data.keys()) - allowed
        if extra:
            return False, f"Unexpected fields: {', '.join(extra)}"
    
    return True, "OK"


# ========================================
# VALIDADORES DE CRITERIOS
# ========================================

def validate_mission_criteria(
    mission_type: MissionType,
    criteria: dict
) -> Tuple[bool, str]:
    """Valida criterios de misión según tipo."""
    
    # Verificar que tenga campo 'type' y coincida
    if criteria.get('type') != mission_type:
        return False, f"Criteria type mismatch: expected '{mission_type}'"
    
    if mission_type == MissionType.STREAK:
        is_valid, error = validate_json_structure(
            criteria,
            required_fields=['type', 'days'],
            optional_fields=['require_consecutive'],
            field_types={'days': int, 'require_consecutive': bool}
        )
        if not is_valid:
            return False, error
        
        if criteria['days'] <= 0:
            return False, "days must be > 0"
        
        return True, "OK"
    
    elif mission_type == MissionType.DAILY:
        is_valid, error = validate_json_structure(
            criteria,
            required_fields=['type', 'count'],
            optional_fields=['specific_reaction'],
            field_types={'count': int, 'specific_reaction': str}
        )
        if not is_valid:
            return False, error
        
        if criteria['count'] <= 0:
            return False, "count must be > 0"
        
        # Validar emoji si se especificó
        if 'specific_reaction' in criteria and criteria['specific_reaction']:
            if not is_valid_emoji(criteria['specific_reaction']):
                return False, "specific_reaction must be valid emoji"
        
        return True, "OK"
    
    elif mission_type == MissionType.WEEKLY:
        is_valid, error = validate_json_structure(
            criteria,
            required_fields=['type', 'target'],
            optional_fields=['specific_days'],
            field_types={'target': int, 'specific_days': list}
        )
        if not is_valid:
            return False, error
        
        if criteria['target'] <= 0:
            return False, "target must be > 0"
        
        # Validar specific_days si existe
        if 'specific_days' in criteria and criteria['specific_days']:
            days = criteria['specific_days']
            if not all(isinstance(d, int) and 0 <= d <= 6 for d in days):
                return False, "specific_days must be list of ints 0-6"
        
        return True, "OK"
    
    elif mission_type == MissionType.ONE_TIME:
        is_valid, error = validate_json_structure(
            criteria,
            required_fields=['type'],
            optional_fields=[]
        )
        return is_valid, error
    
    return False, f"Unknown mission type: {mission_type}"


# ========================================
# VALIDADORES DE METADATA
# ========================================

def validate_reward_metadata(
    reward_type: RewardType,
    metadata: dict
) -> Tuple[bool, str]:
    """Valida metadata de recompensa según tipo."""
    
    if reward_type == RewardType.BADGE:
        is_valid, error = validate_json_structure(
            metadata,
            required_fields=['icon', 'rarity'],
            optional_fields=[],
            field_types={'icon': str, 'rarity': str}
        )
        if not is_valid:
            return False, error
        
        # Validar emoji
        if not is_valid_emoji(metadata['icon']):
            return False, "icon must be valid emoji"
        
        # Validar rarity
        try:
            BadgeRarity(metadata['rarity'])
        except ValueError:
            return False, f"Invalid rarity: {metadata['rarity']}"
        
        return True, "OK"
    
    elif reward_type == RewardType.PERMISSION:
        is_valid, error = validate_json_structure(
            metadata,
            required_fields=['permission_key'],
            optional_fields=['duration_days'],
            field_types={'permission_key': str, 'duration_days': int}
        )
        if not is_valid:
            return False, error
        
        if 'duration_days' in metadata and metadata['duration_days'] <= 0:
            return False, "duration_days must be > 0"
        
        return True, "OK"
    
    elif reward_type == RewardType.BESITOS:
        is_valid, error = validate_json_structure(
            metadata,
            required_fields=['amount'],
            optional_fields=[],
            field_types={'amount': int}
        )
        if not is_valid:
            return False, error
        
        if metadata['amount'] <= 0:
            return False, "amount must be > 0"
        
        return True, "OK"
    
    # ITEM y TITLE pueden tener metadata libre
    return True, "OK"


# ========================================
# VALIDADORES DE UNLOCK CONDITIONS
# ========================================

def validate_unlock_conditions(conditions: dict) -> Tuple[bool, str]:
    """Valida condiciones de desbloqueo."""
    condition_type = conditions.get('type')
    
    if condition_type == 'mission':
        is_valid, error = validate_json_structure(
            conditions,
            required_fields=['type', 'mission_id'],
            optional_fields=[],
            field_types={'mission_id': int}
        )
        return is_valid, error
    
    elif condition_type == 'level':
        is_valid, error = validate_json_structure(
            conditions,
            required_fields=['type', 'level_id'],
            optional_fields=[],
            field_types={'level_id': int}
        )
        return is_valid, error
    
    elif condition_type == 'besitos':
        is_valid, error = validate_json_structure(
            conditions,
            required_fields=['type', 'min_besitos'],
            optional_fields=[],
            field_types={'min_besitos': int}
        )
        if not is_valid:
            return False, error
        
        if conditions['min_besitos'] <= 0:
            return False, "min_besitos must be > 0"
        
        return True, "OK"
    
    elif condition_type == 'multiple':
        is_valid, error = validate_json_structure(
            conditions,
            required_fields=['type', 'conditions'],
            optional_fields=[],
            field_types={'conditions': list}
        )
        if not is_valid:
            return False, error
        
        # Validar cada condición recursivamente
        for idx, cond in enumerate(conditions['conditions']):
            is_valid, error = validate_unlock_conditions(cond)
            if not is_valid:
                return False, f"Condition {idx}: {error}"
        
        return True, "OK"
    
    return False, f"Unknown condition type: {condition_type}"


# ========================================
# VALIDADORES MISCELÁNEOS
# ========================================

def is_valid_emoji(emoji: str) -> bool:
    """Valida que string sea un emoji válido."""
    if not emoji or not isinstance(emoji, str):
        return False
    
    # Regex simple para emojis Unicode
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE
    )
    
    return bool(emoji_pattern.match(emoji))


def validate_mission_progress(
    mission_type: MissionType,
    progress: dict
) -> Tuple[bool, str]:
    """Valida estructura de progreso."""
    
    if mission_type == MissionType.STREAK:
        required = ['days_completed', 'last_reaction_date']
        types = {'days_completed': int, 'last_reaction_date': str}
    
    elif mission_type == MissionType.DAILY:
        required = ['reactions_today', 'date']
        types = {'reactions_today': int, 'date': str}
    
    elif mission_type == MissionType.WEEKLY:
        required = ['reactions_this_week', 'week_start']
        types = {'reactions_this_week': int, 'week_start': str}
    
    else:
        # ONE_TIME no tiene progreso específico
        return True, "OK"
    
    return validate_json_structure(
        progress,
        required_fields=required,
        field_types=types
    )
```

---

## INTEGRACIÓN EN SERVICIOS

```python
# bot/gamification/services/mission.py

from bot.gamification.utils.validators import validate_mission_criteria

async def create_mission(...):
    # Validar antes de guardar
    is_valid, error = validate_mission_criteria(mission_type, criteria)
    if not is_valid:
        raise ValueError(f"Invalid criteria: {error}")
    
    # Continuar con creación...
```

---

## VALIDACIÓN

- ✅ Validadores para todos los tipos de criterios
- ✅ Validadores para metadata de recompensas
- ✅ Validador de unlock conditions (recursivo)
- ✅ Validador de emojis
- ✅ Helper genérico reutilizable
- ✅ Type hints completos
- ✅ Mensajes de error descriptivos

---

**ENTREGABLE:** Archivo `validators.py` completo con validaciones para todos los JSONs dinámicos.
