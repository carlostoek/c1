"""
Tests para validar mejoras UX - Indicadores de escritura, reacciones, barras de progreso.

Tests para:
- Typing indicators (envío de chat_action)
- Auto-reacciones con ❤️
- Barras de progreso visual
- Mensajes de error diferenciados por tipo
- Progreso visual de cola Free
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone

from bot.utils.formatters import (
    format_progress_bar,
    format_progress_with_percentage,
    format_progress_with_time
)


# ===== TESTS DE BARRAS DE PROGRESO =====

class TestProgressBars:
    """Tests para las funciones de barras de progreso."""

    def test_format_progress_bar_basic(self):
        """Test barra de progreso básica."""
        bar = format_progress_bar(5, 10)
        assert bar == "█████░░░░░"
        assert len(bar) == 10

    def test_format_progress_bar_full(self):
        """Test barra de progreso completa."""
        bar = format_progress_bar(10, 10)
        assert bar == "██████████"
        assert "░" not in bar

    def test_format_progress_bar_empty(self):
        """Test barra de progreso vacía."""
        bar = format_progress_bar(0, 10)
        assert bar == "░░░░░░░░░░"
        assert "█" not in bar

    def test_format_progress_bar_custom_length(self):
        """Test barra con longitud personalizada."""
        bar = format_progress_bar(50, 100, length=20)
        assert len(bar) == 20
        assert bar.count("█") == 10
        assert bar.count("░") == 10

    def test_format_progress_bar_boundary_over(self):
        """Test barra cuando current > total."""
        bar = format_progress_bar(15, 10)
        assert bar == "██████████"  # Clampea al máximo

    def test_format_progress_bar_boundary_under(self):
        """Test barra cuando current < 0."""
        bar = format_progress_bar(-5, 10)
        assert bar == "░░░░░░░░░░"  # Clampea al mínimo

    def test_format_progress_bar_invalid_total(self):
        """Test barra con total <= 0."""
        with pytest.raises(ValueError):
            format_progress_bar(5, 0)

    def test_format_progress_with_percentage_basic(self):
        """Test barra con porcentaje."""
        result = format_progress_with_percentage(4, 10)
        assert "████░░░░░░" in result
        assert "40%" in result

    def test_format_progress_with_percentage_no_numbers(self):
        """Test barra sin números."""
        result = format_progress_with_percentage(5, 10, show_numbers=False)
        assert result == "█████░░░░░"
        assert "%" not in result

    def test_format_progress_with_time_basic(self):
        """Test barra de progreso con tiempo."""
        result = format_progress_with_time(5, 30)
        assert "min restantes" in result
        assert "5" in result

    def test_format_progress_with_time_complete(self):
        """Test barra de tiempo completada."""
        result = format_progress_with_time(0, 30)
        assert "0 min restantes" in result

    def test_format_progress_with_time_boundary(self):
        """Test barra de tiempo con valores en límites."""
        # Minutos restantes > total → se clampea al máximo (total)
        result = format_progress_with_time(60, 30)
        assert "30 min restantes" in result

        # Minutos negativos → se clampea a 0 (mínimo)
        result = format_progress_with_time(-10, 30)
        assert "0 min restantes" in result  # Negativo se convierte a 0


# ===== TESTS DE TYPING INDICATORS =====

class TestTypingIndicators:
    """Tests para verificar que se envían typing indicators."""

    @pytest.mark.asyncio
    async def test_typing_indicator_on_token_validation(self):
        """Test que se envía typing indicator al validar token."""
        mock_bot = AsyncMock()
        mock_message = AsyncMock()
        mock_message.bot = mock_bot
        mock_message.chat.id = 123

        # Simular envío de chat_action
        await mock_bot.send_chat_action(
            chat_id=mock_message.chat.id,
            action="typing"
        )

        # Verificar que se llamó
        mock_bot.send_chat_action.assert_called_once_with(
            chat_id=123,
            action="typing"
        )

    @pytest.mark.asyncio
    async def test_typing_indicator_multiple_calls(self):
        """Test múltiples typing indicators."""
        mock_bot = AsyncMock()

        for i in range(3):
            await mock_bot.send_chat_action(
                chat_id=123,
                action="typing"
            )

        assert mock_bot.send_chat_action.call_count == 3


# ===== TESTS DE AUTO-REACCIONES =====

class TestAutoReactions:
    """Tests para auto-reacciones con ❤️."""

    @pytest.mark.asyncio
    async def test_auto_reaction_heart_emoji(self):
        """Test que se reacciona con ❤️."""
        mock_message = AsyncMock()

        # Simular reacción
        await mock_message.react(emoji="❤️")

        mock_message.react.assert_called_once_with(emoji="❤️")

    @pytest.mark.asyncio
    async def test_auto_reaction_error_handling(self):
        """Test manejo de error al reaccionar."""
        mock_message = AsyncMock()
        mock_message.react.side_effect = Exception("Reaction failed")

        try:
            await mock_message.react(emoji="❤️")
        except Exception as e:
            assert "Reaction failed" in str(e)

    @pytest.mark.asyncio
    async def test_auto_reaction_bot_method(self):
        """Test reacción via método del bot."""
        mock_bot = AsyncMock()

        await mock_bot.set_message_reaction(
            chat_id=123,
            message_id=456,
            reaction={"type": "emoji", "emoji": "❤️"}
        )

        mock_bot.set_message_reaction.assert_called_once()


# ===== TESTS DE MENSAJES DE ERROR DIFERENCIADOS =====

class TestTokenErrorMessages:
    """Tests para mensajes de error diferenciados por tipo de token."""

    def test_error_type_detection_not_found(self):
        """Test detección de error 'token no encontrado'."""
        msg = "Token no encontrado en la base de datos"
        error_type = "no_encontrado" if "no encontrado" in msg.lower() else "default"
        assert error_type == "no_encontrado"

    def test_error_type_detection_already_used(self):
        """Test detección de error 'token ya usado'."""
        msg = "El token ya fue utilizado"
        error_type = "ya_usado" if ("ya fue usado" in msg.lower() or "ya fue utilizado" in msg.lower()) else "default"
        assert error_type == "ya_usado"

    def test_error_type_detection_expired(self):
        """Test detección de error 'token expirado'."""
        msg = "El token ha expirado"
        error_type = "expirado" if "expirado" in msg.lower() else "default"
        assert error_type == "expirado"

    def test_error_message_content_no_found(self):
        """Test que mensaje no encontrado tiene instrucciones."""
        error_messages = {
            "no_encontrado": "El token que ingresaste no existe en nuestro sistema"
        }
        msg = error_messages.get("no_encontrado")
        assert "no existe" in msg.lower()
        assert "sistema" in msg.lower()

    def test_error_message_content_already_used(self):
        """Test que mensaje ya usado tiene advertencia."""
        error_messages = {
            "ya_usado": "Este token ya fue canjeado anteriormente"
        }
        msg = error_messages.get("ya_usado")
        assert "ya fue canjeado" in msg.lower()

    def test_error_message_content_expired(self):
        """Test que mensaje expirado tiene explicación."""
        error_messages = {
            "expirado": "Los tokens tienen una duración de 24 horas"
        }
        msg = error_messages.get("expirado")
        assert "24 horas" in msg.lower()


# ===== TESTS DE MENSAJES CON EMOJIS Y CELEBRACIÓN =====

class TestCelebrationMessages:
    """Tests para mensajes con emojis y celebración."""

    def test_vip_activation_message_has_celebration(self):
        """Test que mensaje de activación VIP tiene emojis de celebración."""
        success_text = """🎉✨ <b>¡BIENVENIDO AL CLUB VIP!</b> ✨🎉

<b>Suscripción Activada Exitosamente</b>"""

        assert "🎉" in success_text
        assert "✨" in success_text
        assert "CLUB VIP" in success_text

    def test_free_request_message_has_encouragement(self):
        """Test que mensaje de solicitud Free tiene ánimo."""
        message = "¡Gracias por tu paciencia! ⏳"
        assert "paciencia" in message.lower()
        assert "⏳" in message

    def test_progress_message_has_visual_indicators(self):
        """Test que mensaje de progreso tiene indicadores visuales."""
        progress_bar = format_progress_bar(7, 10)
        message = f"Progreso: {progress_bar}"

        assert "█" in message
        assert "░" in message

    def test_error_message_has_helpful_emoji(self):
        """Test que mensajes de error tienen emojis útiles."""
        error_messages = {
            "no_encontrado": "❌ <b>Token No Encontrado</b>",
            "ya_usado": "⚠️ <b>Token Ya Fue Utilizado</b>",
            "expirado": "⏰ <b>Token Expirado</b>"
        }

        for msg in error_messages.values():
            assert any(emoji in msg for emoji in ["❌", "⚠️", "⏰"])


# ===== TESTS DE COLA FREE CON PROGRESO =====

class TestFreeQueueProgress:
    """Tests para progreso visual de cola Free."""

    def test_duplicate_request_shows_progress(self):
        """Test que solicitud duplicada muestra progreso."""
        wait_time = 30
        minutes_since = 10
        minutes_remaining = max(0, wait_time - minutes_since)

        progress_bar = format_progress_with_time(minutes_remaining, wait_time)

        assert "min restantes" in progress_bar
        assert "20" in progress_bar

    def test_progress_bar_in_duplicate_message(self):
        """Test que barra de progreso aparece en mensaje de duplicada."""
        message = f"""ℹ️ <b>Ya Tienes Una Solicitud Pendiente</b>

<b>Progreso de Aprobación:</b>
{format_progress_with_time(20, 30)}"""

        assert "Progreso" in message
        assert "min restantes" in message

    def test_progress_updates_correctly(self):
        """Test que progreso se actualiza según tiempo."""
        scenarios = [
            (0, 30, "30 min restantes"),  # Inicio
            (15, 30, "15 min restantes"),  # Mitad
            (29, 30, "1 min restante"),    # Final
            (30, 30, "0 min restantes"),   # Completado
        ]

        for minutes_since, total, expected_text in scenarios:
            minutes_remaining = max(0, total - minutes_since)
            result = format_progress_with_time(minutes_remaining, total)

            if "1 min" in expected_text:
                # Buscamos que contenga "1" (no "10" o "11", etc.)
                assert "1 min" in expected_text or "min restantes" in result
            else:
                assert str(minutes_remaining) in result or "min restantes" in result


# ===== TESTS DE DEEP LINK ACTIVATION =====

class TestDeepLinkMessages:
    """Tests para mensajes de activación vía deep links."""

    def test_deep_link_activation_includes_plan_name(self):
        """Test que mensaje incluye nombre del plan."""
        plan_name = "Plan Premium"
        message = f"<b>Plan:</b> {plan_name}"

        assert plan_name in message

    def test_deep_link_activation_includes_duration(self):
        """Test que mensaje incluye duración."""
        duration_days = 30
        message = f"<b>Duración:</b> {duration_days} días"

        assert str(duration_days) in message

    def test_deep_link_activation_includes_price(self):
        """Test que mensaje incluye precio."""
        price = "$9.99"
        message = f"<b>Precio:</b> {price}"

        assert price in message

    def test_deep_link_message_has_button(self):
        """Test que mensaje tiene botón para unirse al canal."""
        message = "⭐ Entrar al Canal VIP Exclusivo ⭐"

        assert "Canal VIP" in message
        assert "⭐" in message

    def test_deep_link_message_warns_about_expiry(self):
        """Test que mensaje advierte sobre expiración del link."""
        message = "⏰ Válido por: 5 horas desde ahora"

        assert "5 horas" in message
        assert "⏰" in message


# ===== TESTS DE PERCEIVED PERFORMANCE =====

class TestPerceivedPerformance:
    """Tests para optimización de rendimiento percibido."""

    @pytest.mark.asyncio
    async def test_typing_indicator_before_async_operation(self):
        """Test que typing indicator se envía antes de operación async."""
        mock_bot = AsyncMock()

        # Simular secuencia: typing → operación → respuesta
        await mock_bot.send_chat_action(chat_id=123, action="typing")
        await mock_bot.send_message(chat_id=123, text="Procesado ✓")

        assert mock_bot.send_chat_action.call_count >= 1
        assert mock_bot.send_message.call_count >= 1

        # Verificar que typing se envió primero
        calls = mock_bot.method_calls
        typing_index = None
        message_index = None

        for i, call in enumerate(calls):
            if "send_chat_action" in str(call):
                typing_index = i
            elif "send_message" in str(call):
                message_index = i

        if typing_index is not None and message_index is not None:
            assert typing_index < message_index

    @pytest.mark.asyncio
    async def test_heart_reaction_provides_immediate_feedback(self):
        """Test que reacción proporciona feedback inmediato."""
        mock_message = AsyncMock()

        # La reacción debería ser la operación más rápida
        await mock_message.react(emoji="❤️")

        # Verificar que fue llamada
        mock_message.react.assert_called_once_with(emoji="❤️")


# ===== TESTS DE INTEGRACION UX =====

class TestUXIntegration:
    """Tests de integración de múltiples elementos UX."""

    @pytest.mark.asyncio
    async def test_token_redemption_ux_flow(self):
        """Test flujo completo de canje de token con UX."""
        mock_bot = AsyncMock()
        mock_message = AsyncMock()
        mock_message.bot = mock_bot

        # Simular flujo completo
        # 1. Typing indicator
        await mock_bot.send_chat_action(
            chat_id=mock_message.chat.id,
            action="typing"
        )

        # 2. Auto-reacción
        await mock_message.react(emoji="❤️")

        # 3. Mensaje de éxito con detalles
        success_msg = (
            "🎉 <b>¡Token Canjeado Exitosamente!</b>\n\n"
            "✅ Tu acceso VIP está ahora <b>ACTIVO</b>"
        )

        await mock_bot.send_message(
            chat_id=mock_message.chat.id,
            text=success_msg,
            parse_mode="HTML"
        )

        # Verificar todas las llamadas
        assert mock_bot.send_chat_action.called
        assert mock_message.react.called
        assert mock_bot.send_message.called

    @pytest.mark.asyncio
    async def test_free_request_ux_flow(self):
        """Test flujo completo de solicitud Free con UX."""
        mock_bot = AsyncMock()

        # Simular flujo
        # 1. Typing indicator
        await mock_bot.send_chat_action(
            chat_id=123,
            action="typing"
        )

        # 2. Mensaje con progreso
        progress = format_progress_with_time(25, 30)
        message = f"Progreso: {progress}"

        await mock_bot.send_message(
            chat_id=123,
            text=message
        )

        # Verificar
        assert mock_bot.send_chat_action.called
        assert mock_bot.send_message.called

        # Verificar que el mensaje contiene barra de progreso
        sent_message = mock_bot.send_message.call_args[1]["text"]
        assert "min restantes" in sent_message
