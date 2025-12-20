#!/usr/bin/env python3
"""
Test básico para el RewardOrchestrator
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from bot.gamification.database.models import Base
from bot.gamification.services.container import GamificationContainer
from bot.gamification.database.enums import RewardType


async def test_reward_orchestrator():
    """Test the RewardOrchestrator functionality"""
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
        
        # Test if reward orchestrator property works
        orchestrator = container.reward_orchestrator
        print("✓ RewardOrchestrator property works correctly")
        
        # Test if the templates exist
        print("✓ Available templates:", list(orchestrator.MISSION_TEMPLATES.keys()) if hasattr(orchestrator, 'MISSION_TEMPLATES') else "No MISSION_TEMPLATES")
        print("✓ Available reward templates:", list(orchestrator.REWARD_TEMPLATES.keys()) if hasattr(orchestrator, 'REWARD_TEMPLATES') else "No REWARD_TEMPLATES")
        
        # Import the class directly to check templates
        from bot.gamification.services.orchestrator.reward import RewardOrchestrator
        print("✓ RewardOrchestrator class can be imported directly")
        print("✓ Reward templates:", list(RewardOrchestrator.REWARD_TEMPLATES.keys()))
        
        # Check if it has the required methods
        assert hasattr(orchestrator, 'create_reward_with_unlock_condition'), "create_reward_with_unlock_condition method missing"
        assert hasattr(orchestrator, 'create_badge_set'), "create_badge_set method missing"
        assert hasattr(orchestrator, 'create_from_template'), "create_from_template method missing"
        print("✓ All required methods are available")
    
    print("\n🎉 RewardOrchestrator test completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_reward_orchestrator())