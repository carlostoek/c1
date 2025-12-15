"""
Pytest configuration and shared fixtures.

Fixtures disponibles:
- db_session: Sesión de BD de prueba
- reaction_service: Instancia de ReactionService para tests
- sample_reactions: Lista de reacciones de prueba
"""
import asyncio
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from unittest.mock import AsyncMock
from bot.database.models import Base, ReactionConfig, MessageReaction, User
from bot.database.enums import UserRole
from bot.services.reactions import ReactionService
from bot.database.engine import init_db, close_db


# Event loop fixture para pytest-asyncio
@pytest.fixture(scope="session")
def event_loop():
    """
    Create an instance of the default event loop for the test session.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Engine y session fixtures
@pytest_asyncio.fixture
async def db_engine():
    """
    Create test database engine.
    Uses in-memory SQLite for speed.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """
    Create test database session.
    """
    async_session = sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def reaction_service(db_session):
    """
    Create ReactionService instance for testing.
    """
    return ReactionService(db_session)


@pytest_asyncio.fixture
async def sample_user(db_session):
    """
    Create a sample user for testing.
    """
    user = User(
        user_id=123456789,
        username="testuser",
        first_name="Test",
        last_name="User",
        role=UserRole.FREE  # Usar el campo role en lugar de intentar asignar is_vip
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def mock_bot():
    """
    Mock de bot de Telegram para pruebas.
    """
    from unittest.mock import AsyncMock
    mock = AsyncMock()
    return mock


@pytest_asyncio.fixture
async def sample_reactions(reaction_service):
    """
    Create sample reaction configs for testing.
    """
    reactions_data = [
        ("❤️", "Me encanta", 5),
        ("👍", "Me gusta", 3),
        ("🔥", "Genial", 4)
    ]
    
    reactions = []
    for emoji, label, besitos in reactions_data:
        reaction = await reaction_service.create_reaction(
            emoji=emoji,
            label=label,
            besitos_reward=besitos
        )
        if reaction:
            reactions.append(reaction)
    
    return reactions