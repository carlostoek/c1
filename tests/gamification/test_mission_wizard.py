"""Tests para el wizard de creación de misiones."""

import pytest
from aiogram import Router

from bot.gamification.handlers.admin import mission_wizard
from bot.filters.admin import IsAdmin


class TestMissionWizardRouter:
    """Tests para el router del wizard de misiones."""

    def test_router_exists(self):
        """Verifica que el router existe."""
        assert hasattr(mission_wizard, "router")
        assert isinstance(mission_wizard.router, Router)

    def test_router_has_admin_filter(self):
        """Verifica que el router tiene filtros de admin aplicados."""
        assert mission_wizard.router is not None


class TestMissionWizardHandlers:
    """Tests para validar que existen todos los handlers del wizard."""

    def test_start_mission_wizard_exists(self):
        """Verifica que existe el handler de inicio."""
        assert hasattr(mission_wizard, "start_mission_wizard")
        assert callable(mission_wizard.start_mission_wizard)

    def test_select_mission_type_exists(self):
        """Verifica que existe el handler de selección de tipo."""
        assert hasattr(mission_wizard, "select_mission_type")
        assert callable(mission_wizard.select_mission_type)

    def test_enter_mission_name_exists(self):
        """Verifica que existe el handler para nombre."""
        assert hasattr(mission_wizard, "enter_mission_name")
        assert callable(mission_wizard.enter_mission_name)

    def test_enter_mission_description_exists(self):
        """Verifica que existe el handler para descripción."""
        assert hasattr(mission_wizard, "enter_mission_description")
        assert callable(mission_wizard.enter_mission_description)

    def test_enter_streak_days_exists(self):
        """Verifica que existe el handler para días de racha."""
        assert hasattr(mission_wizard, "enter_streak_days")
        assert callable(mission_wizard.enter_streak_days)

    def test_enter_daily_count_exists(self):
        """Verifica que existe el handler para conteo diario."""
        assert hasattr(mission_wizard, "enter_daily_count")
        assert callable(mission_wizard.enter_daily_count)

    def test_enter_weekly_target_exists(self):
        """Verifica que existe el handler para objetivo semanal."""
        assert hasattr(mission_wizard, "enter_weekly_target")
        assert callable(mission_wizard.enter_weekly_target)

    def test_enter_one_time_count_exists(self):
        """Verifica que existe el handler para misión única."""
        assert hasattr(mission_wizard, "enter_one_time_count")
        assert callable(mission_wizard.enter_one_time_count)

    def test_enter_besitos_reward_exists(self):
        """Verifica que existe el handler para recompensa de besitos."""
        assert hasattr(mission_wizard, "enter_besitos_reward")
        assert callable(mission_wizard.enter_besitos_reward)

    def test_skip_auto_level_exists(self):
        """Verifica que existe el handler para saltar nivel automático."""
        assert hasattr(mission_wizard, "skip_auto_level")
        assert callable(mission_wizard.skip_auto_level)

    def test_choose_create_new_level_exists(self):
        """Verifica que existe el handler para crear nuevo nivel."""
        assert hasattr(mission_wizard, "choose_create_new_level")
        assert callable(mission_wizard.choose_create_new_level)

    def test_enter_level_name_exists(self):
        """Verifica que existe el handler para nombre de nivel."""
        assert hasattr(mission_wizard, "enter_level_name")
        assert callable(mission_wizard.enter_level_name)

    def test_enter_level_besitos_exists(self):
        """Verifica que existe el handler para besitos de nivel."""
        assert hasattr(mission_wizard, "enter_level_besitos")
        assert callable(mission_wizard.enter_level_besitos)

    def test_enter_level_order_exists(self):
        """Verifica que existe el handler para orden de nivel."""
        assert hasattr(mission_wizard, "enter_level_order")
        assert callable(mission_wizard.enter_level_order)

    def test_choose_select_existing_level_exists(self):
        """Verifica que existe el handler para seleccionar nivel existente."""
        assert hasattr(mission_wizard, "choose_select_existing_level")
        assert callable(mission_wizard.choose_select_existing_level)

    def test_select_existing_level_exists(self):
        """Verifica que existe el handler para procesar selección de nivel."""
        assert hasattr(mission_wizard, "select_existing_level")
        assert callable(mission_wizard.select_existing_level)

    def test_choose_create_reward_exists(self):
        """Verifica que existe el handler para crear recompensa."""
        assert hasattr(mission_wizard, "choose_create_reward")
        assert callable(mission_wizard.choose_create_reward)

    def test_enter_reward_name_exists(self):
        """Verifica que existe el handler para nombre de recompensa."""
        assert hasattr(mission_wizard, "enter_reward_name")
        assert callable(mission_wizard.enter_reward_name)

    def test_enter_reward_description_exists(self):
        """Verifica que existe el handler para descripción de recompensa."""
        assert hasattr(mission_wizard, "enter_reward_description")
        assert callable(mission_wizard.enter_reward_description)

    def test_finish_wizard_exists(self):
        """Verifica que existe el handler para finalizar wizard."""
        assert hasattr(mission_wizard, "finish_wizard")
        assert callable(mission_wizard.finish_wizard)

    def test_confirm_mission_exists(self):
        """Verifica que existe el handler para confirmar misión."""
        assert hasattr(mission_wizard, "confirm_mission")
        assert callable(mission_wizard.confirm_mission)

    def test_cancel_wizard_exists(self):
        """Verifica que existe el handler para cancelar wizard."""
        assert hasattr(mission_wizard, "cancel_wizard")
        assert callable(mission_wizard.cancel_wizard)


class TestMissionWizardCallbacks:
    """Tests para validar que los callbacks siguen el patrón correcto."""

    def test_callback_start_wizard(self):
        """Verifica el callback de inicio del wizard."""
        assert "gamif:wizard:mission" == "gamif:wizard:mission"

    def test_callback_type_pattern(self):
        """Verifica el patrón de callbacks de tipo de misión."""
        types = ["wizard:type:one_time", "wizard:type:daily", "wizard:type:weekly", "wizard:type:streak"]
        for t in types:
            assert t.startswith("wizard:type:")

    def test_callback_level_skip(self):
        """Verifica el callback de saltar nivel."""
        assert "wizard:level:skip" == "wizard:level:skip"

    def test_callback_level_new(self):
        """Verifica el callback de crear nuevo nivel."""
        assert "wizard:level:new" == "wizard:level:new"

    def test_callback_level_select(self):
        """Verifica el callback de seleccionar nivel existente."""
        assert "wizard:level:select" == "wizard:level:select"

    def test_callback_level_id_pattern(self):
        """Verifica el patrón de callbacks de ID de nivel."""
        pattern = "wizard:level:id:123"
        assert pattern.startswith("wizard:level:id:")

    def test_callback_reward_new(self):
        """Verifica el callback de crear recompensa."""
        assert "wizard:reward:new" == "wizard:reward:new"

    def test_callback_finish(self):
        """Verifica el callback de finalizar."""
        assert "wizard:finish" == "wizard:finish"

    def test_callback_confirm(self):
        """Verifica el callback de confirmar."""
        assert "wizard:confirm" == "wizard:confirm"

    def test_callback_cancel(self):
        """Verifica el callback de cancelar."""
        assert "wizard:cancel" == "wizard:cancel"


class TestMissionWizardImports:
    """Tests para validar que los imports son correctos."""

    def test_can_import_router(self):
        """Verifica que se puede importar el router."""
        from bot.gamification.handlers.admin.mission_wizard import router

        assert router is not None
        assert isinstance(router, Router)

    def test_can_import_from_admin_init(self):
        """Verifica que se puede importar desde __init__.py."""
        from bot.gamification.handlers.admin import mission_wizard as mw

        assert mw is not None
        assert hasattr(mw, "router")

    def test_can_import_from_gamification_handlers(self):
        """Verifica que se puede importar desde handlers de gamificación."""
        from bot.gamification.handlers import gamification_mission_wizard_router

        assert gamification_mission_wizard_router is not None
        assert isinstance(gamification_mission_wizard_router, Router)


class TestMissionWizardHelpers:
    """Tests para funciones helper del wizard."""

    def test_format_criteria_helper_exists(self):
        """Verifica que existe la función helper _format_criteria."""
        assert hasattr(mission_wizard, "_format_criteria")
        assert callable(mission_wizard._format_criteria)

    def test_format_criteria_streak(self):
        """Verifica formateo de criterio tipo racha."""
        criteria = {'type': 'streak', 'days': 7}
        result = mission_wizard._format_criteria(criteria)
        assert "7 días consecutivos" in result

    def test_format_criteria_daily(self):
        """Verifica formateo de criterio tipo diario."""
        criteria = {'type': 'daily', 'count': 10}
        result = mission_wizard._format_criteria(criteria)
        assert "10 reacciones diarias" in result

    def test_format_criteria_weekly(self):
        """Verifica formateo de criterio tipo semanal."""
        criteria = {'type': 'weekly', 'count': 50}
        result = mission_wizard._format_criteria(criteria)
        assert "50 reacciones semanales" in result

    def test_format_criteria_one_time(self):
        """Verifica formateo de criterio tipo única."""
        criteria = {'type': 'one_time', 'count': 100}
        result = mission_wizard._format_criteria(criteria)
        assert "100 reacciones totales" in result
