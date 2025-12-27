"""
Pytest configuration específico para tests de narrativa.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import get_session


@pytest.fixture
async def session():
    """
    Fixture: Sesión async de SQLAlchemy.

    Returns:
        AsyncSession para tests
    """
    async with get_session() as s:
        yield s
