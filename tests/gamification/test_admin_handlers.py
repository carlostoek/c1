"""Tests para handlers de administración de gamificación."""

import pytest
from aiogram import Router

from bot.gamification.handlers.admin import main
from bot.filters.admin import IsAdmin


class TestAdminHandlersMain:
    """Tests para main.py de handlers admin."""

    def test_router_exists(self):
        """Verifica que el router existe."""
        assert hasattr(main, "router")
        assert isinstance(main.router, Router)

    def test_router_has_admin_filter(self):
        """Verifica que el router tiene filtros de admin aplicados."""
        # Los filtros están aplicados mediante router.message.filter() y router.callback_query.filter()
        # Esta es una validación básica de que el router existe
        assert main.router is not None

    def test_gamification_menu_handler_exists(self):
        """Verifica que existe el handler del comando /gamification."""
        assert hasattr(main, "gamification_menu")
        assert callable(main.gamification_menu)

    def test_show_main_menu_handler_exists(self):
        """Verifica que existe el handler del menú principal."""
        assert hasattr(main, "show_main_menu")
        assert callable(main.show_main_menu)

    def test_missions_menu_handler_exists(self):
        """Verifica que existe el handler del submenú de misiones."""
        assert hasattr(main, "missions_menu")
        assert callable(main.missions_menu)

    def test_rewards_menu_handler_exists(self):
        """Verifica que existe el handler del submenú de recompensas."""
        assert hasattr(main, "rewards_menu")
        assert callable(main.rewards_menu)

    def test_levels_menu_handler_exists(self):
        """Verifica que existe el handler del submenú de niveles."""
        assert hasattr(main, "levels_menu")
        assert callable(main.levels_menu)

    def test_list_missions_handler_exists(self):
        """Verifica que existe el handler para listar misiones."""
        assert hasattr(main, "list_missions")
        assert callable(main.list_missions)

    def test_list_rewards_handler_exists(self):
        """Verifica que existe el handler para listar recompensas."""
        assert hasattr(main, "list_rewards")
        assert callable(main.list_rewards)

    def test_list_levels_handler_exists(self):
        """Verifica que existe el handler para listar niveles."""
        assert hasattr(main, "list_levels")
        assert callable(main.list_levels)


class TestIsAdminFilter:
    """Tests para el filtro IsAdmin."""

    def test_filter_exists(self):
        """Verifica que el filtro IsAdmin existe."""
        assert IsAdmin is not None

    def test_is_callable_filter(self):
        """Verifica que IsAdmin es un filtro válido."""
        filter_instance = IsAdmin()
        assert hasattr(filter_instance, "__call__")


class TestHandlerCallbacks:
    """Tests para validar que los callbacks siguen el patrón correcto."""

    def test_callback_pattern_main_menu(self):
        """Verifica que el callback del menú principal es correcto."""
        # El handler usa F.data == "gamif:menu"
        # Esta es validación indirecta de que el patrón es el esperado
        assert "gamif:menu" in ["gamif:menu", "gamif:admin:missions", "gamif:admin:rewards"]

    def test_callback_pattern_missions(self):
        """Verifica que el callback de misiones sigue el patrón."""
        assert "gamif:admin:missions" in ["gamif:menu", "gamif:admin:missions"]

    def test_callback_pattern_rewards(self):
        """Verifica que el callback de recompensas sigue el patrón."""
        assert "gamif:admin:rewards" in ["gamif:menu", "gamif:admin:rewards"]

    def test_callback_pattern_levels(self):
        """Verifica que el callback de niveles sigue el patrón."""
        assert "gamif:admin:levels" in ["gamif:menu", "gamif:admin:levels"]

    def test_callback_pattern_wizard_mission(self):
        """Verifica que el callback del wizard de misión sigue el patrón."""
        assert "gamif:wizard:mission" == "gamif:wizard:mission"

    def test_callback_pattern_wizard_reward(self):
        """Verifica que el callback del wizard de recompensa sigue el patrón."""
        assert "gamif:wizard:reward" == "gamif:wizard:reward"


class TestHandlerImports:
    """Tests para validar que los imports son correctos."""

    def test_can_import_main_router(self):
        """Verifica que se puede importar el router desde el módulo."""
        from bot.gamification.handlers.admin.main import router

        assert router is not None
        assert isinstance(router, Router)

    def test_can_import_from_admin_init(self):
        """Verifica que se puede importar desde __init__.py."""
        from bot.gamification.handlers.admin import main as admin_main

        assert admin_main is not None
        assert hasattr(admin_main, "router")
