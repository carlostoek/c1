"""
Tests para RewardsService - Servicio de gestión de recompensas.

Casos cubiertos:
- Obtener recompensas disponibles
- Validación de canjes
- Ejecución de canjes
- Histórico de canjes
- Límites de canje (once, daily, weekly)
"""
import pytest
from datetime import datetime, timezone, timedelta

from bot.database.models import (
    Reward, UserReward, RewardType, RewardLimit, User, UserProgress
)
from bot.services.rewards import RewardsService


@pytest.fixture
async def rewards_service(session):
    """Crea una instancia de RewardsService."""
    return RewardsService(session)


@pytest.fixture
async def sample_user(session):
    """Crea un usuario de prueba."""
    from sqlalchemy import select

    # Buscar si existe
    result = await session.execute(select(User).where(User.user_id == 12345))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            user_id=12345,
            first_name="Test",
            last_name="User",
            role="FREE"
        )
        session.add(user)
        await session.flush()

    return user


@pytest.fixture
async def sample_reward(session):
    """Crea una recompensa de prueba."""
    reward = Reward(
        name="Test Reward",
        description="Test description",
        icon="🎁",
        reward_type=RewardType.BADGE,
        cost=100,
        limit_type=RewardLimit.ONCE,
        required_level=1,
        is_vip_only=False,
        is_active=True,
        stock=None
    )
    session.add(reward)
    await session.flush()
    return reward


class TestRewardsServiceGetAvailable:
    """Tests para get_available_rewards()."""

    async def test_get_available_rewards_returns_list(
        self, rewards_service, sample_user, sample_reward, session
    ):
        """Verifica que retorna una lista de recompensas."""
        rewards = await rewards_service.get_available_rewards(sample_user.user_id)

        assert isinstance(rewards, list)
        assert len(rewards) >= 0

    async def test_get_available_rewards_filters_inactive(
        self, rewards_service, sample_user, session
    ):
        """Verifica que filtra recompensas inactivas."""
        # Crear recompensa inactiva
        inactive_reward = Reward(
            name="Inactive Reward",
            description="Test",
            icon="🎁",
            reward_type=RewardType.BADGE,
            cost=50,
            limit_type=RewardLimit.ONCE,
            required_level=1,
            is_vip_only=False,
            is_active=False
        )
        session.add(inactive_reward)
        await session.flush()

        rewards = await rewards_service.get_available_rewards(sample_user.user_id)

        # No debe incluir la inactiva
        active_count = sum(1 for r in rewards if r.is_active)
        assert active_count == len(rewards)

    async def test_get_available_rewards_filters_no_stock(
        self, rewards_service, sample_user, session
    ):
        """Verifica que filtra recompensas sin stock."""
        # Crear recompensa sin stock
        no_stock_reward = Reward(
            name="No Stock Reward",
            description="Test",
            icon="🎁",
            reward_type=RewardType.BADGE,
            cost=50,
            limit_type=RewardLimit.ONCE,
            required_level=1,
            is_vip_only=False,
            is_active=True,
            stock=0
        )
        session.add(no_stock_reward)
        await session.flush()

        rewards = await rewards_service.get_available_rewards(sample_user.user_id)

        # No debe incluir la sin stock
        available = [r for r in rewards if r.is_available]
        assert len(available) == len(rewards)


class TestRewardsServiceCanRedeem:
    """Tests para can_redeem()."""

    async def test_can_redeem_nonexistent_reward(
        self, rewards_service, sample_user
    ):
        """Verifica rechazo cuando recompensa no existe."""
        can_redeem, error = await rewards_service.can_redeem(
            sample_user.user_id, 99999
        )

        assert not can_redeem
        assert error is not None
        assert "no encontrada" in error.lower()

    async def test_can_redeem_inactive_reward(
        self, rewards_service, sample_user, session
    ):
        """Verifica rechazo cuando recompensa está inactiva."""
        reward = Reward(
            name="Inactive",
            description="Test",
            icon="🎁",
            reward_type=RewardType.BADGE,
            cost=50,
            limit_type=RewardLimit.ONCE,
            required_level=1,
            is_vip_only=False,
            is_active=False
        )
        session.add(reward)
        await session.flush()

        can_redeem, error = await rewards_service.can_redeem(
            sample_user.user_id, reward.id
        )

        assert not can_redeem
        assert "disponible" in error.lower()

    async def test_can_redeem_no_stock(self, rewards_service, sample_user, session):
        """Verifica rechazo cuando no hay stock."""
        reward = Reward(
            name="No Stock",
            description="Test",
            icon="🎁",
            reward_type=RewardType.BADGE,
            cost=50,
            limit_type=RewardLimit.ONCE,
            required_level=1,
            is_vip_only=False,
            is_active=True,
            stock=0
        )
        session.add(reward)
        await session.flush()

        can_redeem, error = await rewards_service.can_redeem(
            sample_user.user_id, reward.id
        )

        assert not can_redeem
        assert "stock" in error.lower()


class TestRewardsServiceCheckLimit:
    """Tests para _check_redeem_limit()."""

    async def test_check_limit_once_allows_first_redeem(
        self, rewards_service, sample_user, session
    ):
        """Verifica que ONCE permite el primer canje."""
        reward = Reward(
            name="Test Reward",
            description="Test",
            icon="🎁",
            reward_type=RewardType.BADGE,
            cost=50,
            limit_type=RewardLimit.ONCE
        )
        session.add(reward)
        await session.flush()

        can_redeem = await rewards_service._check_redeem_limit(
            sample_user.user_id, reward.id, RewardLimit.ONCE
        )

        assert can_redeem

    async def test_check_limit_once_blocks_second_redeem(
        self, rewards_service, sample_user, session
    ):
        """Verifica que ONCE bloquea el segundo canje."""
        reward = Reward(
            name="Test Reward",
            description="Test",
            icon="🎁",
            reward_type=RewardType.BADGE,
            cost=50,
            limit_type=RewardLimit.ONCE
        )
        session.add(reward)
        await session.flush()

        # Registrar primer canje
        user_reward = UserReward(
            user_id=sample_user.user_id,
            reward_id=reward.id,
            cost_paid=50
        )
        session.add(user_reward)
        await session.flush()

        # Intentar segundo canje
        can_redeem = await rewards_service._check_redeem_limit(
            sample_user.user_id, reward.id, RewardLimit.ONCE
        )

        assert not can_redeem

    async def test_check_limit_daily_allows_different_days(
        self, rewards_service, sample_user, session
    ):
        """Verifica que DAILY permite canjes en días diferentes."""
        reward = Reward(
            name="Test Reward",
            description="Test",
            icon="🎁",
            reward_type=RewardType.BADGE,
            cost=50,
            limit_type=RewardLimit.DAILY
        )
        session.add(reward)
        await session.flush()

        # Registrar canje de ayer
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        user_reward = UserReward(
            user_id=sample_user.user_id,
            reward_id=reward.id,
            cost_paid=50,
            redeemed_at=yesterday
        )
        session.add(user_reward)
        await session.flush()

        # Intentar canje hoy
        can_redeem = await rewards_service._check_redeem_limit(
            sample_user.user_id, reward.id, RewardLimit.DAILY
        )

        assert can_redeem

    async def test_check_limit_daily_blocks_same_day(
        self, rewards_service, sample_user, session
    ):
        """Verifica que DAILY bloquea canjes el mismo día."""
        reward = Reward(
            name="Test Reward",
            description="Test",
            icon="🎁",
            reward_type=RewardType.BADGE,
            cost=50,
            limit_type=RewardLimit.DAILY
        )
        session.add(reward)
        await session.flush()

        # Registrar canje hoy
        user_reward = UserReward(
            user_id=sample_user.user_id,
            reward_id=reward.id,
            cost_paid=50
        )
        session.add(user_reward)
        await session.flush()

        # Intentar otro canje hoy
        can_redeem = await rewards_service._check_redeem_limit(
            sample_user.user_id, reward.id, RewardLimit.DAILY
        )

        assert not can_redeem

    async def test_check_limit_weekly_allows_different_weeks(
        self, rewards_service, sample_user, session
    ):
        """Verifica que WEEKLY permite canjes en semanas diferentes."""
        reward = Reward(
            name="Test Reward",
            description="Test",
            icon="🎁",
            reward_type=RewardType.BADGE,
            cost=50,
            limit_type=RewardLimit.WEEKLY
        )
        session.add(reward)
        await session.flush()

        # Registrar canje hace 8 días (semana pasada)
        past_week = datetime.now(timezone.utc) - timedelta(days=8)
        user_reward = UserReward(
            user_id=sample_user.user_id,
            reward_id=reward.id,
            cost_paid=50,
            redeemed_at=past_week
        )
        session.add(user_reward)
        await session.flush()

        # Intentar canje esta semana
        can_redeem = await rewards_service._check_redeem_limit(
            sample_user.user_id, reward.id, RewardLimit.WEEKLY
        )

        assert can_redeem


class TestRewardsServiceGetHistory:
    """Tests para get_user_rewards()."""

    async def test_get_user_rewards_empty(
        self, rewards_service, sample_user
    ):
        """Verifica que retorna lista vacía si no hay canjes."""
        rewards = await rewards_service.get_user_rewards(sample_user.user_id)

        assert isinstance(rewards, list)
        assert len(rewards) == 0

    async def test_get_user_rewards_returns_history(
        self, rewards_service, sample_user, sample_reward, session
    ):
        """Verifica que retorna el histórico de canjes."""
        # Crear algunos canjes
        for i in range(3):
            user_reward = UserReward(
                user_id=sample_user.user_id,
                reward_id=sample_reward.id,
                cost_paid=100
            )
            session.add(user_reward)

        await session.flush()

        rewards = await rewards_service.get_user_rewards(sample_user.user_id)

        assert len(rewards) == 3

    async def test_get_user_rewards_orders_by_date_desc(
        self, rewards_service, sample_user, sample_reward, session
    ):
        """Verifica que ordena por fecha descendente."""
        now = datetime.now(timezone.utc)

        # Crear canjes con fechas diferentes
        for i in range(3):
            user_reward = UserReward(
                user_id=sample_user.user_id,
                reward_id=sample_reward.id,
                cost_paid=100,
                redeemed_at=now - timedelta(days=i)
            )
            session.add(user_reward)

        await session.flush()

        rewards = await rewards_service.get_user_rewards(sample_user.user_id)

        # Verificar orden descendente
        for i in range(len(rewards) - 1):
            assert rewards[i].redeemed_at >= rewards[i + 1].redeemed_at

    async def test_get_user_rewards_respects_limit(
        self, rewards_service, sample_user, sample_reward, session
    ):
        """Verifica que respeta el límite de registros."""
        # Crear muchos canjes
        for i in range(25):
            user_reward = UserReward(
                user_id=sample_user.user_id,
                reward_id=sample_reward.id,
                cost_paid=100
            )
            session.add(user_reward)

        await session.flush()

        rewards = await rewards_service.get_user_rewards(
            sample_user.user_id, limit=10
        )

        assert len(rewards) == 10
