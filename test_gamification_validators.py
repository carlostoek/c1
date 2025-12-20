#!/usr/bin/env python3
"""
Tests para los validadores de gamificación.
"""

import sys
import os

# Asegurar que el path esté configurado correctamente
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from bot.gamification.utils.validators import (
    validate_mission_criteria,
    validate_reward_metadata,
    validate_unlock_conditions,
    is_valid_emoji,
    validate_mission_progress,
    validate_json_structure
)
from bot.gamification.database.enums import MissionType, RewardType, BadgeRarity


def test_mission_criteria_validation():
    """Test validation of mission criteria"""
    print("Testing mission criteria validation...")
    
    # STREAK validation
    result = validate_mission_criteria(MissionType.STREAK, {"type": "streak", "days": 7})
    assert result == (True, "OK"), f"Expected success, got {result}"
    
    result = validate_mission_criteria(MissionType.STREAK, {"type": "streak", "days": -1})
    assert result[0] == False, f"Expected failure for negative days, got {result}"
    
    result = validate_mission_criteria(MissionType.STREAK, {"type": "streak"})
    assert result[0] == False, f"Expected failure for missing days, got {result}"
    
    print("✓ STREAK validation tests passed")
    
    # DAILY validation
    result = validate_mission_criteria(MissionType.DAILY, {"type": "daily", "count": 5})
    assert result == (True, "OK"), f"Expected success, got {result}"
    
    result = validate_mission_criteria(MissionType.DAILY, {"type": "daily", "count": 5, "specific_reaction": "👍"})
    assert result == (True, "OK"), f"Expected success, got {result}"
    
    result = validate_mission_criteria(MissionType.DAILY, {"type": "daily", "count": 5, "specific_reaction": "invalid"})
    assert result[0] == False, f"Expected failure for invalid emoji, got {result}"
    
    print("✓ DAILY validation tests passed")
    
    # WEEKLY validation
    result = validate_mission_criteria(MissionType.WEEKLY, {"type": "weekly", "target": 50})
    assert result == (True, "OK"), f"Expected success, got {result}"
    
    result = validate_mission_criteria(MissionType.WEEKLY, {"type": "weekly", "target": 50, "specific_days": [1, 3, 5]})
    assert result == (True, "OK"), f"Expected success, got {result}"
    
    result = validate_mission_criteria(MissionType.WEEKLY, {"type": "weekly", "target": 50, "specific_days": [1, 3, 10]})
    assert result[0] == False, f"Expected failure for invalid day, got {result}"
    
    print("✓ WEEKLY validation tests passed")
    
    # ONE_TIME validation
    result = validate_mission_criteria(MissionType.ONE_TIME, {"type": "one_time"})
    assert result == (True, "OK"), f"Expected success, got {result}"
    
    print("✓ ONE_TIME validation tests passed")


def test_reward_metadata_validation():
    """Test validation of reward metadata"""
    print("\nTesting reward metadata validation...")
    
    # BADGE validation
    result = validate_reward_metadata(RewardType.BADGE, {"icon": "🏆", "rarity": "epic"})
    assert result == (True, "OK"), f"Expected success, got {result}"
    
    result = validate_reward_metadata(RewardType.BADGE, {"icon": "invalid", "rarity": "epic"})
    assert result[0] == False, f"Expected failure for invalid emoji, got {result}"
    
    result = validate_reward_metadata(RewardType.BADGE, {"icon": "🏆", "rarity": "invalid_rarity"})
    assert result[0] == False, f"Expected failure for invalid rarity, got {result}"
    
    print("✓ BADGE validation tests passed")
    
    # PERMISSION validation
    result = validate_reward_metadata(RewardType.PERMISSION, {"permission_key": "custom_emoji"})
    assert result == (True, "OK"), f"Expected success, got {result}"
    
    result = validate_reward_metadata(RewardType.PERMISSION, {"permission_key": "custom_emoji", "duration_days": 30})
    assert result == (True, "OK"), f"Expected success, got {result}"
    
    result = validate_reward_metadata(RewardType.PERMISSION, {"permission_key": "custom_emoji", "duration_days": -5})
    assert result[0] == False, f"Expected failure for negative duration, got {result}"
    
    print("✓ PERMISSION validation tests passed")
    
    # BESITOS validation
    result = validate_reward_metadata(RewardType.BESITOS, {"amount": 500})
    assert result == (True, "OK"), f"Expected success, got {result}"
    
    result = validate_reward_metadata(RewardType.BESITOS, {"amount": -500})
    assert result[0] == False, f"Expected failure for negative amount, got {result}"
    
    print("✓ BESITOS validation tests passed")


def test_unlock_conditions_validation():
    """Test validation of unlock conditions"""
    print("\nTesting unlock conditions validation...")
    
    # mission condition
    result = validate_unlock_conditions({"type": "mission", "mission_id": 1})
    assert result == (True, "OK"), f"Expected success, got {result}"
    
    # level condition
    result = validate_unlock_conditions({"type": "level", "level_id": 5})
    assert result == (True, "OK"), f"Expected success, got {result}"
    
    # besitos condition
    result = validate_unlock_conditions({"type": "besitos", "min_besitos": 1000})
    assert result == (True, "OK"), f"Expected success, got {result}"
    
    result = validate_unlock_conditions({"type": "besitos", "min_besitos": -100})
    assert result[0] == False, f"Expected failure for negative besitos, got {result}"
    
    # multiple condition
    result = validate_unlock_conditions({
        "type": "multiple",
        "conditions": [
            {"type": "mission", "mission_id": 1},
            {"type": "level", "level_id": 5}
        ]
    })
    assert result == (True, "OK"), f"Expected success, got {result}"
    
    print("✓ Unlock conditions validation tests passed")


def test_emoji_validation():
    """Test emoji validation"""
    print("\nTesting emoji validation...")
    
    assert is_valid_emoji("🏆") == True, "Expected valid emoji"
    assert is_valid_emoji("👍") == True, "Expected valid emoji"
    assert is_valid_emoji("text") == False, "Expected invalid emoji"
    assert is_valid_emoji("") == False, "Expected invalid emoji"
    
    print("✓ Emoji validation tests passed")


def test_mission_progress_validation():
    """Test mission progress validation"""
    print("\nTesting mission progress validation...")
    
    result = validate_mission_progress(MissionType.STREAK, {"days_completed": 5, "last_reaction_date": "2023-01-01"})
    assert result == (True, "OK"), f"Expected success, got {result}"
    
    result = validate_mission_progress(MissionType.DAILY, {"reactions_today": 3, "date": "2023-01-01"})
    assert result == (True, "OK"), f"Expected success, got {result}"
    
    result = validate_mission_progress(MissionType.WEEKLY, {"reactions_this_week": 15, "week_start": "2023-01-01"})
    assert result == (True, "OK"), f"Expected success, got {result}"
    
    print("✓ Mission progress validation tests passed")


def test_json_structure_validation():
    """Test generic JSON structure validation"""
    print("\nTesting JSON structure validation...")
    
    result = validate_json_structure(
        {"name": "test", "value": 123},
        ["name"],
        ["value"],
        {"name": str, "value": int}
    )
    assert result == (True, "OK"), f"Expected success, got {result}"
    
    result = validate_json_structure(
        {"name": "test"},
        ["name", "value"]  # Missing 'value'
    )
    assert result[0] == False, f"Expected failure for missing field, got {result}"
    
    print("✓ JSON structure validation tests passed")


if __name__ == "__main__":
    print("Running validator tests...\n")
    
    test_mission_criteria_validation()
    test_reward_metadata_validation()
    test_unlock_conditions_validation()
    test_emoji_validation()
    test_mission_progress_validation()
    test_json_structure_validation()
    
    print("\n🎉 All validator tests passed successfully!")