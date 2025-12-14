"""
Tests del User Service - Sistema de roles/usuarios.

Valida:
- Creación de usuarios
- Obtención de usuarios
- Cambio de roles
- Verificación de roles
"""
import pytest
from unittest.mock import Mock

from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.engine import get_session_factory
from bot.database.models import User
from bot.database.enums import UserRole
from bot.services.user import UserService


@pytest.mark.asyncio
async def test_get_or_create_user_new():
    """Test: Crear nuevo usuario con rol FREE."""
    async with get_session_factory()() as session:
        service = UserService(session)

        # Mock de Telegram User
        telegram_user = Mock()
        telegram_user.id = 123456789
        telegram_user.username = "testuser"
        telegram_user.first_name = "Test"
        telegram_user.last_name = "User"

        # Crear usuario
        user = await service.get_or_create_user(
            telegram_user=telegram_user,
            default_role=UserRole.FREE
        )

        # Validaciones
        assert user.user_id == 123456789
        assert user.username == "testuser"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.role == UserRole.FREE


@pytest.mark.asyncio
async def test_get_or_create_user_existing():
    """Test: Obtener usuario existente sin crear duplicado."""
    async with get_session_factory()() as session:
        service = UserService(session)

        # Mock de Telegram User
        telegram_user = Mock()
        telegram_user.id = 111111111
        telegram_user.username = "existing"
        telegram_user.first_name = "Existing"
        telegram_user.last_name = "User"

        # Crear usuario primera vez
        user1 = await service.get_or_create_user(
            telegram_user=telegram_user,
            default_role=UserRole.FREE
        )

        # Obtener usuario segunda vez
        user2 = await service.get_or_create_user(
            telegram_user=telegram_user,
            default_role=UserRole.FREE
        )

        # Validaciones - deben ser el mismo usuario
        assert user1.user_id == user2.user_id
        assert user1.role == user2.role


@pytest.mark.asyncio
async def test_get_user():
    """Test: Obtener usuario por ID."""
    async with get_session_factory()() as session:
        service = UserService(session)

        # Crear usuario
        telegram_user = Mock()
        telegram_user.id = 222222222
        telegram_user.username = "gettest"
        telegram_user.first_name = "Get"
        telegram_user.last_name = "Test"

        created = await service.get_or_create_user(telegram_user)

        # Obtener usuario
        retrieved = await service.get_user(222222222)

        # Validaciones
        assert retrieved is not None
        assert retrieved.user_id == created.user_id
        assert retrieved.username == "gettest"


@pytest.mark.asyncio
async def test_get_user_not_found():
    """Test: Obtener usuario no existente retorna None."""
    async with get_session_factory()() as session:
        service = UserService(session)

        # Intentar obtener usuario inexistente
        user = await service.get_user(999999999)

        # Validación
        assert user is None


@pytest.mark.asyncio
async def test_change_role():
    """Test: Cambiar rol de usuario."""
    async with get_session_factory()() as session:
        service = UserService(session)

        # Crear usuario con rol FREE
        telegram_user = Mock()
        telegram_user.id = 333333333
        telegram_user.username = "roletest"
        telegram_user.first_name = "Role"
        telegram_user.last_name = "Test"

        user = await service.get_or_create_user(telegram_user)
        assert user.role == UserRole.FREE

        # Cambiar a VIP
        updated = await service.change_role(333333333, UserRole.VIP, "Token activado")

        # Validaciones
        assert updated is not None
        assert updated.role == UserRole.VIP


@pytest.mark.asyncio
async def test_promote_to_vip():
    """Test: Promocionar a VIP."""
    async with get_session_factory()() as session:
        service = UserService(session)

        # Crear usuario
        telegram_user = Mock()
        telegram_user.id = 444444444
        telegram_user.username = "viptest"
        telegram_user.first_name = "VIP"
        telegram_user.last_name = "Test"

        user = await service.get_or_create_user(telegram_user)
        assert user.is_free

        # Promocionar a VIP
        updated = await service.promote_to_vip(444444444)

        # Validaciones
        assert updated is not None
        assert updated.is_vip
        assert not updated.is_free


@pytest.mark.asyncio
async def test_demote_to_free():
    """Test: Degradar a Free."""
    async with get_session_factory()() as session:
        service = UserService(session)

        # Crear usuario y promocionar a VIP
        telegram_user = Mock()
        telegram_user.id = 555555555
        telegram_user.username = "demotetest"
        telegram_user.first_name = "Demote"
        telegram_user.last_name = "Test"

        user = await service.get_or_create_user(telegram_user)
        await service.promote_to_vip(555555555)

        # Degradar a Free
        updated = await service.demote_to_free(555555555)

        # Validaciones
        assert updated is not None
        assert updated.is_free
        assert not updated.is_vip


@pytest.mark.asyncio
async def test_promote_to_admin():
    """Test: Promocionar a Admin."""
    async with get_session_factory()() as session:
        service = UserService(session)

        # Crear usuario
        telegram_user = Mock()
        telegram_user.id = 666666666
        telegram_user.username = "admintest"
        telegram_user.first_name = "Admin"
        telegram_user.last_name = "Test"

        user = await service.get_or_create_user(telegram_user)
        assert user.is_free

        # Promocionar a Admin
        updated = await service.promote_to_admin(666666666)

        # Validaciones
        assert updated is not None
        assert updated.is_admin


@pytest.mark.asyncio
async def test_is_admin():
    """Test: Verificar si es admin."""
    async with get_session_factory()() as session:
        service = UserService(session)

        # Crear usuario Free
        telegram_user1 = Mock()
        telegram_user1.id = 777777777
        telegram_user1.username = "freeuser"
        telegram_user1.first_name = "Free"
        telegram_user1.last_name = "User"

        user1 = await service.get_or_create_user(telegram_user1)

        # Crear usuario Admin
        telegram_user2 = Mock()
        telegram_user2.id = 888888888
        telegram_user2.username = "adminuser"
        telegram_user2.first_name = "Admin"
        telegram_user2.last_name = "User"

        user2 = await service.get_or_create_user(
            telegram_user2,
            default_role=UserRole.ADMIN
        )

        # Validaciones
        assert not await service.is_admin(777777777)
        assert await service.is_admin(888888888)


@pytest.mark.asyncio
async def test_get_users_by_role():
    """Test: Obtener usuarios por rol."""
    async with get_session_factory()() as session:
        service = UserService(session)

        # Crear múltiples usuarios con diferentes roles
        users_data = [
            (111, "user1", UserRole.FREE),
            (112, "user2", UserRole.FREE),
            (113, "user3", UserRole.VIP),
            (114, "user4", UserRole.ADMIN),
        ]

        for user_id, username, role in users_data:
            telegram_user = Mock()
            telegram_user.id = user_id
            telegram_user.username = username
            telegram_user.first_name = "User"
            telegram_user.last_name = str(user_id)

            await service.get_or_create_user(telegram_user, role)

        # Obtener usuarios por rol
        free_users = await service.get_users_by_role(UserRole.FREE)
        vip_users = await service.get_users_by_role(UserRole.VIP)
        admin_users = await service.get_users_by_role(UserRole.ADMIN)

        # Validaciones
        assert len(free_users) >= 2
        assert len(vip_users) >= 1
        assert len(admin_users) >= 1
