"""
Tests de integración end-to-end del módulo de gamificación.
"""

import pytest
from datetime import datetime, timedelta, UTC

from bot.gamification.services.container import GamificationContainer, set_container
from bot.gamification.database.models import (
    UserGamification, UserStreak, Mission, Level, Reward
)
from bot.gamification.database.enums import MissionType, MissionStatus, RewardType, BadgeRarity
from sqlalchemy import select


@pytest.mark.asyncio
async def test_complete_gamification_flow(db_session, sample_user):
    """
    Flujo: Usuario reacciona → gana besitos → sube nivel → completa misión → obtiene recompensa
    """
    container = GamificationContainer(db_session)
    set_container(container)  # Set global container for internal service access
    user_id = sample_user.user_id

    # Setup: crear reacción
    reaction = await container.reaction.create_reaction(
        emoji="❤️",
        besitos_value=1
    )

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
    
    # Setup: crear recompensa
    reward = await container.reward.create_reward(
        name="Test Reward",
        description="Test",
        reward_type=RewardType.BADGE,
        metadata={"icon": "🏆", "rarity": "common"},
        unlock_conditions={"type": "level", "level_id": level_2.id}
    )
    
    # 1. Usuario reacciona
    success, msg, besitos = await container.reaction.record_reaction(
        user_id=user_id,
        emoji="❤️",
        message_id=1,
        channel_id=-1001234
    )
    assert success
    assert besitos > 0
    
    # 2. Verificar besitos
    user = await db_session.get(UserGamification, user_id)
    assert user.total_besitos > 0
    
    # 3. Dar más besitos para level-up
    await container.besito.grant_besitos(user_id, 99, "test", "test")  # Total should be 100 (1 from reaction + 99)

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
async def test_streak_progression(db_session, sample_user):
    """
    Simula 7 días de reacciones consecutivas.
    Verifica: current_streak incrementa, longest_streak se actualiza
    """
    container = GamificationContainer(db_session)
    set_container(container)
    user_id = sample_user.user_id

    await container.reaction.create_reaction(emoji="🔥", besitos_value=1)

    # Simular 7 días de reacciones
    base_time = datetime.now(UTC) - timedelta(days=7)
    for day in range(7):
        reaction_time = base_time + timedelta(days=day)
        await container.reaction.record_reaction(
            user_id=user_id,
            emoji="🔥",
            message_id=100 + day,
            channel_id=-1001234,
            reacted_at=reaction_time
        )
    
    await db_session.commit()
    
    # Verificar racha
    stmt = select(UserStreak).where(UserStreak.user_id == user_id)
    result = await db_session.execute(stmt)
    streak = result.scalar_one_or_none()
    
    assert streak is not None
    assert streak.current_streak == 7
    assert streak.longest_streak == 7


@pytest.mark.asyncio
async def test_daily_mission_completion(db_session, sample_user, daily_mission):
    """
    Usuario reacciona 5 veces en un día → misión se completa
    """
    container = GamificationContainer(db_session)
    set_container(container)  # Set global container for internal service access
    user_id = sample_user.user_id

    # Setup: crear reacción
    await container.reaction.create_reaction(
        emoji="❤️",
        besitos_value=1
    )

    # Iniciar la misión diaria
    user_mission = await container.mission.start_mission(user_id, daily_mission.id)

    # Reaccionar 5 veces
    for i in range(5):
        await container.reaction.record_reaction(
            user_id=user_id,
            emoji="❤️",
            message_id=200+i,
            channel_id=-1001234
        )

        # Actualizar progreso de la misión
        await container.mission.on_user_reaction(
            user_id=user_id,
            emoji="❤️",
            reacted_at=datetime.now(UTC)
        )
    
    # Verificar que la misión esté completada
    await db_session.refresh(user_mission)
    assert user_mission.status == MissionStatus.COMPLETED


@pytest.mark.asyncio
async def test_reward_unlock_by_level(db_session, sample_user):
    """
    Recompensa bloqueada por nivel → usuario sube nivel → se desbloquea
    """
    container = GamificationContainer(db_session)
    set_container(container)  # Set global container for internal service access
    user_id = sample_user.user_id
    
    # Crear nivel 2 (requerido para desbloquear recompensa)
    level_2 = await container.level.create_level(
        name="Nivel 2",
        min_besitos=100,
        order=2
    )
    
    # Crear recompensa con condición de nivel
    reward = await container.reward.create_reward(
        name="Test Reward",
        description="Test",
        reward_type=RewardType.BADGE,
        metadata={"icon": "🏆", "rarity": "common"},
        unlock_conditions={"type": "level", "level_id": level_2.id}
    )
    
    # Verificar que no puede desbloquear antes de subir de nivel
    can_unlock, reason = await container.reward.check_unlock_conditions(user_id, reward.id)
    assert not can_unlock  # Usuario no ha alcanzado el nivel requerido
    
    # Hacer que el usuario alcance el nivel 2
    await container.besito.grant_besitos(user_id, 100, "test", "test")
    changed, old, new = await container.level.check_and_apply_level_up(user_id)
    assert changed
    assert new.id == level_2.id
    
    # Verificar que ahora puede desbloquear
    can_unlock, reason = await container.reward.check_unlock_conditions(user_id, reward.id)
    assert can_unlock


@pytest.mark.asyncio
async def test_configuration_orchestrator(db_session):
    """
    Aplica configuración completa → verifica que todo se creó correctamente
    """
    container = GamificationContainer(db_session)
    set_container(container)  # Set global container for internal service access
    
    config = {
        'mission': {
            'name': "Test Complete",
            'description': "Test",
            'mission_type': MissionType.ONE_TIME.value,
            'criteria': {"type": "one_time"},
            'besitos_reward': 1200  # Higher than level requirement (1000)
        },
        'auto_level': {
            'name': "Test Level",
            'min_besitos': 1000,
            'order': 10
        },
        'rewards': [
            {
                'name': "Test Badge",
                'description': "Test",
                'reward_type': RewardType.BADGE.value,
                'metadata': {"icon": "🎯", "rarity": BadgeRarity.COMMON.value}
            }
        ]
    }
    
    result = await container.configuration_orchestrator.create_complete_mission_system(
        config=config,
        created_by=1
    )

    # Check if validation errors exist, and if not, check for expected fields
    if 'validation_errors' in result and result['validation_errors']:
        assert False, f"Validation errors occurred: {result['validation_errors']}"

    assert 'mission' in result and result['mission'] is not None
    assert 'created_level' in result and result['created_level'] is not None
    assert 'created_rewards' in result and len(result['created_rewards']) == 1
    assert 'validation_errors' in result and len(result['validation_errors']) == 0


@pytest.mark.asyncio
async def test_atomic_rollback_on_error(db_session, sample_user):
    """Test que errores hacen rollback completo."""
    container = GamificationContainer(db_session)
    set_container(container)  # Set global container for internal service access
    user_id = sample_user.user_id

    # Intentar crear una misión con valores inválidos
    with pytest.raises(Exception):
        await container.mission.create_mission(
            name="Test",
            description="Test",
            mission_type=MissionType.DAILY,
            criteria=lambda x: x,  # Invalid - function can't be serialized to JSON
            besitos_reward=100
        )
    
    # Verificar que no se creó ninguna misión con ese nombre
    stmt = select(Mission).where(Mission.name == "Test")
    result = await db_session.execute(stmt)
    assert result.scalar_one_or_none() is None