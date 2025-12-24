"""Tests para estados FSM de gamificación."""

import pytest
from aiogram.fsm.state import State, StatesGroup

from bot.gamification.states.admin import (
    BroadcastStates,
    EditMissionStates,
    EditRewardStates,
    MissionWizardStates,
    RewardWizardStates,
)


class TestMissionWizardStates:
    """Tests para MissionWizardStates."""

    def test_is_states_group(self):
        """Verifica que MissionWizardStates es un StatesGroup."""
        assert issubclass(MissionWizardStates, StatesGroup)

    def test_has_select_type_state(self):
        """Verifica estado select_type."""
        assert hasattr(MissionWizardStates, "select_type")
        assert isinstance(MissionWizardStates.select_type, State)

    def test_has_criteria_states(self):
        """Verifica estados de criterios."""
        assert hasattr(MissionWizardStates, "enter_streak_days")
        assert hasattr(MissionWizardStates, "enter_daily_count")
        assert hasattr(MissionWizardStates, "enter_weekly_target")
        assert hasattr(MissionWizardStates, "enter_specific_reaction")

    def test_has_besitos_reward_state(self):
        """Verifica estado de recompensa en besitos."""
        assert hasattr(MissionWizardStates, "enter_besitos_reward")

    def test_has_auto_level_states(self):
        """Verifica estados de auto level-up."""
        assert hasattr(MissionWizardStates, "choose_auto_level")
        assert hasattr(MissionWizardStates, "create_new_level")
        assert hasattr(MissionWizardStates, "enter_level_name")
        assert hasattr(MissionWizardStates, "enter_level_besitos")
        assert hasattr(MissionWizardStates, "enter_level_order")

    def test_has_rewards_states(self):
        """Verifica estados de recompensas."""
        assert hasattr(MissionWizardStates, "choose_rewards")
        assert hasattr(MissionWizardStates, "create_new_reward")
        assert hasattr(MissionWizardStates, "enter_reward_name")
        assert hasattr(MissionWizardStates, "enter_reward_description")

    def test_has_confirm_state(self):
        """Verifica estado de confirmación."""
        assert hasattr(MissionWizardStates, "confirm")

    def test_minimum_states_count(self):
        """Verifica que tenga al menos 11 estados."""
        states_count = sum(
            1
            for attr in dir(MissionWizardStates)
            if isinstance(getattr(MissionWizardStates, attr), State)
        )
        assert states_count >= 11


class TestRewardWizardStates:
    """Tests para RewardWizardStates."""

    def test_is_states_group(self):
        """Verifica que RewardWizardStates es un StatesGroup."""
        assert issubclass(RewardWizardStates, StatesGroup)

    def test_has_select_type_state(self):
        """Verifica estado select_type."""
        assert hasattr(RewardWizardStates, "select_type")

    def test_has_metadata_states(self):
        """Verifica estados de metadata."""
        assert hasattr(RewardWizardStates, "enter_badge_icon")
        assert hasattr(RewardWizardStates, "enter_badge_rarity")
        assert hasattr(RewardWizardStates, "enter_permission_key")
        assert hasattr(RewardWizardStates, "enter_permission_duration")
        assert hasattr(RewardWizardStates, "enter_besitos_amount")
        assert hasattr(RewardWizardStates, "enter_item_name")

    def test_has_unlock_condition_states(self):
        """Verifica estados de unlock conditions."""
        assert hasattr(RewardWizardStates, "choose_unlock_type")
        assert hasattr(RewardWizardStates, "select_mission")
        assert hasattr(RewardWizardStates, "select_level")
        assert hasattr(RewardWizardStates, "enter_min_besitos")
        assert hasattr(RewardWizardStates, "add_multiple_conditions")

    def test_has_confirm_state(self):
        """Verifica estado de confirmación."""
        assert hasattr(RewardWizardStates, "confirm")

    def test_minimum_states_count(self):
        """Verifica que tenga al menos 10 estados."""
        states_count = sum(
            1
            for attr in dir(RewardWizardStates)
            if isinstance(getattr(RewardWizardStates, attr), State)
        )
        assert states_count >= 10


class TestBroadcastStates:
    """Tests para BroadcastStates."""

    def test_is_states_group(self):
        """Verifica que BroadcastStates es un StatesGroup."""
        assert issubclass(BroadcastStates, StatesGroup)

    def test_has_waiting_for_message_state(self):
        """Verifica estado waiting_for_message."""
        assert hasattr(BroadcastStates, "waiting_for_message")
        assert isinstance(BroadcastStates.waiting_for_message, State)

    def test_has_confirm_broadcast_state(self):
        """Verifica estado confirm_broadcast."""
        assert hasattr(BroadcastStates, "confirm_broadcast")
        assert isinstance(BroadcastStates.confirm_broadcast, State)

    def test_exact_states_count(self):
        """Verifica que tenga exactamente 2 estados."""
        states_count = sum(
            1
            for attr in dir(BroadcastStates)
            if isinstance(getattr(BroadcastStates, attr), State)
        )
        assert states_count == 2


class TestEditMissionStates:
    """Tests para EditMissionStates."""

    def test_is_states_group(self):
        """Verifica que EditMissionStates es un StatesGroup."""
        assert issubclass(EditMissionStates, StatesGroup)

    def test_has_required_states(self):
        """Verifica que tenga todos los estados requeridos."""
        assert hasattr(EditMissionStates, "select_mission")
        assert hasattr(EditMissionStates, "select_field")
        assert hasattr(EditMissionStates, "enter_new_value")
        assert hasattr(EditMissionStates, "confirm")

    def test_exact_states_count(self):
        """Verifica que tenga exactamente 4 estados."""
        states_count = sum(
            1
            for attr in dir(EditMissionStates)
            if isinstance(getattr(EditMissionStates, attr), State)
        )
        assert states_count == 4


class TestEditRewardStates:
    """Tests para EditRewardStates."""

    def test_is_states_group(self):
        """Verifica que EditRewardStates es un StatesGroup."""
        assert issubclass(EditRewardStates, StatesGroup)

    def test_has_required_states(self):
        """Verifica que tenga todos los estados requeridos."""
        assert hasattr(EditRewardStates, "select_reward")
        assert hasattr(EditRewardStates, "select_field")
        assert hasattr(EditRewardStates, "enter_new_value")
        assert hasattr(EditRewardStates, "confirm")

    def test_exact_states_count(self):
        """Verifica que tenga exactamente 4 estados."""
        states_count = sum(
            1
            for attr in dir(EditRewardStates)
            if isinstance(getattr(EditRewardStates, attr), State)
        )
        assert states_count == 4


class TestStatesImports:
    """Tests para imports desde __init__.py."""

    def test_can_import_from_module(self):
        """Verifica que se puedan importar desde bot.gamification.states."""
        from bot.gamification.states import (
            BroadcastStates as B,
            EditMissionStates as EM,
            EditRewardStates as ER,
            MissionWizardStates as MW,
            RewardWizardStates as RW,
        )

        assert B is BroadcastStates
        assert MW is MissionWizardStates
        assert RW is RewardWizardStates
        assert EM is EditMissionStates
        assert ER is EditRewardStates
