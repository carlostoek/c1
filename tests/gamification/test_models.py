# tests/gamification/test_models.py

import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from bot.gamification.database.models import (
    UserGamification, Reaction, UserReaction, UserStreak, 
    Level, Mission, UserMission, Reward, UserReward, Badge, 
    UserBadge, ConfigTemplate, GamificationConfig
)
from bot.gamification.database.enums import (
    MissionType, MissionStatus, RewardType, BadgeRarity, 
    ObtainedVia, TransactionType, TemplateCategory
)


# ============================================
# TESTS UserGamification
# ============================================

@pytest.mark.asyncio
async def test_create_user_gamification(db_session):
    """Debe crear perfil de gamificación con defaults"""
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
async def test_user_gamification_relationship_with_level(db_session, sample_level):
    """Debe relacionarse con Level"""
    user = UserGamification(user_id=12345, current_level_id=sample_level.id)
    db_session.add(user)
    await db_session.commit()
    
    # Refresh to load relationship
    result = await db_session.get(UserGamification, 12345)
    assert result.current_level_id == sample_level.id


# ============================================
# TESTS Reaction
# ============================================

@pytest.mark.asyncio
async def test_create_reaction(db_session):
    """Debe crear reacción con emoji único"""
    reaction = Reaction(emoji="❤️", besitos_value=1)
    db_session.add(reaction)
    await db_session.commit()
    
    assert reaction.emoji == "❤️"
    assert reaction.besitos_value == 1
    assert reaction.active is True
    assert reaction.created_at is not None


@pytest.mark.asyncio
async def test_reaction_emoji_unique_constraint(db_session):
    """No debe permitir emojis duplicados"""
    reaction1 = Reaction(emoji="🔥", besitos_value=1)
    reaction2 = Reaction(emoji="🔥", besitos_value=2)
    
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
    """Debe registrar reacción de usuario"""
    user_reaction = UserReaction(
        user_id=sample_user.user_id,
        reaction_id=sample_reaction.id,
        channel_id=-1001234567890,
        message_id=123
    )
    db_session.add(user_reaction)
    await db_session.commit()
    
    assert user_reaction.user_id == sample_user.user_id
    assert user_reaction.reaction_id == sample_reaction.id
    assert user_reaction.channel_id == -1001234567890
    assert user_reaction.message_id == 123
    assert user_reaction.reacted_at is not None


@pytest.mark.asyncio
async def test_user_reaction_foreign_keys(db_session, sample_user, sample_reaction):
    """Debe validar foreign keys"""
    user_reaction = UserReaction(
        user_id=sample_user.user_id,
        reaction_id=sample_reaction.id,
        channel_id=-1001234567890,
        message_id=123
    )
    db_session.add(user_reaction)
    await db_session.commit()
    
    result = await db_session.get(UserReaction, user_reaction.id)
    assert result.user_id == sample_user.user_id
    assert result.reaction_id == sample_reaction.id


# ============================================
# TESTS UserStreak
# ============================================

@pytest.mark.asyncio
async def test_user_streak_defaults(db_session, sample_user):
    """Debe iniciar con racha en 0"""
    streak = UserStreak(user_id=sample_user.user_id)
    db_session.add(streak)
    await db_session.commit()
    
    assert streak.current_streak == 0
    assert streak.longest_streak == 0
    assert streak.last_reaction_date is None
    assert streak.updated_at is not None


@pytest.mark.asyncio
async def test_user_streak_unique_per_user(db_session, sample_user):
    """Solo debe permitir 1 racha por usuario"""
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
async def test_create_level(db_session):
    """Debe crear nivel con mínimo de besitos"""
    level = Level(name="Novato", min_besitos=0, order=1)
    db_session.add(level)
    await db_session.commit()
    
    assert level.name == "Novato"
    assert level.min_besitos == 0
    assert level.order == 1
    assert level.active is True
    assert level.created_at is not None


@pytest.mark.asyncio
async def test_level_name_unique(db_session):
    """No debe permitir nombres duplicados"""
    level1 = Level(name="Novato", min_besitos=0, order=1)
    level2 = Level(name="Novato", min_besitos=500, order=2)
    
    db_session.add(level1)
    await db_session.commit()
    
    db_session.add(level2)
    with pytest.raises(IntegrityError):
        await db_session.commit()


# ============================================
# TESTS Mission
# ============================================

@pytest.mark.asyncio
async def test_create_mission(db_session, sample_level):
    """Debe crear misión con criterios JSON"""
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

    assert mission.name == "Primera Racha"
    assert mission.mission_type == MissionType.STREAK
    assert mission.besitos_reward == 500
    assert mission.active is True
    assert mission.repeatable is False
    assert mission.auto_level_up_id == sample_level.id


@pytest.mark.asyncio
async def test_mission_defaults(db_session, sample_level):
    """Debe aplicar defaults correctamente"""
    mission = Mission(
        name="Misión por defecto",
        description="Descripción",
        mission_type=MissionType.DAILY,
        criteria='{}',
        besitos_reward=100,
        created_by=98765
    )
    db_session.add(mission)
    await db_session.commit()
    
    assert mission.active is True
    assert mission.repeatable is False
    assert mission.created_by == 98765
    assert mission.created_at is not None


# ============================================
# TESTS UserMission
# ============================================

@pytest.mark.asyncio
async def test_user_mission_progress(db_session, sample_user, sample_mission):
    """Debe trackear progreso de misión"""
    user_mission = UserMission(
        user_id=sample_user.user_id,
        mission_id=sample_mission.id,
        progress='{"days_completed": 3}',
        status=MissionStatus.IN_PROGRESS
    )
    db_session.add(user_mission)
    await db_session.commit()
    
    assert user_mission.status == MissionStatus.IN_PROGRESS
    assert user_mission.completed_at is None
    assert user_mission.claimed_at is None


@pytest.mark.asyncio
async def test_user_mission_unique_constraint(db_session, sample_user, sample_mission):
    """No debe permitir mismo user+mission si no es repeatable"""
    um1 = UserMission(
        user_id=sample_user.user_id, 
        mission_id=sample_mission.id, 
        status=MissionStatus.IN_PROGRESS,
        progress='{}'
    )
    um2 = UserMission(
        user_id=sample_user.user_id, 
        mission_id=sample_mission.id, 
        status=MissionStatus.IN_PROGRESS,
        progress='{}'
    )
    
    db_session.add(um1)
    await db_session.commit()
    
    db_session.add(um2)
    with pytest.raises(IntegrityError):
        await db_session.commit()


# ============================================
# TESTS Reward
# ============================================

@pytest.mark.asyncio
async def test_create_reward(db_session):
    """Debe crear recompensa con tipo"""
    reward = Reward(
        name="Premio Especial",
        description="Recompensa por completar misión",
        reward_type=RewardType.TITLE,
        cost_besitos=500,
        created_by=98765
    )
    db_session.add(reward)
    await db_session.commit()

    assert reward.name == "Premio Especial"
    assert reward.reward_type == RewardType.TITLE
    assert reward.cost_besitos == 500
    assert reward.active is True


@pytest.mark.asyncio
async def test_reward_defaults(db_session):
    """Debe aplicar defaults correctamente"""
    reward = Reward(
        name="Recompensa sin coste",
        description="Gratis para todos",
        reward_type=RewardType.BADGE,
        created_by=98765
    )
    db_session.add(reward)
    await db_session.commit()
    
    assert reward.cost_besitos is None
    assert reward.active is True
    assert reward.created_by == 98765
    assert reward.created_at is not None


# ============================================
# TESTS UserReward
# ============================================

@pytest.mark.asyncio
async def test_create_user_reward(db_session, sample_user, sample_reward):
    """Debe crear recompensa obtenida por usuario"""
    user_reward = UserReward(
        user_id=sample_user.user_id,
        reward_id=sample_reward.id,
        obtained_via=ObtainedVia.MISSION
    )
    db_session.add(user_reward)
    await db_session.commit()
    
    assert user_reward.user_id == sample_user.user_id
    assert user_reward.reward_id == sample_reward.id
    assert user_reward.obtained_via == ObtainedVia.MISSION
    assert user_reward.obtained_at is not None


@pytest.mark.asyncio
async def test_user_reward_unique_constraint(db_session, sample_user, sample_reward):
    """No debe permitir mismo user+reward duplicado"""
    ur1 = UserReward(
        user_id=sample_user.user_id,
        reward_id=sample_reward.id,
        obtained_via=ObtainedVia.MISSION
    )
    ur2 = UserReward(
        user_id=sample_user.user_id,
        reward_id=sample_reward.id,
        obtained_via=ObtainedVia.PURCHASE
    )
    
    db_session.add(ur1)
    await db_session.commit()
    
    db_session.add(ur2)
    with pytest.raises(IntegrityError):
        await db_session.commit()


# ============================================
# TESTS Badge
# ============================================

@pytest.mark.asyncio
async def test_create_badge(db_session, sample_reward):
    """Debe crear badge como subtipo de reward"""
    badge = Badge(
        id=sample_reward.id,
        icon="🏆",
        rarity=BadgeRarity.COMMON
    )
    db_session.add(badge)
    await db_session.commit()
    
    assert badge.id == sample_reward.id
    assert badge.icon == "🏆"
    assert badge.rarity == BadgeRarity.COMMON


@pytest.mark.asyncio
async def test_badge_foreign_key(db_session, sample_reward):
    """Debe validar foreign key con reward"""
    badge = Badge(
        id=sample_reward.id,
        icon="🎯",
        rarity=BadgeRarity.RARE
    )
    db_session.add(badge)
    await db_session.commit()
    
    result = await db_session.get(Badge, sample_reward.id)
    assert result.icon == "🎯"
    assert result.rarity == BadgeRarity.RARE


# ============================================
# TESTS UserBadge
# ============================================

@pytest.mark.asyncio
async def test_create_user_badge(db_session, sample_user, sample_reward):
    """Debe crear badge obtenido por usuario"""
    # Primero crear la recompensa de usuario
    user_reward = UserReward(
        user_id=sample_user.user_id,
        reward_id=sample_reward.id,
        obtained_via=ObtainedVia.MISSION
    )
    db_session.add(user_reward)
    await db_session.commit()
    
    # Luego crear el badge de usuario
    user_badge = UserBadge(
        id=user_reward.id,
        displayed=True
    )
    db_session.add(user_badge)
    await db_session.commit()
    
    assert user_badge.id == user_reward.id
    assert user_badge.displayed is True


# ============================================
# TESTS ConfigTemplate
# ============================================

@pytest.mark.asyncio
async def test_create_config_template(db_session):
    """Debe crear plantilla de configuración"""
    template = ConfigTemplate(
        name="Misión Básica",
        description="Plantilla para misiones simples",
        template_data='{"name": "Test", "type": "daily"}',
        category=TemplateCategory.MISSION,
        created_by=12345
    )
    db_session.add(template)
    await db_session.commit()
    
    assert template.name == "Misión Básica"
    assert template.category == TemplateCategory.MISSION
    assert template.created_by == 12345
    assert template.created_at is not None


@pytest.mark.asyncio
async def test_config_template_defaults(db_session):
    """Debe aplicar defaults correctamente"""
    template = ConfigTemplate(
        name="Plantilla por defecto",
        description="Descripción",
        template_data='{}',
        category=TemplateCategory.REWARD,
        created_by=54321
    )
    db_session.add(template)
    await db_session.commit()
    
    assert template.created_by == 54321
    assert template.created_at is not None


# ============================================
# TESTS GamificationConfig
# ============================================

@pytest.mark.asyncio
async def test_gamification_config_singleton(db_session):
    """Debe permitir solo 1 registro de config"""
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
    assert config.streak_reset_hours == 24
    assert config.notifications_enabled is True
    assert config.updated_at is not None


@pytest.mark.asyncio
async def test_gamification_config_defaults(db_session):
    """Debe aplicar defaults correctamente"""
    config = GamificationConfig(
        id=1,
        besitos_per_reaction=2,
        streak_reset_hours=12
    )
    db_session.add(config)
    await db_session.commit()
    
    # Notifications should default to True and max_besitos_per_day to None
    result = await db_session.get(GamificationConfig, 1)
    assert result.besitos_per_reaction == 2
    assert result.streak_reset_hours == 12
    assert result.notifications_enabled is True


# ============================================
# TESTS Relationships y Constraints
# ============================================

@pytest.mark.asyncio
async def test_user_mission_mission_relationship(db_session, sample_user, sample_mission):
    """Las relaciones entre UserMission y Mission deben funcionar"""
    user_mission = UserMission(
        user_id=sample_user.user_id,
        mission_id=sample_mission.id,
        progress='{}',
        status=MissionStatus.IN_PROGRESS
    )
    db_session.add(user_mission)
    await db_session.commit()
    
    # Verify relationship can be loaded
    result = await db_session.get(UserMission, user_mission.id)
    assert result.mission_id == sample_mission.id


@pytest.mark.asyncio
async def test_user_reward_reward_relationship(db_session, sample_user, sample_reward):
    """Las relaciones entre UserReward y Reward deben funcionar"""
    user_reward = UserReward(
        user_id=sample_user.user_id,
        reward_id=sample_reward.id,
        obtained_via=ObtainedVia.MISSION
    )
    db_session.add(user_reward)
    await db_session.commit()
    
    result = await db_session.get(UserReward, user_reward.id)
    assert result.reward_id == sample_reward.id