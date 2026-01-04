"""
Tests para Reaction Hook (G5.3).

Valida:
- Procesamiento de eventos de reacción
- Registro de besitos
- Auto level-up
- Actualización de progreso de misiones
- Validaciones de reacciones
"""

import pytest
import pytest_asyncio
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, PropertyMock

from aiogram.types import MessageReactionUpdated, User, Chat, ReactionTypeEmoji

from bot.gamification.database.models import Reaction, Level, UserGamification, GamificationConfig
from bot.gamification.background.reaction_hook import (
    on_reaction_event,
    is_valid_reaction
)


@pytest.fixture
def mock_bot():
    """Mock del bot de Telegram."""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    return bot


@pytest_asyncio.fixture
async def reaction_data(db_session):
    """Crea reacción y nivel de prueba."""
    # Crear configuración de gamificación
    config = GamificationConfig()
    config.id = 1
    config.notifications_enabled = True
    db_session.add(config)

    # Crear reacción activa
    reaction = Reaction(emoji="❤️", name="Corazón", besitos_value=5, active=True)
    db_session.add(reaction)

    # Crear niveles
    level1 = Level(name="Novato", min_besitos=0, order=1, active=True)
    level2 = Level(name="Intermedio", min_besitos=100, order=2, active=True)
    db_session.add_all([level1, level2])

    # Crear usuario
    user = UserGamification(
        user_id=4001,
        total_besitos=95,  # Cerca del level-up
        current_level_id=None  # Se asignará al llamar al servicio
    )
    db_session.add(user)

    await db_session.commit()
    await db_session.refresh(level1)
    await db_session.refresh(level2)

    # Asignar nivel inicial
    user.current_level_id = level1.id
    await db_session.commit()

    return {
        "reaction": reaction,
        "level1": level1,
        "level2": level2,
        "user": user
    }


def create_mock_reaction_update(
    user_id: int,
    chat_id: int,
    message_id: int,
    emoji: str
):
    """Crea un mock de MessageReactionUpdated."""
    # Mock del usuario
    mock_user = MagicMock(spec=User)
    mock_user.id = user_id

    # Mock del chat
    mock_chat = MagicMock(spec=Chat)
    mock_chat.id = chat_id

    # Mock de la reacción
    mock_reaction = MagicMock(spec=ReactionTypeEmoji)
    mock_reaction.emoji = emoji

    # Mock del update
    mock_update = MagicMock(spec=MessageReactionUpdated)
    mock_update.user = mock_user
    mock_update.chat = mock_chat
    mock_update.message_id = message_id
    mock_update.new_reaction = [mock_reaction]

    return mock_update


@pytest.mark.asyncio
async def test_on_reaction_event_records_besitos(db_session, reaction_data, mock_bot):
    """Verifica que se registren besitos correctamente."""
    # Crear mock update
    update = create_mock_reaction_update(
        user_id=4001,
        chat_id=12345,
        message_id=67890,
        emoji="❤️"
    )

    # Procesar evento
    await on_reaction_event(update, db_session, mock_bot)

    # Verificar que se registraron besitos
    await db_session.refresh(reaction_data["user"])
    assert reaction_data["user"].total_besitos == 100  # 95 + 5


@pytest.mark.asyncio
async def test_on_reaction_event_triggers_level_up(db_session, reaction_data, mock_bot):
    """Verifica que se dispare level-up automáticamente."""
    # Crear mock update
    update = create_mock_reaction_update(
        user_id=4001,
        chat_id=12345,
        message_id=67890,
        emoji="❤️"
    )

    # Procesar evento
    await on_reaction_event(update, db_session, mock_bot)

    # Verificar level-up
    await db_session.refresh(reaction_data["user"])
    assert reaction_data["user"].current_level_id == reaction_data["level2"].id
    assert reaction_data["user"].total_besitos == 100


@pytest.mark.asyncio
async def test_on_reaction_event_without_user(db_session, reaction_data, mock_bot):
    """Verifica que se maneje correctamente evento sin usuario."""
    # Crear update sin usuario
    mock_update = MagicMock(spec=MessageReactionUpdated)
    mock_update.user = None

    # No debería causar error
    await on_reaction_event(mock_update, db_session, mock_bot)

    # Besitos del usuario no deberían cambiar
    await db_session.refresh(reaction_data["user"])
    assert reaction_data["user"].total_besitos == 95


@pytest.mark.asyncio
async def test_on_reaction_event_without_new_reactions(db_session, reaction_data, mock_bot):
    """Verifica que se maneje evento sin reacciones nuevas."""
    # Crear update sin reacciones
    mock_user = MagicMock(spec=User)
    mock_user.id = 4001

    mock_chat = MagicMock(spec=Chat)
    mock_chat.id = 12345

    mock_update = MagicMock(spec=MessageReactionUpdated)
    mock_update.user = mock_user
    mock_update.chat = mock_chat
    mock_update.message_id = 67890
    mock_update.new_reaction = []  # Sin reacciones

    # No debería causar error
    await on_reaction_event(mock_update, db_session, mock_bot)

    # Besitos no deberían cambiar
    await db_session.refresh(reaction_data["user"])
    assert reaction_data["user"].total_besitos == 95


@pytest.mark.asyncio
async def test_on_reaction_event_with_inactive_emoji(db_session, reaction_data, mock_bot):
    """Verifica que reacciones con emoji inactivo se manejen correctamente."""
    # Crear mock update con emoji no configurado
    update = create_mock_reaction_update(
        user_id=4001,
        chat_id=12345,
        message_id=67890,
        emoji="💀"  # Emoji no configurado
    )

    # Procesar evento (no debería dar error, pero no debe registrar besitos)
    await on_reaction_event(update, db_session, mock_bot)

    # Besitos no deberían cambiar (emoji no configurado)
    await db_session.refresh(reaction_data["user"])
    assert reaction_data["user"].total_besitos == 95


@pytest.mark.asyncio
async def test_is_valid_reaction_with_valid_update():
    """Verifica validación de reacción válida."""
    # Crear update válido
    update = create_mock_reaction_update(
        user_id=5001,
        chat_id=12345,
        message_id=67890,
        emoji="❤️"
    )

    # Debería ser válida
    assert await is_valid_reaction(update) is True


@pytest.mark.asyncio
async def test_is_valid_reaction_without_user():
    """Verifica validación de reacción sin usuario."""
    # Crear update sin usuario
    mock_update = MagicMock(spec=MessageReactionUpdated)
    mock_update.user = None
    mock_update.new_reaction = [MagicMock(emoji="❤️")]

    # No debería ser válida
    assert await is_valid_reaction(mock_update) is False


@pytest.mark.asyncio
async def test_is_valid_reaction_without_new_reactions():
    """Verifica validación de reacción sin reacciones nuevas."""
    # Crear update sin reacciones
    mock_user = MagicMock(spec=User)
    mock_user.id = 5001

    mock_update = MagicMock(spec=MessageReactionUpdated)
    mock_update.user = mock_user
    mock_update.new_reaction = []  # Sin reacciones

    # No debería ser válida
    assert await is_valid_reaction(mock_update) is False


@pytest.mark.asyncio
async def test_is_valid_reaction_with_only_custom_emojis():
    """Verifica validación cuando solo hay custom emojis."""
    # Crear update con solo custom emoji (sin atributo emoji)
    mock_user = MagicMock(spec=User)
    mock_user.id = 5001

    mock_custom_reaction = MagicMock()
    # Custom emoji no tiene atributo 'emoji' standard
    del mock_custom_reaction.emoji

    mock_update = MagicMock(spec=MessageReactionUpdated)
    mock_update.user = mock_user
    mock_update.new_reaction = [mock_custom_reaction]

    # No debería ser válida (solo custom emojis)
    assert await is_valid_reaction(mock_update) is False


@pytest.mark.asyncio
async def test_on_reaction_event_handles_errors_gracefully(db_session, reaction_data, mock_bot):
    """Verifica que errores en procesamiento se manejen sin crashear."""
    # Crear update que causará error (usuario no existe en BD)
    update = create_mock_reaction_update(
        user_id=9999999,  # Usuario que no existe
        chat_id=12345,
        message_id=67890,
        emoji="❤️"
    )

    # No debería crashear (error es capturado y logueado)
    await on_reaction_event(update, db_session, mock_bot)

    # Usuario original no debería verse afectado
    await db_session.refresh(reaction_data["user"])
    assert reaction_data["user"].total_besitos == 95
