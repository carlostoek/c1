"""
Tests para T7: Protección de Contenido.

Validaciones:
- BroadcastService pasa protect_content=True a Telegram API
- Mensaje con protección activada no se puede copiar/forward
- Mensaje sin protección (default) es normal
- Toggle de protección funciona en UI
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from bot.services.broadcast import BroadcastService
from bot.database.models import BroadcastMessage


@pytest.mark.asyncio
async def test_broadcast_with_protection_enabled():
    """Test: Mensaje con protección activada pasa protect_content=True."""
    # Setup: Mock session y bot
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Setup: Mock bot con send_message
        mock_bot = AsyncMock()
        mock_message = AsyncMock()
        mock_message.message_id = 12345
        mock_message.chat.id = -1001234567890
        mock_bot.send_message = AsyncMock(return_value=mock_message)

        # Setup: Mock ConfigService para retornar canal VIP
        with patch('bot.services.broadcast.ConfigService') as MockConfigService:
            mock_config = MockConfigService.return_value
            mock_config.get_vip_channel_id = AsyncMock(return_value="-1001234567890")

            # Setup: BroadcastService
            service = BroadcastService(session, mock_bot)

            # Execute: Enviar con protección habilitada
            result = await service.send_broadcast_with_gamification(
                target="vip",
                content_type="text",
                content_text="Test message",
                sent_by=123456789,
                content_protected=True  # ✅ Protección activada
            )

            # Verify: send_message llamado con protect_content=True
            mock_bot.send_message.assert_called_once()
            call_kwargs = mock_bot.send_message.call_args.kwargs
            assert call_kwargs.get("protect_content") is True


@pytest.mark.asyncio
async def test_broadcast_without_protection():
    """Test: Mensaje sin protección (default) no pasa protect_content."""
    # Setup: Mock session y bot
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Setup: Mock bot
        mock_bot = AsyncMock()
        mock_message = AsyncMock()
        mock_message.message_id = 12346
        mock_message.chat.id = -1001234567890
        mock_bot.send_message = AsyncMock(return_value=mock_message)

        # Setup: Mock ConfigService
        with patch('bot.services.broadcast.ConfigService') as MockConfigService:
            mock_config = MockConfigService.return_value
            mock_config.get_vip_channel_id = AsyncMock(return_value="-1001234567890")

            # Setup: BroadcastService
            service = BroadcastService(session, mock_bot)

            # Execute: Enviar sin protección (default=False)
            result = await service.send_broadcast_with_gamification(
                target="vip",
                content_type="text",
                content_text="Test message",
                sent_by=123456789,
                content_protected=False  # ❌ Sin protección
            )

            # Verify: send_message llamado SIN protect_content
            mock_bot.send_message.assert_called_once()
            call_kwargs = mock_bot.send_message.call_args.kwargs
            assert "protect_content" not in call_kwargs or call_kwargs.get("protect_content") is False


@pytest.mark.asyncio
async def test_broadcast_message_stores_protection_flag():
    """Test: BroadcastMessage almacena el flag de protección correctamente."""
    # Setup: Mock session y bot
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from bot.database.base import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Setup: Mock bot
        mock_bot = AsyncMock()
        mock_message = AsyncMock()
        mock_message.message_id = 12347
        mock_message.chat.id = -1001234567890
        mock_bot.send_message = AsyncMock(return_value=mock_message)

        # Setup: Mock ConfigService
        with patch('bot.services.broadcast.ConfigService') as MockConfigService:
            mock_config = MockConfigService.return_value
            mock_config.get_vip_channel_id = AsyncMock(return_value="-1001234567890")

            # Setup: BroadcastService
            service = BroadcastService(session, mock_bot)

            # Execute: Enviar con protección y gamificación
            result = await service.send_broadcast_with_gamification(
                target="vip",
                content_type="text",
                content_text="Test protected message",
                sent_by=123456789,
                gamification_config={"enabled": True, "reaction_types": [1, 2]},
                content_protected=True  # ✅ Protección activada
            )

            # Verify: BroadcastMessage creado con content_protected=True
            from sqlalchemy import select
            stmt = select(BroadcastMessage).where(
                BroadcastMessage.message_id == 12347
            )
            db_result = await session.execute(stmt)
            broadcast_msg = db_result.scalar_one_or_none()

            assert broadcast_msg is not None
            assert broadcast_msg.content_protected is True


@pytest.mark.asyncio
async def test_broadcast_default_protection_is_false():
    """Test: Por defecto, content_protected es False."""
    # Setup
    broadcast_msg = BroadcastMessage(
        message_id=99999,
        chat_id=-1001234567890,
        content_type="text",
        content_text="Default test",
        sent_by=123456789
    )

    # Verify: Default es False
    assert broadcast_msg.content_protected is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
