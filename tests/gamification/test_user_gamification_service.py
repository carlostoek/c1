"""Tests para UserGamificationService."""

import pytest
from datetime import datetime, UTC, timedelta
from bot.gamification.services.user_gamification import UserGamificationService
from bot.gamification.database.models import (
    UserGamification, Level, UserStreak, UserReaction, Mission,
    UserMission, Reward, UserReward, Badge, UserBadge, Reaction
)
from bot.gamification.database.enums import (
    MissionType, MissionStatus, RewardType, BadgeRarity,
    ObtainedVia, TransactionType
)


# ==================================
# TESTS: INICIALIZACIÓN
# ==================================


@pytest.mark.asyncio
async def test_ensure_user_exists_creates_new(db_session):
    """Ensure user exists crea usuario nuevo."""
    service = UserGamificationService(db_session)

    # Crear nivel inicial
    level = Level(name="Novato", min_besitos=0, order=1, active=True)
    db_session.add(level)
    await db_session.commit()

    user = await service.ensure_user_exists(12345)

    assert user.user_id == 12345
    assert user.total_besitos == 0
    assert user.current_level_id == level.id


@pytest.mark.asyncio
async def test_ensure_user_exists_returns_existing(db_session, sample_user):
    """Ensure user exists retorna usuario existente."""
    service = UserGamificationService(db_session)

    user = await service.ensure_user_exists(sample_user.user_id)

    assert user.user_id == sample_user.user_id
    assert user.total_besitos == sample_user.total_besitos


@pytest.mark.asyncio
async def test_initialize_new_user(db_session):
    """Inicializar usuario nuevo completo."""
    service = UserGamificationService(db_session)

    # Crear nivel inicial
    level = Level(name="Novato", min_besitos=0, order=1, active=True)
    db_session.add(level)
    await db_session.commit()

    profile = await service.initialize_new_user(99999, username="test_user")

    assert profile['user_id'] == 99999
    assert profile['besitos']['total'] == 0
    # El perfil debe incluir streak info (aunque sea 0)
    assert 'streak' in profile
    assert profile['streak']['current'] == 0


# ==================================
# TESTS: PERFIL COMPLETO
# ==================================


@pytest.mark.asyncio
async def test_get_user_profile_complete(db_session, sample_user):
    """Obtener perfil completo con todos los datos."""
    service = UserGamificationService(db_session)

    # Crear datos adicionales
    streak = UserStreak(user_id=sample_user.user_id, current_streak=5, longest_streak=10)
    db_session.add(streak)

    # Crear reacción primero
    reaction_def = Reaction(emoji="❤️", name="Corazón", besitos_value=10, active=True)
    db_session.add(reaction_def)
    await db_session.commit()

    user_reaction = UserReaction(
        user_id=sample_user.user_id,
        channel_id=-1001234,
        message_id=1,
        reaction_id=reaction_def.id,
        reacted_at=datetime.now(UTC)
    )
    db_session.add(user_reaction)
    await db_session.commit()

    profile = await service.get_user_profile(sample_user.user_id)

    assert profile['user_id'] == sample_user.user_id
    assert 'besitos' in profile
    assert 'level' in profile
    assert 'streak' in profile
    assert 'missions' in profile
    assert 'rewards' in profile
    assert 'stats' in profile


@pytest.mark.asyncio
async def test_get_level_progress_with_next_level(db_session, sample_user):
    """Calcular progreso cuando hay siguiente nivel."""
    service = UserGamificationService(db_session)

    # Crear niveles
    level1 = Level(name="Novato", min_besitos=0, order=1, active=True)
    level2 = Level(name="Fanático", min_besitos=1000, order=2, active=True)
    db_session.add_all([level1, level2])
    await db_session.commit()

    # Usuario en nivel 1 con 500 besitos
    sample_user.current_level_id = level1.id
    sample_user.total_besitos = 500
    await db_session.commit()

    progress = await service._get_level_progress(sample_user.user_id)

    assert progress['current'].name == "Novato"
    assert progress['next'].name == "Fanático"
    assert progress['progress_percentage'] == 50.0
    assert progress['besitos_to_next'] == 500


@pytest.mark.asyncio
async def test_get_level_progress_no_next_level(db_session, sample_user):
    """Progreso cuando no hay siguiente nivel."""
    service = UserGamificationService(db_session)

    # Solo un nivel
    level = Level(name="Maestro", min_besitos=0, order=1, active=True)
    db_session.add(level)
    await db_session.commit()

    sample_user.current_level_id = level.id
    await db_session.commit()

    progress = await service._get_level_progress(sample_user.user_id)

    assert progress['current'].name == "Maestro"
    assert progress['next'] is None
    assert progress['besitos_to_next'] is None


# ==================================
# TESTS: RESÚMENES
# ==================================


@pytest.mark.asyncio
async def test_get_profile_summary(db_session, sample_user):
    """Generar resumen formateado."""
    service = UserGamificationService(db_session)

    # Crear nivel
    level = Level(name="Fanático", min_besitos=0, order=1, active=True)
    db_session.add(level)
    await db_session.commit()

    sample_user.current_level_id = level.id
    sample_user.total_besitos = 1500
    await db_session.commit()

    # Crear streak
    streak = UserStreak(user_id=sample_user.user_id, current_streak=7, longest_streak=15)
    db_session.add(streak)
    await db_session.commit()

    summary = await service.get_profile_summary(sample_user.user_id)

    assert "👤" in summary
    assert "Fanático" in summary
    assert "1,500" in summary
    # Verificar que incluye racha
    assert "🔥" in summary
    assert "días" in summary


@pytest.mark.asyncio
async def test_get_profile_summary_with_badges(db_session, sample_user):
    """Resumen incluyendo badges mostrados."""
    service = UserGamificationService(db_session)

    # Crear nivel
    level = Level(name="Novato", min_besitos=0, order=1, active=True)
    db_session.add(level)
    sample_user.current_level_id = level.id
    await db_session.commit()

    # Crear badge
    reward = Reward(
        name="Primer Paso",
        description="Test",
        reward_type=RewardType.BADGE.value,
        active=True,
        created_by=999
    )
    db_session.add(reward)
    await db_session.commit()
    await db_session.refresh(reward)

    badge = Badge(id=reward.id, icon="🏆", rarity=BadgeRarity.COMMON.value)
    db_session.add(badge)

    user_reward = UserReward(
        user_id=sample_user.user_id,
        reward_id=reward.id,
        obtained_at=datetime.now(UTC),
        obtained_via=ObtainedVia.ADMIN_GRANT.value
    )
    db_session.add(user_reward)
    await db_session.commit()
    await db_session.refresh(user_reward)

    user_badge = UserBadge(id=user_reward.id, displayed=True)
    db_session.add(user_badge)
    await db_session.commit()

    summary = await service.get_profile_summary(sample_user.user_id)

    assert "🏆" in summary
    assert "Primer Paso" in summary


@pytest.mark.asyncio
async def test_get_leaderboard_position(db_session, sample_user):
    """Obtener posición en leaderboard."""
    service = UserGamificationService(db_session)

    # Crear otros usuarios con más besitos
    user2 = UserGamification(user_id=22222, total_besitos=2000)
    user3 = UserGamification(user_id=33333, total_besitos=3000)
    db_session.add_all([user2, user3])

    sample_user.total_besitos = 1000
    await db_session.commit()

    position = await service.get_leaderboard_position(sample_user.user_id)

    assert position['besitos_rank'] == 3
    assert position['total_users'] == 3


# ==================================
# TESTS: ESTADÍSTICAS
# ==================================


@pytest.mark.asyncio
async def test_get_user_stats_reactions(db_session, sample_user):
    """Estadísticas de reacciones."""
    service = UserGamificationService(db_session)

    # Crear definiciones de reacciones
    r1 = Reaction(emoji="❤️", name="Corazón", besitos_value=10, active=True)
    r2 = Reaction(emoji="🔥", name="Fuego", besitos_value=10, active=True)
    db_session.add_all([r1, r2])
    await db_session.commit()

    # Crear user reactions
    reactions = [
        UserReaction(
            user_id=sample_user.user_id,
            channel_id=-1001234,
            message_id=i,
            reaction_id=r1.id if i % 2 == 0 else r2.id,
            reacted_at=datetime.now(UTC) - timedelta(days=i)
        )
        for i in range(1, 11)
    ]
    db_session.add_all(reactions)
    await db_session.commit()

    stats = await service.get_user_stats(sample_user.user_id)

    assert stats['reactions']['total'] == 10
    assert stats['reactions']['by_emoji']['❤️'] == 5
    assert stats['reactions']['by_emoji']['🔥'] == 5
    assert stats['reactions']['avg_per_day'] > 0


@pytest.mark.asyncio
async def test_get_user_stats_besitos(db_session, sample_user):
    """Estadísticas de besitos."""
    service = UserGamificationService(db_session)

    # Sin BesitoTransaction, solo actualizamos totales
    sample_user.besitos_earned = 600
    sample_user.besitos_spent = 100
    await db_session.commit()

    stats = await service.get_user_stats(sample_user.user_id)

    assert stats['besitos']['total_earned'] == 600
    assert stats['besitos']['total_spent'] == 100
    # from_reactions y from_missions requieren BesitoTransaction
    assert stats['besitos']['from_reactions'] == 0
    assert stats['besitos']['from_missions'] == 0


@pytest.mark.asyncio
async def test_get_user_stats_missions(db_session, sample_user):
    """Estadísticas de misiones."""
    service = UserGamificationService(db_session)

    # Crear misiones
    mission1 = Mission(
        name="M1", description="T", mission_type=MissionType.ONE_TIME.value,
        criteria='{}', besitos_reward=100, active=True, created_by=999
    )
    mission2 = Mission(
        name="M2", description="T", mission_type=MissionType.ONE_TIME.value,
        criteria='{}', besitos_reward=100, active=True, created_by=999
    )
    db_session.add_all([mission1, mission2])
    await db_session.commit()

    # Crear user missions
    um1 = UserMission(
        user_id=sample_user.user_id,
        mission_id=mission1.id,
        status=MissionStatus.CLAIMED.value,
        progress='{}',
        started_at=datetime.now(UTC)
    )
    um2 = UserMission(
        user_id=sample_user.user_id,
        mission_id=mission2.id,
        status=MissionStatus.IN_PROGRESS.value,
        progress='{}',
        started_at=datetime.now(UTC)
    )
    db_session.add_all([um1, um2])
    await db_session.commit()

    stats = await service.get_user_stats(sample_user.user_id)

    assert stats['missions']['total_completed'] == 1
    assert stats['missions']['completion_rate'] == 50.0


@pytest.mark.asyncio
async def test_get_user_stats_activity(db_session, sample_user):
    """Estadísticas de actividad."""
    service = UserGamificationService(db_session)

    # Crear definición de reacción
    reaction_def = Reaction(emoji="❤️", name="Corazón", besitos_value=10, active=True)
    db_session.add(reaction_def)
    await db_session.commit()

    # Crear reacciones en diferentes días
    now = datetime.now(UTC)
    reactions = [
        UserReaction(
            user_id=sample_user.user_id,
            channel_id=-1001234,
            message_id=i,
            reaction_id=reaction_def.id,
            reacted_at=now - timedelta(days=i)
        )
        for i in range(5)
    ]
    db_session.add_all(reactions)
    await db_session.commit()

    stats = await service.get_user_stats(sample_user.user_id)

    assert stats['activity']['days_since_start'] >= 4
    assert stats['activity']['active_days'] == 5
    assert stats['activity']['first_seen'] is not None
    assert stats['activity']['last_active'] is not None
