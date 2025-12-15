"""
End-to-end tests for user reaction flow.

Tests:
- Flujo completo de usuario reaccionando
- Rate limiting en acción
- Otorgamiento de besitos
- Actualización de contadores
"""
import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

from bot.services.container import ServiceContainer
from bot.handlers.user.reactions import (
    _validate_rate_limiting,
    _award_besitos_for_reaction,
    _update_reaction_counter
)
from bot.database.models import User
from bot.database.enums import UserRole
from bot.services.container import ServiceContainer
from pytest import fixture


# ===== FIXTURES ESPECÍFICAS =====

@pytest.fixture
def multiple_users(db_session):
    """
    Crear múltiples usuarios para tests.
    """
    async def _create_users(count):
        users = []
        for i in range(count):
            user = User(
                user_id=5000 + i,
                username=f"user{i}",
                first_name=f"Name{i}",
                last_name="Test",
                role=UserRole.FREE
            )
            db_session.add(user)
            users.append(user)

        await db_session.commit()
        return users

    return _create_users


@fixture
def container_with_mock_bot(db_session, mock_bot):
    """
    ServiceContainer con bot mockeado.
    """
    return ServiceContainer(db_session, mock_bot)


@pytest.fixture
def mock_callback_query():
    """
    Mock de CallbackQuery de Telegram.
    """
    callback = MagicMock()
    callback.from_user = MagicMock()
    callback.from_user.id = 123456789
    callback.data = "react:❤️:-1001234567890:12345"
    callback.answer = AsyncMock()
    callback.bot = AsyncMock()
    
    return callback


# ===== TESTS END-TO-END =====

@pytest.mark.asyncio
async def test_complete_user_reaction_flow(
    container_with_mock_bot,
    sample_reactions,
    sample_user
):
    """
    Test: Flujo completo de reacción de usuario.
    
    Pasos:
    1. Usuario hace click en botón
    2. Se valida rate limiting (pasa)
    3. Se registra reacción en BD
    4. Se otorgan besitos
    5. Se actualiza contador
    """
    # Arrange
    container = container_with_mock_bot
    channel_id = -1001234567890
    message_id = 12345
    user_id = sample_user.user_id
    emoji = sample_reactions[0].emoji
    
    # Paso 1: Parse de callback (simulado)
    callback_data = f"react:{emoji}:{channel_id}:{message_id}"
    parts = callback_data.split(":")
    
    assert len(parts) == 4
    parsed_emoji = parts[1]
    parsed_channel_id = int(parts[2])
    parsed_message_id = int(parts[3])
    
    # Paso 2: Validar rate limiting
    can_react, reason = await _validate_rate_limiting(
        user_id=user_id,
        session=container._session
    )
    
    assert can_react == True
    
    # Paso 3: Registrar reacción
    reaction = await container.reactions.record_user_reaction(
        channel_id=parsed_channel_id,
        message_id=parsed_message_id,
        user_id=user_id,
        emoji=parsed_emoji
    )
    
    assert reaction is not None
    assert reaction.emoji == emoji
    
    # Paso 4: Otorgar besitos
    besitos = await _award_besitos_for_reaction(
        user_id=user_id,
        reaction=reaction,
        session=container._session,
        bot=container._bot
    )
    
    assert besitos > 0
    
    # Paso 5: Verificar contador
    counts = await container.reactions.get_message_reaction_counts(
        channel_id=parsed_channel_id,
        message_id=parsed_message_id
    )
    
    assert emoji in counts
    assert counts[emoji] == 1


@pytest.mark.asyncio
async def test_user_changes_reaction(
    container_with_mock_bot,
    sample_reactions,
    sample_user
):
    """
    Test: Usuario cambia su reacción (upsert).
    """
    # Arrange
    container = container_with_mock_bot
    channel_id = -1001234567890
    message_id = 12345
    user_id = sample_user.user_id
    first_emoji = sample_reactions[0].emoji
    second_emoji = sample_reactions[1].emoji
    
    # Paso 1: Primera reacción
    first_reaction = await container.reactions.record_user_reaction(
        channel_id=channel_id,
        message_id=message_id,
        user_id=user_id,
        emoji=first_emoji
    )
    
    first_id = first_reaction.id
    
    # Paso 2: Cambiar reacción
    second_reaction = await container.reactions.record_user_reaction(
        channel_id=channel_id,
        message_id=message_id,
        user_id=user_id,
        emoji=second_emoji
    )
    
    # Assert - Es el mismo registro actualizado
    assert second_reaction.id == first_id
    assert second_reaction.emoji == second_emoji
    
    # Assert - Contador solo cuenta 1 (mismo usuario)
    counts = await container.reactions.get_message_reaction_counts(
        channel_id=channel_id,
        message_id=message_id
    )
    
    assert counts.get(first_emoji, 0) == 0  # Ya no tiene la primera
    assert counts.get(second_emoji, 0) == 1  # Ahora tiene la segunda


@pytest.mark.asyncio
async def test_rate_limiting_blocks_rapid_reactions(
    container_with_mock_bot,
    sample_reactions,
    sample_user
):
    """
    Test: Rate limiting bloquea reacciones rápidas (< 5 seg).
    """
    # Arrange
    container = container_with_mock_bot
    channel_id = -1001234567890
    message_id = 12345
    user_id = sample_user.user_id
    emoji = sample_reactions[0].emoji
    
    # Paso 1: Primera reacción
    await container.reactions.record_user_reaction(
        channel_id=channel_id,
        message_id=message_id,
        user_id=user_id,
        emoji=emoji
    )
    
    # Paso 2: Intentar reaccionar inmediatamente (debe fallar)
    can_react, reason = await _validate_rate_limiting(
        user_id=user_id,
        session=container._session
    )
    
    assert can_react == False
    assert "Espera" in reason
    assert "segundos" in reason


@pytest.mark.asyncio
async def test_rate_limiting_allows_after_5_seconds(
    container_with_mock_bot,
    sample_reactions,
    sample_user
):
    """
    Test: Rate limiting permite reaccionar después de 5 segundos.
    """
    # Arrange
    container = container_with_mock_bot
    user_id = sample_user.user_id
    emoji = sample_reactions[0].emoji
    
    # Paso 1: Primera reacción
    await container.reactions.record_user_reaction(
        channel_id=-1001234567890,
        message_id=12345,
        user_id=user_id,
        emoji=emoji
    )
    
    # Paso 2: Esperar 6 segundos
    await asyncio.sleep(6)
    
    # Paso 3: Intentar reaccionar de nuevo (debe pasar)
    can_react, reason = await _validate_rate_limiting(
        user_id=user_id,
        session=container._session
    )
    
    assert can_react == True


@pytest.mark.asyncio
async def test_multiple_users_reacting_updates_counters(
    container_with_mock_bot,
    sample_reactions,
    multiple_users
):
    """
    Test: Múltiples usuarios reaccionando actualiza contadores correctamente.
    """
    # Arrange
    container = container_with_mock_bot
    users = await multiple_users(5)
    channel_id = -1001234567890
    message_id = 12345
    emoji = sample_reactions[0].emoji
    
    # Act - 5 usuarios reaccionan con el mismo emoji
    for user in users:
        await container.reactions.record_user_reaction(
            channel_id=channel_id,
            message_id=message_id,
            user_id=user.user_id,
            emoji=emoji
        )
    
    # Assert
    counts = await container.reactions.get_message_reaction_counts(
        channel_id=channel_id,
        message_id=message_id
    )
    
    assert counts[emoji] == 5


@pytest.mark.asyncio
async def test_besitos_awarded_correctly(
    container_with_mock_bot,
    sample_reactions,
    sample_user
):
    """
    Test: Besitos se otorgan correctamente según configuración.
    """
    # Arrange
    container = container_with_mock_bot
    user_id = sample_user.user_id
    emoji = sample_reactions[0].emoji
    expected_besitos = sample_reactions[0].besitos_reward
    
    # Act - Crear reacción
    reaction = await container.reactions.record_user_reaction(
        channel_id=-1001234567890,
        message_id=12345,
        user_id=user_id,
        emoji=emoji
    )
    
    # Act - Otorgar besitos
    besitos = await _award_besitos_for_reaction(
        user_id=user_id,
        reaction=reaction,
        session=container._session,
        bot=container._bot
    )
    
    # Assert
    assert besitos == expected_besitos


@pytest.mark.asyncio
async def test_invalid_emoji_rejected(
    container_with_mock_bot,
    sample_user
):
    """
    Test: Emoji no configurado es rechazado.
    """
    # Arrange
    container = container_with_mock_bot
    user_id = sample_user.user_id
    invalid_emoji = "🤷"  # No configurado
    
    # Act
    reaction = await container.reactions.record_user_reaction(
        channel_id=-1001234567890,
        message_id=12345,
        user_id=user_id,
        emoji=invalid_emoji
    )
    
    # Assert
    assert reaction is None


@pytest.mark.asyncio
async def test_inactive_emoji_rejected(
    container_with_mock_bot,
    sample_reactions,
    sample_user
):
    """
    Test: Emoji desactivado es rechazado.
    """
    # Arrange
    container = container_with_mock_bot
    user_id = sample_user.user_id
    emoji = sample_reactions[0].emoji
    
    # Desactivar emoji
    await container.reactions.update_reaction(
        reaction_id=sample_reactions[0].id,
        active=False
    )
    
    # Act - Intentar reaccionar con emoji desactivado
    reaction = await container.reactions.record_user_reaction(
        channel_id=-1001234567890,
        message_id=12345,
        user_id=user_id,
        emoji=emoji
    )
    
    # Assert
    assert reaction is None


@pytest.mark.asyncio
async def test_user_statistics_tracked_correctly(
    container_with_mock_bot,
    sample_reactions,
    sample_user
):
    """
    Test: Estadísticas de usuario se trackean correctamente.
    """
    # Arrange
    container = container_with_mock_bot
    user_id = sample_user.user_id
    emoji = sample_reactions[0].emoji
    
    # Act - Usuario reacciona a 3 mensajes diferentes
    for i in range(3):
        await container.reactions.record_user_reaction(
            channel_id=-1001234567890,
            message_id=10000 + i,
            user_id=user_id,
            emoji=emoji
        )
    
    # Assert
    total = await container.reactions.get_user_total_reactions(user_id)
    assert total == 3


# ===== TEST DE ESCENARIO COMPLETO =====

@pytest.mark.asyncio
async def test_complete_scenario_multiple_users_multiple_messages(
    container_with_mock_bot,
    sample_reactions,
    multiple_users
):
    """
    Test: Escenario completo con múltiples usuarios y mensajes.
    
    Simula:
    - Admin publica 3 mensajes con reacciones
    - 5 usuarios reaccionan a cada mensaje
    - Verifica contadores, besitos, estadísticas
    """
    # Arrange
    container = container_with_mock_bot
    users = await multiple_users(5)
    channel_id = -1001234567890
    message_ids = [100, 200, 300]
    
    # Act - Cada usuario reacciona a cada mensaje
    for message_id in message_ids:
        for i, user in enumerate(users):
            # Alternar emojis
            emoji = sample_reactions[i % len(sample_reactions)].emoji
            
            await container.reactions.record_user_reaction(
                channel_id=channel_id,
                message_id=message_id,
                user_id=user.user_id,
                emoji=emoji
            )
            
            # Pequeña pausa para evitar rate limiting en tests
            await asyncio.sleep(0.1)
    
    # Assert - Verificar contadores de cada mensaje
    for message_id in message_ids:
        counts = await container.reactions.get_message_reaction_counts(
            channel_id=channel_id,
            message_id=message_id
        )
        
        # Debe tener contadores para múltiples emojis
        assert len(counts) > 0
        
        # Total de reacciones debe ser 5 (5 usuarios)
        total = await container.reactions.get_message_total_reactions(
            channel_id=channel_id,
            message_id=message_id
        )
        assert total == 5
    
    # Assert - Verificar estadísticas de usuarios
    for user in users:
        total = await container.reactions.get_user_total_reactions(
            user.user_id
        )
        assert total == 3
