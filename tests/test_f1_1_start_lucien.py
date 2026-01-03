"""
Tests para F1.1 - Reescribir /start con voz de Lucien.

Valida:
- Mensajes de Lucien están disponibles
- Detección de tipos de usuario
- Construcción de menús según rol
"""
import pytest
from datetime import datetime, timezone, timedelta

from bot.utils.lucien_messages import LucienMessages


class TestLucienStartMessages:
    """Tests para mensajes de START en LucienMessages."""

    def test_start_new_user_1_exists(self):
        """Verifica que el mensaje NEW_USER_1 existe."""
        msg = LucienMessages.start("NEW_USER_1")
        assert "Lucien" in msg
        assert "filtro" in msg
        assert len(msg) > 50

    def test_start_new_user_2_exists(self):
        """Verifica que el mensaje NEW_USER_2 existe."""
        msg = LucienMessages.start("NEW_USER_2")
        assert "Besitos" in msg
        assert "Niveles" in msg
        assert "Gabinete" in msg
        assert len(msg) > 100

    def test_start_returning_user_with_params(self):
        """Verifica que RETURNING_USER acepta parámetros."""
        msg = LucienMessages.start("RETURNING_USER", days_away=3)
        assert "3 días" in msg or "3" in msg
        assert "persistencia" in msg.lower()

    def test_start_vip_user_with_params(self):
        """Verifica que VIP_USER acepta parámetros."""
        msg = LucienMessages.start("VIP_USER", user_name="Carlos", days_remaining=15)
        assert "Carlos" in msg
        assert "15" in msg
        assert "VIP" in msg

    def test_start_admin_with_params(self):
        """Verifica que ADMIN acepta parámetros."""
        msg = LucienMessages.start("ADMIN", user_name="Ana")
        assert "Ana" in msg
        assert "/admin" in msg

    def test_all_start_messages_exist(self):
        """Verifica que todos los mensajes de START existen."""
        messages = [
            "NEW_USER_1",
            "NEW_USER_2",
            "RETURNING_USER",
            "INACTIVE_USER",
            "LONG_INACTIVE_USER",
            "VIP_USER",
            "ADMIN",
        ]

        for msg_key in messages:
            msg = LucienMessages.start(msg_key)
            assert msg is not None
            assert len(msg) > 0, f"Mensaje {msg_key} está vacío"


class TestStartImports:
    """Tests para validar imports del handler start."""

    def test_start_handler_imports_lucien(self):
        """Verifica que start.py puede importar LucienMessages."""
        from bot.handlers.user import start
        assert hasattr(start, 'LucienMessages')

    def test_start_handler_has_detect_user_type(self):
        """Verifica que existe la función _detect_user_type."""
        from bot.handlers.user.start import _detect_user_type
        assert callable(_detect_user_type)


class TestGetMenuPrompt:
    """Tests para la función _get_menu_prompt."""

    def test_get_menu_prompt_for_new_user(self):
        """Verifica prompt para usuario nuevo."""
        from bot.handlers.user.start import _get_menu_prompt
        prompt = _get_menu_prompt('new')
        assert "comenzar" in prompt.lower()

    def test_get_menu_prompt_for_vip(self):
        """Verifica prompt para usuario VIP."""
        from bot.handlers.user.start import _get_menu_prompt
        prompt = _get_menu_prompt('vip')
        assert "círculo íntimo" in prompt.lower() or "intimo" in prompt.lower()

    def test_get_menu_prompt_default(self):
        """Verifica prompt por defecto."""
        from bot.handlers.user.start import _get_menu_prompt
        prompt = _get_menu_prompt('unknown')
        assert "Seleccione una opción" in prompt
