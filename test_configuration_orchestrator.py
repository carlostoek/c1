#!/usr/bin/env python3
"""
Test básico para el ConfigurationOrchestrator
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from bot.gamification.database.models import Base
from bot.gamification.services.container import GamificationContainer
from bot.gamification.database.enums import MissionType


async def test_configuration_orchestrator():
    """Test the ConfigurationOrchestrator functionality"""
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
        
        # Test if configuration orchestrator property works
        orchestrator = container.configuration_orchestrator
        print("✓ ConfigurationOrchestrator property works correctly")
        
        # Test if the templates exist
        print("✓ Available templates:", list(orchestrator.SYSTEM_TEMPLATES.keys()))
        
        # Import the class directly to check templates
        from bot.gamification.services.orchestrator.configuration import ConfigurationOrchestrator
        print("✓ ConfigurationOrchestrator class can be imported directly")
        print("✓ System templates:", list(ConfigurationOrchestrator.SYSTEM_TEMPLATES.keys()))
        
        # Check if it has the required methods
        assert hasattr(orchestrator, 'create_complete_mission_system'), "create_complete_mission_system method missing"
        assert hasattr(orchestrator, 'apply_system_template'), "apply_system_template method missing"
        assert hasattr(orchestrator, 'validate_complete_config'), "validate_complete_config method missing"
        print("✓ All required methods are available")
    
    print("\n🎉 ConfigurationOrchestrator test completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_configuration_orchestrator())