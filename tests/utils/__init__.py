"""
Utilidades compartidas para tests.

Proporciona helpers y mocks reutilizables across test suites.
"""

from unittest.mock import Mock, AsyncMock
from typing import Dict, Any, Optional

from bot.database.models import User
from sqlalchemy.ext.asyncio import AsyncSession


class MockedBot(Mock):
    """Mock del bot de Telegram para tests.

    Proporciona mocks de métodos comunes de la API de Telegram.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = 123456789
        self.username = "test_bot"

        # Mock de métodos comunes
        self.get_chat = AsyncMock()
        self.get_chat_member = AsyncMock()
        self.create_chat_invite_link = AsyncMock()
        self.ban_chat_member = AsyncMock()
        self.unban_chat_member = AsyncMock()
        self.send_message = AsyncMock()
        self.edit_message_text = AsyncMock()
        self.edit_message_reply_markup = AsyncMock()
        self.answer_callback_query = AsyncMock()
        self.approve_chat_join_request = AsyncMock()
        self.decline_chat_join_request = AsyncMock()


async def create_user_from_dict(
    session: AsyncSession,
    user_data: Dict[str, Any]
) -> User:
    """Crea un usuario en BD desde un diccionario.

    Args:
        session: Sesión de BD
        user_data: Dict con campos de usuario (user_id, username, etc.)

    Returns:
        User creado
    """
    user = User(
        user_id=user_data.get("user_id", 123456789),
        username=user_data.get("username"),
        first_name=user_data.get("first_name", "Test"),
        last_name=user_data.get("last_name"),
        role=user_data.get("role", "free"),
        archetype=user_data.get("archetype"),
        archetype_confidence=user_data.get("archetype_confidence", 0.0),
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


async def patch_and_get_user(
    session: AsyncSession,
    user_id: int,
    updates: Optional[Dict[str, Any]] = None
) -> User:
    """Obtiene o crea un usuario, aplicando updates si se proporcionan.

    Args:
        session: Sesión de BD
        user_id: ID del usuario
        updates: Dict con campos a actualizar

    Returns:
        User obtenido o creado
    """
    from sqlalchemy import select

    stmt = select(User).where(User.user_id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            user_id=user_id,
            username=f"user_{user_id}",
            first_name="Test",
            role="free"
        )
        session.add(user)
    elif updates:
        for key, value in updates.items():
            if hasattr(user, key):
                setattr(user, key, value)

    await session.commit()
    await session.refresh(user)

    return user
