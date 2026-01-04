"""Fixtures para tests del módulo de gamificación."""

import pytest
import pytest_asyncio
from datetime import datetime, UTC
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from bot.gamification.database.models import (
    Base, UserGamification, Reaction, Level, Mission,
    ConfigTemplate, GamificationConfig
)
from bot.gamification.database.enums import MissionType


@pytest_asyncio.fixture
async def db_engine():
    """Crea engine de SQLite en memoria para tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Sesión de BD en memoria para tests."""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def sample_user(db_session):
    """Usuario de prueba."""
    user = UserGamification(user_id=12345, total_besitos=0)
    db_session.add(user)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def sample_reaction(db_session):
    """Reacción de prueba."""
    reaction = Reaction(emoji="❤️", name="Corazón", besitos_value=1, active=True)
    db_session.add(reaction)
    await db_session.commit()
    return reaction


@pytest_asyncio.fixture
async def sample_level(db_session):
    """Nivel de prueba."""
    level = Level(name="Novato", min_besitos=0, order=1, active=True)
    db_session.add(level)
    await db_session.commit()
    return level


@pytest_asyncio.fixture
async def sample_mission(db_session):
    """Misión de prueba."""
    mission = Mission(
        name="Primera Racha",
        description="Completa 7 días consecutivos",
        mission_type=MissionType.STREAK.value,
        criteria='{"type": "streak", "days": 7}',
        besitos_reward=500,
        repeatable=False,
        active=True,
        created_by=999
    )
    db_session.add(mission)
    await db_session.commit()
    return mission


@pytest_asyncio.fixture
async def sample_config_template(db_session):
    """Plantilla de configuración de prueba."""
    template = ConfigTemplate(
        name="Sistema Básico",
        description="Configuración básica recomendada",
        template_data='{"missions": [], "rewards": [], "levels": []}',
        category="full_system",
        created_by=999
    )
    db_session.add(template)
    await db_session.commit()
    return template
