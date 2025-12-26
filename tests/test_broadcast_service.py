"""
Tests para BroadcastService.

Valida:
- Envío con gamificación habilitada
- Envío sin gamificación (backward compatible)
- Construcción correcta de keyboards
- Protección de contenido
- Registro en BroadcastMessage
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from bot.services.broadcast import BroadcastService
from bot.database.models import BroadcastMessage, BotConfig
from bot.gamification.database.models import Reaction


@pytest.mark.asyncio
async def test_send_broadcast_with_gamification(db_setup, mock_bot):
    """Test: Envío con gamificación habilitada"""
    from bot.database.engine import get_session

    async with get_session() as session:
        # Setup: Configurar canales
        config = await session.get(BotConfig, 1)
        config.vip_channel_id = "-1001234567890"
        await session.commit()

        # Setup: Crear reacciones en BD
        reaction1 = Reaction(
            id=1,
            emoji="👍",
            besitos_value=10,
            active=True,
            button_emoji="👍",
            button_label="Me Gusta",
            sort_order=1
        )
        reaction2 = Reaction(
            id=2,
            emoji="❤️",
            besitos_value=15,
            active=True,
            button_emoji="❤️",
            button_label="Me Encanta",
            sort_order=2
        )
        session.add_all([reaction1, reaction2])
        await session.commit()

        # Mock del bot para send_message
        mock_message = MagicMock()
        mock_message.message_id = 12345
        mock_bot.send_message = AsyncMock(return_value=mock_message)

        # Service
        service = BroadcastService(session, mock_bot)

        # Execute
        result = await service.send_broadcast_with_gamification(
            target="vip",
            content_type="text",
            content_text="Hola VIP!",
            sent_by=111,
            gamification_config={
                "enabled": True,
                "reaction_types": [1, 2]
            },
            content_protected=False
        )

        # Assert
        assert result["success"] is True
        assert "VIP" in result["channels_sent"]
        assert len(result["broadcast_message_ids"]) == 1

        # Verificar que se registró en BD
        broadcast_msg = await session.get(BroadcastMessage, result["broadcast_message_ids"][0])
        assert broadcast_msg is not None
        assert broadcast_msg.gamification_enabled is True
        assert len(broadcast_msg.reaction_buttons) == 2
        assert broadcast_msg.content_text == "Hola VIP!"

        # Verificar que se llamó a bot.send_message con keyboard
        assert mock_bot.send_message.called
        call_kwargs = mock_bot.send_message.call_args.kwargs
        assert "reply_markup" in call_kwargs


@pytest.mark.asyncio
async def test_send_broadcast_without_gamification(db_setup, mock_bot):
    """Test: Envío sin gamificación (backward compatible)"""
    from bot.database.engine import get_session

    async with get_session() as session:
        # Setup: Configurar canales
        config = await session.get(BotConfig, 1)
        config.free_channel_id = "-1009876543210"
        await session.commit()

        # Mock del bot
        mock_message = MagicMock()
        mock_message.message_id = 54321
        mock_bot.send_message = AsyncMock(return_value=mock_message)

        # Service
        service = BroadcastService(session, mock_bot)

        # Execute (sin gamification_config)
        result = await service.send_broadcast_with_gamification(
            target="free",
            content_type="text",
            content_text="Hola Free!",
            sent_by=111
        )

        # Assert
        assert result["success"] is True
        assert "Free" in result["channels_sent"]
        assert len(result["broadcast_message_ids"]) == 0  # No se registra en BD

        # Verificar que se llamó a bot.send_message SIN keyboard
        assert mock_bot.send_message.called
        call_kwargs = mock_bot.send_message.call_args.kwargs
        assert "reply_markup" not in call_kwargs or call_kwargs.get("reply_markup") is None


@pytest.mark.asyncio
async def test_build_reaction_keyboard(db_setup, mock_bot):
    """Test: Construcción de keyboard correcta"""
    from bot.database.engine import get_session

    async with get_session() as session:
        # Setup: Crear 4 reacciones (debe hacer 2 filas: 3 + 1)
        reactions = [
            Reaction(id=1, emoji="👍", besitos_value=10, active=True, button_emoji="👍", button_label="Like", sort_order=1),
            Reaction(id=2, emoji="❤️", besitos_value=15, active=True, button_emoji="❤️", button_label="Love", sort_order=2),
            Reaction(id=3, emoji="🔥", besitos_value=20, active=True, button_emoji="🔥", button_label="Fire", sort_order=3),
            Reaction(id=4, emoji="😂", besitos_value=10, active=True, button_emoji="😂", button_label="Haha", sort_order=4),
        ]
        session.add_all(reactions)
        await session.commit()

        # Service
        service = BroadcastService(session, mock_bot)

        # Execute
        keyboard = await service._build_reaction_keyboard([1, 2, 3, 4])

        # Assert
        assert keyboard is not None
        assert len(keyboard.inline_keyboard) == 2  # 2 filas
        assert len(keyboard.inline_keyboard[0]) == 3  # Primera fila: 3 botones
        assert len(keyboard.inline_keyboard[1]) == 1  # Segunda fila: 1 botón

        # Verificar callback_data
        assert keyboard.inline_keyboard[0][0].callback_data == "react:1"
        assert keyboard.inline_keyboard[0][1].callback_data == "react:2"


@pytest.mark.asyncio
async def test_build_reaction_config(db_setup, mock_bot):
    """Test: Construcción de config JSON"""
    from bot.database.engine import get_session

    async with get_session() as session:
        # Setup
        reaction = Reaction(
            id=1,
            emoji="👍",
            besitos_value=10,
            active=True,
            button_emoji="👍",
            button_label="Me Gusta",
            sort_order=1
        )
        session.add(reaction)
        await session.commit()

        # Service
        service = BroadcastService(session, mock_bot)

        # Execute
        config = await service._build_reaction_config([1])

        # Assert
        assert len(config) == 1
        assert config[0]["emoji"] == "👍"
        assert config[0]["label"] == "Me Gusta"
        assert config[0]["reaction_type_id"] == 1
        assert config[0]["besitos"] == 10


@pytest.mark.asyncio
async def test_content_protection_applied(db_setup, mock_bot):
    """Test: Protección de contenido aplicada"""
    from bot.database.engine import get_session

    async with get_session() as session:
        # Setup
        config = await session.get(BotConfig, 1)
        config.vip_channel_id = "-1001234567890"
        await session.commit()

        # Mock
        mock_message = MagicMock()
        mock_message.message_id = 99999
        mock_bot.send_message = AsyncMock(return_value=mock_message)

        # Service
        service = BroadcastService(session, mock_bot)

        # Execute con content_protected=True
        result = await service.send_broadcast_with_gamification(
            target="vip",
            content_type="text",
            content_text="Contenido protegido",
            sent_by=111,
            content_protected=True
        )

        # Assert
        assert result["success"] is True

        # Verificar que protect_content=True se pasó
        call_kwargs = mock_bot.send_message.call_args.kwargs
        assert call_kwargs.get("protect_content") is True


@pytest.mark.asyncio
async def test_no_channels_configured(db_setup, mock_bot):
    """Test: Manejo cuando no hay canales configurados"""
    from bot.database.engine import get_session

    async with get_session() as session:
        # NO configurar canales

        # Service
        service = BroadcastService(session, mock_bot)

        # Execute
        result = await service.send_broadcast_with_gamification(
            target="vip",
            content_type="text",
            content_text="Test",
            sent_by=111
        )

        # Assert
        assert result["success"] is False
        assert len(result["channels_sent"]) == 0
        assert len(result["errors"]) > 0
