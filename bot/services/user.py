"""
User Service - Gestión de usuarios y roles.

Proporciona operaciones para:
- Crear/actualizar usuarios
- Obtener usuarios por ID
- Cambiar roles
- Verificar permisos
"""
import logging
from typing import Optional, List
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import User as TelegramUser

from bot.database.models import User
from bot.database.enums import UserRole

logger = logging.getLogger(__name__)


class UserService:
    """
    Servicio para gestionar usuarios del sistema.

    Attributes:
        session: Sesión de base de datos
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio de usuarios.

        Args:
            session: Sesión de SQLAlchemy
        """
        self.session = session

    async def get_or_create_user(
        self,
        telegram_user: TelegramUser,
        default_role: UserRole = UserRole.FREE
    ) -> User:
        """
        Obtiene un usuario existente o lo crea si no existe.

        Args:
            telegram_user: Objeto User de Telegram
            default_role: Rol por defecto si se crea (default: FREE)

        Returns:
            User del sistema

        Examples:
            >>> user = await service.get_or_create_user(message.from_user)
        """
        # Buscar usuario existente
        result = await self.session.execute(
            select(User).where(User.user_id == telegram_user.id)
        )
        user = result.scalar_one_or_none()

        if user:
            # Usuario existe - actualizar datos si cambiaron
            updated = False

            if user.username != telegram_user.username:
                user.username = telegram_user.username
                updated = True

            if user.first_name != telegram_user.first_name:
                user.first_name = telegram_user.first_name
                updated = True

            if user.last_name != telegram_user.last_name:
                user.last_name = telegram_user.last_name
                updated = True

            if updated:
                user.updated_at = datetime.utcnow()
                # No commit - dejar que el handler maneje la transacción
                logger.debug(f"👤 Usuario actualizado: {user.user_id}")

            return user

        # Usuario no existe - crear
        user = User(
            user_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            role=default_role,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        self.session.add(user)
        # No commit - dejar que el handler maneje la transacción

        logger.info(
            f"✅ Usuario creado: {user.user_id} (@{user.username}) - "
            f"Rol: {default_role.value}"
        )

        return user

    async def get_user(self, user_id: int) -> Optional[User]:
        """
        Obtiene un usuario por ID.

        Args:
            user_id: ID de Telegram del usuario

        Returns:
            User o None si no existe
        """
        result = await self.session.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def change_role(
        self,
        user_id: int,
        new_role: UserRole,
        reason: str = "Manual"
    ) -> Optional[User]:
        """
        Cambia el rol de un usuario.

        Args:
            user_id: ID del usuario
            new_role: Nuevo rol a asignar
            reason: Razón del cambio (para logging)

        Returns:
            User actualizado o None si no existe

        Examples:
            >>> await service.change_role(123456, UserRole.VIP, "Token activado")
        """
        user = await self.get_user(user_id)

        if not user:
            logger.warning(f"⚠️ Usuario no encontrado para cambio de rol: {user_id}")
            return None

        old_role = user.role
        user.role = new_role
        user.updated_at = datetime.utcnow()

        # No commit - dejar que el handler maneje la transacción

        logger.info(
            f"🔄 Rol cambiado: User {user_id} | "
            f"{old_role.value} → {new_role.value} | "
            f"Razón: {reason}"
        )

        return user

    async def promote_to_vip(self, user_id: int) -> Optional[User]:
        """
        Promociona un usuario a VIP.

        Args:
            user_id: ID del usuario

        Returns:
            User actualizado o None si no existe
        """
        return await self.change_role(user_id, UserRole.VIP, "Promoción a VIP")

    async def demote_to_free(self, user_id: int) -> Optional[User]:
        """
        Degrada un usuario a Free.

        Args:
            user_id: ID del usuario

        Returns:
            User actualizado o None si no existe
        """
        return await self.change_role(user_id, UserRole.FREE, "Degradación a Free")

    async def promote_to_admin(self, user_id: int) -> Optional[User]:
        """
        Promociona un usuario a Admin (uso manual).

        Args:
            user_id: ID del usuario

        Returns:
            User actualizado o None si no existe
        """
        return await self.change_role(user_id, UserRole.ADMIN, "Promoción a Admin")

    async def is_admin(self, user_id: int) -> bool:
        """
        Verifica si un usuario es admin.

        Args:
            user_id: ID del usuario

        Returns:
            True si es admin, False si no
        """
        user = await self.get_user(user_id)
        return user.is_admin if user else False

    async def get_users_by_role(self, role: UserRole) -> List[User]:
        """
        Obtiene todos los usuarios con un rol específico.

        Args:
            role: Rol a filtrar

        Returns:
            Lista de Users
        """
        result = await self.session.execute(
            select(User).where(User.role == role).order_by(User.created_at.desc())
        )
        return list(result.scalars().all())
