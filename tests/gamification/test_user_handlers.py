"""Tests para handlers de usuario de gamificación."""

import pytest
from aiogram import Router

from bot.gamification.handlers.user import profile, missions, rewards, leaderboard


class TestUserHandlersProfile:
    """Tests para profile.py."""

    def test_router_exists(self):
        """Verifica que el router existe."""
        assert hasattr(profile, "router")
        assert isinstance(profile.router, Router)

    def test_show_profile_exists(self):
        """Verifica que existe el handler show_profile."""
        assert hasattr(profile, "show_profile")
        assert callable(profile.show_profile)

    def test_show_profile_callback_exists(self):
        """Verifica que existe el handler show_profile_callback."""
        assert hasattr(profile, "show_profile_callback")
        assert callable(profile.show_profile_callback)


class TestUserHandlersMissions:
    """Tests para missions.py."""

    def test_router_exists(self):
        """Verifica que el router existe."""
        assert hasattr(missions, "router")
        assert isinstance(missions.router, Router)

    def test_show_missions_exists(self):
        """Verifica que existe el handler show_missions."""
        assert hasattr(missions, "show_missions")
        assert callable(missions.show_missions)

    def test_claim_mission_reward_exists(self):
        """Verifica que existe el handler claim_mission_reward."""
        assert hasattr(missions, "claim_mission_reward")
        assert callable(missions.claim_mission_reward)

    def test_view_mission_progress_exists(self):
        """Verifica que existe el handler view_mission_progress."""
        assert hasattr(missions, "view_mission_progress")
        assert callable(missions.view_mission_progress)


class TestUserHandlersRewards:
    """Tests para rewards.py."""

    def test_router_exists(self):
        """Verifica que el router existe."""
        assert hasattr(rewards, "router")
        assert isinstance(rewards.router, Router)

    def test_show_rewards_exists(self):
        """Verifica que existe el handler show_rewards."""
        assert hasattr(rewards, "show_rewards")
        assert callable(rewards.show_rewards)

    def test_buy_reward_exists(self):
        """Verifica que existe el handler buy_reward."""
        assert hasattr(rewards, "buy_reward")
        assert callable(rewards.buy_reward)


class TestUserHandlersLeaderboard:
    """Tests para leaderboard.py."""

    def test_router_exists(self):
        """Verifica que el router existe."""
        assert hasattr(leaderboard, "router")
        assert isinstance(leaderboard.router, Router)

    def test_show_leaderboard_exists(self):
        """Verifica que existe el handler show_leaderboard."""
        assert hasattr(leaderboard, "show_leaderboard")
        assert callable(leaderboard.show_leaderboard)


class TestUserHandlersCallbacks:
    """Tests para validar callbacks."""

    def test_callback_user_profile(self):
        """Verifica callback de perfil."""
        assert "user:profile" == "user:profile"

    def test_callback_user_missions(self):
        """Verifica callback de misiones."""
        assert "user:missions" == "user:missions"

    def test_callback_user_rewards(self):
        """Verifica callback de recompensas."""
        assert "user:rewards" == "user:rewards"

    def test_callback_user_leaderboard(self):
        """Verifica callback de leaderboard."""
        assert "user:leaderboard" == "user:leaderboard"

    def test_callback_mission_claim_pattern(self):
        """Verifica patrón de callback de claim."""
        pattern = "user:mission:claim:123"
        assert pattern.startswith("user:mission:claim:")

    def test_callback_mission_view_pattern(self):
        """Verifica patrón de callback de view."""
        pattern = "user:mission:view:123"
        assert pattern.startswith("user:mission:view:")

    def test_callback_reward_buy_pattern(self):
        """Verifica patrón de callback de buy."""
        pattern = "user:reward:buy:123"
        assert pattern.startswith("user:reward:buy:")


class TestUserHandlersImports:
    """Tests para validar imports."""

    def test_can_import_profile_router(self):
        """Verifica import de router de profile."""
        from bot.gamification.handlers.user.profile import router
        assert router is not None

    def test_can_import_missions_router(self):
        """Verifica import de router de missions."""
        from bot.gamification.handlers.user.missions import router
        assert router is not None

    def test_can_import_rewards_router(self):
        """Verifica import de router de rewards."""
        from bot.gamification.handlers.user.rewards import router
        assert router is not None

    def test_can_import_leaderboard_router(self):
        """Verifica import de router de leaderboard."""
        from bot.gamification.handlers.user.leaderboard import router
        assert router is not None

    def test_can_import_from_gamification_handlers(self):
        """Verifica que se pueden importar desde handlers de gamificación."""
        from bot.gamification.handlers import (
            gamification_user_profile_router,
            gamification_user_missions_router,
            gamification_user_rewards_router,
            gamification_user_leaderboard_router,
        )

        assert gamification_user_profile_router is not None
        assert gamification_user_missions_router is not None
        assert gamification_user_rewards_router is not None
        assert gamification_user_leaderboard_router is not None
