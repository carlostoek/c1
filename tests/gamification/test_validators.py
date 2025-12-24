"""Tests para validadores del módulo de gamificación."""

import pytest

from bot.gamification.database.enums import (
    MissionType, RewardType, BadgeRarity
)
from bot.gamification.utils.validators import (
    validate_json_structure,
    validate_mission_criteria,
    validate_reward_metadata,
    validate_unlock_conditions,
    is_valid_emoji,
    validate_mission_progress,
)


# ========================================
# TESTS: validate_json_structure
# ========================================

def test_validate_json_structure_valid():
    """Test validación exitosa de estructura JSON."""
    data = {"name": "Test", "count": 5}
    is_valid, error = validate_json_structure(
        data,
        required_fields=["name", "count"],
        field_types={"name": str, "count": int}
    )
    assert is_valid is True
    assert error == "OK"


def test_validate_json_structure_missing_field():
    """Test detección de campo faltante."""
    data = {"name": "Test"}
    is_valid, error = validate_json_structure(
        data,
        required_fields=["name", "count"]
    )
    assert is_valid is False
    assert "Missing required field: count" in error


def test_validate_json_structure_wrong_type():
    """Test detección de tipo incorrecto."""
    data = {"name": "Test", "count": "invalid"}
    is_valid, error = validate_json_structure(
        data,
        required_fields=["name", "count"],
        field_types={"count": int}
    )
    assert is_valid is False
    assert "must be int" in error


def test_validate_json_structure_unexpected_field():
    """Test detección de campos inesperados."""
    data = {"name": "Test", "extra": "field"}
    is_valid, error = validate_json_structure(
        data,
        required_fields=["name"],
        optional_fields=[]
    )
    assert is_valid is False
    assert "Unexpected fields" in error


def test_validate_json_structure_optional_fields():
    """Test campos opcionales permitidos."""
    data = {"name": "Test", "optional": "value"}
    is_valid, error = validate_json_structure(
        data,
        required_fields=["name"],
        optional_fields=["optional"]
    )
    assert is_valid is True


# ========================================
# TESTS: validate_mission_criteria
# ========================================

def test_validate_mission_criteria_streak_valid():
    """Test validación STREAK válido."""
    criteria = {"type": MissionType.STREAK, "days": 7, "require_consecutive": True}
    is_valid, error = validate_mission_criteria(MissionType.STREAK, criteria)
    assert is_valid is True


def test_validate_mission_criteria_streak_invalid_days():
    """Test STREAK con días <= 0."""
    criteria = {"type": MissionType.STREAK, "days": 0}
    is_valid, error = validate_mission_criteria(MissionType.STREAK, criteria)
    assert is_valid is False
    assert "days must be > 0" in error


def test_validate_mission_criteria_daily_valid():
    """Test validación DAILY válido."""
    criteria = {"type": MissionType.DAILY, "count": 5, "specific_reaction": "❤️"}
    is_valid, error = validate_mission_criteria(MissionType.DAILY, criteria)
    assert is_valid is True


def test_validate_mission_criteria_daily_invalid_count():
    """Test DAILY con count <= 0."""
    criteria = {"type": MissionType.DAILY, "count": -1}
    is_valid, error = validate_mission_criteria(MissionType.DAILY, criteria)
    assert is_valid is False
    assert "count must be > 0" in error


def test_validate_mission_criteria_daily_invalid_emoji():
    """Test DAILY con emoji inválido."""
    criteria = {"type": MissionType.DAILY, "count": 5, "specific_reaction": "invalid"}
    is_valid, error = validate_mission_criteria(MissionType.DAILY, criteria)
    assert is_valid is False
    assert "must be valid emoji" in error


def test_validate_mission_criteria_weekly_valid():
    """Test validación WEEKLY válido."""
    criteria = {"type": MissionType.WEEKLY, "target": 50, "specific_days": [1, 3, 5]}
    is_valid, error = validate_mission_criteria(MissionType.WEEKLY, criteria)
    assert is_valid is True


def test_validate_mission_criteria_weekly_invalid_target():
    """Test WEEKLY con target <= 0."""
    criteria = {"type": MissionType.WEEKLY, "target": 0}
    is_valid, error = validate_mission_criteria(MissionType.WEEKLY, criteria)
    assert is_valid is False
    assert "target must be > 0" in error


def test_validate_mission_criteria_weekly_invalid_days():
    """Test WEEKLY con specific_days fuera de rango."""
    criteria = {"type": MissionType.WEEKLY, "target": 50, "specific_days": [1, 7, 10]}
    is_valid, error = validate_mission_criteria(MissionType.WEEKLY, criteria)
    assert is_valid is False
    assert "specific_days must be list of ints 0-6" in error


def test_validate_mission_criteria_one_time_valid():
    """Test validación ONE_TIME válido."""
    criteria = {"type": MissionType.ONE_TIME}
    is_valid, error = validate_mission_criteria(MissionType.ONE_TIME, criteria)
    assert is_valid is True


def test_validate_mission_criteria_type_mismatch():
    """Test detección de type mismatch."""
    criteria = {"type": MissionType.DAILY, "count": 5}
    is_valid, error = validate_mission_criteria(MissionType.STREAK, criteria)
    assert is_valid is False
    assert "type mismatch" in error


# ========================================
# TESTS: validate_reward_metadata
# ========================================

def test_validate_reward_metadata_badge_valid():
    """Test validación BADGE válido."""
    metadata = {"icon": "🏆", "rarity": BadgeRarity.EPIC}
    is_valid, error = validate_reward_metadata(RewardType.BADGE, metadata)
    assert is_valid is True


def test_validate_reward_metadata_badge_invalid_emoji():
    """Test BADGE con emoji inválido."""
    metadata = {"icon": "invalid", "rarity": BadgeRarity.COMMON}
    is_valid, error = validate_reward_metadata(RewardType.BADGE, metadata)
    assert is_valid is False
    assert "icon must be valid emoji" in error


def test_validate_reward_metadata_badge_invalid_rarity():
    """Test BADGE con rarity inválida."""
    metadata = {"icon": "🏆", "rarity": "invalid_rarity"}
    is_valid, error = validate_reward_metadata(RewardType.BADGE, metadata)
    assert is_valid is False
    assert "Invalid rarity" in error


def test_validate_reward_metadata_permission_valid():
    """Test validación PERMISSION válido."""
    metadata = {"permission_key": "custom_emoji", "duration_days": 30}
    is_valid, error = validate_reward_metadata(RewardType.PERMISSION, metadata)
    assert is_valid is True


def test_validate_reward_metadata_permission_invalid_duration():
    """Test PERMISSION con duration <= 0."""
    metadata = {"permission_key": "custom_emoji", "duration_days": 0}
    is_valid, error = validate_reward_metadata(RewardType.PERMISSION, metadata)
    assert is_valid is False
    assert "duration_days must be > 0" in error


def test_validate_reward_metadata_besitos_valid():
    """Test validación BESITOS válido."""
    metadata = {"amount": 500}
    is_valid, error = validate_reward_metadata(RewardType.BESITOS, metadata)
    assert is_valid is True


def test_validate_reward_metadata_besitos_invalid_amount():
    """Test BESITOS con amount <= 0."""
    metadata = {"amount": -100}
    is_valid, error = validate_reward_metadata(RewardType.BESITOS, metadata)
    assert is_valid is False
    assert "amount must be > 0" in error


def test_validate_reward_metadata_item_free_form():
    """Test ITEM permite metadata libre."""
    metadata = {"custom_field": "value", "another": 123}
    is_valid, error = validate_reward_metadata(RewardType.ITEM, metadata)
    assert is_valid is True


# ========================================
# TESTS: validate_unlock_conditions
# ========================================

def test_validate_unlock_conditions_mission_valid():
    """Test validación unlock condition MISSION."""
    conditions = {"type": "mission", "mission_id": 1}
    is_valid, error = validate_unlock_conditions(conditions)
    assert is_valid is True


def test_validate_unlock_conditions_level_valid():
    """Test validación unlock condition LEVEL."""
    conditions = {"type": "level", "level_id": 5}
    is_valid, error = validate_unlock_conditions(conditions)
    assert is_valid is True


def test_validate_unlock_conditions_besitos_valid():
    """Test validación unlock condition BESITOS."""
    conditions = {"type": "besitos", "min_besitos": 1000}
    is_valid, error = validate_unlock_conditions(conditions)
    assert is_valid is True


def test_validate_unlock_conditions_besitos_invalid():
    """Test BESITOS con min_besitos <= 0."""
    conditions = {"type": "besitos", "min_besitos": 0}
    is_valid, error = validate_unlock_conditions(conditions)
    assert is_valid is False
    assert "min_besitos must be > 0" in error


def test_validate_unlock_conditions_multiple_valid():
    """Test validación unlock condition MULTIPLE (recursivo)."""
    conditions = {
        "type": "multiple",
        "conditions": [
            {"type": "mission", "mission_id": 1},
            {"type": "level", "level_id": 3},
            {"type": "besitos", "min_besitos": 500}
        ]
    }
    is_valid, error = validate_unlock_conditions(conditions)
    assert is_valid is True


def test_validate_unlock_conditions_multiple_invalid_nested():
    """Test MULTIPLE detecta condición inválida anidada."""
    conditions = {
        "type": "multiple",
        "conditions": [
            {"type": "mission", "mission_id": 1},
            {"type": "besitos", "min_besitos": -100}  # Inválido
        ]
    }
    is_valid, error = validate_unlock_conditions(conditions)
    assert is_valid is False
    assert "Condition 1" in error


def test_validate_unlock_conditions_unknown_type():
    """Test detección de tipo desconocido."""
    conditions = {"type": "unknown"}
    is_valid, error = validate_unlock_conditions(conditions)
    assert is_valid is False
    assert "Unknown condition type" in error


# ========================================
# TESTS: is_valid_emoji
# ========================================

def test_is_valid_emoji_valid():
    """Test emojis válidos."""
    assert is_valid_emoji("❤️") is True
    assert is_valid_emoji("🏆") is True
    assert is_valid_emoji("🎮") is True
    assert is_valid_emoji("⭐") is True


def test_is_valid_emoji_invalid():
    """Test strings que no son emojis."""
    assert is_valid_emoji("not an emoji") is False
    assert is_valid_emoji("123") is False
    assert is_valid_emoji("") is False
    assert is_valid_emoji(None) is False


# ========================================
# TESTS: validate_mission_progress
# ========================================

def test_validate_mission_progress_streak_valid():
    """Test validación progreso STREAK."""
    progress = {"days_completed": 3, "last_reaction_date": "2024-12-24"}
    is_valid, error = validate_mission_progress(MissionType.STREAK, progress)
    assert is_valid is True


def test_validate_mission_progress_daily_valid():
    """Test validación progreso DAILY."""
    progress = {"reactions_today": 5, "date": "2024-12-24"}
    is_valid, error = validate_mission_progress(MissionType.DAILY, progress)
    assert is_valid is True


def test_validate_mission_progress_weekly_valid():
    """Test validación progreso WEEKLY."""
    progress = {"reactions_this_week": 20, "week_start": "2024-12-18"}
    is_valid, error = validate_mission_progress(MissionType.WEEKLY, progress)
    assert is_valid is True


def test_validate_mission_progress_one_time_no_validation():
    """Test ONE_TIME no requiere progreso específico."""
    progress = {"any": "data"}
    is_valid, error = validate_mission_progress(MissionType.ONE_TIME, progress)
    assert is_valid is True


def test_validate_mission_progress_missing_field():
    """Test detección de campo faltante en progreso."""
    progress = {"days_completed": 3}  # Falta last_reaction_date
    is_valid, error = validate_mission_progress(MissionType.STREAK, progress)
    assert is_valid is False
    assert "Missing required field" in error
