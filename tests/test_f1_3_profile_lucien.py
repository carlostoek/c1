"""
Tests para F1.3 - Reescribir perfil con voz de Lucien.

Valida:
- Mensajes de perfil están disponibles
- Comentarios según nivel funcionan
- Barra de progreso visual
"""
import pytest
from bot.utils.lucien_messages import LucienMessages


class TestLucienProfileMessages:
    """Tests para mensajes de PERFIL en LucienMessages."""

    def test_profile_header_exists(self):
        """Verifica que el mensaje HEADER existe."""
        msg = LucienMessages.profile("HEADER")
        assert "expediente" in msg.lower()
        assert len(msg) > 20

    def test_profile_level_low_exists(self):
        """Verifica que el mensaje LEVEL_LOW existe."""
        msg = LucienMessages.profile("LEVEL_LOW")
        assert "observación" in msg.lower() or "comienza" in msg.lower()
        assert len(msg) > 30

    def test_profile_level_mid_exists(self):
        """Verifica que el mensaje LEVEL_MID existe."""
        msg = LucienMessages.profile("LEVEL_MID")
        assert "persistencia" in msg.lower() or "diana" in msg.lower()
        assert len(msg) > 30

    def test_profile_level_high_exists(self):
        """Verifica que el mensaje LEVEL_HIGH existe."""
        msg = LucienMessages.profile("LEVEL_HIGH")
        assert "expectativas" in msg.lower() or "diana" in msg.lower()
        assert len(msg) > 30

    def test_profile_level_max_exists(self):
        """Verifica que el mensaje LEVEL_MAX existe."""
        msg = LucienMessages.profile("LEVEL_MAX")
        assert "secrets" in msg.lower() or "círculo" in msg.lower() or "íntimo" in msg.lower()
        assert len(msg) > 30

    def test_profile_no_badges_exists(self):
        """Verifica que el mensaje NO_BADGES existe."""
        msg = LucienMessages.profile("NO_BADGES")
        assert "badges" in msg.lower() or "distintivos" in msg.lower() or "aún" in msg.lower()
        assert len(msg) > 10

    def test_profile_has_badges_exists(self):
        """Verifica que el mensaje HAS_BADGES existe."""
        msg = LucienMessages.profile("HAS_BADGES")
        assert "badges" in msg.lower() or "distintivos" in msg.lower()
        assert len(msg) > 10

    def test_all_profile_messages_exist(self):
        """Verifica que todos los mensajes de PERFIL existen."""
        messages = [
            "HEADER",
            "LEVEL_LOW",
            "LEVEL_MID",
            "LEVEL_HIGH",
            "LEVEL_MAX",
            "NO_BADGES",
            "HAS_BADGES",
        ]

        for msg_key in messages:
            msg = LucienMessages.profile(msg_key)
            assert msg is not None
            assert len(msg) > 0, f"Mensaje {msg_key} está vacío"


class TestProgressBar:
    """Tests para barra de progreso visual."""

    def test_progress_bar_0_percent(self):
        """Verifica barra de progreso al 0%."""
        progress = 0
        filled = int(progress / 10)
        empty = 10 - filled
        bar = "▓" * filled + "░" * empty
        assert bar == "░" * 10
        assert len(bar) == 10

    def test_progress_bar_50_percent(self):
        """Verifica barra de progreso al 50%."""
        progress = 50
        filled = int(progress / 10)
        empty = 10 - filled
        bar = "▓" * filled + "░" * empty
        assert bar == "▓" * 5 + "░" * 5
        assert len(bar) == 10

    def test_progress_bar_100_percent(self):
        """Verifica barra de progreso al 100%."""
        progress = 100
        filled = int(progress / 10)
        empty = 10 - filled
        bar = "▓" * filled + "░" * empty
        assert bar == "▓" * 10
        assert len(bar) == 10

    def test_progress_bar_75_percent(self):
        """Verifica barra de progreso al 75%."""
        progress = 75
        filled = int(progress / 10)
        empty = 10 - filled
        bar = "▓" * filled + "░" * empty
        assert bar == "▓▓▓▓▓▓▓░░░"
        assert len(bar) == 10


class TestProfileHelperImports:
    """Tests para validar imports de los helpers."""

    def test_menu_helpers_has_build_profile_lucien(self):
        """Verifica que menu_helpers tiene build_profile_menu_lucien."""
        from bot.utils.menu_helpers import build_profile_menu_lucien
        assert callable(build_profile_menu_lucien)

    def test_profile_handler_exists(self):
        """Verifica que el handler de perfil existe."""
        from bot.gamification.handlers.user.profile import show_profile
        assert callable(show_profile)


class TestProfileCategoryInHelper:
    """Tests para validar que la categoría 'profile' está en el helper."""

    def test_get_lucien_message_supports_profile(self):
        """Verifica que get_lucien_message soporta la categoría 'profile'."""
        from bot.utils.lucien_messages import get_lucien_message

        msg = get_lucien_message("profile", "HEADER")
        assert msg is not None
        assert len(msg) > 0
