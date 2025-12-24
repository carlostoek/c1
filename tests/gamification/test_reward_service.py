"""Tests para RewardService."""

import pytest
from bot.gamification.services.reward import RewardService
from bot.gamification.database.models import (
    Reward, UserReward, Badge, UserBadge, UserGamification, Level, Mission, UserMission
)
from bot.gamification.database.enums import (
    RewardType, ObtainedVia, BadgeRarity, MissionType, MissionStatus
)


# ==================================
# TESTS: CRUD RECOMPENSAS
# ==================================


@pytest.mark.asyncio
async def test_create_reward_basic(db_session):
    """Crear recompensa básica."""
    service = RewardService(db_session)

    reward = await service.create_reward(
        name="Bonus Besitos",
        description="500 besitos extra",
        reward_type=RewardType.BESITOS,
        cost_besitos=100,
        reward_metadata={"amount": 500},
        created_by=999
    )

    assert reward.id is not None
    assert reward.name == "Bonus Besitos"
    assert reward.reward_type == RewardType.BESITOS.value
    assert reward.cost_besitos == 100


@pytest.mark.asyncio
async def test_create_badge(db_session):
    """Crear badge completo."""
    service = RewardService(db_session)

    reward, badge = await service.create_badge(
        name="Primer Paso",
        description="Completa tu primera misión",
        icon="🏆",
        rarity=BadgeRarity.COMMON,
        created_by=999
    )

    assert reward.reward_type == RewardType.BADGE.value
    assert badge.id == reward.id
    assert badge.icon == "🏆"
    assert badge.rarity == BadgeRarity.COMMON.value


@pytest.mark.asyncio
async def test_update_reward(db_session):
    """Actualizar recompensa."""
    service = RewardService(db_session)

    reward = await service.create_reward(
        "Test", "Test", RewardType.ITEM, cost_besitos=50, created_by=999
    )

    updated = await service.update_reward(
        reward.id,
        name="Updated",
        cost_besitos=75
    )

    assert updated.name == "Updated"
    assert updated.cost_besitos == 75


@pytest.mark.asyncio
async def test_delete_reward(db_session):
    """Soft-delete de recompensa."""
    service = RewardService(db_session)

    reward = await service.create_reward(
        "Test", "Test", RewardType.ITEM, created_by=999
    )

    result = await service.delete_reward(reward.id)
    assert result is True

    deleted = await service.get_reward_by_id(reward.id)
    assert deleted.active is False


@pytest.mark.asyncio
async def test_get_all_rewards_filtered(db_session):
    """Obtener recompensas con filtros."""
    service = RewardService(db_session)

    await service.create_badge("Badge 1", "Test", "🏆", BadgeRarity.COMMON, created_by=999)
    await service.create_reward("Item 1", "Test", RewardType.ITEM, created_by=999)

    all_rewards = await service.get_all_rewards()
    assert len(all_rewards) == 2

    badges_only = await service.get_all_rewards(reward_type=RewardType.BADGE)
    assert len(badges_only) == 1


# ==================================
# TESTS: UNLOCK CONDITIONS
# ==================================


@pytest.mark.asyncio
async def test_check_unlock_no_conditions(db_session, sample_user):
    """Recompensa sin condiciones está disponible."""
    service = RewardService(db_session)

    reward = await service.create_reward(
        "Free Reward", "No conditions", RewardType.ITEM, created_by=999
    )

    can_unlock, reason = await service.check_unlock_conditions(
        sample_user.user_id, reward.id
    )

    assert can_unlock is True
    assert reason == "Available"


@pytest.mark.asyncio
async def test_check_unlock_already_obtained(db_session, sample_user):
    """No permitir desbloquear si ya se obtuvo."""
    service = RewardService(db_session)

    reward = await service.create_reward(
        "Test", "Test", RewardType.ITEM, created_by=999
    )

    # Otorgar la recompensa
    await service.grant_reward(
        sample_user.user_id, reward.id, ObtainedVia.ADMIN_GRANT
    )

    # Intentar desbloquear de nuevo
    can_unlock, reason = await service.check_unlock_conditions(
        sample_user.user_id, reward.id
    )

    assert can_unlock is False
    assert reason == "Already obtained"


@pytest.mark.asyncio
async def test_validate_mission_condition(db_session, sample_user):
    """Validar condición tipo mission."""
    service = RewardService(db_session)

    # Crear misión
    mission = Mission(
        name="Test Mission",
        description="Test",
        mission_type=MissionType.ONE_TIME.value,
        criteria='{}',
        besitos_reward=100,
        active=True,
        repeatable=False,
        created_by=999
    )
    db_session.add(mission)
    await db_session.commit()

    # Crear recompensa con condición de misión
    reward = await service.create_reward(
        "Reward",
        "Requires mission",
        RewardType.ITEM,
        unlock_conditions={"type": "mission", "mission_id": mission.id},
        created_by=999
    )

    # Sin completar misión (bloqueada)
    can_unlock, _ = await service.check_unlock_conditions(
        sample_user.user_id, reward.id
    )
    assert can_unlock is False

    # Completar misión
    user_mission = UserMission(
        user_id=sample_user.user_id,
        mission_id=mission.id,
        status=MissionStatus.CLAIMED.value,
        progress='{}',
        started_at=datetime.now(UTC)
    )
    db_session.add(user_mission)
    await db_session.commit()

    # Con misión completada (desbloqueada)
    can_unlock, _ = await service.check_unlock_conditions(
        sample_user.user_id, reward.id
    )
    assert can_unlock is True


@pytest.mark.asyncio
async def test_validate_level_condition(db_session, sample_user):
    """Validar condición tipo level."""
    service = RewardService(db_session)

    # Crear niveles
    level1 = Level(name="Novato", min_besitos=0, order=1, active=True)
    level2 = Level(name="Expert", min_besitos=1000, order=2, active=True)
    db_session.add_all([level1, level2])
    await db_session.commit()

    # Usuario en level1
    sample_user.current_level_id = level1.id
    await db_session.commit()

    # Recompensa que requiere level2
    reward = await service.create_reward(
        "Expert Reward",
        "Requires level 2",
        RewardType.ITEM,
        unlock_conditions={"type": "level", "level_id": level2.id},
        created_by=999
    )

    # Bloqueada (nivel insuficiente)
    can_unlock, _ = await service.check_unlock_conditions(
        sample_user.user_id, reward.id
    )
    assert can_unlock is False

    # Subir a level2
    sample_user.current_level_id = level2.id
    await db_session.commit()

    # Desbloqueada
    can_unlock, _ = await service.check_unlock_conditions(
        sample_user.user_id, reward.id
    )
    assert can_unlock is True


@pytest.mark.asyncio
async def test_validate_besitos_condition(db_session, sample_user):
    """Validar condición tipo besitos."""
    service = RewardService(db_session)

    reward = await service.create_reward(
        "Rich Reward",
        "Requires 5000 besitos",
        RewardType.ITEM,
        unlock_conditions={"type": "besitos", "min_besitos": 5000},
        created_by=999
    )

    # Sin besitos suficientes
    sample_user.total_besitos = 3000
    await db_session.commit()

    can_unlock, _ = await service.check_unlock_conditions(
        sample_user.user_id, reward.id
    )
    assert can_unlock is False

    # Con besitos suficientes
    sample_user.total_besitos = 6000
    await db_session.commit()

    can_unlock, _ = await service.check_unlock_conditions(
        sample_user.user_id, reward.id
    )
    assert can_unlock is True


# ==================================
# TESTS: GRANT REWARD
# ==================================


@pytest.mark.asyncio
async def test_grant_reward_success(db_session, sample_user):
    """Otorgar recompensa exitosamente."""
    service = RewardService(db_session)

    reward = await service.create_reward(
        "Test", "Test", RewardType.ITEM, created_by=999
    )

    success, message, user_reward = await service.grant_reward(
        sample_user.user_id,
        reward.id,
        ObtainedVia.ADMIN_GRANT
    )

    assert success is True
    assert "obtenida" in message.lower()
    assert user_reward.user_id == sample_user.user_id


@pytest.mark.asyncio
async def test_grant_badge_creates_user_badge(db_session, sample_user):
    """Otorgar badge crea UserBadge."""
    service = RewardService(db_session)

    reward, badge = await service.create_badge(
        "Test Badge", "Test", "🏆", BadgeRarity.RARE, created_by=999
    )

    success, _, user_reward = await service.grant_reward(
        sample_user.user_id,
        reward.id,
        ObtainedVia.ADMIN_GRANT
    )

    assert success is True

    # Verificar UserBadge creado
    user_badge = await db_session.get(UserBadge, user_reward.id)
    assert user_badge is not None
    assert user_badge.displayed is False


@pytest.mark.asyncio
async def test_grant_besitos_reward_grants_besitos(db_session, sample_user):
    """Recompensa de besitos otorga besitos extra."""
    service = RewardService(db_session)

    reward = await service.create_reward(
        "Bonus",
        "500 extra",
        RewardType.BESITOS,
        reward_metadata={"amount": 500},
        created_by=999
    )

    initial_besitos = sample_user.total_besitos

    success, _, _ = await service.grant_reward(
        sample_user.user_id,
        reward.id,
        ObtainedVia.ADMIN_GRANT
    )

    assert success is True

    await db_session.refresh(sample_user)
    assert sample_user.total_besitos == initial_besitos + 500


# ==================================
# TESTS: PURCHASE REWARD
# ==================================


@pytest.mark.asyncio
async def test_purchase_reward_success(db_session, sample_user):
    """Comprar recompensa con besitos."""
    service = RewardService(db_session)

    sample_user.total_besitos = 1000
    await db_session.commit()

    reward = await service.create_reward(
        "Purchasable", "Test", RewardType.ITEM,
        cost_besitos=200,
        created_by=999
    )

    success, message, user_reward = await service.purchase_reward(
        sample_user.user_id,
        reward.id
    )

    assert success is True
    assert user_reward is not None

    # Verificar besitos gastados
    await db_session.refresh(sample_user)
    assert sample_user.total_besitos == 800


@pytest.mark.asyncio
async def test_purchase_reward_insufficient_besitos(db_session, sample_user):
    """No permitir compra sin besitos suficientes."""
    service = RewardService(db_session)

    sample_user.total_besitos = 50
    await db_session.commit()

    reward = await service.create_reward(
        "Expensive", "Test", RewardType.ITEM,
        cost_besitos=200,
        created_by=999
    )

    success, message, _ = await service.purchase_reward(
        sample_user.user_id,
        reward.id
    )

    assert success is False
    assert "Insufficient" in message


@pytest.mark.asyncio
async def test_purchase_reward_not_purchasable(db_session, sample_user):
    """No permitir compra de recompensa sin cost_besitos."""
    service = RewardService(db_session)

    reward = await service.create_reward(
        "Not for sale", "Test", RewardType.ITEM,
        cost_besitos=None,  # No es comprable
        created_by=999
    )

    success, message, _ = await service.purchase_reward(
        sample_user.user_id,
        reward.id
    )

    assert success is False
    assert "cannot be purchased" in message


# ==================================
# TESTS: CONSULTAS
# ==================================


@pytest.mark.asyncio
async def test_get_user_rewards(db_session, sample_user):
    """Obtener recompensas de usuario."""
    service = RewardService(db_session)

    reward1 = await service.create_reward("R1", "R1", RewardType.ITEM, created_by=999)
    reward2 = await service.create_reward("R2", "R2", RewardType.ITEM, created_by=999)

    await service.grant_reward(sample_user.user_id, reward1.id, ObtainedVia.ADMIN_GRANT)

    user_rewards = await service.get_user_rewards(sample_user.user_id)

    assert len(user_rewards) == 1
    assert user_rewards[0].reward_id == reward1.id


@pytest.mark.asyncio
async def test_has_reward(db_session, sample_user):
    """Verificar si usuario tiene recompensa."""
    service = RewardService(db_session)

    reward = await service.create_reward("Test", "Test", RewardType.ITEM, created_by=999)

    has_it = await service.has_reward(sample_user.user_id, reward.id)
    assert has_it is False

    await service.grant_reward(sample_user.user_id, reward.id, ObtainedVia.ADMIN_GRANT)

    has_it = await service.has_reward(sample_user.user_id, reward.id)
    assert has_it is True


@pytest.mark.asyncio
async def test_get_available_rewards(db_session, sample_user):
    """Obtener recompensas disponibles."""
    service = RewardService(db_session)

    sample_user.total_besitos = 5000
    await db_session.commit()

    # Recompensa bloqueada (requiere 10000 besitos)
    r1 = await service.create_reward(
        "Locked", "Test", RewardType.ITEM,
        unlock_conditions={"type": "besitos", "min_besitos": 10000},
        created_by=999
    )

    # Recompensa disponible (sin condiciones)
    r2 = await service.create_reward(
        "Available", "Test", RewardType.ITEM,
        created_by=999
    )

    available = await service.get_available_rewards(sample_user.user_id)

    assert len(available) == 1
    assert available[0].id == r2.id


# ==================================
# TESTS: BADGES
# ==================================


@pytest.mark.asyncio
async def test_get_user_badges(db_session, sample_user):
    """Obtener badges de usuario."""
    service = RewardService(db_session)

    reward, badge = await service.create_badge(
        "Badge 1", "Test", "🏆", BadgeRarity.EPIC,
        created_by=999
    )

    await service.grant_reward(
        sample_user.user_id,
        reward.id,
        ObtainedVia.ADMIN_GRANT
    )

    badges = await service.get_user_badges(sample_user.user_id)

    assert len(badges) == 1
    assert badges[0][0].icon == "🏆"


@pytest.mark.asyncio
async def test_set_displayed_badges(db_session, sample_user):
    """Configurar badges mostrados."""
    service = RewardService(db_session)

    # Crear 2 badges
    r1, b1 = await service.create_badge("B1", "T1", "🏆", BadgeRarity.COMMON, created_by=999)
    r2, b2 = await service.create_badge("B2", "T2", "🎖️", BadgeRarity.RARE, created_by=999)

    # Otorgar ambos
    _, _, ur1 = await service.grant_reward(sample_user.user_id, r1.id, ObtainedVia.ADMIN_GRANT)
    _, _, ur2 = await service.grant_reward(sample_user.user_id, r2.id, ObtainedVia.ADMIN_GRANT)

    # Marcar solo el primero
    result = await service.set_displayed_badges(
        sample_user.user_id,
        [ur1.id]
    )

    assert result is True

    # Verificar
    await db_session.refresh(await db_session.get(UserBadge, ur1.id))
    await db_session.refresh(await db_session.get(UserBadge, ur2.id))

    ub1 = await db_session.get(UserBadge, ur1.id)
    ub2 = await db_session.get(UserBadge, ur2.id)

    assert ub1.displayed is True
    assert ub2.displayed is False


@pytest.mark.asyncio
async def test_set_displayed_badges_max_limit(db_session, sample_user):
    """No permitir más de 3 badges displayed."""
    service = RewardService(db_session)

    result = await service.set_displayed_badges(
        sample_user.user_id,
        [1, 2, 3, 4]  # 4 badges (excede límite de 3)
    )

    assert result is False


# Helper import
from datetime import datetime, UTC
