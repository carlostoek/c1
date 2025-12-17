"""
Tests para MissionsService - Servicio de gestión de misiones.

Casos cubiertos:
- Obtener misiones disponibles
- Tracking de progreso
- Reset automático
- Completado de misiones
- Límites temporales (daily, weekly, permanent)
"""
import pytest
from datetime import datetime, timezone, timedelta

from bot.database.models import (
    Mission, UserMission, MissionType, ObjectiveType, User
)
from bot.services.missions import MissionsService


@pytest.fixture
async def missions_service(session):
    """Crea una instancia de MissionsService."""
    return MissionsService(session)


@pytest.fixture
async def sample_user(session):
    """Crea un usuario de prueba."""
    from sqlalchemy import select

    result = await session.execute(select(User).where(User.user_id == 54321))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            user_id=54321,
            first_name="Test",
            last_name="Mission",
            role="FREE"
        )
        session.add(user)
        await session.flush()

    return user


@pytest.fixture
async def sample_mission(session):
    """Crea una misión de prueba."""
    mission = Mission(
        name="Test Mission",
        description="Test description",
        icon="🎯",
        mission_type=MissionType.PERMANENT,
        objective_type=ObjectiveType.POINTS,
        objective_value=100,
        required_level=1,
        is_vip_only=False,
        is_active=True
    )
    session.add(mission)
    await session.flush()
    return mission


class TestMissionsServiceGetActive:
    """Tests para get_active_missions()."""

    async def test_get_active_missions_returns_list(
        self, missions_service, sample_user, sample_mission, session
    ):
        """Verifica que retorna una lista de misiones."""
        missions = await missions_service.get_active_missions(sample_user.user_id)

        assert isinstance(missions, list)

    async def test_get_active_missions_filters_inactive(
        self, missions_service, sample_user, session
    ):
        """Verifica que filtra misiones inactivas."""
        # Crear misión inactiva
        inactive = Mission(
            name="Inactive",
            description="Test",
            icon="🎯",
            mission_type=MissionType.PERMANENT,
            objective_type=ObjectiveType.POINTS,
            objective_value=50,
            is_active=False
        )
        session.add(inactive)
        await session.flush()

        missions = await missions_service.get_active_missions(sample_user.user_id)

        # Solo activas
        assert all(m.is_active for m in missions)

    async def test_get_active_missions_filters_by_type(
        self, missions_service, sample_user, session
    ):
        """Verifica que filtra por tipo de misión."""
        # Crear misión daily
        daily = Mission(
            name="Daily",
            description="Test",
            icon="🎯",
            mission_type=MissionType.DAILY,
            objective_type=ObjectiveType.POINTS,
            objective_value=100,
            is_active=True
        )
        session.add(daily)
        await session.flush()

        missions = await missions_service.get_active_missions(
            sample_user.user_id,
            mission_type=MissionType.DAILY
        )

        # Solo daily
        assert all(m.mission_type == MissionType.DAILY for m in missions)


class TestMissionsServiceGetOrCreate:
    """Tests para get_or_create_user_mission()."""

    async def test_get_or_create_creates_if_not_exists(
        self, missions_service, sample_user, sample_mission
    ):
        """Verifica que crea UserMission si no existe."""
        um = await missions_service.get_or_create_user_mission(
            sample_user.user_id,
            sample_mission.id
        )

        assert um is not None
        assert um.user_id == sample_user.user_id
        assert um.mission_id == sample_mission.id
        assert um.current_progress == 0
        assert um.is_completed == False

    async def test_get_or_create_returns_existing(
        self, missions_service, sample_user, sample_mission, session
    ):
        """Verifica que retorna UserMission existente."""
        # Crear uno
        um1 = await missions_service.get_or_create_user_mission(
            sample_user.user_id,
            sample_mission.id
        )

        # Obtener el mismo
        um2 = await missions_service.get_or_create_user_mission(
            sample_user.user_id,
            sample_mission.id
        )

        assert um1.id == um2.id


class TestMissionsServiceShouldReset:
    """Tests para UserMission.should_reset()."""

    async def test_should_reset_permanent_never(
        self, missions_service, sample_user, session
    ):
        """Verifica que misiones permanentes nunca se resetean."""
        perm_mission = Mission(
            name="Perm",
            description="Test",
            icon="🎯",
            mission_type=MissionType.PERMANENT,
            objective_type=ObjectiveType.POINTS,
            objective_value=100
        )
        session.add(perm_mission)
        await session.flush()

        um = await missions_service.get_or_create_user_mission(
            sample_user.user_id,
            perm_mission.id
        )

        now = datetime.now(timezone.utc)
        assert not um.should_reset(now)

    async def test_should_reset_daily_after_day(
        self, missions_service, sample_user, session
    ):
        """Verifica que daily se resetea después de 24 hrs."""
        daily_mission = Mission(
            name="Daily",
            description="Test",
            icon="🎯",
            mission_type=MissionType.DAILY,
            objective_type=ObjectiveType.POINTS,
            objective_value=100
        )
        session.add(daily_mission)
        await session.flush()

        um = await missions_service.get_or_create_user_mission(
            sample_user.user_id,
            daily_mission.id
        )

        # Simular que se reseteó ayer
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        um.last_reset_at = yesterday

        now = datetime.now(timezone.utc)
        assert um.should_reset(now)

    async def test_should_reset_daily_same_day_false(
        self, missions_service, sample_user, session
    ):
        """Verifica que daily NO se resetea el mismo día."""
        daily_mission = Mission(
            name="Daily",
            description="Test",
            icon="🎯",
            mission_type=MissionType.DAILY,
            objective_type=ObjectiveType.POINTS,
            objective_value=100
        )
        session.add(daily_mission)
        await session.flush()

        um = await missions_service.get_or_create_user_mission(
            sample_user.user_id,
            daily_mission.id
        )

        # Reseteo hace 1 hora (mismo día)
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        um.last_reset_at = one_hour_ago

        now = datetime.now(timezone.utc)
        assert not um.should_reset(now)

    async def test_should_reset_weekly_after_week(
        self, missions_service, sample_user, session
    ):
        """Verifica que weekly se resetea después de una semana."""
        weekly_mission = Mission(
            name="Weekly",
            description="Test",
            icon="🎯",
            mission_type=MissionType.WEEKLY,
            objective_type=ObjectiveType.REACTIONS,
            objective_value=10
        )
        session.add(weekly_mission)
        await session.flush()

        um = await missions_service.get_or_create_user_mission(
            sample_user.user_id,
            weekly_mission.id
        )

        # Reseteo hace 8 días
        eight_days_ago = datetime.now(timezone.utc) - timedelta(days=8)
        um.last_reset_at = eight_days_ago

        now = datetime.now(timezone.utc)
        assert um.should_reset(now)


class TestMissionsServiceUpdateProgress:
    """Tests para update_progress()."""

    async def test_update_progress_increments(
        self, missions_service, sample_user, sample_mission, session
    ):
        """Verifica que incrementa el progreso."""
        updated = await missions_service.update_progress(
            sample_user.user_id,
            ObjectiveType.POINTS,
            10
        )

        assert len(updated) > 0
        assert updated[0].current_progress == 10

    async def test_update_progress_detects_completion(
        self, missions_service, sample_user, sample_mission, session
    ):
        """Verifica que detecta cuando se completa."""
        # Actualizar exactamente hasta el objetivo
        updated = await missions_service.update_progress(
            sample_user.user_id,
            ObjectiveType.POINTS,
            100
        )

        assert len(updated) > 0
        assert updated[0].is_completed == True
        assert updated[0].completed_at is not None

    async def test_update_progress_respects_limits(
        self, missions_service, sample_user, session
    ):
        """Verifica que respeta límites de tipo de objetivo."""
        # Crear misión de reacciones
        reaction_mission = Mission(
            name="React",
            description="Test",
            icon="🎯",
            mission_type=MissionType.PERMANENT,
            objective_type=ObjectiveType.REACTIONS,
            objective_value=5
        )
        session.add(reaction_mission)
        await session.flush()

        # Actualizar con tipo diferente (POINTS en misión de REACTIONS)
        updated = await missions_service.update_progress(
            sample_user.user_id,
            ObjectiveType.POINTS,
            50
        )

        # No debe actualizar la misión de reacciones
        for um in updated:
            if um.mission_id == reaction_mission.id:
                # No debe estar entre los actualizados
                assert False, "Should not update reaction mission with points"


class TestMissionsServiceGetUser:
    """Tests para get_user_missions()."""

    async def test_get_user_missions_empty(
        self, missions_service, sample_user
    ):
        """Verifica que retorna lista vacía si no hay misiones."""
        missions = await missions_service.get_user_missions(sample_user.user_id)

        assert isinstance(missions, list)
        assert len(missions) == 0

    async def test_get_user_missions_excludes_completed(
        self, missions_service, sample_user, sample_mission, session
    ):
        """Verifica que excluye completadas por default."""
        um = await missions_service.get_or_create_user_mission(
            sample_user.user_id,
            sample_mission.id
        )
        um.is_completed = True
        await session.commit()

        missions = await missions_service.get_user_missions(sample_user.user_id)

        assert len(missions) == 0

    async def test_get_user_missions_includes_completed(
        self, missions_service, sample_user, sample_mission, session
    ):
        """Verifica que incluye completadas si se solicita."""
        um = await missions_service.get_or_create_user_mission(
            sample_user.user_id,
            sample_mission.id
        )
        um.is_completed = True
        await session.commit()

        missions = await missions_service.get_user_missions(
            sample_user.user_id,
            include_completed=True
        )

        assert len(missions) >= 1
