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

    # ========================================
    # CONDICIONES NARRATIVAS
    # ========================================

    elif condition_type == 'narrative_chapter':
        is_valid, error = validate_json_structure(
            conditions,
            required_fields=['type', 'chapter_slug'],
            optional_fields=[],
            field_types={'chapter_slug': str}
        )
        if not is_valid:
            return False, error

        # Validar que chapter_slug no esté vacío
        if not conditions['chapter_slug'].strip():
            return False, "chapter_slug cannot be empty"

        return True, "OK"

    elif condition_type == 'narrative_fragment':
        is_valid, error = validate_json_structure(
            conditions,
            required_fields=['type', 'fragment_key'],
            optional_fields=[],
            field_types={'fragment_key': str}
        )
        if not is_valid:
            return False, error

        # Validar que fragment_key no esté vacío
        if not conditions['fragment_key'].strip():
            return False, "fragment_key cannot be empty"

        return True, "OK"

    elif condition_type == 'narrative_decision':
        is_valid, error = validate_json_structure(
            conditions,
            required_fields=['type', 'decision_key'],
            optional_fields=[],
            field_types={'decision_key': str}
        )
        if not is_valid:
            return False, error

        # Validar que decision_key no esté vacío
        if not conditions['decision_key'].strip():
            return False, "decision_key cannot be empty"

        return True, "OK"

    elif condition_type == 'archetype':
        is_valid, error = validate_json_structure(
            conditions,
            required_fields=['type', 'archetype'],
            optional_fields=[],
            field_types={'archetype': str}
        )
        if not is_valid:
            return False, error

        # Validar que el arquetipo sea válido
        valid_archetypes = ['unknown', 'impulsive', 'contemplative', 'silent']
        if conditions['archetype'] not in valid_archetypes:
            return False, f"Invalid archetype. Valid: {', '.join(valid_archetypes)}"

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
