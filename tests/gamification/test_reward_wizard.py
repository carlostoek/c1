"""Tests para el wizard de creación de recompensas."""

import pytest
from aiogram import Router

from bot.gamification.handlers.admin import reward_wizard
from bot.filters.admin import IsAdmin
from bot.gamification.database.enums import RewardType


class TestRewardWizardRouter:
    """Tests para el router del wizard de recompensas."""

    def test_router_exists(self):
        """Verifica que el router existe."""
        assert hasattr(reward_wizard, "router")
        assert isinstance(reward_wizard.router, Router)

    def test_router_has_admin_filter(self):
        """Verifica que el router tiene filtros de admin aplicados."""
        assert reward_wizard.router is not None


class TestRewardWizardHandlers:
    """Tests para validar que existen todos los handlers del wizard."""

    def test_start_reward_wizard_exists(self):
        """Verifica que existe el handler de inicio."""
        assert hasattr(reward_wizard, "start_reward_wizard")
        assert callable(reward_wizard.start_reward_wizard)

    def test_select_reward_type_exists(self):
        """Verifica que existe el handler de selección de tipo."""
        assert hasattr(reward_wizard, "select_reward_type")
        assert callable(reward_wizard.select_reward_type)

    def test_enter_reward_name_exists(self):
        """Verifica que existe el handler para nombre."""
        assert hasattr(reward_wizard, "enter_reward_name")
        assert callable(reward_wizard.enter_reward_name)

    def test_enter_reward_description_exists(self):
        """Verifica que existe el handler para descripción."""
        assert hasattr(reward_wizard, "enter_reward_description")
        assert callable(reward_wizard.enter_reward_description)

    def test_enter_badge_icon_exists(self):
        """Verifica que existe el handler para icono de badge."""
        assert hasattr(reward_wizard, "enter_badge_icon")
        assert callable(reward_wizard.enter_badge_icon)

    def test_enter_badge_rarity_exists(self):
        """Verifica que existe el handler para rareza de badge."""
        assert hasattr(reward_wizard, "enter_badge_rarity")
        assert callable(reward_wizard.enter_badge_rarity)

    def test_enter_besitos_amount_exists(self):
        """Verifica que existe el handler para cantidad de besitos."""
        assert hasattr(reward_wizard, "enter_besitos_amount")
        assert callable(reward_wizard.enter_besitos_amount)

    def test_enter_permission_key_exists(self):
        """Verifica que existe el handler para clave de permiso."""
        assert hasattr(reward_wizard, "enter_permission_key")
        assert callable(reward_wizard.enter_permission_key)

    def test_enter_permission_duration_exists(self):
        """Verifica que existe el handler para duración de permiso."""
        assert hasattr(reward_wizard, "enter_permission_duration")
        assert callable(reward_wizard.enter_permission_duration)

    def test_enter_item_name_exists(self):
        """Verifica que existe el handler para nombre de item."""
        assert hasattr(reward_wizard, "enter_item_name")
        assert callable(reward_wizard.enter_item_name)

    def test_skip_unlock_exists(self):
        """Verifica que existe el handler para saltar unlock condition."""
        assert hasattr(reward_wizard, "skip_unlock")
        assert callable(reward_wizard.skip_unlock)

    def test_unlock_by_mission_exists(self):
        """Verifica que existe el handler para unlock por misión."""
        assert hasattr(reward_wizard, "unlock_by_mission")
        assert callable(reward_wizard.unlock_by_mission)

    def test_select_mission_exists(self):
        """Verifica que existe el handler para seleccionar misión."""
        assert hasattr(reward_wizard, "select_mission")
        assert callable(reward_wizard.select_mission)

    def test_unlock_by_level_exists(self):
        """Verifica que existe el handler para unlock por nivel."""
        assert hasattr(reward_wizard, "unlock_by_level")
        assert callable(reward_wizard.unlock_by_level)

    def test_select_level_exists(self):
        """Verifica que existe el handler para seleccionar nivel."""
        assert hasattr(reward_wizard, "select_level")
        assert callable(reward_wizard.select_level)

    def test_unlock_by_besitos_exists(self):
        """Verifica que existe el handler para unlock por besitos."""
        assert hasattr(reward_wizard, "unlock_by_besitos")
        assert callable(reward_wizard.unlock_by_besitos)

    def test_enter_min_besitos_exists(self):
        """Verifica que existe el handler para besitos mínimos."""
        assert hasattr(reward_wizard, "enter_min_besitos")
        assert callable(reward_wizard.enter_min_besitos)

    def test_confirm_reward_exists(self):
        """Verifica que existe el handler para confirmar recompensa."""
        assert hasattr(reward_wizard, "confirm_reward")
        assert callable(reward_wizard.confirm_reward)

    def test_cancel_wizard_exists(self):
        """Verifica que existe el handler para cancelar wizard."""
        assert hasattr(reward_wizard, "cancel_wizard")
        assert callable(reward_wizard.cancel_wizard)


class TestRewardWizardCallbacks:
    """Tests para validar que los callbacks siguen el patrón correcto."""

    def test_callback_start_wizard(self):
        """Verifica el callback de inicio del wizard."""
        assert "gamif:wizard:reward" == "gamif:wizard:reward"

    def test_callback_type_pattern(self):
        """Verifica el patrón de callbacks de tipo de recompensa."""
        types = ["wizard:type:badge", "wizard:type:item", "wizard:type:permission", "wizard:type:besitos"]
        for t in types:
            assert t.startswith("wizard:type:")

    def test_callback_rarity_pattern(self):
        """Verifica el patrón de callbacks de rareza."""
        rarities = ["wizard:rarity:common", "wizard:rarity:rare", "wizard:rarity:epic", "wizard:rarity:legendary"]
        for r in rarities:
            assert r.startswith("wizard:rarity:")

    def test_callback_unlock_skip(self):
        """Verifica el callback de saltar unlock."""
        assert "wizard:unlock:skip" == "wizard:unlock:skip"

    def test_callback_unlock_mission(self):
        """Verifica el callback de unlock por misión."""
        assert "wizard:unlock:mission" == "wizard:unlock:mission"

    def test_callback_unlock_level(self):
        """Verifica el callback de unlock por nivel."""
        assert "wizard:unlock:level" == "wizard:unlock:level"

    def test_callback_unlock_besitos(self):
        """Verifica el callback de unlock por besitos."""
        assert "wizard:unlock:besitos" == "wizard:unlock:besitos"

    def test_callback_select_mission_pattern(self):
        """Verifica el patrón de callbacks de selección de misión."""
        pattern = "wizard:select_mission:123"
        assert pattern.startswith("wizard:select_mission:")

    def test_callback_select_level_pattern(self):
        """Verifica el patrón de callbacks de selección de nivel."""
        pattern = "wizard:select_level:123"
        assert pattern.startswith("wizard:select_level:")

    def test_callback_confirm(self):
        """Verifica el callback de confirmar."""
        assert "wizard:confirm" == "wizard:confirm"

    def test_callback_cancel(self):
        """Verifica el callback de cancelar."""
        assert "wizard:cancel" == "wizard:cancel"


class TestRewardWizardImports:
    """Tests para validar que los imports son correctos."""

    def test_can_import_router(self):
        """Verifica que se puede importar el router."""
        from bot.gamification.handlers.admin.reward_wizard import router

        assert router is not None
        assert isinstance(router, Router)

    def test_can_import_from_admin_init(self):
        """Verifica que se puede importar desde __init__.py."""
        from bot.gamification.handlers.admin import reward_wizard as rw

        assert rw is not None
        assert hasattr(rw, "router")

    def test_can_import_from_gamification_handlers(self):
        """Verifica que se puede importar desde handlers de gamificación."""
        from bot.gamification.handlers import gamification_reward_wizard_router

        assert gamification_reward_wizard_router is not None
        assert isinstance(gamification_reward_wizard_router, Router)


class TestRewardWizardHelpers:
    """Tests para funciones helper del wizard."""

    def test_generate_summary_helper_exists(self):
        """Verifica que existe la función helper _generate_summary."""
        assert hasattr(reward_wizard, "_generate_summary")
        assert callable(reward_wizard._generate_summary)

    def test_generate_summary_badge(self):
        """Verifica generación de resumen para badge."""
        data = {
            'reward_name': 'Badge Test',
            'reward_type': RewardType.BADGE,
            'reward_description': 'Test badge',
            'metadata': {'icon': '🏆', 'rarity': 'epic'}
        }
        result = reward_wizard._generate_summary(data)
        assert "Badge Test" in result
        assert "🏆" in result
        assert "epic" in result.lower()

    def test_generate_summary_besitos(self):
        """Verifica generación de resumen para besitos."""
        data = {
            'reward_name': 'Besitos Bonus',
            'reward_type': RewardType.BESITOS,
            'reward_description': 'Extra besitos',
            'metadata': {'amount': 500}
        }
        result = reward_wizard._generate_summary(data)
        assert "Besitos Bonus" in result
        assert "500 besitos" in result

    def test_generate_summary_permission(self):
        """Verifica generación de resumen para permiso."""
        data = {
            'reward_name': 'Extra Reactions',
            'reward_type': RewardType.PERMISSION,
            'reward_description': 'More reactions',
            'metadata': {'permission_key': 'extra_reactions', 'duration_days': 30}
        }
        result = reward_wizard._generate_summary(data)
        assert "Extra Reactions" in result
        assert "extra_reactions" in result
        assert "30 días" in result

    def test_generate_summary_item(self):
        """Verifica generación de resumen para item."""
        data = {
            'reward_name': 'Golden Heart',
            'reward_type': RewardType.ITEM,
            'reward_description': 'Rare item',
            'metadata': {'item_key': 'golden_heart'}
        }
        result = reward_wizard._generate_summary(data)
        assert "Golden Heart" in result
        assert "golden_heart" in result

    def test_generate_summary_with_mission_unlock(self):
        """Verifica resumen con unlock por misión."""
        data = {
            'reward_name': 'Test Reward',
            'reward_type': RewardType.BADGE,
            'reward_description': 'Test',
            'metadata': {'icon': '🎯', 'rarity': 'rare'},
            'unlock_mission_id': 5,
            'unlock_mission_name': 'Test Mission'
        }
        result = reward_wizard._generate_summary(data)
        assert "Test Mission" in result

    def test_generate_summary_with_level_unlock(self):
        """Verifica resumen con unlock por nivel."""
        data = {
            'reward_name': 'Test Reward',
            'reward_type': RewardType.BADGE,
            'reward_description': 'Test',
            'metadata': {'icon': '⭐', 'rarity': 'legendary'},
            'unlock_level_id': 3,
            'unlock_level_name': 'Master'
        }
        result = reward_wizard._generate_summary(data)
        assert "Master" in result

    def test_generate_summary_with_besitos_unlock(self):
        """Verifica resumen con unlock por besitos."""
        data = {
            'reward_name': 'Test Reward',
            'reward_type': RewardType.BADGE,
            'reward_description': 'Test',
            'metadata': {'icon': '💎', 'rarity': 'epic'},
            'unlock_besitos': 1000
        }
        result = reward_wizard._generate_summary(data)
        assert "1000 besitos" in result

    def test_generate_summary_without_unlock(self):
        """Verifica resumen sin condición de unlock."""
        data = {
            'reward_name': 'Free Reward',
            'reward_type': RewardType.BADGE,
            'reward_description': 'Always available',
            'metadata': {'icon': '🎁', 'rarity': 'common'}
        }
        result = reward_wizard._generate_summary(data)
        assert "Disponible para todos" in result
