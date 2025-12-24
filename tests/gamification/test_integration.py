"""
Tests de integración end-to-end del módulo de gamificación.
"""

import pytest
from datetime import datetime, timedelta, UTC
from sqlalchemy import select

from bot.gamification.services.container import GamificationContainer
from bot.gamification.database.models import (
    UserGamification, UserStreak, Mission, Level, Reward, UserMission
)
from bot.gamification.database.enums import (
    MissionType, MissionStatus, RewardType, TransactionType
)


@pytest.mark.asyncio
async def test_complete_gamification_flow(db_session):
    """Test flujo completo: reacción → besitos → level-up → misión → recompensa."""
    container = GamificationContainer(db_session)

    # Setup: crear usuario
    user_id = 12345
    await container.user_gamification.initialize_new_user(user_id)

    # Setup: crear nivel
    level_2 = await container.level.create_level(
        name="Nivel 2",
        min_besitos=100,
        order=2
    )

    # Setup: crear misión
    mission = await container.mission.create_mission(
        name="Test Mission",
        description="Test",
        mission_type=MissionType.DAILY,
        criteria={"type": "daily", "count": 1},
        besitos_reward=50
    )

    # Setup: crear reacción activa
    await container.reaction.create_reaction(emoji="❤️", besitos_value=5)

    # Setup: crear recompensa
    reward = await container.reward.create_reward(
        name="Test Reward",
        description="Test",
        reward_type=RewardType.BADGE,
        reward_metadata={"icon": "🏆", "rarity": "common"},
        unlock_conditions={"type": "level", "level_id": level_2.id}
    )

    # 1. Usuario reacciona
    success, msg, besitos = await container.reaction.record_reaction(
        user_id=user_id,
        emoji="❤️",
        channel_id=-1001234,
        message_id=1
    )
    assert success
    assert besitos > 0

    # 2. Verificar besitos
    user = await db_session.get(UserGamification, user_id)
    assert user.total_besitos > 0

    # 3. Dar más besitos para level-up
    await container.besito.grant_besitos(
        user_id, 100, TransactionType.ADMIN_GRANT, "test level-up"
    )

    # 4. Verificar level-up
    changed, old, new = await container.level.check_and_apply_level_up(user_id)
    assert changed
    assert new.id == level_2.id

    # 5. Verificar recompensa desbloqueada
    can_unlock, reason = await container.reward.check_unlock_conditions(user_id, reward.id)
    assert can_unlock

    # 6. Iniciar y completar misión
    user_mission = await container.mission.start_mission(user_id, mission.id)
    assert user_mission.status == MissionStatus.IN_PROGRESS

    # Simular completar
    user_mission.status = MissionStatus.COMPLETED
    await db_session.commit()

    # 7. Reclamar recompensa
    success, msg, info = await container.mission.claim_reward(user_id, mission.id)
    assert success


@pytest.mark.asyncio
async def test_streak_progression(db_session):
    """Test que el sistema de rachas se inicializa y rastrea correctamente."""
    container = GamificationContainer(db_session)
    user_id = 12345

    await container.user_gamification.initialize_new_user(user_id)

    # Crear reacción activa
    await container.reaction.create_reaction(emoji="🔥", besitos_value=1)

    # Primera reacción del usuario
    success1, msg1, besitos1 = await container.reaction.record_reaction(
        user_id=user_id,
        emoji="🔥",
        channel_id=-1001234,
        message_id=100
    )
    assert success1

    # Verificar que se creó el registro de racha
    stmt = select(UserStreak).where(UserStreak.user_id == user_id)
    result = await db_session.execute(stmt)
    streak = result.scalar_one_or_none()

    assert streak is not None
    assert streak.current_streak >= 1
    assert streak.longest_streak >= 1
    assert streak.last_reaction_date is not None

    # Segunda reacción (mismo día, debería mantener racha)
    success2, msg2, besitos2 = await container.reaction.record_reaction(
        user_id=user_id,
        emoji="🔥",
        channel_id=-1001234,
        message_id=101
    )
    assert success2

    # Refresh y verificar que la racha se mantiene
    await db_session.refresh(streak)
    assert streak.current_streak >= 1
    assert streak.longest_streak >= 1


@pytest.mark.asyncio
async def test_daily_mission_completion(db_session):
    """Test completar misión diaria."""
    container = GamificationContainer(db_session)
    user_id = 12345

    await container.user_gamification.initialize_new_user(user_id)

    # Crear reacción activa
    await container.reaction.create_reaction(emoji="❤️", besitos_value=1)

    # Crear misión diaria (5 reacciones)
    mission = await container.mission.create_mission(
        name="Reactor Diario",
        description="5 reacciones",
        mission_type=MissionType.DAILY,
        criteria={"type": "daily", "count": 5},
        besitos_reward=200
    )

    # Iniciar
    user_mission = await container.mission.start_mission(user_id, mission.id)

    # Reaccionar 5 veces
    for i in range(5):
        await container.reaction.record_reaction(
            user_id=user_id,
            emoji="❤️",
            channel_id=-1001234,
            message_id=200+i
        )

        # Actualizar progreso
        await container.mission.on_user_reaction(
            user_id=user_id,
            emoji="❤️",
            reacted_at=datetime.now(UTC)
        )

    # Verificar completada
    await db_session.refresh(user_mission)
    assert user_mission.status == MissionStatus.COMPLETED


@pytest.mark.asyncio
async def test_configuration_orchestrator(db_session):
    """Test orchestrator crea configuración completa."""
    container = GamificationContainer(db_session)

    config = {
        'mission': {
            'name': "Test Complete",
            'description': "Test",
            'mission_type': MissionType.ONE_TIME,
            'criteria': {"type": "one_time"},
            'besitos_reward': 100
        },
        'auto_level': {
            'name': "Test Level",
            'min_besitos': 100,
            'order': 10
        },
        'rewards': [
            {
                'name': "Test Badge",
                'description': "Test",
                'reward_type': RewardType.BADGE,
                'metadata': {"icon": "🎯", "rarity": "common"}
            }
        ]
    }

    result = await container.configuration_orchestrator.create_complete_mission_system(
        config=config,
        created_by=1
    )

    # Verificar que no hay errores de validación
    assert 'validation_errors' not in result or result['validation_errors'] == []
    assert result['mission'] is not None
    assert result['created_level'] is not None
    assert len(result['created_rewards']) == 1
    assert 'summary' in result


@pytest.mark.asyncio
async def test_reward_unlock_by_level(db_session):
    """Test recompensa bloqueada por nivel → usuario sube nivel → se desbloquea."""
    container = GamificationContainer(db_session)
    user_id = 12345

    # Setup: crear usuario
    await container.user_gamification.initialize_new_user(user_id)

    # Setup: crear niveles
    level_1 = await container.level.create_level(
        name="Nivel 1",
        min_besitos=0,
        order=1
    )

    level_2 = await container.level.create_level(
        name="Nivel 2",
        min_besitos=100,
        order=2
    )

    # Setup: crear recompensa bloqueada por nivel 2
    reward = await container.reward.create_reward(
        name="Recompensa Nivel 2",
        description="Solo disponible en nivel 2",
        reward_type=RewardType.BADGE,
        reward_metadata={"icon": "🏆", "rarity": "rare"},
        unlock_conditions={"type": "level", "level_id": level_2.id}
    )

    # 1. Verificar que está bloqueada en nivel 1
    can_unlock, reason = await container.reward.check_unlock_conditions(user_id, reward.id)
    assert not can_unlock
    assert "nivel" in reason.lower() or "level" in reason.lower()

    # 2. Dar besitos para level-up
    await container.besito.grant_besitos(
        user_id, 100, TransactionType.ADMIN_GRANT, "test level-up"
    )

    # 3. Aplicar level-up
    changed, old, new = await container.level.check_and_apply_level_up(user_id)
    assert changed
    assert new.id == level_2.id

    # 4. Verificar que ahora está desbloqueada
    can_unlock, reason = await container.reward.check_unlock_conditions(user_id, reward.id)
    assert can_unlock
