"""Tests para el servicio de estadísticas."""

import pytest
from datetime import datetime, timedelta, UTC
from sqlalchemy.ext.asyncio import AsyncSession

from bot.gamification.services.stats import StatsService
from bot.gamification.services.level import LevelService
from bot.gamification.services.mission import MissionService
from bot.gamification.services.besito import BesitoService
from bot.gamification.services.reaction import ReactionService
from bot.gamification.database.enums import MissionType, MissionStatus, TransactionType
from bot.gamification.database.models import (
    UserGamification, UserMission, UserReaction, UserStreak
)


@pytest.mark.asyncio
async def test_get_system_overview_empty(db_session: AsyncSession):
    """Verifica estadísticas generales con sistema vacío."""
    stats_service = StatsService(db_session)
    overview = await stats_service.get_system_overview()

    assert overview['total_users'] == 0
    assert overview['active_users_7d'] == 0
    assert overview['total_besitos_distributed'] == 0
    assert overview['total_missions'] == 0
    assert overview['missions_completed'] == 0
    assert overview['rewards_claimed'] == 0


@pytest.mark.asyncio
async def test_get_system_overview_with_data(db_session: AsyncSession, sample_level):
    """Verifica estadísticas generales con datos."""
    # Crear usuario con besitos
    besito_service = BesitoService(db_session)
    await besito_service.grant_besitos(
        user_id=100, amount=500, transaction_type=TransactionType.REACTION, description="test"
    )
    await besito_service.grant_besitos(
        user_id=200, amount=300, transaction_type=TransactionType.REACTION, description="test"
    )

    # Crear misión
    mission_service = MissionService(db_session)
    mission = await mission_service.create_mission(
        name="Test Mission",
        description="Test",
        mission_type=MissionType.ONE_TIME,
        criteria={"type": "one_time"},
        besitos_reward=100,
        created_by=1
    )

    # Completar misión
    from bot.gamification.database.models import UserMission
    user_mission = UserMission(
        user_id=100,
        mission_id=mission.id,
        progress="{}",
        status=MissionStatus.CLAIMED,
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        claimed_at=datetime.now(UTC)
    )
    db_session.add(user_mission)
    await db_session.commit()

    # Obtener estadísticas
    stats_service = StatsService(db_session)
    overview = await stats_service.get_system_overview()

    assert overview['total_users'] == 2
    assert overview['total_besitos_distributed'] == 800  # 500 + 300
    assert overview['total_missions'] == 1
    assert overview['missions_completed'] == 1


@pytest.mark.asyncio
async def test_get_user_distribution(db_session: AsyncSession):
    """Verifica distribución de usuarios por nivel."""
    # Crear niveles
    level_service = LevelService(db_session)
    nivel1 = await level_service.create_level("Novato", 0, 1)
    nivel2 = await level_service.create_level("Regular", 500, 2)

    # Crear usuarios
    besito_service = BesitoService(db_session)
    await besito_service.grant_besitos(
        user_id=100, amount=100, transaction_type=TransactionType.REACTION, description="test"
    )
    await besito_service.grant_besitos(
        user_id=200, amount=200, transaction_type=TransactionType.REACTION, description="test"
    )
    await besito_service.grant_besitos(
        user_id=300, amount=600, transaction_type=TransactionType.REACTION, description="test"
    )

    # Actualizar niveles manualmente
    from sqlalchemy import update
    await db_session.execute(
        update(UserGamification)
        .where(UserGamification.user_id == 300)
        .values(current_level_id=nivel2.id)
    )
    await db_session.commit()

    # Obtener distribución
    stats_service = StatsService(db_session)
    distribution = await stats_service.get_user_distribution()

    assert 'by_level' in distribution
    assert 'top_users' in distribution
    assert 'avg_besitos' in distribution
    assert distribution['avg_besitos'] == 300  # (100 + 200 + 600) / 3


@pytest.mark.asyncio
async def test_get_mission_stats(db_session: AsyncSession, sample_mission):
    """Verifica estadísticas de misiones."""
    # Crear user missions
    user_mission1 = UserMission(
        user_id=100,
        mission_id=sample_mission.id,
        progress="{}",
        status=MissionStatus.IN_PROGRESS,
        started_at=datetime.now(UTC)
    )
    user_mission2 = UserMission(
        user_id=200,
        mission_id=sample_mission.id,
        progress="{}",
        status=MissionStatus.COMPLETED,
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC)
    )
    db_session.add_all([user_mission1, user_mission2])
    await db_session.commit()

    # Obtener estadísticas
    stats_service = StatsService(db_session)
    mission_stats = await stats_service.get_mission_stats()

    assert mission_stats['total_starts'] == 2
    assert mission_stats['total_completions'] == 1
    assert mission_stats['completion_rate'] == 50.0


@pytest.mark.asyncio
async def test_get_engagement_stats_empty(db_session: AsyncSession):
    """Verifica estadísticas de engagement con datos vacíos."""
    stats_service = StatsService(db_session)
    engagement = await stats_service.get_engagement_stats()

    assert engagement['total_reactions'] == 0
    assert engagement['reactions_7d'] == 0
    assert engagement['avg_reactions_per_user'] == 0
    assert engagement['top_emojis'] == {}
    assert engagement['active_streaks'] == 0
    assert engagement['longest_streak'] == 0


@pytest.mark.asyncio
async def test_get_engagement_stats_with_data(db_session: AsyncSession, sample_reaction):
    """Verifica estadísticas de engagement con datos."""
    # Crear usuario
    besito_service = BesitoService(db_session)
    await besito_service.grant_besitos(
        user_id=100, amount=10, transaction_type=TransactionType.REACTION, description="test"
    )

    # Crear otra reacción para tener dos emojis diferentes
    from bot.gamification.services.reaction import ReactionService
    reaction_service = ReactionService(db_session)
    reaction2 = await reaction_service.create_reaction(
        emoji="🔥", besitos_value=5
    )

    # Crear reacciones de usuario (solo campos que existen en el modelo)
    reaction1 = UserReaction(
        user_id=100,
        reaction_id=sample_reaction.id,
        channel_id=123456,
        message_id=789012,
        reacted_at=datetime.now(UTC)
    )
    reaction_dup = UserReaction(
        user_id=100,
        reaction_id=sample_reaction.id,
        channel_id=123456,
        message_id=789013,
        reacted_at=datetime.now(UTC)
    )
    reaction3 = UserReaction(
        user_id=100,
        reaction_id=reaction2.id,
        channel_id=123456,
        message_id=789014,
        reacted_at=datetime.now(UTC) - timedelta(days=10)  # Hace 10 días
    )
    db_session.add_all([reaction1, reaction_dup, reaction3])

    # Crear racha activa
    streak = UserStreak(
        user_id=100,
        current_streak=5,
        longest_streak=10,
        last_reaction_date=datetime.now(UTC).date()
    )
    db_session.add(streak)
    await db_session.commit()

    # Obtener estadísticas
    stats_service = StatsService(db_session)
    engagement = await stats_service.get_engagement_stats()

    assert engagement['total_reactions'] == 3
    assert engagement['reactions_7d'] == 2  # Solo las de hoy
    # El emoji de sample_reaction aparece 2 veces, el de reaction2 aparece 1 vez
    assert len(engagement['top_emojis']) == 2
    assert engagement['active_streaks'] == 1
    assert engagement['longest_streak'] == 10


@pytest.mark.asyncio
async def test_stats_service_in_container(db_session: AsyncSession):
    """Verifica que StatsService se integra correctamente con el container."""
    from bot.gamification.services.container import GamificationContainer

    container = GamificationContainer(db_session)
    stats_service = container.stats

    assert stats_service is not None
    assert isinstance(stats_service, StatsService)
    assert 'stats' in container.get_loaded_services()
