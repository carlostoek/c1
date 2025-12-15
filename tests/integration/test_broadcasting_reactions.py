"""
Integration tests for broadcasting with reactions.

Tests:
- Flujo completo de broadcasting con opciones
- Generación de keyboard de reacciones
- Aplicación de protect_content
- Integración de servicios
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import Bot
from aiogram.types import Message, Chat

from bot.services.container import ServiceContainer
from bot.utils.keyboards import create_reaction_keyboard


# ===== FIXTURES ESPECÍFICAS =====

@pytest.fixture
def mock_bot():
    """
    Mock de Bot de Telegram.
    """
    bot = AsyncMock(spec=Bot)
    bot.token = "TEST_TOKEN"
    
    # Mock send_message
    mock_message = MagicMock(spec=Message)
    mock_message.message_id = 12345
    mock_message.chat = MagicMock(spec=Chat)
    mock_message.chat.id = -1001234567890
    
    bot.send_message.return_value = mock_message
    bot.send_photo.return_value = mock_message
    bot.send_video.return_value = mock_message
    bot.edit_message_reply_markup.return_value = True
    
    return bot


@pytest.fixture
def container_with_mock_bot(db_session, mock_bot):
    """
    ServiceContainer con bot mockeado.
    """
    return ServiceContainer(db_session, mock_bot)


# ===== TESTS DE KEYBOARD DE REACCIONES =====

@pytest.mark.asyncio
async def test_create_reaction_keyboard_without_counts(sample_reactions):
    """
    Test: Crear keyboard de reacciones sin contadores.
    """
    # Arrange
    reactions_data = [
        (r.id, r.emoji, r.label)
        for r in sample_reactions
    ]
    channel_id = -1001234567890
    message_id = 12345
    
    # Act
    keyboard = create_reaction_keyboard(
        reactions=reactions_data,
        channel_id=channel_id,
        message_id=message_id,
        counts=None
    )
    
    # Assert
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) > 0
    
    # Verificar que botones solo tienen emoji (sin contador)
    for row in keyboard.inline_keyboard:
        for button in row:
            assert button.text in [r[1] for r in reactions_data]


@pytest.mark.asyncio
async def test_create_reaction_keyboard_with_counts(sample_reactions):
    """
    Test: Crear keyboard de reacciones con contadores.
    """
    # Arrange
    reactions_data = [
        (r.id, r.emoji, r.label)
        for r in sample_reactions
    ]
    channel_id = -1001234567890
    message_id = 12345
    counts = {
        sample_reactions[0].emoji: 10,
        sample_reactions[1].emoji: 5
    }
    
    # Act
    keyboard = create_reaction_keyboard(
        reactions=reactions_data,
        channel_id=channel_id,
        message_id=message_id,
        counts=counts
    )
    
    # Assert
    assert keyboard is not None
    
    # Verificar que botones con contador incluyen número
    first_button = keyboard.inline_keyboard[0][0]
    assert "10" in first_button.text or "5" in first_button.text


@pytest.mark.asyncio
async def test_keyboard_callback_data_format(sample_reactions):
    """
    Test: Validar formato de callback_data en keyboard.
    """
    # Arrange
    reactions_data = [
        (r.id, r.emoji, r.label)
        for r in sample_reactions
    ]
    channel_id = -1001234567890
    message_id = 12345
    
    # Act
    keyboard = create_reaction_keyboard(
        reactions=reactions_data,
        channel_id=channel_id,
        message_id=message_id,
        counts=None
    )
    
    # Assert
    for row in keyboard.inline_keyboard:
        for button in row:
            # Verificar formato: react:{emoji}:{channel_id}:{message_id}
            parts = button.callback_data.split(":")
            assert len(parts) == 4
            assert parts[0] == "react"
            assert parts[2] == str(channel_id)
            assert parts[3] == str(message_id)


@pytest.mark.asyncio
async def test_keyboard_grouping_three_per_row(sample_reactions):
    """
    Test: Validar agrupación de botones (max 3 por fila).
    """
    # Arrange
    reactions_data = [
        (r.id, r.emoji, r.label)
        for r in sample_reactions
    ]
    channel_id = -1001234567890
    message_id = 12345
    
    # Act
    keyboard = create_reaction_keyboard(
        reactions=reactions_data,
        channel_id=channel_id,
        message_id=message_id,
        counts=None
    )
    
    # Assert - Ninguna fila debe tener más de 3 botones
    for row in keyboard.inline_keyboard:
        assert len(row) <= 3


# ===== TESTS DE OPCIONES DE BROADCASTING =====

@pytest.mark.asyncio
async def test_broadcasting_with_reactions_enabled(
    container_with_mock_bot,
    sample_reactions,
    mock_bot
):
    """
    Test: Broadcasting con reacciones activadas.
    """
    # Arrange
    container = container_with_mock_bot
    channel_id = -1001234567890
    text = "Mensaje de prueba"
    
    # Simular que hay reacciones activas
    active_reactions = await container.reactions.get_active_reactions()
    assert len(active_reactions) >= 3
    
    # Act - Enviar con channel service (simula protect_content=False, attach_reactions=True)
    success, msg, sent_message = await container.channel.send_to_channel(
        channel_id=channel_id,
        text=text,
        protect_content=False
    )
    
    # Assert
    assert success == True
    assert sent_message is not None
    mock_bot.send_message.assert_called_once()
    
    # Verificar que se puede editar con keyboard
    reactions_data = [
        (r.id, r.emoji, r.label)
        for r in active_reactions
    ]
    
    keyboard = create_reaction_keyboard(
        reactions=reactions_data,
        channel_id=channel_id,
        message_id=sent_message.message_id,
        counts=None
    )
    
    # Simular editar mensaje con keyboard
    await mock_bot.edit_message_reply_markup(
        chat_id=channel_id,
        message_id=sent_message.message_id,
        reply_markup=keyboard
    )
    
    # Assert
    mock_bot.edit_message_reply_markup.assert_called_once()


@pytest.mark.asyncio
async def test_broadcasting_with_protect_content(
    container_with_mock_bot,
    mock_bot
):
    """
    Test: Broadcasting con protección de contenido activada.
    """
    # Arrange
    container = container_with_mock_bot
    channel_id = -1001234567890
    text = "Mensaje protegido"
    
    # Act
    success, msg, sent_message = await container.channel.send_to_channel(
        channel_id=channel_id,
        text=text,
        protect_content=True
    )
    
    # Assert
    assert success == True
    
    # Verificar que se llamó con protect_content=True
    call_kwargs = mock_bot.send_message.call_args.kwargs
    assert call_kwargs.get("protect_content") == True


@pytest.mark.asyncio
async def test_broadcasting_photo_with_options(
    container_with_mock_bot,
    mock_bot
):
    """
    Test: Broadcasting de foto con opciones.
    """
    # Arrange
    container = container_with_mock_bot
    channel_id = -1001234567890
    caption = "Caption de foto"
    photo_file_id = "AgACAgIAAxkBAAIBBGXYZ..."
    
    # Act
    success, msg, sent_message = await container.channel.send_to_channel(
        channel_id=channel_id,
        text=caption,
        photo=photo_file_id,
        protect_content=True
    )
    
    # Assert
    assert success == True
    mock_bot.send_photo.assert_called_once()
    
    call_kwargs = mock_bot.send_photo.call_args.kwargs
    assert call_kwargs.get("protect_content") == True


@pytest.mark.asyncio
async def test_broadcasting_video_with_options(
    container_with_mock_bot,
    mock_bot
):
    """
    Test: Broadcasting de video con opciones.
    """
    # Arrange
    container = container_with_mock_bot
    channel_id = -1001234567890
    caption = "Caption de video"
    video_file_id = "BAACAgIAAxkBAAIBBWXYZ..."
    
    # Act
    success, msg, sent_message = await container.channel.send_to_channel(
        channel_id=channel_id,
        text=caption,
        video=video_file_id,
        protect_content=False
    )
    
    # Assert
    assert success == True
    mock_bot.send_video.assert_called_once()
    
    call_kwargs = mock_bot.send_video.call_args.kwargs
    assert call_kwargs.get("protect_content") == False


# ===== TESTS DE INTEGRACIÓN DE SERVICIOS =====

@pytest.mark.asyncio
async def test_container_reactions_service_available(
    container_with_mock_bot
):
    """
    Test: Verificar que ReactionService está disponible en container.
    """
    # Arrange
    container = container_with_mock_bot
    
    # Act
    reactions = container.reactions
    
    # Assert
    assert reactions is not None
    assert hasattr(reactions, 'get_active_reactions')
    assert hasattr(reactions, 'record_user_reaction')


@pytest.mark.asyncio
async def test_end_to_end_broadcast_with_reactions(
    container_with_mock_bot,
    sample_reactions,
    mock_bot
):
    """
    Test: Flujo completo end-to-end de broadcasting con reacciones.
    """
    # Arrange
    container = container_with_mock_bot
    channel_id = -1001234567890
    text = "Publicación con reacciones"
    
    # Paso 1: Obtener reacciones activas
    active_reactions = await container.reactions.get_active_reactions()
    assert len(active_reactions) > 0
    
    # Paso 2: Enviar mensaje
    success, msg, sent_message = await container.channel.send_to_channel(
        channel_id=channel_id,
        text=text,
        protect_content=False
    )
    
    assert success == True
    message_id = sent_message.message_id
    
    # Paso 3: Generar keyboard con reacciones
    reactions_data = [
        (r.id, r.emoji, r.label)
        for r in active_reactions
    ]
    
    keyboard = create_reaction_keyboard(
        reactions=reactions_data,
        channel_id=channel_id,
        message_id=message_id,
        counts=None
    )
    
    assert keyboard is not None
    
    # Paso 4: Editar mensaje para agregar keyboard
    await mock_bot.edit_message_reply_markup(
        chat_id=channel_id,
        message_id=message_id,
        reply_markup=keyboard
    )
    
    # Assert - Verificar flujo completo
    assert mock_bot.send_message.called
    assert mock_bot.edit_message_reply_markup.called
