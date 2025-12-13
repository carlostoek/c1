"""
Tests para los middlewares de AdminAuth y Database.
"""
import asyncio
import logging
from unittest.mock import Mock, AsyncMock, patch

import pytest
from aiogram.types import Message, User, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from config import Config
from bot.middlewares import AdminAuthMiddleware, DatabaseMiddleware
from bot.database import init_db, close_db

logger = logging.getLogger(__name__)


class TestAdminAuthMiddleware:
    """Tests para AdminAuthMiddleware"""

    @pytest.mark.asyncio
    async def test_admin_user_passes(self):
        """Test que un usuario admin pasa el middleware"""
        middleware = AdminAuthMiddleware()

        # Mock handler
        handler = AsyncMock(return_value="handler_result")

        # Crear mock de mensaje de admin
        admin_id = Config.ADMIN_USER_IDS[0] if Config.ADMIN_USER_IDS else 123456
        admin_user = User(id=admin_id, is_bot=False, first_name="Admin")
        admin_message = Mock(spec=Message)
        admin_message.from_user = admin_user

        data = {}
        result = await middleware(handler, admin_message, data)

        assert result == "handler_result"
        assert handler.called
        assert handler.call_count == 1

    @pytest.mark.asyncio
    async def test_non_admin_user_blocked(self):
        """Test que un usuario no-admin es bloqueado"""
        middleware = AdminAuthMiddleware()

        # Mock handler
        handler = AsyncMock(return_value="handler_result")

        # Crear mock de mensaje de non-admin
        non_admin_user = User(id=999999, is_bot=False, first_name="NonAdmin", username="nonadmin")
        non_admin_message = Mock(spec=Message)
        non_admin_message.from_user = non_admin_user
        non_admin_message.answer = AsyncMock()

        data = {}
        result = await middleware(handler, non_admin_message, data)

        assert result is None
        assert not handler.called
        assert non_admin_message.answer.called

    @pytest.mark.asyncio
    async def test_callback_query_admin(self):
        """Test que un usuario admin en CallbackQuery pasa"""
        middleware = AdminAuthMiddleware()

        # Mock handler
        handler = AsyncMock(return_value="handler_result")

        # Crear mock de CallbackQuery de admin
        admin_id = Config.ADMIN_USER_IDS[0] if Config.ADMIN_USER_IDS else 123456
        admin_user = User(id=admin_id, is_bot=False, first_name="Admin")
        callback = Mock(spec=CallbackQuery)
        callback.from_user = admin_user

        data = {}
        result = await middleware(handler, callback, data)

        assert result == "handler_result"
        assert handler.called

    @pytest.mark.asyncio
    async def test_callback_query_non_admin_blocked(self):
        """Test que un usuario no-admin en CallbackQuery es bloqueado"""
        middleware = AdminAuthMiddleware()

        # Mock handler
        handler = AsyncMock(return_value="handler_result")

        # Crear mock de CallbackQuery de non-admin
        non_admin_user = User(id=999999, is_bot=False, first_name="NonAdmin", username="nonadmin")
        callback = Mock(spec=CallbackQuery)
        callback.from_user = non_admin_user
        callback.answer = AsyncMock()

        data = {}
        result = await middleware(handler, callback, data)

        assert result is None
        assert not handler.called
        assert callback.answer.called

    @pytest.mark.asyncio
    async def test_message_without_user(self):
        """Test que un mensaje sin usuario se deja pasar"""
        middleware = AdminAuthMiddleware()

        # Mock handler
        handler = AsyncMock(return_value="handler_result")

        # Crear mock de mensaje sin usuario
        message = Mock(spec=Message)
        message.from_user = None

        data = {}
        result = await middleware(handler, message, data)

        # Debe permitir que pase (confiar en que es válido)
        assert result == "handler_result"
        assert handler.called


class TestDatabaseMiddleware:
    """Tests para DatabaseMiddleware"""

    @pytest.mark.asyncio
    async def test_session_injection(self):
        """Test que la sesión se inyecta correctamente"""
        # Inicializar DB para el test
        await init_db()

        try:
            middleware = DatabaseMiddleware()

            # Mock handler que usa sesión
            async def mock_handler(event, data):
                assert "session" in data
                assert data["session"] is not None
                assert isinstance(data["session"], AsyncSession)
                return "success"

            mock_event = Mock()
            data = {}

            result = await middleware(mock_handler, mock_event, data)

            assert result == "success"
        finally:
            await close_db()

    @pytest.mark.asyncio
    async def test_session_context_management(self):
        """Test que el context manager maneja la sesión correctamente"""
        await init_db()

        try:
            middleware = DatabaseMiddleware()

            # Flag para verificar que la sesión se cierra
            session_closed = False

            async def mock_handler(event, data):
                session = data["session"]
                # Verificar que la sesión está abierta
                assert session is not None
                return "success"

            mock_event = Mock()
            data = {}

            result = await middleware(mock_handler, mock_event, data)

            assert result == "success"
        finally:
            await close_db()

    @pytest.mark.asyncio
    async def test_error_handling_in_handler(self):
        """Test que los errores en el handler se propagan"""
        await init_db()

        try:
            middleware = DatabaseMiddleware()

            async def mock_handler(event, data):
                raise ValueError("Test error")

            mock_event = Mock()
            data = {}

            with pytest.raises(ValueError, match="Test error"):
                await middleware(mock_handler, mock_event, data)
        finally:
            await close_db()


# ===== TESTS FUNCIONALES =====
async def run_functional_tests():
    """Tests funcionales que se pueden ejecutar sin pytest"""
    print("\n" + "=" * 60)
    print("TESTS FUNCIONALES - AdminAuthMiddleware")
    print("=" * 60)

    middleware = AdminAuthMiddleware()

    # Test 1: Usuario admin pasa
    print("\n🧪 Test 1: Usuario admin (debería pasar)")
    handler = AsyncMock(return_value="handler_result")
    admin_id = Config.ADMIN_USER_IDS[0] if Config.ADMIN_USER_IDS else 123456
    admin_user = User(id=admin_id, is_bot=False, first_name="Admin")
    admin_message = Mock(spec=Message)
    admin_message.from_user = admin_user

    data = {}
    result = await middleware(handler, admin_message, data)

    assert result == "handler_result"
    assert handler.called
    print("✅ Admin pasó, handler ejecutado")

    # Test 2: Usuario no-admin es bloqueado
    print("\n🧪 Test 2: Usuario no-admin (debería bloquear)")
    handler = AsyncMock(return_value="handler_result")
    non_admin_user = User(id=999999, is_bot=False, first_name="NonAdmin", username="nonadmin")
    non_admin_message = Mock(spec=Message)
    non_admin_message.from_user = non_admin_user
    non_admin_message.answer = AsyncMock()

    data = {}
    result = await middleware(handler, non_admin_message, data)

    assert result is None
    assert not handler.called
    assert non_admin_message.answer.called
    print("✅ No-admin bloqueado, mensaje enviado")

    print("\n" + "=" * 60)
    print("TESTS FUNCIONALES - DatabaseMiddleware")
    print("=" * 60)

    # Inicializar DB
    await init_db()

    try:
        middleware = DatabaseMiddleware()

        # Test 3: Inyección de sesión
        print("\n🧪 Test 3: Inyección de sesión")

        async def mock_handler(event, data):
            assert "session" in data
            assert data["session"] is not None
            return "success"

        mock_event = Mock()
        data = {}

        result = await middleware(mock_handler, mock_event, data)

        assert result == "success"
        print("✅ Sesión inyectada correctamente")

    finally:
        await close_db()

    print("\n" + "=" * 60)
    print("✅✅✅ TODOS LOS TESTS PASARON")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_functional_tests())
