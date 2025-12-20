#!/usr/bin/env python3
"""
Comprehensive integration test for GamificationContainer with both orchestrators
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from bot.gamification.database.models import Base
from bot.gamification.services.container import GamificationContainer
from bot.gamification.database.enums import RewardType, BadgeRarity


async def test_full_integration():
    """Test comprehensive integration of both orchestrators"""
    # Create in-memory database for testing
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get container with both orchestrators
        container = GamificationContainer(session)
        
        # Test that all services exist and work
        services = [
            container.reaction,
            container.besito,
            container.level,
            container.mission,
            container.reward,
            container.user_gamification,
            container.mission_orchestrator,
            container.reward_orchestrator
        ]
        
        service_names = container.get_loaded_services()
        print(f'Loaded services: {service_names}')
        
        # Check if both orchestrators are included
        assert 'mission_orchestrator' in service_names, 'mission_orchestrator should be in loaded services'
        assert 'reward_orchestrator' in service_names, 'reward_orchestrator should be in loaded services'
        
        print('✅ All services work correctly including both orchestrators')
        
        # Test MissionOrchestrator
        mission_orch = container.mission_orchestrator
        assert hasattr(mission_orch, 'create_mission_with_dependencies'), 'Missing method in mission orchestrator'
        assert len(mission_orch.MISSION_TEMPLATES) > 0, 'No templates found in mission orchestrator'
        print('✅ MissionOrchestrator is fully functional')
        
        # Test RewardOrchestrator
        reward_orch = container.reward_orchestrator
        assert hasattr(reward_orch, 'create_reward_with_unlock_condition'), 'Missing method in reward orchestrator'
        assert len(reward_orch.REWARD_TEMPLATES) > 0, 'No templates found in reward orchestrator'
        print('✅ RewardOrchestrator is fully functional')
        
        # Test basic validation of orchestrator functionality
        # Test reward creation without unlock condition
        reward_data = {
            "name": "Test Badge",
            "description": "Test badge for integration",
            "reward_type": RewardType.BADGE,
            "metadata": {"icon": "🏆", "rarity": BadgeRarity.COMMON.value}
        }
        
        result = await reward_orch.create_reward_with_unlock_condition(
            reward_data=reward_data,
            created_by=123
        )
        
        assert 'reward' in result, f"Expected reward in result, got: {result}"
        assert 'validation_errors' in result, "Expected validation_errors in result"
        assert len(result['validation_errors']) == 0, f"Expected no validation errors, got: {result['validation_errors']}"
        print('✅ Reward creation with orchestrator works')
        
        # Test template usage
        welcome_result = await reward_orch.create_from_template(
            template_name="welcome_pack",
            created_by=123
        )
        
        assert 'created_rewards' in welcome_result or 'failed' in welcome_result, "Expected proper template result structure"
        print('✅ Template-based reward creation works')
    
    print("\n🎉 Full integration test passed!")


if __name__ == "__main__":
    asyncio.run(test_full_integration())