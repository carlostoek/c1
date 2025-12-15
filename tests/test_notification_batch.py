"""
Tests para RewardBatch - Sistema de agrupación de recompensas.

Valida que el sistema de batching funcione correctamente para
agrupar múltiples recompensas en una sola notificación.
"""
import pytest

from bot.notifications.batch import Reward, RewardBatch


class TestReward:
    """Tests para la clase Reward."""

    def test_reward_format_with_description(self):
        """Test que reward formatea correctamente con descripción."""
        reward = Reward(
            type="besitos",
            value="+50 Besitos 💋",
            icon="💋",
            description="Primera reacción del día"
        )

        formatted = reward.format()

        assert "💋" in formatted
        assert "+50 Besitos 💋" in formatted
        assert "Primera reacción del día" in formatted
        assert "-" in formatted  # Separador entre valor y descripción

    def test_reward_format_without_description(self):
        """Test que reward formatea correctamente sin descripción."""
        reward = Reward(
            type="badge",
            value="🔥 Hot Streak",
            icon="🏆"
        )

        formatted = reward.format()

        assert "🏆" in formatted
        assert "🔥 Hot Streak" in formatted
        assert "-" not in formatted  # No hay separador sin descripción


class TestRewardBatch:
    """Tests para la clase RewardBatch."""

    def test_batch_initialization(self):
        """Test que batch se inicializa correctamente."""
        batch = RewardBatch(user_id=123, action="Reaccionaste a un mensaje")

        assert batch.user_id == 123
        assert batch.action == "Reaccionaste a un mensaje"
        assert batch.is_empty is True
        assert batch.count == 0

    def test_add_besitos(self):
        """Test que se agregan Besitos correctamente."""
        batch = RewardBatch(user_id=123, action="Prueba")
        batch.add_besitos(50, "Test reward")

        assert batch.count == 1
        assert batch.is_empty is False
        assert batch.rewards[0].type == "besitos"
        assert "+50" in batch.rewards[0].value
        assert "Besitos" in batch.rewards[0].value

    def test_add_badge(self):
        """Test que se agregan insignias correctamente."""
        batch = RewardBatch(user_id=123, action="Prueba")
        batch.add_badge("🔥 Hot Streak", "10 días consecutivos")

        assert batch.count == 1
        assert batch.rewards[0].type == "badge"
        assert batch.rewards[0].value == "🔥 Hot Streak"
        assert batch.rewards[0].description == "10 días consecutivos"

    def test_add_rank_up(self):
        """Test que se agrega subida de rango correctamente."""
        batch = RewardBatch(user_id=123, action="Prueba")
        batch.add_rank_up("Novato", "Bronce")

        assert batch.count == 1
        assert batch.rewards[0].type == "rank"
        assert "Novato" in batch.rewards[0].value
        assert "Bronce" in batch.rewards[0].value
        assert "→" in batch.rewards[0].value

    def test_add_custom(self):
        """Test que se agregan recompensas personalizadas."""
        batch = RewardBatch(user_id=123, action="Prueba")
        batch.add_custom("⭐", "Logro especial", "Descripción del logro")

        assert batch.count == 1
        assert batch.rewards[0].type == "custom"
        assert batch.rewards[0].icon == "⭐"
        assert batch.rewards[0].value == "Logro especial"

    def test_multiple_rewards(self):
        """Test que se pueden agregar múltiples recompensas."""
        batch = RewardBatch(user_id=123, action="Reaccionaste a un mensaje")

        # Agregar múltiples recompensas
        batch.add_besitos(50)
        batch.add_badge("🔥 Hot Streak")
        batch.add_rank_up("Novato", "Bronce")

        assert batch.count == 3
        assert not batch.is_empty

    def test_format_message_empty_batch(self):
        """Test que batch vacío retorna string vacío."""
        batch = RewardBatch(user_id=123, action="Prueba")

        message = batch.format_message()

        assert message == ""

    def test_format_message_single_reward(self):
        """Test que batch con una recompensa formatea correctamente."""
        batch = RewardBatch(user_id=123, action="Acción importante")
        batch.add_besitos(50, "Razón del premio")

        message = batch.format_message()

        assert "🎉" in message  # Título por defecto
        assert "Acción importante" in message
        assert "50 Besitos" in message
        assert "Razón del premio" in message
        assert "<b>" in message  # Tags HTML

    def test_format_message_multiple_rewards(self):
        """Test que batch con múltiples recompensas formatea todas."""
        batch = RewardBatch(user_id=123, action="Reaccionaste a un mensaje")
        batch.add_besitos(50)
        batch.add_badge("🔥 Hot Streak")
        batch.add_rank_up("Novato", "Bronce")

        message = batch.format_message()

        # Verificar que contiene todas las recompensas
        assert "50 Besitos" in message
        assert "Hot Streak" in message
        assert "Novato → Bronce" in message

        # Verificar formato HTML
        assert "<b>" in message
        assert "\n" in message  # Saltos de línea

    def test_format_message_custom_title(self):
        """Test que batch puede tener título personalizado."""
        batch = RewardBatch(
            user_id=123,
            action="Prueba",
            title="✨ ¡Sorpresa!"
        )
        batch.add_besitos(100)

        message = batch.format_message()

        assert "✨ ¡Sorpresa!" in message

    def test_batch_count_property(self):
        """Test que count refleja cantidad correcta de recompensas."""
        batch = RewardBatch(user_id=123, action="Prueba")

        assert batch.count == 0

        batch.add_besitos(50)
        assert batch.count == 1

        batch.add_badge("Badge")
        assert batch.count == 2

        batch.add_rank_up("A", "B")
        assert batch.count == 3

    def test_batch_is_empty_property(self):
        """Test que is_empty refleja estado correcto."""
        batch = RewardBatch(user_id=123, action="Prueba")

        assert batch.is_empty is True
        assert batch.count == 0

        batch.add_besitos(50)

        assert batch.is_empty is False
        assert batch.count == 1

    def test_reward_with_emojis(self):
        """Test que rewards con emojis se formatean correctamente."""
        batch = RewardBatch(user_id=123, action="Prueba")
        batch.add_besitos(50, "🎁 Recompensa especial")
        batch.add_badge("🔥 Hot Streak 🌟", "Logro épico")

        message = batch.format_message()

        assert "🎁" in message
        assert "🔥" in message
        assert "🌟" in message
        assert "💋" in message  # Icon de besitos

    def test_reward_batch_html_escaping(self):
        """Test que mensaje usa HTML tags correctamente."""
        batch = RewardBatch(user_id=123, action="Prueba")
        batch.add_besitos(50, "Razón")

        message = batch.format_message()

        # Verificar estructura HTML
        assert message.count("<b>") == message.count("</b>")
        assert "<b>50 Besitos 💋</b>" in message or "<b>" in message


class TestRewardBatchIntegration:
    """Tests de integración del RewardBatch."""

    def test_complete_flow(self):
        """Test del flujo completo de un batch típico."""
        # Simular: Usuario reacciona → Gana Besitos + Badge + Rank
        batch = RewardBatch(
            user_id=123,
            action="Reaccionaste a un mensaje importante"
        )

        # Agregar recompensas
        batch.add_besitos(50, "Reacción")
        batch.add_badge("🔥 Reactor Pro", "50 reacciones totales")
        batch.add_rank_up("Novato", "Bronce")

        # Verificaciones
        assert batch.count == 3
        assert not batch.is_empty

        # Formato de mensaje
        message = batch.format_message()

        assert "50 Besitos" in message
        assert "Reactor Pro" in message
        assert "Novato → Bronce" in message
        assert "Reaccionaste a un mensaje importante" in message

        # Verificar que es válido para enviar a Telegram (HTML válido)
        assert len(message) > 0
        assert "<b>" in message

    def test_empty_batch_not_sent(self):
        """Test que batch vacío retorna string vacío (no enviar)."""
        batch = RewardBatch(user_id=123, action="Prueba")

        # Sin agregar recompensas
        message = batch.format_message()

        # No se debe enviar
        assert message == ""
        assert batch.is_empty is True

    def test_batch_with_many_rewards(self):
        """Test batch con muchas recompensas."""
        batch = RewardBatch(user_id=123, action="Logro épico")

        # Agregar 5 recompensas
        for i in range(5):
            batch.add_besitos(10 * (i + 1), f"Razón {i + 1}")

        assert batch.count == 5
        message = batch.format_message()

        # Todas deben aparecer
        for i in range(5):
            assert f"{10 * (i + 1)} Besitos" in message
