"""
Reactions System - Sistema de reacciones inline con botones.

Como Telegram no permite identificar quién reacciona en canales,
usamos botones inline debajo de cada mensaje broadcast.
"""
import logging
from typing import List

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)


class ReactionButton:
    """
    Definición de un botón de reacción.

    Attributes:
        emoji: Emoji de la reacción
        type: Tipo identificador (like, love, fire, etc.)
        callback_prefix: Prefijo para callback_data
    """

    def __init__(self, emoji: str, reaction_type: str):
        """
        Inicializa un botón de reacción.

        Args:
            emoji: Emoji a mostrar
            reaction_type: Tipo de reacción (identificador)
        """
        self.emoji = emoji
        self.type = reaction_type
        self.callback_prefix = "react"

    def to_callback_data(self, message_id: int, channel_id: int) -> str:
        """
        Genera callback_data para el botón.

        Format: react:TYPE:MESSAGE_ID:CHANNEL_ID

        Args:
            message_id: ID del mensaje
            channel_id: ID del canal

        Returns:
            String de callback_data
        """
        return f"{self.callback_prefix}:{self.type}:{message_id}:{channel_id}"

    def to_inline_button(self, message_id: int, channel_id: int) -> InlineKeyboardButton:
        """
        Convierte a InlineKeyboardButton.

        Args:
            message_id: ID del mensaje
            channel_id: ID del canal

        Returns:
            InlineKeyboardButton
        """
        return InlineKeyboardButton(
            text=self.emoji,
            callback_data=self.to_callback_data(message_id, channel_id)
        )


class ReactionSystem:
    """
    Sistema de reacciones inline.

    Maneja la creación de keyboards con botones de reacción.
    """

    # Reacciones por defecto
    DEFAULT_REACTIONS = [
        ReactionButton("👍", "like"),
        ReactionButton("❤️", "love"),
        ReactionButton("🔥", "fire"),
        ReactionButton("😂", "funny"),
        ReactionButton("😮", "wow"),
    ]

    @classmethod
    def create_reaction_keyboard(
        cls,
        message_id: int,
        channel_id: int,
        reactions: List[ReactionButton] = None
    ) -> InlineKeyboardMarkup:
        """
        Crea un keyboard con botones de reacción.

        Args:
            message_id: ID del mensaje
            channel_id: ID del canal
            reactions: Lista de reacciones (None = usar default)

        Returns:
            InlineKeyboardMarkup con botones de reacción

        Examples:
            >>> keyboard = ReactionSystem.create_reaction_keyboard(
            ...     message_id=12345,
            ...     channel_id=67890
            ... )
        """
        if reactions is None:
            reactions = cls.DEFAULT_REACTIONS

        # Crear botones
        buttons = [
            reaction.to_inline_button(message_id, channel_id)
            for reaction in reactions
        ]

        # Crear keyboard (una fila con todos los botones)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])

        return keyboard

    @classmethod
    def parse_reaction_callback(cls, callback_data: str) -> tuple:
        """
        Parsea callback_data de reacción.

        Args:
            callback_data: String de callback

        Returns:
            Tuple[str, int, int]: (reaction_type, message_id, channel_id)

        Raises:
            ValueError: Si el formato es inválido

        Examples:
            >>> reaction_type, msg_id, ch_id = ReactionSystem.parse_reaction_callback(
            ...     "react:like:12345:67890"
            ... )
        """
        try:
            parts = callback_data.split(":")

            if len(parts) != 4 or parts[0] != "react":
                raise ValueError("Formato inválido")

            reaction_type = parts[1]
            message_id = int(parts[2])
            channel_id = int(parts[3])

            return reaction_type, message_id, channel_id

        except (ValueError, IndexError) as e:
            raise ValueError(f"Callback data inválido: {callback_data}") from e

    @classmethod
    def get_reactions_from_config(cls, emoji_list: List[str]) -> List[ReactionButton]:
        """
        Convierte una lista de emojis a ReactionButtons.

        Args:
            emoji_list: Lista de emojis (ej: ["👍", "❤️", "🔥"])

        Returns:
            Lista de ReactionButton
        """
        reactions = []

        # Mapeo emoji → type
        emoji_to_type = {
            "👍": "like",
            "❤️": "love",
            "🔥": "fire",
            "😂": "funny",
            "😮": "wow",
            "💯": "perfect",
            "🎉": "celebrate",
            "👏": "clap",
            "😍": "adore",
            "🤩": "starstruck",
        }

        for i, emoji in enumerate(emoji_list):
            # Buscar type conocido, o usar índice
            reaction_type = emoji_to_type.get(emoji, f"custom_{i}")
            reactions.append(ReactionButton(emoji, reaction_type))

        return reactions
