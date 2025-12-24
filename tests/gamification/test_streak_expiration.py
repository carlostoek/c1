"""
Tests para Streak Expiration Checker (G5.2).

Valida:
- Reseteo de rachas expiradas
- Threshold de expiración correcto
- Notificaciones a usuarios
- Manejo de config
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock

from bot.gamification.database.models import UserStreak, GamificationConfig
from bot.gamification.background.streak_expiration_checker import (
    check_expired_streaks,
    notify_streak_lost
)


@pytest_asyncio.fixture
async def gamification_config(db_session):
    """Crea configuración de gamificación."""
    config = GamificationConfig(
        id=1,
        streak_reset_hours=24,
        notifications_enabled=True,
        besitos_per_reaction=1,
        max_besitos_per_day=1000
    )
    db_session.add(config)
    await db_session.commit()
    return config


@pytest_asyncio.fixture
async def expired_streaks(db_session, gamification_config):
    """
    Crea rachas de prueba (expiradas y activas).

    - User 1: Racha expirada (3 días, última reacción hace 30 horas)
    - User 2: Racha activa (5 días, última reacción hace 10 horas)
    - User 3: Racha expirada (7 días, última reacción hace 48 horas)
    """
    now = datetime.now(UTC)

    # Racha expirada (30 horas atrás)
    streak1 = UserStreak(
        user_id=2001,
        current_streak=3,
        longest_streak=5,
        last_reaction_date=now - timedelta(hours=30)
    )

    # Racha activa (10 horas atrás)
    streak2 = UserStreak(
        user_id=2002,
        current_streak=5,
        longest_streak=5,
        last_reaction_date=now - timedelta(hours=10)
    )

    # Racha expirada (48 horas atrás)
    streak3 = UserStreak(
        user_id=2003,
        current_streak=7,
        longest_streak=10,
        last_reaction_date=now - timedelta(hours=48)
    )

    db_session.add_all([streak1, streak2, streak3])
    await db_session.commit()

    return [streak1, streak2, streak3]


@pytest.mark.asyncio
async def test_check_expired_streaks_resets_only_expired(
    db_session,
    gamification_config,
    expired_streaks
):
    """Verifica que solo se resetean rachas expiradas."""
    # Mock del bot
    mock_bot = AsyncMock()
    mock_bot.send_message = AsyncMock()

    # Ejecutar verificación
    await check_expired_streaks(db_session, mock_bot)

    # Verificar que racha expirada 1 se reseteó
    await db_session.refresh(expired_streaks[0])
    assert expired_streaks[0].current_streak == 0

    # Verificar que racha activa 2 NO se reseteó
    await db_session.refresh(expired_streaks[1])
    assert expired_streaks[1].current_streak == 5

    # Verificar que racha expirada 3 se reseteó
    await db_session.refresh(expired_streaks[2])
    assert expired_streaks[2].current_streak == 0


@pytest.mark.asyncio
async def test_check_expired_streaks_sends_notifications(
    db_session,
    gamification_config,
    expired_streaks
):
    """Verifica que se envían notificaciones para rachas expiradas."""
    # Mock del bot
    mock_bot = AsyncMock()
    mock_bot.send_message = AsyncMock()

    # Ejecutar verificación
    await check_expired_streaks(db_session, mock_bot)

    # Verificar que se enviaron 2 notificaciones (User 2001 y 2003)
    assert mock_bot.send_message.call_count == 2

    # Verificar contenido de las notificaciones
    calls = mock_bot.send_message.call_args_list

    # Primera notificación (User 2001, racha de 3 días)
    assert calls[0][0][0] == 2001
    assert "Racha Perdida" in calls[0][0][1]
    assert "3 días" in calls[0][0][1]

    # Segunda notificación (User 2003, racha de 7 días)
    assert calls[1][0][0] == 2003
    assert "Racha Perdida" in calls[1][0][1]
    assert "7 días" in calls[1][0][1]


@pytest.mark.asyncio
async def test_check_expired_streaks_no_notifications_if_disabled(
    db_session,
    gamification_config,
    expired_streaks
):
    """Verifica que no se envían notificaciones si están deshabilitadas."""
    # Deshabilitar notificaciones
    gamification_config.notifications_enabled = False
    await db_session.commit()

    # Mock del bot
    mock_bot = AsyncMock()
    mock_bot.send_message = AsyncMock()

    # Ejecutar verificación
    await check_expired_streaks(db_session, mock_bot)

    # Verificar que NO se enviaron notificaciones
    mock_bot.send_message.assert_not_called()

    # Pero las rachas deben haberse reseteado igual
    await db_session.refresh(expired_streaks[0])
    assert expired_streaks[0].current_streak == 0


@pytest.mark.asyncio
async def test_notify_streak_lost_sends_correct_message(db_session):
    """Verifica que notify_streak_lost envía el mensaje correcto."""
    # Mock del bot
    mock_bot = AsyncMock()
    mock_bot.send_message = AsyncMock()

    # Llamar a notify_streak_lost
    await notify_streak_lost(mock_bot, 12345, 10)

    # Verificar llamada
    mock_bot.send_message.assert_called_once()

    # Verificar contenido del mensaje
    call_args = mock_bot.send_message.call_args
    assert call_args[0][0] == 12345
    message_text = call_args[0][1]
    assert "🔥" in message_text
    assert "Racha Perdida" in message_text
    assert "10 días" in message_text
    assert "expiró por inactividad" in message_text
    assert call_args[1]["parse_mode"] == "HTML"


@pytest.mark.asyncio
async def test_notify_streak_lost_handles_send_error(db_session):
    """Verifica que notify_streak_lost maneja errores al enviar mensajes."""
    # Mock del bot que falla al enviar
    mock_bot = AsyncMock()
    mock_bot.send_message = AsyncMock(side_effect=Exception("User blocked bot"))

    # No debería lanzar excepción
    await notify_streak_lost(mock_bot, 12345, 5)

    # Verificar que intentó enviar
    mock_bot.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_check_expired_streaks_uses_config_threshold(db_session):
    """Verifica que se usa el threshold de configuración correctamente."""
    # Crear config con threshold de 48 horas
    config = GamificationConfig(
        id=1,
        streak_reset_hours=48,  # 48 horas
        notifications_enabled=False,
        besitos_per_reaction=1,
        max_besitos_per_day=1000
    )
    db_session.add(config)
    await db_session.commit()

    now = datetime.now(UTC)

    # Racha con 30 horas de inactividad (NO debería expirar con threshold de 48h)
    streak1 = UserStreak(
        user_id=3001,
        current_streak=5,
        longest_streak=5,
        last_reaction_date=now - timedelta(hours=30)
    )

    # Racha con 50 horas de inactividad (SÍ debería expirar)
    streak2 = UserStreak(
        user_id=3002,
        current_streak=7,
        longest_streak=7,
        last_reaction_date=now - timedelta(hours=50)
    )

    db_session.add_all([streak1, streak2])
    await db_session.commit()

    # Mock del bot
    mock_bot = AsyncMock()

    # Ejecutar verificación
    await check_expired_streaks(db_session, mock_bot)

    # Verificar que racha 1 NO se reseteó (30h < 48h)
    await db_session.refresh(streak1)
    assert streak1.current_streak == 5

    # Verificar que racha 2 SÍ se reseteó (50h > 48h)
    await db_session.refresh(streak2)
    assert streak2.current_streak == 0


@pytest.mark.asyncio
async def test_check_expired_streaks_handles_no_config(db_session):
    """Verifica que maneja correctamente la ausencia de configuración."""
    # No crear GamificationConfig (no existe)

    # Mock del bot
    mock_bot = AsyncMock()

    # Ejecutar verificación (no debería crashear)
    await check_expired_streaks(db_session, mock_bot)

    # No debería hacer nada (retorna early)
    # Simplemente verificar que no hubo errores
    assert True


@pytest.mark.asyncio
async def test_check_expired_streaks_handles_individual_notification_errors(
    db_session,
    gamification_config,
    expired_streaks
):
    """Verifica que errores en notificaciones individuales no detienen el proceso."""
    # Mock del bot que falla para el primer usuario
    mock_bot = AsyncMock()

    call_count = 0
    def side_effect_send(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:  # Primera llamada falla
            raise Exception("User blocked bot")
        # Segunda llamada funciona
        return AsyncMock()

    mock_bot.send_message = AsyncMock(side_effect=side_effect_send)

    # Ejecutar verificación (no debería lanzar excepción)
    await check_expired_streaks(db_session, mock_bot)

    # Verificar que ambas rachas se resetearon a pesar del error
    await db_session.refresh(expired_streaks[0])
    assert expired_streaks[0].current_streak == 0

    await db_session.refresh(expired_streaks[2])
    assert expired_streaks[2].current_streak == 0
