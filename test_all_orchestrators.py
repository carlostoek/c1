#!/usr/bin/env python3
"""
Comprehensive integration test for all orchestrators
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


async def test_all_orchestrators():
    """Test all orchestrators working together"""
    # Create in-memory database for testing
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get container with all orchestrators
        container = GamificationContainer(session)

        # Access ALL services to load them (lazy loading)
        _ = container.reaction
        _ = container.besito
        _ = container.level
        _ = container.mission
        _ = container.reward
        _ = container.user_gamification
        _ = container.mission_orchestrator
        _ = container.reward_orchestrator
        _ = container.configuration_orchestrator

        service_names = container.get_loaded_services()
        expected_services = {
            'reaction', 'besito', 'level', 'mission', 'reward',
            'user_gamification', 'mission_orchestrator',
            'reward_orchestrator', 'configuration_orchestrator'
        }
        actual_services = set(service_names)

        print(f'Expected: {expected_services}')
        print(f'Actual: {actual_services}')
        print(f'✅ All expected services loaded: {service_names}')
        assert expected_services <= actual_services, f'Expected services {expected_services}, got {actual_services}'
        
        # Test individual orchestrators
        mission_orch = container.mission_orchestrator
        reward_orch = container.reward_orchestrator
        config_orch = container.configuration_orchestrator
        
        print(f'✅ Mission orchestrator templates: {list(mission_orch.MISSION_TEMPLATES.keys())}')
        print(f'✅ Reward orchestrator templates: {list(reward_orch.REWARD_TEMPLATES.keys())}')
        print(f'✅ Configuration orchestrator templates: {list(config_orch.SYSTEM_TEMPLATES.keys())}')
        
        # Test configuration orchestrator's complete mission system
        config_data = {
            'mission': {
                'name': 'Test Mission',
                'description': 'Test mission for integration',
                'mission_type': MissionType.DAILY,
                'criteria': {'type': 'daily', 'count': 5},
                'besitos_reward': 200,
                'repeatable': True
            },
            'auto_level': {
                'name': 'Test Level',
                'min_besitos': 100,
                'order': 1
            },
            'rewards': [
                {
                    'name': 'Test Badge',
                    'description': 'Test badge reward',
                    'reward_type': RewardType.BADGE,
                    'metadata': {'icon': '🏆', 'rarity': 'common'}
                }
            ]
        }
        
        result = await config_orch.create_complete_mission_system(
            config=config_data,
            created_by=123
        )
        
        assert 'mission' in result, f"Expected mission in result, got: {result}"
        assert 'created_level' in result, f"Expected created_level in result, got: {result}"
        assert 'created_rewards' in result, f"Expected created_rewards in result, got: {result}"
        assert 'validation_errors' in result, "Expected validation_errors in result"
        assert len(result['validation_errors']) == 0, f"Expected no validation errors, got: {result['validation_errors']}"
        print('✅ Complete mission system creation works')
        
        # Test template application
        template_result = await config_orch.apply_system_template(
            template_name="starter_pack",
            created_by=123
        )
        
        assert 'missions_created' in template_result, "Expected missions_created in template result"
        assert 'levels_created' in template_result, "Expected levels_created in template result"
        assert 'rewards_created' in template_result, "Expected rewards_created in template result"
        assert 'summary' in template_result, "Expected summary in template result"
        print('✅ Template-based system creation works')
        
        print('✅ All orchestrators work together seamlessly')
    
    print("\n🎉 All orchestrators integration test passed!")


if __name__ == "__main__":
    asyncio.run(test_all_orchestrators())