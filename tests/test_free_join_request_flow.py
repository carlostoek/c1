"""
Tests E2E para el flujo Free con ChatJoinRequest.

Valida:
- Creación de solicitudes desde ChatJoinRequest
- Rechazo de solicitudes duplicadas
- Envío de notificaciones con variables
- Aprobación automática después del tiempo de espera
- Configuración de mensaje personalizado
- Validación de seguridad (canal autorizado)
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from bot.database.engine import get_session
from bot.database.models import BotConfig, FreeChannelRequest
from bot.services.container import ServiceContainer


@pytest.fixture
def configured_free_channel(event_loop):
    """Configura canal Free en BD y retorna el ID."""
    async def _setup():
        async with get_session() as session:
            config = await session.get(BotConfig, 1)
            if not config:
                config = BotConfig(id=1)
                session.add(config)

            config.free_channel_id = "-1001234567890"
            config.wait_time_minutes = 5

            await session.commit()
            await session.refresh(config)

            return config.free_channel_id

    return event_loop.run_until_complete(_setup())


# ===== TEST 1: Crear solicitud desde ChatJoinRequest =====


@pytest.mark.asyncio
async def test_create_free_request_from_join_request(mock_bot, configured_free_channel):
    """
    Test: Crear solicitud Free desde ChatJoinRequest válido.

    Verifica:
    - Solicitud creada en BD
    - Retorna success=True
    - FreeChannelRequest tiene datos correctos
    """
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        user_id = 123456789
        from_chat_id = configured_free_channel

        # Crear solicitud
        success, message, request = await container.subscription.create_free_request_from_join_request(
            user_id=user_id,
            from_chat_id=from_chat_id
        )

        # Validaciones
        assert success is True
        assert "exitosamente" in message.lower()
        assert request is not None
        assert request.user_id == user_id
        assert request.processed is False
        assert request.request_date is not None


# ===== TEST 2: Rechazar solicitud duplicada =====


@pytest.mark.asyncio
async def test_reject_duplicate_join_request(mock_bot, configured_free_channel):
    """
    Test: Rechazar solicitud duplicada.

    Verifica:
    - Primera solicitud se crea
    - Segunda solicitud se rechaza
    - Mensaje indica solicitud pendiente
    - Retorna solicitud existente
    """
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        user_id = 123456789
        from_chat_id = configured_free_channel

        # Primera solicitud (usando create_free_request directamente para evitar verificación de duplicados)
        req1 = await container.subscription.create_free_request(user_id)

        # Segunda solicitud (duplicada) usando create_free_request_from_join_request
        success2, msg2, req2 = await container.subscription.create_free_request_from_join_request(
            user_id=user_id,
            from_chat_id=from_chat_id
        )

        # Validaciones
        assert req1 is not None
        assert success2 is False
        assert "pendiente" in msg2.lower()
        assert req1.id == req2.id  # Misma solicitud


# ===== TEST 3: Enviar notificación con variables =====


@pytest.mark.asyncio
async def test_send_free_request_notification(mock_bot):
    """
    Test: Enviar notificación con variables reemplazadas.

    Verifica:
    - send_message llamado
    - Variables reemplazadas correctamente
    - Sin parse_mode (seguridad)
    """
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        user_id = 123456789
        user_name = "Juan"
        channel_name = "Canal Test"
        wait_time = 10

        # Enviar notificación
        sent = await container.subscription.send_free_request_notification(
            user_id=user_id,
            user_name=user_name,
            channel_name=channel_name,
            wait_time_minutes=wait_time
        )

        # Validaciones
        assert sent is True
        assert mock_bot.send_message.called

        # Verificar argumentos de send_message
        call_args = mock_bot.send_message.call_args
        assert call_args.kwargs["chat_id"] == user_id

        message_text = call_args.kwargs["text"]
        assert user_name in message_text
        assert channel_name in message_text
        assert str(wait_time) in message_text

        # Verificar sin parse_mode (seguridad)
        assert call_args.kwargs.get("parse_mode") is None


# ===== TEST 4: Aprobar solicitudes listas =====


@pytest.mark.asyncio
async def test_approve_ready_free_requests(mock_bot, configured_free_channel):
    """
    Test: Aprobar solicitudes que cumplieron tiempo de espera.

    Verifica:
    - Solicitud con tiempo cumplido se aprueba
    - approve_chat_join_request llamado
    - Solicitud marcada como processed=True
    """
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        user_id = 123456789

        # Crear solicitud antigua (hace 10 minutos)
        request = FreeChannelRequest(
            user_id=user_id,
            request_date=datetime.utcnow() - timedelta(minutes=10),
            processed=False
        )
        session.add(request)
        await session.commit()
        await session.refresh(request)

        # Aprobar solicitudes (wait_time = 5 min)
        success_count, error_count = await container.subscription.approve_ready_free_requests(
            wait_time_minutes=5,
            free_channel_id=configured_free_channel
        )

        # Validaciones
        assert success_count == 1
        assert error_count == 0
        assert mock_bot.approve_chat_join_request.called

        # Verificar que solicitud fue marcada como procesada
        await session.refresh(request)
        assert request.processed is True
        assert request.processed_at is not None


# ===== TEST 5: NO aprobar solicitudes recientes =====


@pytest.mark.asyncio
async def test_not_approve_recent_requests(mock_bot, configured_free_channel):
    """
    Test: NO aprobar solicitudes que no cumplieron tiempo de espera.

    Verifica:
    - Solicitud reciente NO se aprueba
    - approve_chat_join_request NO llamado
    - Solicitud sigue como processed=False
    """
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        user_id = 123456789

        # Crear solicitud reciente (hace 2 minutos)
        request = FreeChannelRequest(
            user_id=user_id,
            request_date=datetime.utcnow() - timedelta(minutes=2),
            processed=False
        )
        session.add(request)
        await session.commit()
        await session.refresh(request)

        # Intentar aprobar solicitudes (wait_time = 5 min)
        success_count, error_count = await container.subscription.approve_ready_free_requests(
            wait_time_minutes=5,
            free_channel_id=configured_free_channel
        )

        # Validaciones
        assert success_count == 0
        assert error_count == 0
        assert not mock_bot.approve_chat_join_request.called

        # Verificar que solicitud NO fue procesada
        await session.refresh(request)
        assert request.processed is False


# ===== TEST 6: Configurar mensaje personalizado =====


@pytest.mark.asyncio
async def test_custom_welcome_message_config(mock_bot):
    """
    Test: Configurar mensaje de bienvenida personalizado.

    Verifica:
    - set_free_welcome_message actualiza BD
    - get_free_welcome_message retorna mensaje correcto
    - Validación de longitud funciona
    """
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        custom_message = "Hola {user_name}, bienvenido a {channel_name}. Espera {wait_time} minutos."

        # Configurar mensaje
        await container.config.set_free_welcome_message(custom_message)

        # Obtener mensaje configurado
        retrieved_message = await container.config.get_free_welcome_message()

        # Validaciones
        assert retrieved_message == custom_message

        # Validar mensaje muy corto (debe fallar)
        with pytest.raises(ValueError, match="al menos 10"):
            await container.config.set_free_welcome_message("Corto")

        # Validar mensaje muy largo (debe fallar)
        long_message = "x" * 1001
        with pytest.raises(ValueError, match="1000"):
            await container.config.set_free_welcome_message(long_message)


# ===== TEST 7: Rechazar solicitudes de canal no autorizado =====


@pytest.mark.asyncio
async def test_reject_unauthorized_channel_join_request(mock_bot, configured_free_channel):
    """
    Test: Rechazar solicitudes desde canal no autorizado.

    Verifica:
    - Solicitud desde canal diferente se rechaza
    - Retorna success=False
    - Mensaje indica canal no autorizado
    - NO crea FreeChannelRequest en BD
    """
    async with get_session() as session:
        container = ServiceContainer(session, mock_bot)

        user_id = 123456789
        unauthorized_channel_id = "-1009999999999"  # Canal diferente

        # Intentar crear solicitud desde canal no autorizado
        success, message, request = await container.subscription.create_free_request_from_join_request(
            user_id=user_id,
            from_chat_id=unauthorized_channel_id
        )

        # Validaciones
        assert success is False
        assert "no autorizado" in message.lower()
        assert request is None
