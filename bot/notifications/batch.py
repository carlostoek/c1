"""
Reward Batch - Sistema para agrupar recompensas.

Permite acumular múltiples recompensas (Besitos, badges, ranks)
en una sola notificación unificada.
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Reward:
    """
    Una recompensa individual.

    Attributes:
        type: Tipo de recompensa (points, badge, rank, etc.)
        value: Valor/nombre de la recompensa
        icon: Emoji o icono
        description: Descripción adicional
    """

    type: str
    value: str
    icon: str = "🎁"
    description: str = ""

    def format(self) -> str:
        """Formatea la recompensa para display."""
        if self.description:
            return f"{self.icon} <b>{self.value}</b> - {self.description}"
        else:
            return f"{self.icon} <b>{self.value}</b>"


@dataclass
class RewardBatch:
    """
    Lote de recompensas para enviar en una sola notificación.

    Agrupa múltiples recompensas para evitar spam de notificaciones.

    Attributes:
        user_id: ID del usuario que recibe
        rewards: Lista de recompensas
        action: Acción que desencadenó las recompensas
        title: Título de la notificación

    Examples:
        >>> batch = RewardBatch(user_id=123, action="Reaccionaste a un mensaje")
        >>> batch.add_besitos(50, "Primera reacción del día")
        >>> batch.add_badge("🔥 Hot Streak", "10 días consecutivos")
        >>> batch.add_rank_up("Bronce", "Plata")
        >>>
        >>> # Resultado: Una sola notificación con 3 recompensas
    """

    user_id: int
    action: str
    rewards: List[Reward] = field(default_factory=list)
    title: str = "🎉 ¡Recompensas Ganadas!"

    def add_besitos(self, amount: int, reason: str = ""):
        """
        Agrega Besitos (puntos) al lote.

        Args:
            amount: Cantidad de Besitos
            reason: Razón de la recompensa
        """
        self.rewards.append(
            Reward(
                type="besitos",
                value=f"+{amount} Besitos 💋",
                icon="💋",
                description=reason,
            )
        )

    def add_badge(self, badge_name: str, description: str = ""):
        """
        Agrega una insignia desbloqueada.

        Args:
            badge_name: Nombre de la insignia (puede incluir emoji)
            description: Descripción de cómo se obtuvo
        """
        self.rewards.append(
            Reward(type="badge", value=badge_name, icon="🏆", description=description)
        )

    def add_rank_up(self, old_rank: str, new_rank: str):
        """
        Agrega un cambio de rango.

        Args:
            old_rank: Rango anterior
            new_rank: Rango nuevo
        """
        self.rewards.append(
            Reward(
                type="rank",
                value=f"{old_rank} → {new_rank}",
                icon="⭐",
                description="¡Subiste de rango!",
            )
        )

    def add_custom(self, icon: str, value: str, description: str = ""):
        """
        Agrega una recompensa personalizada.

        Args:
            icon: Emoji o icono
            value: Valor principal
            description: Descripción
        """
        self.rewards.append(Reward(type="custom", value=value, icon=icon, description=description))

    @property
    def is_empty(self) -> bool:
        """Verifica si el lote está vacío."""
        return len(self.rewards) == 0

    @property
    def count(self) -> int:
        """Cantidad de recompensas en el lote."""
        return len(self.rewards)

    def format_message(self) -> str:
        """
        Formatea el mensaje completo con todas las recompensas.

        Returns:
            String HTML formateado
        """
        if self.is_empty:
            return ""

        message = f"{self.title}\n\n"
        message += f"<b>{self.action}</b>\n\n"

        # Listar recompensas
        for reward in self.rewards:
            message += f"{reward.format()}\n"

        return message.strip()
