"""
Media Set Service - Gestión de sets multimedia (CMS).

Maneja:
- Creación de sets multimedia
- Adición de items a sets
- Envío de sets a usuarios

NOTE: Implementación básica para SPRINT 1.
SPRINT 4 completará la funcionalidad completa.
"""
import logging
from typing import List, Tuple, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from aiogram import Bot

from bot.database.gamification_models import MediaSet, MediaSetItem
from bot.database.enums import MediaType

logger = logging.getLogger(__name__)


class MediaSetService:
    """
    Servicio para gestión de sets multimedia (CMS).

    Attributes:
        _session: Sesión de base de datos SQLAlchemy
        _bot: Instancia del bot de Telegram
    """

    def __init__(self, session: AsyncSession, bot: Bot):
        """
        Inicializa el MediaSetService.

        Args:
            session: Sesión de base de datos SQLAlchemy
            bot: Instancia del bot de Telegram
        """
        self._session = session
        self._bot = bot

    # ===== SETS =====

    async def get_all_sets(self, active_only: bool = True) -> List[MediaSet]:
        """
        Obtiene todos los sets multimedia.

        Args:
            active_only: Solo sets activos

        Returns:
            List[MediaSet]: Lista de sets
        """
        query = select(MediaSet)

        if active_only:
            query = query.where(MediaSet.active == True)

        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def get_set(self, set_id: int) -> Optional[MediaSet]:
        """
        Obtiene un set por ID con sus items.

        Args:
            set_id: ID del set

        Returns:
            MediaSet o None si no existe
        """
        result = await self._session.execute(
            select(MediaSet)
            .where(MediaSet.id == set_id)
            .options(selectinload(MediaSet.items))
        )
        return result.scalar_one_or_none()

    # ===== ENVÍO =====

    async def send_set_to_user(
        self,
        user_id: int,
        set_id: int
    ) -> Tuple[bool, str]:
        """
        Envía un set multimedia a un usuario.

        Args:
            user_id: ID del usuario
            set_id: ID del set a enviar

        Returns:
            Tuple[bool, str]: (éxito, mensaje)

        NOTE: Implementación completa en SPRINT 4
        """
        # TODO: Implementar:
        # - Obtener set con items
        # - Enviar cada item según tipo (photo, video, document, audio)
        # - Manejar errores de envío
        return False, "Implementación pendiente (SPRINT 4)"
