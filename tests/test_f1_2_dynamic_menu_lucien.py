"""
Tests para F1.2 - Reescribir menú dinámico con voz de Lucien.

Valida:
- Mensajes de menú están disponibles
- Versiones cortas de errores para callbacks
- Callbacks responden correctamente
"""
import pytest
from bot.utils.lucien_messages import LucienMessages


class TestLucienMenuMessages:
    """Tests para mensajes de MENU en LucienMessages."""

    def test_menu_back_to_start_exists(self):
        """Verifica que el mensaje BACK_TO_START existe."""
        msg = LucienMessages.menu("BACK_TO_START")
        assert "volver" in msg.lower()
        assert len(msg) > 50

    def test_menu_item_not_available_exists(self):
        """Verifica que el mensaje ITEM_NOT_AVAILABLE existe."""
        msg = LucienMessages.menu("ITEM_NOT_AVAILABLE")
        assert "existe" in msg.lower() or "misterios" in msg.lower()
        assert len(msg) > 30

    def test_menu_item_inactive_exists(self):
        """Verifica que el mensaje ITEM_INACTIVE existe."""
        msg = LucienMessages.menu("ITEM_INACTIVE")
        assert "disponible" in msg.lower() or "cambia" in msg.lower()
        assert len(msg) > 30

    def test_menu_item_info_header_exists(self):
        """Verifica que el mensaje ITEM_INFO_HEADER existe."""
        msg = LucienMessages.menu("ITEM_INFO_HEADER")
        assert "información" in msg.lower()
        assert len(msg) > 30

    def test_menu_item_contact_header_exists(self):
        """Verifica que el mensaje ITEM_CONTACT_HEADER existe."""
        msg = LucienMessages.menu("ITEM_CONTACT_HEADER")
        assert "contacto" in msg.lower()
        assert len(msg) > 30

    def test_all_menu_messages_exist(self):
        """Verifica que todos los mensajes de MENU existen."""
        messages = [
            "BACK_TO_START",
            "ITEM_NOT_AVAILABLE",
            "ITEM_INACTIVE",
            "ITEM_INFO_HEADER",
            "ITEM_CONTACT_HEADER",
        ]

        for msg_key in messages:
            msg = LucienMessages.menu(msg_key)
            assert msg is not None
            assert len(msg) > 0, f"Mensaje {msg_key} está vacío"


class TestShortErrorMessages:
    """Tests para mensajes cortos de error (para callbacks)."""

    def test_error_short_exists(self):
        """Verifica que ERROR_SHORT existe y es corto (<200 chars)."""
        msg = LucienMessages.errors("ERROR_SHORT")
        assert len(msg) < 200
        assert len(msg) > 0

    def test_not_found_short_exists(self):
        """Verifica que NOT_FOUND_SHORT existe y es corto."""
        msg = LucienMessages.errors("NOT_FOUND_SHORT")
        assert len(msg) < 200
        assert "existe" in msg.lower() or "no" in msg.lower()

    def test_permission_short_exists(self):
        """Verifica que PERMISSION_SHORT existe y es corto."""
        msg = LucienMessages.errors("PERMISSION_SHORT")
        assert len(msg) < 200
        assert "autorización" in msg.lower() or "permiso" in msg.lower()

    def test_inactive_short_exists(self):
        """Verifica que INACTIVE_SHORT existe y es corto."""
        msg = LucienMessages.errors("INACTIVE_SHORT")
        assert len(msg) < 200
        assert "disponible" in msg.lower() or "no" in msg.lower()

    def test_rate_limit_short_exists(self):
        """Verifica que RATE_LIMIT_SHORT existe y es corto."""
        msg = LucienMessages.errors("RATE_LIMIT_SHORT")
        assert len(msg) < 200
        assert "rápido" in msg.lower() or "espere" in msg.lower()

    def test_all_short_errors_under_200_chars(self):
        """Verifica que todos los errores cortos cumplen el límite."""
        short_errors = [
            "ERROR_SHORT",
            "NOT_FOUND_SHORT",
            "PERMISSION_SHORT",
            "INACTIVE_SHORT",
            "RATE_LIMIT_SHORT",
        ]

        for error_key in short_errors:
            msg = LucienMessages.errors(error_key)
            assert len(msg) < 200, f"{error_key} excede 200 caracteres: {len(msg)}"
            assert len(msg) > 0, f"{error_key} está vacío"


class TestDynamicMenuImports:
    """Tests para validar imports del handler dynamic_menu."""

    def test_dynamic_menu_imports_lucien(self):
        """Verifica que dynamic_menu.py puede importar LucienMessages."""
        from bot.handlers.user import dynamic_menu
        assert hasattr(dynamic_menu, 'LucienMessages')

    def test_dynamic_menu_has_callbacks(self):
        """Verifica que existen los callbacks principales."""
        from bot.handlers.user.dynamic_menu import (
            callback_dynamic_menu_item,
            callback_back_to_start_menu
        )
        assert callable(callback_dynamic_menu_item)
        assert callable(callback_back_to_start_menu)


class TestMenuCategoryInHelper:
    """Tests para validar que la categoría 'menu' está en el helper."""

    def test_get_lucien_message_supports_menu(self):
        """Verifica que get_lucien_message soporta la categoría 'menu'."""
        from bot.utils.lucien_messages import get_lucien_message

        msg = get_lucien_message("menu", "BACK_TO_START")
        assert msg is not None
        assert len(msg) > 0
