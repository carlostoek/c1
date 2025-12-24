"""
Tests para el sistema de notificaciones del módulo de gamificación.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from bot.gamification.services.notifications import NotificationService
from bot.gamification.database.models import Level, Mission, Reward, GamificationConfig
from bot.gamification.database.enums import RewardType


@pytest.mark.asyncio
async def test_notify_level_up(db_session):
    """Test notificación de level-up."""
    # Setup
    mock_bot = AsyncMock()
    service = NotificationService(mock_bot, db_session)

    # Crear configuración con notificaciones habilitadas
    config = GamificationConfig()
    config.id = 1
    config.notifications_enabled = True
    db_session.add(config)
    await db_session.commit()

    # Crear niveles
    old_level = Level(id=1, name="Novato", min_besitos=0, order=1)
    new_level = Level(id=2, name="Experto", min_besitos=100, order=2)
    db_session.add_all([old_level, new_level])
    await db_session.commit()

    # Ejecutar
    await service.notify_level_up(user_id=123, old_level=old_level, new_level=new_level)

    # Verificar
    mock_bot.send_message.assert_called_once()
    call_args = mock_bot.send_message.call_args
    assert call_args[0][0] == 123  # user_id
    assert "Novato" in call_args[0][1]
    assert "Experto" in call_args[0][1]
    assert call_args[1]['parse_mode'] == "HTML"


@pytest.mark.asyncio
async def test_notify_mission_completed(db_session):
    """Test notificación de misión completada."""
    # Setup
    mock_bot = AsyncMock()
    service = NotificationService(mock_bot, db_session)

    config = GamificationConfig()
    config.id = 1
    config.notifications_enabled = True
    db_session.add(config)
    await db_session.commit()

    mission = Mission(
        id=1,
        name="Misión de Prueba",
        description="Test",
        mission_type="one_time",
        criteria='{"type": "one_time"}',
        besitos_reward=50,
        created_by=1
    )
    db_session.add(mission)
    await db_session.commit()

    # Ejecutar
    await service.notify_mission_completed(user_id=123, mission=mission)

    # Verificar
    mock_bot.send_message.assert_called_once()
    call_args = mock_bot.send_message.call_args
    assert call_args[0][0] == 123
    assert "Misión de Prueba" in call_args[0][1]
    assert "50" in call_args[0][1]
    assert "/profile" in call_args[0][1]


@pytest.mark.asyncio
async def test_notify_reward_unlocked(db_session):
    """Test notificación de recompensa desbloqueada."""
    # Setup
    mock_bot = AsyncMock()
    service = NotificationService(mock_bot, db_session)

    config = GamificationConfig()
    config.id = 1
    config.notifications_enabled = True
    db_session.add(config)
    await db_session.commit()

    reward = Reward(
        id=1,
        name="Badge Especial",
        description="Un badge único",
        reward_type=RewardType.BADGE.value,
        metadata='{"icon": "🏆", "rarity": "legendary"}',
        created_by=1
    )
    db_session.add(reward)
    await db_session.commit()

    # Ejecutar
    await service.notify_reward_unlocked(user_id=123, reward=reward)

    # Verificar
    mock_bot.send_message.assert_called_once()
    call_args = mock_bot.send_message.call_args
    assert call_args[0][0] == 123
    assert "Badge Especial" in call_args[0][1]
    assert "Un badge único" in call_args[0][1]


@pytest.mark.asyncio
async def test_notify_streak_milestone_valid(db_session):
    """Test notificación de milestone de racha (válido)."""
    # Setup
    mock_bot = AsyncMock()
    service = NotificationService(mock_bot, db_session)

    config = GamificationConfig()
    config.id = 1
    config.notifications_enabled = True
    db_session.add(config)
    await db_session.commit()

    # Ejecutar con milestone válido (7 días)
    await service.notify_streak_milestone(user_id=123, days=7)

    # Verificar
    mock_bot.send_message.assert_called_once()
    call_args = mock_bot.send_message.call_args
    assert call_args[0][0] == 123
    assert "7 días" in call_args[0][1] or "7" in call_args[0][1]
    assert "🔥" in call_args[0][1]


@pytest.mark.asyncio
async def test_notify_streak_milestone_invalid(db_session):
    """Test que NO notifica milestones no válidos (evita spam)."""
    # Setup
    mock_bot = AsyncMock()
    service = NotificationService(mock_bot, db_session)

    config = GamificationConfig()
    config.id = 1
    config.notifications_enabled = True
    db_session.add(config)
    await db_session.commit()

    # Ejecutar con milestone NO válido (5 días, no está en [7, 14, 30, 60, 100])
    await service.notify_streak_milestone(user_id=123, days=5)

    # Verificar que NO se envió notificación
    mock_bot.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_notify_streak_lost_significant(db_session):
    """Test notificación de racha perdida (significativa)."""
    # Setup
    mock_bot = AsyncMock()
    service = NotificationService(mock_bot, db_session)

    config = GamificationConfig()
    config.id = 1
    config.notifications_enabled = True
    db_session.add(config)
    await db_session.commit()

    # Ejecutar con racha significativa (>= 7 días)
    await service.notify_streak_lost(user_id=123, days=10)

    # Verificar
    mock_bot.send_message.assert_called_once()
    call_args = mock_bot.send_message.call_args
    assert call_args[0][0] == 123
    assert "10" in call_args[0][1]
    assert "💔" in call_args[0][1]


@pytest.mark.asyncio
async def test_notify_streak_lost_insignificant(db_session):
    """Test que NO notifica rachas perdidas insignificantes."""
    # Setup
    mock_bot = AsyncMock()
    service = NotificationService(mock_bot, db_session)

    config = GamificationConfig()
    config.id = 1
    config.notifications_enabled = True
    db_session.add(config)
    await db_session.commit()

    # Ejecutar con racha insignificante (< 7 días)
    await service.notify_streak_lost(user_id=123, days=3)

    # Verificar que NO se envió notificación
    mock_bot.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_notifications_disabled(db_session):
    """Test que NO envía notificaciones si está deshabilitado."""
    # Setup
    mock_bot = AsyncMock()
    service = NotificationService(mock_bot, db_session)

    # Configuración con notificaciones DESHABILITADAS
    config = GamificationConfig()
    config.id = 1
    config.notifications_enabled = False
    db_session.add(config)
    await db_session.commit()

    old_level = Level(id=1, name="Novato", min_besitos=0, order=1)
    new_level = Level(id=2, name="Experto", min_besitos=100, order=2)
    db_session.add_all([old_level, new_level])
    await db_session.commit()

    # Ejecutar
    await service.notify_level_up(user_id=123, old_level=old_level, new_level=new_level)

    # Verificar que NO se envió
    mock_bot.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_notification_failure_handling(db_session):
    """Test manejo de errores en envío de notificaciones."""
    # Setup
    mock_bot = AsyncMock()
    mock_bot.send_message.side_effect = Exception("Bot blocked by user")
    service = NotificationService(mock_bot, db_session)

    config = GamificationConfig()
    config.id = 1
    config.notifications_enabled = True
    db_session.add(config)
    await db_session.commit()

    old_level = Level(id=1, name="Novato", min_besitos=0, order=1)
    new_level = Level(id=2, name="Experto", min_besitos=100, order=2)
    db_session.add_all([old_level, new_level])
    await db_session.commit()

    # Ejecutar (no debe crashear)
    await service.notify_level_up(user_id=123, old_level=old_level, new_level=new_level)

    # Verificar que se intentó enviar
    mock_bot.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_notification_service_in_container(db_session):
    """Test que NotificationService está disponible en container."""
    from bot.gamification.services.container import GamificationContainer
    from unittest.mock import MagicMock

    # Setup
    mock_bot = MagicMock()
    container = GamificationContainer(db_session, mock_bot)

    # Verificar que el servicio se carga correctamente
    assert container.notifications is not None
    assert isinstance(container.notifications, NotificationService)

    # Verificar que está en loaded_services después de acceder
    loaded = container.get_loaded_services()
    assert 'notifications' in loaded


@pytest.mark.asyncio
async def test_container_without_bot_raises_error(db_session):
    """Test que container sin bot lanza error al acceder notifications."""
    from bot.gamification.services.container import GamificationContainer

    # Setup: Container SIN bot
    container = GamificationContainer(db_session, bot=None)

    # Verificar que lanza RuntimeError
    with pytest.raises(RuntimeError, match="NotificationService requires a Bot instance"):
        _ = container.notifications
