#!/usr/bin/env python3
"""
Comprehensive test for MissionOrchestrator functionality
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from bot.gamification.database.models import Base
from bot.gamification.services.container import GamificationContainer
from bot.gamification.database.enums import MissionType, RewardType


async def test_mission_orchestrator_comprehensive():
    """Test comprehensive MissionOrchestrator functionality"""
    # Create in-memory database for testing
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get container with orchestrator
        container = GamificationContainer(session)
        orchestrator = container.mission_orchestrator
        
        print("Testing validation without dependencies...")
        
        # Test validation without dependencies
        mission_data = {
            "name": "Test Mission",
            "description": "Test description",
            "mission_type": MissionType.DAILY,
            "criteria": {"type": "daily", "count": 5},
            "besitos_reward": 100,
            "repeatable": True
        }
        
        is_valid, errors = await orchestrator.validate_mission_creation(mission_data)
        print(f"Validation result: {is_valid}, errors: {errors}")
        assert is_valid, f"Validation should pass, got errors: {errors}"
        print("✓ Basic validation works")
        
        # Test validation with auto level data
        print("\nTesting validation with auto level data...")
        auto_level_data = {
            "name": "Test Level",
            "min_besitos": 500,
            "order": 1
        }
        
        is_valid, errors = await orchestrator.validate_mission_creation(mission_data, auto_level_data)
        print(f"Validation with level result: {is_valid}, errors: {errors}")
        assert is_valid, f"Validation with level should pass, got errors: {errors}"
        print("✓ Validation with level data works")
        
        # Test validation with reward data
        print("\nTesting validation with reward data...")
        rewards_data = [
            {
                "name": "Test Badge",
                "description": "Test badge reward",
                "reward_type": RewardType.BADGE,
                "metadata": {"icon": "🏆", "rarity": "common"}
            }
        ]
        
        is_valid, errors = await orchestrator.validate_mission_creation(
            mission_data, 
            auto_level_data, 
            rewards_data
        )
        print(f"Validation with reward result: {is_valid}, errors: {errors}")
        assert is_valid, f"Validation with reward should pass, got errors: {errors}"
        print("✓ Validation with reward data works")
        
        # Test template functionality
        print("\nTesting template functionality...")
        template_names = list(orchestrator.MISSION_TEMPLATES.keys())
        print(f"Available templates: {template_names}")
        assert len(template_names) > 0, "Should have templates defined"
        print("✓ Templates are available")
        
        # Test accessing a specific template
        welcome_template = orchestrator.MISSION_TEMPLATES["welcome"]
        print(f"Welcome template keys: {list(welcome_template.keys())}")
        assert "mission_data" in welcome_template
        print("✓ Template structure is correct")
    
    print("\n🎉 All comprehensive tests passed!")


if __name__ == "__main__":
    asyncio.run(test_mission_orchestrator_comprehensive())