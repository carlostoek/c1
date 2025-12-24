"""Tests para MissionService."""

import pytest
from datetime import datetime, UTC, timedelta
from bot.gamification.services.mission import MissionService
from bot.gamification.database.models import (
    Mission, UserMission, UserGamification, UserStreak, Level
)
from bot.gamification.database.enums import MissionType, MissionStatus


# ========================================
# TESTS: CRUD MISIONES
# ========================================


@pytest.mark.asyncio
async def test_create_mission_streak(db_session):
    """Crear misión tipo STREAK exitosamente."""
    service = MissionService(db_session)

    mission = await service.create_mission(
        name="Racha 7 días",
        description="Completa 7 días consecutivos",
        mission_type=MissionType.STREAK,
        criteria={"type": "streak", "days": 7},
        besitos_reward=500,
        created_by=999
    )

    assert mission.id is not None
    assert mission.name == "Racha 7 días"
    assert mission.mission_type == MissionType.STREAK.value
    assert mission.besitos_reward == 500
    assert mission.active is True


@pytest.mark.asyncio
async def test_create_mission_daily(db_session):
    """Crear misión tipo DAILY."""
    service = MissionService(db_session)

    mission = await service.create_mission(
        name="5 reacciones diarias",
        description="Reacciona 5 veces hoy",
        mission_type=MissionType.DAILY,
        criteria={"type": "daily", "count": 5, "specific_reaction": "❤️"},
        besitos_reward=100,
        created_by=999
    )

    assert mission.mission_type == MissionType.DAILY.value
    assert '\"count\": 5' in mission.criteria
    # El emoji se escapa como unicode en JSON (normal)
    assert '"specific_reaction"' in mission.criteria


@pytest.mark.asyncio
async def test_update_mission(db_session):
    """Actualizar misión existente."""
    service = MissionService(db_session)

    mission = await service.create_mission(
        name="Test",
        description="Original",
        mission_type=MissionType.ONE_TIME,
        criteria={},
        besitos_reward=100,
        created_by=999
    )

    updated = await service.update_mission(
        mission.id,
        description="Updated description",
        besitos_reward=200
    )

    assert updated.description == "Updated description"
    assert updated.besitos_reward == 200
    assert updated.name == "Test"  # No cambió


@pytest.mark.asyncio
async def test_delete_mission(db_session):
    """Soft-delete de misión."""
    service = MissionService(db_session)

    mission = await service.create_mission(
        name="Test",
        description="Test",
        mission_type=MissionType.ONE_TIME,
        criteria={},
        besitos_reward=100,
        created_by=999
    )

    result = await service.delete_mission(mission.id)
    assert result is True

    # Verificar soft-delete
    deleted = await service.get_mission_by_id(mission.id)
    assert deleted.active is False


@pytest.mark.asyncio
async def test_get_all_missions_active_only(db_session):
    """Obtener solo misiones activas."""
    service = MissionService(db_session)

    await service.create_mission(
        "Active", "Active", MissionType.ONE_TIME, {}, 100, created_by=999
    )
    mission2 = await service.create_mission(
        "To Delete", "To Delete", MissionType.ONE_TIME, {}, 100, created_by=999
    )
    await service.delete_mission(mission2.id)

    missions = await service.get_all_missions(active_only=True)
    assert len(missions) == 1
    assert missions[0].name == "Active"


# ========================================
# TESTS: USER MISSIONS
# ========================================


@pytest.mark.asyncio
async def test_start_mission_success(db_session, sample_user):
    """Iniciar misión exitosamente."""
    service = MissionService(db_session)

    mission = await service.create_mission(
        "Test", "Test", MissionType.ONE_TIME, {}, 100, created_by=999
    )

    user_mission = await service.start_mission(sample_user.user_id, mission.id)

    assert user_mission.user_id == sample_user.user_id
    assert user_mission.mission_id == mission.id
    assert user_mission.status == MissionStatus.IN_PROGRESS.value
    assert user_mission.started_at is not None


@pytest.mark.asyncio
async def test_start_mission_duplicate_non_repeatable(db_session, sample_user):
    """No permitir duplicados en misiones no repetibles."""
    service = MissionService(db_session)

    mission = await service.create_mission(
        "Test", "Test", MissionType.ONE_TIME, {}, 100, repeatable=False, created_by=999
    )

    await service.start_mission(sample_user.user_id, mission.id)

    with pytest.raises(ValueError, match="already in progress"):
        await service.start_mission(sample_user.user_id, mission.id)


@pytest.mark.asyncio
async def test_start_mission_repeatable_allows_duplicate(db_session, sample_user):
    """Permitir reinicio de misiones repetibles."""
    service = MissionService(db_session)

    mission = await service.create_mission(
        "Daily", "Daily", MissionType.DAILY, {"count": 5}, 100, repeatable=True, created_by=999
    )

    user_mission1 = await service.start_mission(sample_user.user_id, mission.id)
    # Marcar como completada
    user_mission1.status = MissionStatus.CLAIMED.value
    await db_session.commit()

    # Debería permitir reiniciar
    user_mission2 = await service.start_mission(sample_user.user_id, mission.id)
    assert user_mission2.id != user_mission1.id


@pytest.mark.asyncio
async def test_get_user_missions_by_status(db_session, sample_user):
    """Obtener misiones de usuario filtradas por estado."""
    service = MissionService(db_session)

    mission1 = await service.create_mission(
        "M1", "M1", MissionType.ONE_TIME, {}, 100, created_by=999
    )
    mission2 = await service.create_mission(
        "M2", "M2", MissionType.ONE_TIME, {}, 100, created_by=999
    )

    um1 = await service.start_mission(sample_user.user_id, mission1.id)
    um2 = await service.start_mission(sample_user.user_id, mission2.id)

    # Completar primera
    um1.status = MissionStatus.COMPLETED.value
    await db_session.commit()

    # Obtener IN_PROGRESS
    in_progress = await service.get_user_missions(
        sample_user.user_id, status=MissionStatus.IN_PROGRESS
    )
    assert len(in_progress) == 1
    assert in_progress[0].mission_id == mission2.id


@pytest.mark.asyncio
async def test_get_available_missions(db_session, sample_user):
    """Obtener misiones disponibles para usuario."""
    service = MissionService(db_session)

    # Misión completada no repetible
    m1 = await service.create_mission(
        "M1", "M1", MissionType.ONE_TIME, {}, 100, repeatable=False, created_by=999
    )
    um1 = await service.start_mission(sample_user.user_id, m1.id)
    um1.status = MissionStatus.CLAIMED.value
    await db_session.commit()

    # Misión repetible completada
    m2 = await service.create_mission(
        "M2", "M2", MissionType.DAILY, {"count": 5}, 100, repeatable=True, created_by=999
    )
    um2 = await service.start_mission(sample_user.user_id, m2.id)
    um2.status = MissionStatus.CLAIMED.value
    await db_session.commit()

    # Misión nueva
    m3 = await service.create_mission(
        "M3", "M3", MissionType.ONE_TIME, {}, 100, created_by=999
    )

    available = await service.get_available_missions(sample_user.user_id)

    # Debe incluir M2 (repetible) y M3 (nueva)
    # No debe incluir M1 (completada y no repetible)
    assert len(available) == 2
    mission_ids = [m.id for m in available]
    assert m2.id in mission_ids
    assert m3.id in mission_ids
    assert m1.id not in mission_ids


# ========================================
# TESTS: PROGRESO STREAK
# ========================================


@pytest.mark.asyncio
async def test_update_streak_progress_success(db_session, sample_user):
    """Actualizar progreso de misión STREAK."""
    service = MissionService(db_session)

    mission = await service.create_mission(
        "Racha 7", "7 días", MissionType.STREAK, {"days": 7}, 500, created_by=999
    )
    user_mission = await service.start_mission(sample_user.user_id, mission.id)

    # Crear racha del usuario
    streak = UserStreak(user_id=sample_user.user_id, current_streak=5, longest_streak=5)
    db_session.add(streak)
    await db_session.commit()

    # Actualizar progreso
    completed = await service._update_streak_progress(user_mission, streak, mission)

    assert completed is False  # 5 < 7
    assert user_mission.status == MissionStatus.IN_PROGRESS.value

    # Incrementar racha a 7
    streak.current_streak = 7
    await db_session.commit()

    completed = await service._update_streak_progress(user_mission, streak, mission)

    assert completed is True
    assert user_mission.status == MissionStatus.COMPLETED.value
    assert user_mission.completed_at is not None


# ========================================
# TESTS: PROGRESO DAILY
# ========================================


@pytest.mark.asyncio
async def test_update_daily_progress_success(db_session, sample_user):
    """Actualizar progreso de misión DAILY."""
    service = MissionService(db_session)

    mission = await service.create_mission(
        "5 reacciones", "5 al día", MissionType.DAILY,
        {"count": 5, "specific_reaction": None}, 100, created_by=999
    )
    user_mission = await service.start_mission(sample_user.user_id, mission.id)

    now = datetime.now(UTC)

    # 4 reacciones (no completa)
    for _ in range(4):
        await service._update_daily_progress(user_mission, "❤️", now, mission)

    assert user_mission.status == MissionStatus.IN_PROGRESS.value

    # 5ta reacción (completa)
    completed = await service._update_daily_progress(user_mission, "❤️", now, mission)

    assert completed is True
    assert user_mission.status == MissionStatus.COMPLETED.value


@pytest.mark.asyncio
async def test_update_daily_progress_specific_emoji(db_session, sample_user):
    """Misión DAILY con emoji específico."""
    service = MissionService(db_session)

    mission = await service.create_mission(
        "5 corazones", "5 ❤️", MissionType.DAILY,
        {"count": 5, "specific_reaction": "❤️"}, 100, created_by=999
    )
    user_mission = await service.start_mission(sample_user.user_id, mission.id)

    now = datetime.now(UTC)

    # Reacción incorrecta (no cuenta)
    await service._update_daily_progress(user_mission, "👍", now, mission)
    progress = eval(user_mission.progress)
    assert progress.get('reactions_today', 0) == 0

    # Reacción correcta (cuenta)
    await service._update_daily_progress(user_mission, "❤️", now, mission)
    progress = eval(user_mission.progress)
    assert progress['reactions_today'] == 1


@pytest.mark.asyncio
async def test_update_daily_progress_reset_on_new_day(db_session, sample_user):
    """Progreso DAILY resetea al cambiar de día."""
    service = MissionService(db_session)

    mission = await service.create_mission(
        "5 reacciones", "5 al día", MissionType.DAILY,
        {"count": 5, "specific_reaction": None}, 100, created_by=999
    )
    user_mission = await service.start_mission(sample_user.user_id, mission.id)

    today = datetime.now(UTC)
    tomorrow = today + timedelta(days=1)

    # 3 reacciones hoy
    for _ in range(3):
        await service._update_daily_progress(user_mission, "❤️", today, mission)

    progress = eval(user_mission.progress)
    assert progress['reactions_today'] == 3

    # 1 reacción mañana (resetea)
    await service._update_daily_progress(user_mission, "❤️", tomorrow, mission)

    progress = eval(user_mission.progress)
    assert progress['reactions_today'] == 1


# ========================================
# TESTS: PROGRESO WEEKLY
# ========================================


@pytest.mark.asyncio
async def test_update_weekly_progress_success(db_session, sample_user):
    """Actualizar progreso de misión WEEKLY."""
    service = MissionService(db_session)

    mission = await service.create_mission(
        "50 semanal", "50 en semana", MissionType.WEEKLY,
        {"target": 50, "specific_days": None}, 200, created_by=999
    )
    user_mission = await service.start_mission(sample_user.user_id, mission.id)

    now = datetime.now(UTC)

    # 49 reacciones (no completa)
    for _ in range(49):
        await service._update_weekly_progress(user_mission, "❤️", now, mission)

    assert user_mission.status == MissionStatus.IN_PROGRESS.value

    # 50va reacción (completa)
    completed = await service._update_weekly_progress(user_mission, "❤️", now, mission)

    assert completed is True
    assert user_mission.status == MissionStatus.COMPLETED.value


# ========================================
# TESTS: CLAIM REWARD
# ========================================


@pytest.mark.asyncio
async def test_claim_reward_success(db_session, sample_user, sample_level):
    """Reclamar recompensa exitosamente."""
    service = MissionService(db_session)

    mission = await service.create_mission(
        "Test", "Test", MissionType.ONE_TIME, {}, 500, created_by=999
    )
    user_mission = await service.start_mission(sample_user.user_id, mission.id)

    # Marcar como completada
    user_mission.status = MissionStatus.COMPLETED.value
    user_mission.completed_at = datetime.now(UTC)
    await db_session.commit()

    # Reclamar
    success, message, rewards = await service.claim_reward(
        sample_user.user_id, mission.id
    )

    assert success is True
    assert "500" in message
    assert rewards['besitos'] == 500

    # Verificar estado
    await db_session.refresh(user_mission)
    assert user_mission.status == MissionStatus.CLAIMED.value
    assert user_mission.claimed_at is not None


@pytest.mark.asyncio
async def test_claim_reward_not_completed(db_session, sample_user):
    """No permitir reclamar si no está completada."""
    service = MissionService(db_session)

    mission = await service.create_mission(
        "Test", "Test", MissionType.ONE_TIME, {}, 100, created_by=999
    )
    user_mission = await service.start_mission(sample_user.user_id, mission.id)

    # Intentar reclamar (IN_PROGRESS)
    success, message, _ = await service.claim_reward(
        sample_user.user_id, mission.id
    )

    assert success is False
    assert "not completed" in message


@pytest.mark.asyncio
async def test_claim_reward_already_claimed(db_session, sample_user):
    """No permitir reclamar dos veces."""
    service = MissionService(db_session)

    mission = await service.create_mission(
        "Test", "Test", MissionType.ONE_TIME, {}, 100, created_by=999
    )
    user_mission = await service.start_mission(sample_user.user_id, mission.id)

    # Completar y reclamar
    user_mission.status = MissionStatus.COMPLETED.value
    user_mission.completed_at = datetime.now(UTC)
    await db_session.commit()

    await service.claim_reward(sample_user.user_id, mission.id)

    # Intentar reclamar de nuevo
    success, message, _ = await service.claim_reward(
        sample_user.user_id, mission.id
    )

    assert success is False
    assert "already claimed" in message


@pytest.mark.asyncio
async def test_claim_reward_with_level_up(db_session, sample_user):
    """Reclamar recompensa con level-up automático."""
    service = MissionService(db_session)

    # Crear nivel
    level = Level(name="Expert", min_besitos=1000, order=3, active=True)
    db_session.add(level)
    await db_session.commit()

    mission = await service.create_mission(
        "Level Up Mission", "Test", MissionType.ONE_TIME, {},
        500, auto_level_up_id=level.id, created_by=999
    )
    user_mission = await service.start_mission(sample_user.user_id, mission.id)

    # Completar
    user_mission.status = MissionStatus.COMPLETED.value
    user_mission.completed_at = datetime.now(UTC)
    await db_session.commit()

    # Reclamar
    success, _, rewards = await service.claim_reward(
        sample_user.user_id, mission.id
    )

    assert success is True
    assert rewards['level_up'] is not None
    assert rewards['level_up'].name == "Expert"

    # Verificar que usuario cambió de nivel
    await db_session.refresh(sample_user)
    assert sample_user.current_level_id == level.id


# ========================================
# TESTS: ON_USER_REACTION HOOK
# ========================================


@pytest.mark.asyncio
async def test_on_user_reaction_updates_missions(db_session, sample_user):
    """Hook on_user_reaction actualiza progreso de misiones activas."""
    service = MissionService(db_session)

    mission = await service.create_mission(
        "5 daily", "Test", MissionType.DAILY,
        {"count": 5, "specific_reaction": None}, 100, created_by=999
    )
    await service.start_mission(sample_user.user_id, mission.id)

    now = datetime.now(UTC)

    # Simular 5 reacciones
    for _ in range(5):
        await service.on_user_reaction(sample_user.user_id, "❤️", now)

    # Verificar que se completó
    user_missions = await service.get_user_missions(sample_user.user_id)
    assert len(user_missions) == 1
    assert user_missions[0].status == MissionStatus.COMPLETED.value
