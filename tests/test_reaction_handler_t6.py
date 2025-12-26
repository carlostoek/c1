"""
Tests para T6: Handler de Callbacks de Reacciones.

Validaciones:
- Usuario presiona botón de reacción y gana besitos
- Prevención de reacciones duplicadas
- Actualización de keyboard con checkmarks
- Contadores públicos correctos
- Manejo de errores
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, UTC

from bot.gamification.handlers.user.reactions import (
    handle_reaction_button,
    build_reaction_keyboard_with_marks,
    get_reaction_counts
)
from bot.database.models import BroadcastMessage
from bot.gamification.database.models import CustomReaction, Reaction
from bot.gamification.database.enums import TransactionType


@pytest.mark.asyncio
async def test_handle_reaction_button_success(session, mock_bot):
    """Test: Usuario reacciona exitosamente y gana besitos."""
    # Setup: Crear BroadcastMessage
    broadcast_msg = BroadcastMessage(
        message_id=12345,
        chat_id=-1001234567890,
        content_type="text",
        content_text="Test message",
        sent_by=123456789,
        gamification_enabled=True,
        reaction_buttons=[
            {"emoji": "👍", "label": "Me Gusta", "reaction_type_id": 1, "besitos": 10}
        ]
    )
    session.add(broadcast_msg)
    await session.commit()

    # Setup: Crear Reaction type
    reaction_type = Reaction(
        id=1,
        name="Me Gusta",
        emoji="👍",
        besitos_reward=10,
        is_active=True,
        button_emoji="👍",
        button_label="Me Gusta",
        sort_order=1
    )
    session.add(reaction_type)
    await session.commit()

    # Setup: Mock callback query
    callback = AsyncMock()
    callback.data = "react:1"
    callback.from_user.id = 987654321
    callback.message.message_id = 12345
    callback.message.chat.id = -1001234567890
    callback.answer = AsyncMock()
    callback.message.edit_reply_markup = AsyncMock()
    callback.bot = mock_bot

    # Execute
    await handle_reaction_button(callback, session)

    # Verify: Callback answer llamado con besitos ganados
    callback.answer.assert_called_once()
    answer_text = callback.answer.call_args[0][0]
    assert "+10 besitos!" in answer_text
    assert "Total:" in answer_text

    # Verify: CustomReaction creada en BD
    from sqlalchemy import select
    stmt = select(CustomReaction).where(
        CustomReaction.broadcast_message_id == broadcast_msg.id,
        CustomReaction.user_id == 987654321,
        CustomReaction.reaction_type_id == 1
    )
    result = await session.execute(stmt)
    custom_reaction = result.scalar_one_or_none()
    assert custom_reaction is not None
    assert custom_reaction.emoji == "👍"


@pytest.mark.asyncio
async def test_handle_reaction_button_duplicate(session, mock_bot):
    """Test: Prevenir reacciones duplicadas."""
    # Setup: Crear BroadcastMessage y Reaction
    broadcast_msg = BroadcastMessage(
        message_id=12346,
        chat_id=-1001234567890,
        content_type="text",
        content_text="Test message",
        sent_by=123456789,
        gamification_enabled=True,
        reaction_buttons=[
            {"emoji": "❤️", "label": "Me Encanta", "reaction_type_id": 2, "besitos": 15}
        ]
    )
    session.add(broadcast_msg)
    await session.commit()

    reaction_type = Reaction(
        id=2,
        name="Me Encanta",
        emoji="❤️",
        besitos_reward=15,
        is_active=True
    )
    session.add(reaction_type)
    await session.commit()

    # Setup: Usuario ya reaccionó
    existing_reaction = CustomReaction(
        broadcast_message_id=broadcast_msg.id,
        user_id=987654321,
        reaction_type_id=2,
        emoji="❤️",
        besitos_earned=15,
        created_at=datetime.now(UTC)
    )
    session.add(existing_reaction)
    await session.commit()

    # Setup: Mock callback
    callback = AsyncMock()
    callback.data = "react:2"
    callback.from_user.id = 987654321
    callback.message.message_id = 12346
    callback.message.chat.id = -1001234567890
    callback.answer = AsyncMock()
    callback.bot = mock_bot

    # Execute
    await handle_reaction_button(callback, session)

    # Verify: Mensaje de ya reaccionado
    callback.answer.assert_called_once()
    answer_text = callback.answer.call_args[0][0]
    assert "Ya reaccionaste" in answer_text


@pytest.mark.asyncio
async def test_build_reaction_keyboard_with_marks(session):
    """Test: Construcción de keyboard con contadores y checkmarks."""
    # Setup: Crear BroadcastMessage
    broadcast_msg = BroadcastMessage(
        message_id=12347,
        chat_id=-1001234567890,
        content_type="text",
        content_text="Test",
        sent_by=123456789
    )
    session.add(broadcast_msg)
    await session.commit()

    # Setup: 3 usuarios reaccionaron con diferentes emojis
    for i, (rt_id, emoji) in enumerate([(1, "👍"), (1, "👍"), (2, "❤️")]):
        reaction = CustomReaction(
            broadcast_message_id=broadcast_msg.id,
            user_id=100 + i,
            reaction_type_id=rt_id,
            emoji=emoji,
            besitos_earned=10,
            created_at=datetime.now(UTC)
        )
        session.add(reaction)
    await session.commit()

    # Execute: Construir keyboard (usuario 100 ya reaccionó con rt_id=1)
    reaction_config = [
        {"emoji": "👍", "label": "Me Gusta", "reaction_type_id": 1, "besitos": 10},
        {"emoji": "❤️", "label": "Me Encanta", "reaction_type_id": 2, "besitos": 15},
    ]
    user_reacted_ids = [1]  # Usuario ya reaccionó con tipo 1

    keyboard = await build_reaction_keyboard_with_marks(
        session=session,
        broadcast_message_id=broadcast_msg.id,
        reaction_config=reaction_config,
        user_reacted_ids=user_reacted_ids
    )

    # Verify: Keyboard tiene 2 botones
    assert len(keyboard.inline_keyboard) == 1  # 1 fila (2 botones < 3)
    assert len(keyboard.inline_keyboard[0]) == 2

    # Verify: Primer botón tiene checkmark (usuario reaccionó)
    btn1_text = keyboard.inline_keyboard[0][0].text
    assert "👍" in btn1_text
    assert "2" in btn1_text  # 2 reacciones de tipo 1
    assert "✓" in btn1_text  # Checkmark

    # Verify: Segundo botón NO tiene checkmark
    btn2_text = keyboard.inline_keyboard[0][1].text
    assert "❤️" in btn2_text
    assert "1" in btn2_text  # 1 reacción de tipo 2
    assert "✓" not in btn2_text


@pytest.mark.asyncio
async def test_get_reaction_counts(session):
    """Test: Obtener contadores de reacciones."""
    # Setup: Crear BroadcastMessage
    broadcast_msg = BroadcastMessage(
        message_id=12348,
        chat_id=-1001234567890,
        content_type="text",
        content_text="Test",
        sent_by=123456789
    )
    session.add(broadcast_msg)
    await session.commit()

    # Setup: Crear reacciones
    reactions_data = [
        (1, "👍"),  # Tipo 1
        (1, "👍"),  # Tipo 1
        (1, "👍"),  # Tipo 1
        (2, "❤️"),  # Tipo 2
        (2, "❤️"),  # Tipo 2
    ]

    for i, (rt_id, emoji) in enumerate(reactions_data):
        reaction = CustomReaction(
            broadcast_message_id=broadcast_msg.id,
            user_id=200 + i,
            reaction_type_id=rt_id,
            emoji=emoji,
            besitos_earned=10,
            created_at=datetime.now(UTC)
        )
        session.add(reaction)
    await session.commit()

    # Execute
    counts = await get_reaction_counts(session, broadcast_msg.id)

    # Verify
    assert counts[1] == 3  # 3 reacciones de tipo 1
    assert counts[2] == 2  # 2 reacciones de tipo 2


@pytest.mark.asyncio
async def test_handle_reaction_button_message_not_found(mock_bot):
    """Test: Manejo de mensaje no encontrado."""
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    # Setup: Sesión vacía
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Setup: Mock callback
        callback = AsyncMock()
        callback.data = "react:1"
        callback.from_user.id = 987654321
        callback.message.message_id = 99999  # No existe
        callback.message.chat.id = -1001234567890
        callback.answer = AsyncMock()
        callback.bot = mock_bot

        # Execute
        await handle_reaction_button(callback, session)

        # Verify: Error message
        callback.answer.assert_called_once()
        answer_text = callback.answer.call_args[0][0]
        assert "no encontrado" in answer_text.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
