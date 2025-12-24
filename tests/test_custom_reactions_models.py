"""
Tests unitarios para modelos de reacciones personalizadas.

Tests:
- Creación de BroadcastMessage
- Creación de CustomReaction
- Modificaciones a Reaction (campos de UI)
- Índices únicos
- Relaciones entre modelos
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import select, inspect
from sqlalchemy.exc import IntegrityError

from bot.database.models import BroadcastMessage, User
from bot.gamification.database.models import CustomReaction, Reaction


class TestBroadcastMessageModel:
    """Tests para el modelo BroadcastMessage."""

    @pytest.mark.asyncio
    async def test_create_broadcast_message(self, db_setup, event_loop):
        """Test: Crear mensaje de broadcasting básico."""
        from bot.database.engine import get_session

        async with get_session() as session:
            # Crear usuario primero
            user = User(
                user_id=123456789,
                username="testuser",
                first_name="Test",
                role="FREE"
            )
            session.add(user)
            await session.commit()

            # Crear broadcast message
            broadcast_msg = BroadcastMessage(
                message_id=999888777,
                chat_id=-1001234567890,
                content_type="text",
                content_text="Mensaje de prueba",
                sent_by=user.user_id,
                gamification_enabled=False
            )
            session.add(broadcast_msg)
            await session.commit()

            # Verificar
            result = await session.execute(
                select(BroadcastMessage).where(BroadcastMessage.id == broadcast_msg.id)
            )
            saved_msg = result.scalar_one()

            assert saved_msg.message_id == 999888777
            assert saved_msg.chat_id == -1001234567890
            assert saved_msg.content_type == "text"
            assert saved_msg.content_text == "Mensaje de prueba"
            assert saved_msg.sent_by == user.user_id
            assert saved_msg.gamification_enabled is False
            assert saved_msg.total_reactions == 0
            assert saved_msg.unique_reactors == 0

    @pytest.mark.asyncio
    async def test_broadcast_message_with_gamification(self, db_setup, event_loop):
        """Test: Crear mensaje con gamificación habilitada."""
        from bot.database.engine import get_session

        async with get_session() as session:
            # Crear usuario
            user = User(
                user_id=123456790,
                username="admin",
                first_name="Admin",
                role="ADMIN"
            )
            session.add(user)
            await session.commit()

            # Configuración de reacciones
            reaction_config = [
                {"emoji": "👍", "label": "Me Gusta", "reaction_type_id": 1, "besitos": 10},
                {"emoji": "❤️", "label": "Me Encanta", "reaction_type_id": 2, "besitos": 15}
            ]

            # Crear broadcast con gamificación
            broadcast_msg = BroadcastMessage(
                message_id=888777666,
                chat_id=-1001234567890,
                content_type="photo",
                content_text="Foto exclusiva",
                media_file_id="AgACAgIAAxkBAAID",
                sent_by=user.user_id,
                gamification_enabled=True,
                reaction_buttons=reaction_config,
                content_protected=True
            )
            session.add(broadcast_msg)
            await session.commit()

            # Verificar
            result = await session.execute(
                select(BroadcastMessage).where(BroadcastMessage.id == broadcast_msg.id)
            )
            saved_msg = result.scalar_one()

            assert saved_msg.gamification_enabled is True
            assert saved_msg.content_protected is True
            assert len(saved_msg.reaction_buttons) == 2
            assert saved_msg.reaction_buttons[0]["emoji"] == "👍"
            assert saved_msg.reaction_buttons[1]["besitos"] == 15

    @pytest.mark.asyncio
    async def test_broadcast_message_unique_index(self, db_setup, event_loop):
        """Test: Índice único (chat_id, message_id) previene duplicados."""
        from bot.database.engine import get_session

        async with get_session() as session:
            # Crear usuario
            user = User(
                user_id=123456791,
                username="testuser2",
                first_name="Test2",
                role="FREE"
            )
            session.add(user)
            await session.commit()

            # Primer mensaje
            broadcast_msg1 = BroadcastMessage(
                message_id=777666555,
                chat_id=-1001234567890,
                content_type="text",
                content_text="Mensaje 1",
                sent_by=user.user_id
            )
            session.add(broadcast_msg1)
            await session.commit()

        # Nueva sesión para el test de duplicado
        async with get_session() as session:
            user = await session.get(User, 123456791)

            # Segundo mensaje con mismo chat_id y message_id (debe fallar)
            broadcast_msg2 = BroadcastMessage(
                message_id=777666555,  # Mismo message_id
                chat_id=-1001234567890,  # Mismo chat_id
                content_type="text",
                content_text="Mensaje 2 duplicado",
                sent_by=user.user_id
            )
            session.add(broadcast_msg2)

            with pytest.raises(IntegrityError):
                await session.flush()

            await session.rollback()


class TestBroadcastMessageRelations:
    """Tests para validar relaciones del modelo BroadcastMessage."""

    @pytest.mark.asyncio
    async def test_broadcast_message_sender_relationship(self, db_setup, event_loop):
        """Test: Relación con usuario que envió el broadcast."""
        from bot.database.engine import get_session

        async with get_session() as session:
            # Crear usuario
            user = User(
                user_id=123456794,
                username="sender",
                first_name="Sender",
                role="ADMIN"
            )
            session.add(user)
            await session.commit()

            # Crear broadcast
            broadcast_msg = BroadcastMessage(
                message_id=444333222,
                chat_id=-1001234567890,
                content_type="text",
                content_text="Test relationship",
                sent_by=user.user_id
            )
            session.add(broadcast_msg)
            await session.commit()

            # Verificar relación
            result = await session.execute(
                select(BroadcastMessage).where(BroadcastMessage.id == broadcast_msg.id)
            )
            saved_msg = result.scalar_one()

            assert saved_msg.sender is not None
            assert saved_msg.sender.user_id == user.user_id
            assert saved_msg.sender.username == "sender"

    @pytest.mark.asyncio
    async def test_broadcast_message_update_stats(self, db_setup, event_loop):
        """Test: Actualizar estadísticas de reacciones (cache)."""
        from bot.database.engine import get_session

        async with get_session() as session:
            # Crear usuario y broadcast
            user = User(
                user_id=123456795,
                username="statuser",
                first_name="StatUser",
                role="ADMIN"
            )
            session.add(user)

            broadcast_msg = BroadcastMessage(
                message_id=333222111,
                chat_id=-1001234567890,
                content_type="text",
                content_text="Test stats",
                sent_by=user.user_id,
                gamification_enabled=True
            )
            session.add(broadcast_msg)
            await session.commit()

            # Simular incremento de stats
            broadcast_msg.total_reactions = 150
            broadcast_msg.unique_reactors = 75
            await session.commit()

            # Verificar actualización
            result = await session.execute(
                select(BroadcastMessage).where(BroadcastMessage.id == broadcast_msg.id)
            )
            saved_msg = result.scalar_one()

            assert saved_msg.total_reactions == 150
            assert saved_msg.unique_reactors == 75
