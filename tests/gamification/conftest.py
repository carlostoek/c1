# tests/gamification/conftest.py

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from bot.gamification.database.models import (
    Base, UserGamification, Reaction, UserReaction, UserStreak, 
    Level, Mission, UserMission, Reward, UserReward, Badge, 
    UserBadge, ConfigTemplate, GamificationConfig
)
from bot.gamification.database.enums import MissionType, MissionStatus, RewardType, BadgeRarity, ObtainedVia


@pytest_asyncio.fixture
async def db_session():
    """Sesión de BD en memoria para tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
    
    await engine.dispose()


@pytest_asyncio.fixture
async def sample_user(db_session):
    """Usuario de prueba."""
    user = UserGamification(user_id=12345, total_besitos=0)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def sample_reaction(db_session):
    """Reacción de prueba."""
    reaction = Reaction(emoji="❤️", besitos_value=1)
    db_session.add(reaction)
    await db_session.commit()
    await db_session.refresh(reaction)
    return reaction


@pytest_asyncio.fixture
async def sample_level(db_session):
    """Nivel de prueba."""
    level = Level(name="Novato", min_besitos=0, order=1)
    db_session.add(level)
    await db_session.commit()
    await db_session.refresh(level)
    return level


@pytest_asyncio.fixture
async def sample_mission(db_session, sample_level):
    """Misión de prueba."""
    mission = Mission(
        name="Primera Racha",
        description="Completa 7 días consecutivos",
        mission_type=MissionType.STREAK,
        criteria='{"type": "streak", "days": 7}',
        besitos_reward=500,
        auto_level_up_id=sample_level.id,
        created_by=98765
    )
    db_session.add(mission)
    await db_session.commit()
    await db_session.refresh(mission)
    return mission


@pytest_asyncio.fixture
async def sample_reward(db_session):
    """Recompensa de prueba."""
    reward = Reward(
        name="Primer Paso",
        description="Completaste tu primera misión",
        reward_type=RewardType.BADGE,
        cost_besitos=100,
        created_by=98765
    )
    db_session.add(reward)
    await db_session.commit()
    await db_session.refresh(reward)
    return reward


@pytest_asyncio.fixture
async def sample_badge(db_session, sample_reward):
    """Badge de prueba."""
    badge = Badge(
        id=sample_reward.id,
        icon="🏆",
        rarity=BadgeRarity.COMMON
    )
    db_session.add(badge)
    await db_session.commit()
    await db_session.refresh(badge)
    return badge