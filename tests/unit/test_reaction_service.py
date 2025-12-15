"""
Unit tests for ReactionService.

Tests all CRUD operations and user reaction management.
"""
import pytest
from datetime import datetime, timezone


# ===== TESTS CRUD DE CONFIGS =====

@pytest.mark.asyncio
async def test_create_reaction_success(reaction_service):
    """
    Test: Crear una reacción exitosamente.
    """
    # Arrange
    emoji = "❤️"
    label = "Me encanta"
    besitos = 5
    
    # Act
    reaction = await reaction_service.create_reaction(
        emoji=emoji,
        label=label,
        besitos_reward=besitos
    )
    
    # Assert
    assert reaction is not None
    assert reaction.emoji == emoji
    assert reaction.label == label
    assert reaction.besitos_reward == besitos
    assert reaction.active == True


@pytest.mark.asyncio
async def test_create_reaction_duplicate_emoji(reaction_service, sample_reactions):
    """
    Test: No permite crear reacción con emoji duplicado.
    """
    # Arrange
    existing_emoji = sample_reactions[0].emoji
    
    # Act
    reaction = await reaction_service.create_reaction(
        emoji=existing_emoji,
        label="Otra label",
        besitos_reward=10
    )
    
    # Assert
    assert reaction is None


@pytest.mark.asyncio
async def test_create_reaction_max_limit(reaction_service):
    """
    Test: No permite crear más de MAX_ACTIVE_REACTIONS.
    """
    # Arrange - Crear 6 reacciones (límite)
    for i in range(reaction_service.MAX_ACTIVE_REACTIONS):
        await reaction_service.create_reaction(
            emoji=f"emoji_{i}",
            label=f"Label {i}",
            besitos_reward=5
        )
    
    # Act - Intentar crear una más
    reaction = await reaction_service.create_reaction(
        emoji="extra",
        label="Extra",
        besitos_reward=5
    )
    
    # Assert
    assert reaction is None


@pytest.mark.asyncio
async def test_get_active_reactions(reaction_service, sample_reactions):
    """
    Test: Obtener solo reacciones activas.
    """
    # Arrange - Desactivar una reacción
    await reaction_service.update_reaction(
        reaction_id=sample_reactions[0].id,
        active=False
    )
    
    # Act
    active = await reaction_service.get_active_reactions()
    
    # Assert
    assert len(active) == len(sample_reactions) - 1
    assert all(r.active for r in active)


@pytest.mark.asyncio
async def test_get_all_reactions(reaction_service, sample_reactions):
    """
    Test: Obtener todas las reacciones incluyendo inactivas.
    """
    # Arrange - Desactivar una
    await reaction_service.update_reaction(
        reaction_id=sample_reactions[0].id,
        active=False
    )
    
    # Act
    all_reactions = await reaction_service.get_all_reactions(include_inactive=True)
    
    # Assert
    assert len(all_reactions) == len(sample_reactions)


@pytest.mark.asyncio
async def test_get_reaction_by_id(reaction_service, sample_reactions):
    """
    Test: Obtener reacción por ID.
    """
    # Arrange
    target_id = sample_reactions[0].id
    
    # Act
    reaction = await reaction_service.get_reaction_by_id(target_id)
    
    # Assert
    assert reaction is not None
    assert reaction.id == target_id


@pytest.mark.asyncio
async def test_get_reaction_by_emoji(reaction_service, sample_reactions):
    """
    Test: Obtener reacción por emoji.
    """
    # Arrange
    target_emoji = sample_reactions[0].emoji
    
    # Act
    reaction = await reaction_service.get_reaction_by_emoji(target_emoji)
    
    # Assert
    assert reaction is not None
    assert reaction.emoji == target_emoji


@pytest.mark.asyncio
async def test_update_reaction_label(reaction_service, sample_reactions):
    """
    Test: Actualizar label de una reacción.
    """
    # Arrange
    reaction_id = sample_reactions[0].id
    new_label = "Nuevo label"
    
    # Act
    updated = await reaction_service.update_reaction(
        reaction_id=reaction_id,
        label=new_label
    )
    
    # Assert
    assert updated is not None
    assert updated.label == new_label


@pytest.mark.asyncio
async def test_update_reaction_besitos(reaction_service, sample_reactions):
    """
    Test: Actualizar besitos de una reacción.
    """
    # Arrange
    reaction_id = sample_reactions[0].id
    new_besitos = 10
    
    # Act
    updated = await reaction_service.update_reaction(
        reaction_id=reaction_id,
        besitos_reward=new_besitos
    )
    
    # Assert
    assert updated is not None
    assert updated.besitos_reward == new_besitos


@pytest.mark.asyncio
async def test_update_reaction_active(reaction_service, sample_reactions):
    """
    Test: Activar/desactivar reacción.
    """
    # Arrange
    reaction_id = sample_reactions[0].id
    
    # Act - Desactivar
    updated = await reaction_service.update_reaction(
        reaction_id=reaction_id,
        active=False
    )
    
    # Assert
    assert updated is not None
    assert updated.active == False
    
    # Act - Reactivar
    updated = await reaction_service.update_reaction(
        reaction_id=reaction_id,
        active=True
    )
    
    # Assert
    assert updated.active == True


@pytest.mark.asyncio
async def test_delete_reaction_no_history(reaction_service, sample_reactions):
    """
    Test: Eliminar reacción sin histórico (se elimina de verdad).
    """
    # Arrange
    reaction_id = sample_reactions[0].id
    
    # Act
    deleted = await reaction_service.delete_reaction(reaction_id)
    
    # Assert
    assert deleted == True
    
    # Verify - No existe en BD
    reaction = await reaction_service.get_reaction_by_id(reaction_id)
    assert reaction is None


@pytest.mark.asyncio
async def test_count_active_reactions(reaction_service, sample_reactions):
    """
    Test: Contar reacciones activas.
    """
    # Act
    count = await reaction_service.count_active_reactions()
    
    # Assert
    assert count == len(sample_reactions)


# ===== TESTS GESTIÓN DE REACCIONES DE USUARIOS =====

@pytest.mark.asyncio
async def test_record_user_reaction_new(
    reaction_service,
    sample_reactions,
    sample_user
):
    """
    Test: Registrar primera reacción de un usuario.
    """
    # Arrange
    channel_id = -1001234567890
    message_id = 12345
    user_id = sample_user.user_id
    emoji = sample_reactions[0].emoji
    
    # Act
    reaction = await reaction_service.record_user_reaction(
        channel_id=channel_id,
        message_id=message_id,
        user_id=user_id,
        emoji=emoji
    )
    
    # Assert
    assert reaction is not None
    assert reaction.channel_id == channel_id
    assert reaction.message_id == message_id
    assert reaction.user_id == user_id
    assert reaction.emoji == emoji
    assert reaction.besitos_awarded == sample_reactions[0].besitos_reward


@pytest.mark.asyncio
async def test_record_user_reaction_update(
    reaction_service,
    sample_reactions,
    sample_user
):
    """
    Test: Actualizar reacción existente (upsert).
    """
    # Arrange
    channel_id = -1001234567890
    message_id = 12345
    user_id = sample_user.user_id
    first_emoji = sample_reactions[0].emoji
    second_emoji = sample_reactions[1].emoji
    
    # Act - Primera reacción
    first_reaction = await reaction_service.record_user_reaction(
        channel_id=channel_id,
        message_id=message_id,
        user_id=user_id,
        emoji=first_emoji
    )
    first_id = first_reaction.id
    
    # Act - Cambiar reacción
    second_reaction = await reaction_service.record_user_reaction(
        channel_id=channel_id,
        message_id=message_id,
        user_id=user_id,
        emoji=second_emoji
    )
    
    # Assert
    assert second_reaction.id == first_id  # Mismo registro
    assert second_reaction.emoji == second_emoji  # Emoji actualizado


@pytest.mark.asyncio
async def test_record_user_reaction_invalid_emoji(
    reaction_service,
    sample_user
):
    """
    Test: No permite reaccionar con emoji no configurado.
    """
    # Arrange
    channel_id = -1001234567890
    message_id = 12345
    user_id = sample_user.user_id
    invalid_emoji = "🤷"  # No configurado
    
    # Act
    reaction = await reaction_service.record_user_reaction(
        channel_id=channel_id,
        message_id=message_id,
        user_id=user_id,
        emoji=invalid_emoji
    )
    
    # Assert
    assert reaction is None


@pytest.mark.asyncio
async def test_get_user_reaction(
    reaction_service,
    sample_reactions,
    sample_user
):
    """
    Test: Obtener reacción de un usuario a un mensaje.
    """
    # Arrange
    channel_id = -1001234567890
    message_id = 12345
    user_id = sample_user.user_id
    emoji = sample_reactions[0].emoji
    
    # Crear reacción
    await reaction_service.record_user_reaction(
        channel_id=channel_id,
        message_id=message_id,
        user_id=user_id,
        emoji=emoji
    )
    
    # Act
    reaction = await reaction_service.get_user_reaction(
        channel_id=channel_id,
        message_id=message_id,
        user_id=user_id
    )
    
    # Assert
    assert reaction is not None
    assert reaction.emoji == emoji


@pytest.mark.asyncio
async def test_has_user_reacted(
    reaction_service,
    sample_reactions,
    sample_user
):
    """
    Test: Verificar si usuario ha reaccionado.
    """
    # Arrange
    channel_id = -1001234567890
    message_id = 12345
    user_id = sample_user.user_id
    
    # Act - Antes de reaccionar
    has_reacted_before = await reaction_service.has_user_reacted(
        channel_id=channel_id,
        message_id=message_id,
        user_id=user_id
    )
    
    # Assert
    assert has_reacted_before == False
    
    # Arrange - Crear reacción
    await reaction_service.record_user_reaction(
        channel_id=channel_id,
        message_id=message_id,
        user_id=user_id,
        emoji=sample_reactions[0].emoji
    )
    
    # Act - Después de reaccionar
    has_reacted_after = await reaction_service.has_user_reacted(
        channel_id=channel_id,
        message_id=message_id,
        user_id=user_id
    )
    
    # Assert
    assert has_reacted_after == True


@pytest.mark.asyncio
async def test_remove_user_reaction(
    reaction_service,
    sample_reactions,
    sample_user
):
    """
    Test: Eliminar reacción de un usuario.
    """
    # Arrange
    channel_id = -1001234567890
    message_id = 12345
    user_id = sample_user.user_id
    
    # Crear reacción
    await reaction_service.record_user_reaction(
        channel_id=channel_id,
        message_id=message_id,
        user_id=user_id,
        emoji=sample_reactions[0].emoji
    )
    
    # Act
    removed = await reaction_service.remove_user_reaction(
        channel_id=channel_id,
        message_id=message_id,
        user_id=user_id
    )
    
    # Assert
    assert removed == True
    
    # Verify
    has_reacted = await reaction_service.has_user_reacted(
        channel_id=channel_id,
        message_id=message_id,
        user_id=user_id
    )
    assert has_reacted == False


# ===== TESTS CONTADORES Y ANALYTICS =====

@pytest.mark.asyncio
async def test_get_message_reaction_counts(
    reaction_service,
    sample_reactions,
    sample_user,
    db_session
):
    """
    Test: Obtener contadores de reacciones de un mensaje.
    """
    # Arrange
    channel_id = -1001234567890
    message_id = 12345
    
    # Crear varios usuarios reaccionando
    from bot.database.models import User
    users = []
    for i in range(3):
        user = User(user_id=1000 + i, username=f"user{i}", first_name=f"Name{i}")
        db_session.add(user)
        users.append(user)

    await db_session.commit()
    
    # Usuario 1 y 2 reaccionan con ❤️
    for user in users[:2]:
        await reaction_service.record_user_reaction(
            channel_id=channel_id,
            message_id=message_id,
            user_id=user.user_id,
            emoji=sample_reactions[0].emoji
        )
    
    # Usuario 3 reacciona con 👍
    await reaction_service.record_user_reaction(
        channel_id=channel_id,
        message_id=message_id,
        user_id=users[2].user_id,
        emoji=sample_reactions[1].emoji
    )
    
    # Act
    counts = await reaction_service.get_message_reaction_counts(
        channel_id=channel_id,
        message_id=message_id
    )
    
    # Assert
    assert counts[sample_reactions[0].emoji] == 2  # ❤️
    assert counts[sample_reactions[1].emoji] == 1  # 👍


@pytest.mark.asyncio
async def test_get_message_total_reactions(
    reaction_service,
    sample_reactions,
    db_session
):
    """
    Test: Obtener total de reacciones de un mensaje.
    """
    # Arrange
    channel_id = -1001234567890
    message_id = 12345
    
    # Crear 3 usuarios reaccionando
    from bot.database.models import User
    for i in range(3):
        user = User(user_id=2000 + i, username=f"user{i}", first_name=f"Name{i}")
        db_session.add(user)

    await db_session.commit()
    
    for i in range(3):
        await reaction_service.record_user_reaction(
            channel_id=channel_id,
            message_id=message_id,
            user_id=2000 + i,
            emoji=sample_reactions[0].emoji
        )
    
    # Act
    total = await reaction_service.get_message_total_reactions(
        channel_id=channel_id,
        message_id=message_id
    )
    
    # Assert
    assert total == 3


@pytest.mark.asyncio
async def test_get_user_total_reactions(
    reaction_service,
    sample_reactions,
    sample_user
):
    """
    Test: Obtener total de reacciones de un usuario.
    """
    # Arrange
    channel_id = -1001234567890
    user_id = sample_user.user_id
    
    # Usuario reacciona a 3 mensajes diferentes
    for i in range(3):
        await reaction_service.record_user_reaction(
            channel_id=channel_id,
            message_id=10000 + i,
            user_id=user_id,
            emoji=sample_reactions[0].emoji
        )
    
    # Act
    total = await reaction_service.get_user_total_reactions(user_id)
    
    # Assert
    assert total == 3


@pytest.mark.asyncio
async def test_get_top_reacted_messages(
    reaction_service,
    sample_reactions,
    db_session
):
    """
    Test: Obtener mensajes con más reacciones.
    """
    # Arrange
    channel_id = -1001234567890
    
    # Crear usuarios
    from bot.database.models import User
    for i in range(5):
        user = User(user_id=3000 + i, username=f"user{i}", first_name=f"Name{i}")
        db_session.add(user)

    await db_session.commit()
    
    # Mensaje 1: 3 reacciones
    for i in range(3):
        await reaction_service.record_user_reaction(
            channel_id=channel_id,
            message_id=100,
            user_id=3000 + i,
            emoji=sample_reactions[0].emoji
        )
    
    # Mensaje 2: 2 reacciones
    for i in range(2):
        await reaction_service.record_user_reaction(
            channel_id=channel_id,
            message_id=200,
            user_id=3000 + i,
            emoji=sample_reactions[0].emoji
        )
    
    # Mensaje 3: 5 reacciones (más reaccionado)
    for i in range(5):
        await reaction_service.record_user_reaction(
            channel_id=channel_id,
            message_id=300,
            user_id=3000 + i,
            emoji=sample_reactions[0].emoji
        )
    
    # Act
    top = await reaction_service.get_top_reacted_messages(
        channel_id=channel_id,
        limit=3
    )
    
    # Assert
    assert len(top) == 3
    assert top[0][0] == 300  # Mensaje 300 primero (5 reacciones)
    assert top[0][1] == 5
    assert top[1][0] == 100  # Mensaje 100 segundo (3 reacciones)
    assert top[1][1] == 3


@pytest.mark.asyncio
async def test_get_most_used_emoji(
    reaction_service,
    sample_reactions,
    db_session
):
    """
    Test: Obtener emoji más usado.
    """
    # Arrange
    channel_id = -1001234567890
    
    # Crear usuarios
    from bot.database.models import User
    for i in range(5):
        user = User(user_id=4000 + i, username=f"user{i}", first_name=f"Name{i}")
        db_session.add(user)

    await db_session.commit()
    
    # 3 reacciones con ❤️
    for i in range(3):
        await reaction_service.record_user_reaction(
            channel_id=channel_id,
            message_id=100 + i,
            user_id=4000 + i,
            emoji=sample_reactions[0].emoji
        )
    
    # 2 reacciones con 👍
    for i in range(2):
        await reaction_service.record_user_reaction(
            channel_id=channel_id,
            message_id=200 + i,
            user_id=4000 + i,
            emoji=sample_reactions[1].emoji
        )
    
    # Act
    most_used = await reaction_service.get_most_used_emoji(
        channel_id=channel_id
    )
    
    # Assert
    assert most_used is not None
    assert most_used[0] == sample_reactions[0].emoji  # ❤️
    assert most_used[1] == 3
