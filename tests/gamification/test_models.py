"""Tests unitarios para modelos de gamificación."""

import pytest
from datetime import datetime, UTC
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from bot.gamification.database.models import (
    UserGamification, Reaction, UserReaction, UserStreak, Level,
    Mission, UserMission, Reward, UserReward, Badge, UserBadge,
    ConfigTemplate, GamificationConfig
)
from bot.gamification.database.enums import (
    MissionType, MissionStatus, RewardType, BadgeRarity,
    ObtainedVia, TemplateCategory
)


# ============================================
# TESTS UserGamification
# ============================================

@pytest.mark.asyncio
async def test_create_user_gamification_defaults(db_session):
    """Debe crear perfil de gamificación con defaults correctos."""
    user = UserGamification(user_id=12345)
    db_session.add(user)
    await db_session.commit()

    assert user.total_besitos == 0
    assert user.besitos_earned == 0
    assert user.besitos_spent == 0
    assert user.current_level_id is None
    assert user.created_at is not None
    assert user.updated_at is not None


@pytest.mark.asyncio
async def test_user_gamification_with_level(db_session, sample_level):
    """Debe relacionarse correctamente con Level."""
    user = UserGamification(user_id=12345, current_level_id=sample_level.id)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user, ['current_level'])

    assert user.current_level.name == "Novato"


# ============================================
# TESTS Reaction
# ============================================

@pytest.mark.asyncio
async def test_create_reaction_with_defaults(db_session):
    """Debe crear reacción con valores por defecto."""
    reaction = Reaction(emoji="🔥")
    db_session.add(reaction)
    await db_session.commit()

    assert reaction.emoji == "🔥"
    assert reaction.besitos_value == 1
    assert reaction.active is True
    assert reaction.created_at is not None


@pytest.mark.asyncio
async def test_reaction_emoji_unique_constraint(db_session):
    """No debe permitir emojis duplicados."""
    reaction1 = Reaction(emoji="👍")
    reaction2 = Reaction(emoji="👍")

    db_session.add(reaction1)
    await db_session.commit()

    db_session.add(reaction2)
    with pytest.raises(IntegrityError):
        await db_session.commit()


# ============================================
# TESTS UserReaction
# ============================================

@pytest.mark.asyncio
async def test_create_user_reaction(db_session, sample_user, sample_reaction):
    """Debe registrar reacción de usuario."""
    user_reaction = UserReaction(
        user_id=sample_user.user_id,
        reaction_id=sample_reaction.id,
        channel_id=-1001234567890,
        message_id=123,
        reacted_at=datetime.now(UTC)
    )
    db_session.add(user_reaction)
    await db_session.commit()

    assert user_reaction.user_id == sample_user.user_id
    assert user_reaction.reaction_id == sample_reaction.id
    assert user_reaction.channel_id == -1001234567890


@pytest.mark.asyncio
async def test_user_reaction_cascade_delete(db_session, sample_user):
    """Al eliminar usuario, sus reacciones se borran."""
    reaction = Reaction(emoji="💯")
    db_session.add(reaction)
    await db_session.commit()

    user_reaction = UserReaction(
        user_id=sample_user.user_id,
        reaction_id=reaction.id,
        channel_id=-1001234567890,
        message_id=123,
        reacted_at=datetime.now(UTC)
    )
    db_session.add(user_reaction)
    await db_session.commit()

    await db_session.delete(sample_user)
    await db_session.commit()

    # Verificar que se borró la reacción
    result = await db_session.execute(
        select(UserReaction).where(
            UserReaction.user_id == sample_user.user_id
        )
    )
    assert result.scalar() is None


# ============================================
# TESTS UserStreak
# ============================================

@pytest.mark.asyncio
async def test_user_streak_defaults(db_session, sample_user):
    """Debe iniciar racha con valores por defecto."""
    streak = UserStreak(user_id=sample_user.user_id)
    db_session.add(streak)
    await db_session.commit()

    assert streak.current_streak == 0
    assert streak.longest_streak == 0
    assert streak.last_reaction_date is None


@pytest.mark.asyncio
async def test_user_streak_unique_constraint(db_session, sample_user):
    """Solo debe permitir 1 racha por usuario."""
    streak1 = UserStreak(user_id=sample_user.user_id)
    streak2 = UserStreak(user_id=sample_user.user_id)

    db_session.add(streak1)
    await db_session.commit()

    db_session.add(streak2)
    with pytest.raises(IntegrityError):
        await db_session.commit()


# ============================================
# TESTS Level
# ============================================

@pytest.mark.asyncio
async def test_create_level_with_order(db_session):
    """Debe crear nivel con parámetros básicos."""
    level = Level(name="Regular", min_besitos=500, order=2)
    db_session.add(level)
    await db_session.commit()

    assert level.name == "Regular"
    assert level.min_besitos == 500
    assert level.order == 2
    assert level.active is True


@pytest.mark.asyncio
async def test_level_name_unique_constraint(db_session):
    """No debe permitir nombres de nivel duplicados."""
    level1 = Level(name="Fanático", min_besitos=5000, order=4)
    level2 = Level(name="Fanático", min_besitos=4000, order=3)

    db_session.add(level1)
    await db_session.commit()

    db_session.add(level2)
    with pytest.raises(IntegrityError):
        await db_session.commit()


# ============================================
# TESTS Mission
# ============================================

@pytest.mark.asyncio
async def test_create_mission_with_criteria(db_session):
    """Debe crear misión con criterios JSON."""
    mission = Mission(
        name="Racha de 7 Días",
        description="Mantén una racha de 7 días",
        mission_type=MissionType.STREAK.value,
        criteria='{"type": "streak", "days": 7}',
        besitos_reward=500,
        created_by=999
    )
    db_session.add(mission)
    await db_session.commit()

    assert mission.besitos_reward == 500
    assert mission.active is True
    assert mission.repeatable is False


@pytest.mark.asyncio
async def test_mission_with_level_up(db_session, sample_level):
    """Misión puede desbloquear auto-levelup."""
    mission = Mission(
        name="Nivel Up",
        description="Sube de nivel",
        mission_type=MissionType.ONE_TIME.value,
        criteria='{"type": "one_time"}',
        besitos_reward=1000,
        auto_level_up_id=sample_level.id,
        created_by=999
    )
    db_session.add(mission)
    await db_session.commit()
    await db_session.refresh(mission, ['auto_level_up'])

    assert mission.auto_level_up.name == "Novato"


# ============================================
# TESTS UserMission
# ============================================

@pytest.mark.asyncio
async def test_create_user_mission_in_progress(db_session, sample_user, sample_mission):
    """Debe crear progreso de misión para usuario."""
    user_mission = UserMission(
        user_id=sample_user.user_id,
        mission_id=sample_mission.id,
        progress='{"days_completed": 3}',
        status=MissionStatus.IN_PROGRESS.value,
        started_at=datetime.now(UTC)
    )
    db_session.add(user_mission)
    await db_session.commit()

    assert user_mission.status == MissionStatus.IN_PROGRESS.value
    assert user_mission.completed_at is None
    assert user_mission.claimed_at is None


@pytest.mark.asyncio
async def test_user_mission_claimed_status(db_session, sample_user, sample_mission):
    """UserMission puede marcarse como reclamada."""
    from datetime import timedelta
    user_mission = UserMission(
        user_id=sample_user.user_id,
        mission_id=sample_mission.id,
        progress='{}',
        status=MissionStatus.COMPLETED.value,
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        claimed_at=datetime.now(UTC) + timedelta(minutes=1)
    )
    db_session.add(user_mission)
    await db_session.commit()

    assert user_mission.status == MissionStatus.COMPLETED.value
    assert user_mission.claimed_at is not None


# ============================================
# TESTS Reward
# ============================================

@pytest.mark.asyncio
async def test_create_reward_badge_type(db_session):
    """Debe crear recompensa tipo badge."""
    reward = Reward(
        name="Primer Logro",
        description="Completaste tu primera misión",
        reward_type=RewardType.BADGE.value,
        created_by=999
    )
    db_session.add(reward)
    await db_session.commit()

    assert reward.reward_type == "badge"
    assert reward.active is True


@pytest.mark.asyncio
async def test_create_reward_with_cost(db_session):
    """Debe crear recompensa con costo en besitos."""
    reward = Reward(
        name="Título Especial",
        description="Compra un título",
        reward_type=RewardType.TITLE.value,
        cost_besitos=1000,
        created_by=999
    )
    db_session.add(reward)
    await db_session.commit()

    assert reward.cost_besitos == 1000


# ============================================
# TESTS UserReward
# ============================================

@pytest.mark.asyncio
async def test_create_user_reward(db_session, sample_user):
    """Debe registrar recompensa obtenida por usuario."""
    reward = Reward(
        name="Test Badge",
        description="Badge de prueba",
        reward_type=RewardType.BADGE.value,
        created_by=999
    )
    db_session.add(reward)
    await db_session.commit()

    user_reward = UserReward(
        user_id=sample_user.user_id,
        reward_id=reward.id,
        obtained_at=datetime.now(UTC),
        obtained_via=ObtainedVia.MISSION.value
    )
    db_session.add(user_reward)
    await db_session.commit()

    assert user_reward.obtained_via == "mission"


@pytest.mark.asyncio
async def test_user_reward_obtained_via_purchase(db_session, sample_user):
    """UserReward puede obtenerse de diferentes formas."""
    reward = Reward(
        name="Purchase Badge",
        description="Badge comprado",
        reward_type=RewardType.BADGE.value,
        created_by=999
    )
    db_session.add(reward)
    await db_session.commit()

    user_reward = UserReward(
        user_id=sample_user.user_id,
        reward_id=reward.id,
        obtained_at=datetime.now(UTC),
        obtained_via=ObtainedVia.PURCHASE.value,
        reference_id=1000  # ID de transacción
    )
    db_session.add(user_reward)
    await db_session.commit()

    assert user_reward.obtained_via == "purchase"
    assert user_reward.reference_id == 1000


# ============================================
# TESTS Badge (Herencia)
# ============================================

@pytest.mark.asyncio
async def test_create_badge_from_reward(db_session):
    """Debe crear badge como herencia de reward."""
    reward = Reward(
        name="Superstar",
        description="Eres una superestrella",
        reward_type=RewardType.BADGE.value,
        created_by=999
    )
    db_session.add(reward)
    await db_session.commit()

    badge = Badge(
        id=reward.id,
        icon="⭐",
        rarity=BadgeRarity.EPIC.value
    )
    db_session.add(badge)
    await db_session.commit()

    assert badge.icon == "⭐"
    assert badge.rarity == "epic"


@pytest.mark.asyncio
async def test_badge_relationships(db_session):
    """Badge debe relacionarse correctamente con Reward."""
    reward = Reward(
        name="Delete Badge",
        description="Badge a eliminar",
        reward_type=RewardType.BADGE.value,
        created_by=999
    )
    db_session.add(reward)
    await db_session.commit()

    badge = Badge(
        id=reward.id,
        icon="🗑️",
        rarity=BadgeRarity.COMMON.value
    )
    db_session.add(badge)
    await db_session.commit()
    await db_session.refresh(badge, ['reward'])

    assert badge.reward.name == "Delete Badge"


# ============================================
# TESTS UserBadge (Herencia)
# ============================================

@pytest.mark.asyncio
async def test_create_user_badge(db_session, sample_user):
    """Debe crear badge obtenido por usuario."""
    reward = Reward(
        name="User Badge Test",
        description="Test",
        reward_type=RewardType.BADGE.value,
        created_by=999
    )
    db_session.add(reward)
    await db_session.commit()

    badge = Badge(
        id=reward.id,
        icon="🎯",
        rarity=BadgeRarity.RARE.value
    )
    db_session.add(badge)
    await db_session.commit()

    user_reward = UserReward(
        user_id=sample_user.user_id,
        reward_id=reward.id,
        obtained_at=datetime.now(UTC),
        obtained_via=ObtainedVia.MISSION.value
    )
    db_session.add(user_reward)
    await db_session.commit()

    user_badge = UserBadge(
        id=user_reward.id,
        displayed=True
    )
    db_session.add(user_badge)
    await db_session.commit()

    assert user_badge.displayed is True


# ============================================
# TESTS ConfigTemplate
# ============================================

@pytest.mark.asyncio
async def test_create_config_template(db_session):
    """Debe crear plantilla de configuración."""
    template = ConfigTemplate(
        name="Config Básica",
        description="Configuración básica",
        template_data='{"missions": []}',
        category=TemplateCategory.MISSION.value,
        created_by=999
    )
    db_session.add(template)
    await db_session.commit()

    assert template.category == "mission"
    assert template.template_data == '{"missions": []}'


@pytest.mark.asyncio
async def test_config_template_full_system(db_session):
    """Puede crear plantilla de sistema completo."""
    template = ConfigTemplate(
        name="Sistema Completo",
        description="Todo el sistema",
        template_data='{"complete": true}',
        category=TemplateCategory.FULL_SYSTEM.value,
        created_by=999
    )
    db_session.add(template)
    await db_session.commit()

    assert template.category == "full_system"


# ============================================
# TESTS GamificationConfig (Singleton)
# ============================================

@pytest.mark.asyncio
async def test_gamification_config_singleton(db_session):
    """Debe crear configuración singleton."""
    config = GamificationConfig(
        id=1,
        besitos_per_reaction=1,
        streak_reset_hours=24,
        notifications_enabled=True
    )
    db_session.add(config)
    await db_session.commit()

    assert config.id == 1
    assert config.besitos_per_reaction == 1
    assert config.notifications_enabled is True


@pytest.mark.asyncio
async def test_gamification_config_with_max_besitos(db_session):
    """Config puede incluir límite máximo de besitos por día."""
    config = GamificationConfig(
        id=1,
        besitos_per_reaction=2,
        max_besitos_per_day=5000,
        streak_reset_hours=24,
        notifications_enabled=True
    )
    db_session.add(config)
    await db_session.commit()

    assert config.max_besitos_per_day == 5000
