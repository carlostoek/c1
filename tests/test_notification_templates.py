"""
Tests para NotificationTemplates - Validación de templates HTML.

Verifica que los templates se renderizan correctamente con variables.
"""
import pytest

from bot.notifications.templates import NotificationTemplates


class TestNotificationTemplates:
    """Tests para la clase NotificationTemplates."""

    def test_welcome_template_render(self):
        """Test que template de bienvenida se renderiza correctamente."""
        context = {
            "first_name": "Juan",
            "role_name": "Free",
            "role_emoji": "👤"
        }

        result = NotificationTemplates.render("WELCOME_DEFAULT", context)

        assert "Juan" in result
        assert "Free" in result
        assert "👤" in result
        assert "<b>" in result  # HTML tags

    def test_besitos_earned_template(self):
        """Test que template de Besitos se renderiza correctamente."""
        context = {
            "amount": 50,
            "reason": "Primera reacción",
            "total_besitos": 150
        }

        result = NotificationTemplates.render("BESITOS_EARNED", context)

        assert "50" in result
        assert "Primera reacción" in result
        assert "150" in result
        assert "💋" in result

    def test_badge_unlocked_template(self):
        """Test que template de insignia se renderiza correctamente."""
        context = {
            "badge_icon": "🏆",
            "badge_name": "Reactor Pro",
            "badge_description": "50 reacciones totales",
            "total_badges": 3
        }

        result = NotificationTemplates.render("BADGE_UNLOCKED", context)

        assert "Reactor Pro" in result
        assert "50 reacciones totales" in result
        assert "3" in result

    def test_rank_up_template(self):
        """Test que template de subida de rango se renderiza correctamente."""
        context = {
            "old_rank": "Novato",
            "new_rank": "Bronce",
            "total_besitos": 500
        }

        result = NotificationTemplates.render("RANK_UP", context)

        assert "Novato" in result
        assert "Bronce" in result
        assert "500" in result

    def test_vip_activated_template(self):
        """Test que template de VIP activado se renderiza correctamente."""
        context = {
            "plan_name": "Plan Mensual",
            "price": "$10",
            "duration_days": 30,
            "expiry_date": "2024-01-15"
        }

        result = NotificationTemplates.render("VIP_ACTIVATED", context)

        assert "Plan Mensual" in result
        assert "$10" in result
        assert "30" in result
        assert "2024-01-15" in result

    def test_daily_login_template(self):
        """Test que template de login diario se renderiza correctamente."""
        context = {
            "besitos": 25,
            "streak_days": 5,
            "streak_bonus": "+10 Besitos extra por racha"
        }

        result = NotificationTemplates.render("DAILY_LOGIN", context)

        assert "25" in result
        assert "5" in result
        assert "racha" in result

    def test_info_template(self):
        """Test que template de info se renderiza correctamente."""
        context = {
            "message": "El bot será actualizado el 15 de enero"
        }

        result = NotificationTemplates.render("INFO", context)

        assert "El bot será actualizado el 15 de enero" in result
        assert "ℹ️" in result

    def test_warning_template(self):
        """Test que template de advertencia se renderiza correctamente."""
        context = {
            "message": "Tu suscripción expira en 3 días"
        }

        result = NotificationTemplates.render("WARNING", context)

        assert "Tu suscripción expira en 3 días" in result
        assert "⚠️" in result

    def test_error_template(self):
        """Test que template de error se renderiza correctamente."""
        context = {
            "message": "Error al procesar tu solicitud"
        }

        result = NotificationTemplates.render("ERROR", context)

        assert "Error al procesar tu solicitud" in result
        assert "❌" in result

    def test_render_nonexistent_template(self):
        """Test que render lanza error para template inexistente."""
        with pytest.raises(ValueError, match="Template no encontrado"):
            NotificationTemplates.render("TEMPLATE_INEXISTENTE", {})

    def test_render_missing_variable(self):
        """Test que render lanza error si falta variable."""
        context = {
            "amount": 50
            # Falta "reason" y "total_besitos"
        }

        with pytest.raises(ValueError, match="Variable faltante en template"):
            NotificationTemplates.render("BESITOS_EARNED", context)

    def test_all_templates_have_html_tags(self):
        """Test que todos los templates tienen HTML tags (excepto INFO/WARNING/ERROR sin variables)."""
        templates_to_check = [
            ("WELCOME_DEFAULT", {"first_name": "Test", "role_name": "Free", "role_emoji": "👤"}),
            ("BESITOS_EARNED", {"amount": 50, "reason": "Test", "total_besitos": 100}),
            ("BADGE_UNLOCKED", {"badge_icon": "🏆", "badge_name": "Test", "badge_description": "Desc", "total_badges": 1}),
        ]

        for template_name, context in templates_to_check:
            result = NotificationTemplates.render(template_name, context)
            assert "<b>" in result, f"Template {template_name} no tiene tags HTML"

    def test_templates_contain_emojis(self):
        """Test que templates contienen emojis apropiados."""
        test_cases = [
            ("WELCOME_DEFAULT", "👋", {"first_name": "Test", "role_name": "Free", "role_emoji": "👤"}),
            ("BESITOS_EARNED", "💋", {"amount": 50, "reason": "Test", "total_besitos": 100}),
            ("BADGE_UNLOCKED", "🏆", {"badge_icon": "🏆", "badge_name": "Test", "badge_description": "D", "total_badges": 1}),
            ("RANK_UP", "⭐", {"old_rank": "A", "new_rank": "B", "total_besitos": 100}),
            ("VIP_ACTIVATED", "🎉", {"plan_name": "P", "price": "$", "duration_days": 30, "expiry_date": "Date"}),
        ]

        for template_name, expected_emoji, context in test_cases:
            result = NotificationTemplates.render(template_name, context)
            assert expected_emoji in result, f"Template {template_name} debería contener {expected_emoji}"

    def test_long_context_values(self):
        """Test que templates manejan valores largos correctamente."""
        context = {
            "first_name": "Juan Carlos Roberto García del Río Martínez",
            "role_name": "Premium VIP Plus Deluxe Ultra Máximo",
            "role_emoji": "👑"
        }

        result = NotificationTemplates.render("WELCOME_DEFAULT", context)

        assert "Juan Carlos Roberto García del Río Martínez" in result
        assert "Premium VIP Plus Deluxe Ultra Máximo" in result

    def test_special_characters_in_context(self):
        """Test que templates manejan caracteres especiales."""
        context = {
            "amount": 100,
            "reason": "Test <b>Bold</b> & Special \"Chars\"",
            "total_besitos": 500
        }

        # Las comillas y caracteres especiales deben pasar sin problemas
        result = NotificationTemplates.render("BESITOS_EARNED", context)

        assert "Test" in result
        assert "500" in result


class TestTemplateStructure:
    """Tests de estructura de templates."""

    def test_all_templates_are_strings(self):
        """Test que todos los templates del repositorio son strings."""
        # Obtener todos los atributos de NotificationTemplates
        template_attrs = [
            attr for attr in dir(NotificationTemplates)
            if not attr.startswith("_") and attr.isupper()
        ]

        for attr_name in template_attrs:
            attr = getattr(NotificationTemplates, attr_name)
            assert isinstance(attr, str), f"{attr_name} no es string"

    def test_template_placeholders_format(self):
        """Test que placeholders en templates tienen formato correcto."""
        context = {
            "first_name": "Test",
            "role_name": "Free",
            "role_emoji": "👤"
        }

        result = NotificationTemplates.render("WELCOME_DEFAULT", context)

        # No debe quedar ningún placeholder sin reemplazar
        assert "{" not in result, "Quedan placeholders sin reemplazar en el template"
        assert "}" not in result, "Quedan placeholders sin reemplazar en el template"
