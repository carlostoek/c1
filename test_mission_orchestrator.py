#!/usr/bin/env python3
"""
Test básico para el MissionOrchestrator
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from bot.gamification.database.models import Base
from bot.gamification.services.container import GamificationContainer


async def test_mission_orchestrator():
    """Test the MissionOrchestrator functionality"""
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
        
        # Test if mission orchestrator property works
        orchestrator = container.mission_orchestrator
        print("✓ MissionOrchestrator property works correctly")
        
        # Test if the template exists
        print("✓ Available templates:", list(orchestrator.__class__.__dict__.get('MISSION_TEMPLATES', {}).keys()))
        
        # Test importing the class directly
        from bot.gamification.services.orchestrator.mission import MissionOrchestrator
        print("✓ MissionOrchestrator class can be imported directly")
        
        # Check if it has the required methods
        assert hasattr(orchestrator, 'create_mission_with_dependencies'), "create_mission_with_dependencies method missing"
        assert hasattr(orchestrator, 'validate_mission_creation'), "validate_mission_creation method missing"
        assert hasattr(orchestrator, 'create_from_template'), "create_from_template method missing"
        print("✓ All required methods are available")
    
    print("\n🎉 MissionOrchestrator test completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_mission_orchestrator())