"""
Reaction Service - Gestión de reacciones personalizadas en publicaciones.

Maneja:
- Publicaciones con botones de reacción
- Reacciones de usuarios
- Conteos de reacciones
- Generación de keyboards inline
- Emojis predeterminados globales
"""
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple

from sqlalchemy import select, desc, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.database.gamification_models import (
    Publication, UserReaction, GamificationConfig
)
from bot.database.enums import ChannelType
from bot.database.models import User

logger = logging.getLogger(__name__)


class ReactionService:
    """
    Servicio para gestión de reacciones personalizadas.

    Responsabilidades:
    - Crear publicaciones con botones de reacción
    - Procesar reacciones de usuarios
    - Contar reacciones por emoji
    - Generar keyboards inline
    - Configurar emojis predeterminados globales

    Attributes:
        _session: Sesión de base de datos SQLAlchemy
        _bot: Instancia del bot de Telegram
    """

    def __init__(self, session: AsyncSession, bot: Bot):
        """
        Inicializa el ReactionService.

        Args:
            session: Sesión de base de datos SQLAlchemy
            bot: Instancia del bot de Telegram
        """
        self._session = session
        self._bot = bot

    # ===== CONFIGURACIÓN =====

    async def _get_config(self) -> GamificationConfig:
        """
        Obtiene la configuración de gamificación.

        Returns:
            GamificationConfig: Configuración global (singleton id=1)
        """
        result = await self._session.execute(
            select(GamificationConfig).where(GamificationConfig.id == 1)
        )
        config = result.scalar_one_or_none()

        if config is None:
            # Crear configuración por defecto si no existe
            config = GamificationConfig(
                points_per_reaction=1,
                daily_gift_points=5,
                streak_multiplier=1.5,
                default_reaction_emojis=["👍", "❤️", "🔥", "🎉", "💯"]
            )
            self._session.add(config)
            await self._session.commit()

        return config

    async def get_default_emojis(self) -> List[str]:
        """
        Obtiene los emojis predeterminados para reacciones.

        Returns:
            List[str]: Lista de emojis
        """
        config = await self._get_config()
        return config.default_reaction_emojis if config.default_reaction_emojis else []

    async def set_default_emojis(self, emojis: List[str]) -> None:
        """
        Establece los emojis predeterminados globales.

        Args:
            emojis: Lista de emojis (mínimo 1, máximo 10)

        Raises:
            ValueError: Si la lista está vacía o tiene más de 10 emojis
        """
        if not emojis:
            raise ValueError("Debe haber al menos 1 emoji")
        if len(emojis) > 10:
            raise ValueError("Máximo 10 emojis permitidos")

        config = await self._get_config()
        config.default_reaction_emojis = emojis
        config.updated_at = datetime.utcnow()
        await self._session.commit()

        logger.info(f"🎨 Emojis predeterminados actualizados: {emojis}")

    # ===== PUBLICACIONES =====

    async def create_publication(
        self,
        channel_id: str,
        message_id: int,
        channel_type: ChannelType,
        emojis: Optional[List[str]] = None
    ) -> Publication:
        """
        Crea una nueva publicación con botones de reacción.

        Args:
            channel_id: ID del canal de Telegram
            message_id: ID del mensaje en Telegram
            channel_type: Tipo de canal (VIP/FREE)
            emojis: Lista de emojis (si es None, usa predeterminados)

        Returns:
            Publication: Publicación creada
        """
        # Usar emojis predeterminados si no se especifican
        if emojis is None:
            emojis = await self.get_default_emojis()

        if not emojis:
            raise ValueError("No hay emojis configurados")

        # Crear publicación
        publication = Publication(
            channel_id=channel_id,
            message_id=message_id,
            channel_type=channel_type,
            reaction_buttons=emojis,
            active=True
        )

        self._session.add(publication)
        await self._session.commit()
        await self._session.refresh(publication)

        logger.info(
            f"📝 Publicación creada: channel={channel_type.value}, "
            f"message_id={message_id}, emojis={emojis}"
        )

        return publication

    async def get_publication(
        self,
        channel_id: str,
        message_id: int
    ) -> Optional[Publication]:
        """
        Obtiene una publicación por canal y mensaje.

        Args:
            channel_id: ID del canal
            message_id: ID del mensaje

        Returns:
            Publication o None si no existe
        """
        result = await self._session.execute(
            select(Publication)
            .where(
                and_(
                    Publication.channel_id == channel_id,
                    Publication.message_id == message_id
                )
            )
            .options(selectinload(Publication.reactions))
        )
        return result.scalar_one_or_none()

    async def get_publication_by_id(self, publication_id: int) -> Optional[Publication]:
        """
        Obtiene una publicación por ID.

        Args:
            publication_id: ID de la publicación

        Returns:
            Publication o None si no existe
        """
        result = await self._session.execute(
            select(Publication)
            .where(Publication.id == publication_id)
            .options(selectinload(Publication.reactions))
        )
        return result.scalar_one_or_none()

    async def get_recent_publications(
        self,
        channel_id: Optional[str] = None,
        channel_type: Optional[ChannelType] = None,
        limit: int = 10
    ) -> List[Publication]:
        """
        Obtiene las publicaciones más recientes.

        Args:
            channel_id: Filtrar por canal (opcional)
            channel_type: Filtrar por tipo de canal (opcional)
            limit: Máximo de resultados

        Returns:
            List[Publication]: Lista de publicaciones
        """
        query = select(Publication).where(Publication.active == True)

        if channel_id:
            query = query.where(Publication.channel_id == channel_id)
        if channel_type:
            query = query.where(Publication.channel_type == channel_type)

        query = query.order_by(desc(Publication.created_at)).limit(limit)

        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def deactivate_publication(self, publication_id: int) -> bool:
        """
        Desactiva una publicación (no acepta más reacciones).

        Args:
            publication_id: ID de la publicación

        Returns:
            bool: True si se desactivó correctamente
        """
        publication = await self.get_publication_by_id(publication_id)
        if publication:
            publication.active = False
            await self._session.commit()
            logger.info(f"🔒 Publicación {publication_id} desactivada")
            return True
        return False

    # ===== REACCIONES =====

    async def add_reaction(
        self,
        user_id: int,
        publication_id: int,
        emoji: str,
        points_awarded: int
    ) -> Tuple[bool, str, Optional[UserReaction]]:
        """
        Añade una reacción de usuario a una publicación.

        Args:
            user_id: ID del usuario
            publication_id: ID de la publicación
            emoji: Emoji de la reacción
            points_awarded: Puntos otorgados por esta reacción

        Returns:
            Tuple[bool, str, UserReaction]: (éxito, mensaje, reacción_creada)
        """
        # Verificar si ya reaccionó
        existing = await self.get_user_reaction(user_id, publication_id)

        if existing:
            return False, "Ya has reaccionado a esta publicación", existing

        # Verificar que la publicación existe y está activa
        publication = await self.get_publication_by_id(publication_id)
        if publication is None:
            return False, "Publicación no encontrada", None

        if not publication.active:
            return False, "Esta publicación ya no acepta reacciones", None

        # Verificar que el emoji esté permitido
        if emoji not in publication.reaction_buttons:
            return False, f"Emoji '{emoji}' no permitido", None

        # Asegurar que el usuario tenga UserPoints (crear si no existe)
        from bot.services.points import PointsService
        points_service = PointsService(self._session, self._bot)
        await points_service.get_or_create_points(user_id)

        # Crear reacción PRIMERO (para que calculate_streak la encuentre)
        reaction = UserReaction(
            user_id=user_id,
            publication_id=publication_id,
            emoji=emoji,
            points_awarded=points_awarded
        )

        self._session.add(reaction)
        await self._session.commit()
        await self._session.refresh(reaction)

        # Otorgar puntos al usuario
        await points_service.award_points(
            user_id=user_id,
            amount=points_awarded,
            transaction_type="reaction",
            description=f"Reacción {emoji} en publicación {publication_id}",
            reference_id=publication_id
        )

        # Actualizar racha del usuario (ahora la reacción ya existe en BD)
        from bot.services.streak import StreakService
        streak_service = StreakService(self._session, self._bot)
        new_streak, is_record = await streak_service.update_streak_after_reaction(
            user_id=user_id,
            channel_id=publication.channel_id
        )

        logger.info(
            f"👍 User {user_id} reaccionó en publicación {publication_id} "
            f"con {emoji} (+{points_awarded} pts, 🔥 racha: {new_streak})"
        )

        return True, "Reacción registrada", reaction

    async def get_user_reaction(
        self,
        user_id: int,
        publication_id: int
    ) -> Optional[UserReaction]:
        """
        Obtiene la reacción de un usuario en una publicación.

        Args:
            user_id: ID del usuario
            publication_id: ID de la publicación

        Returns:
            UserReaction o None si no ha reaccionado
        """
        result = await self._session.execute(
            select(UserReaction)
            .where(
                and_(
                    UserReaction.user_id == user_id,
                    UserReaction.publication_id == publication_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def has_reacted(self, user_id: int, publication_id: int) -> bool:
        """
        Verifica si un usuario ya reaccionó a una publicación.

        Args:
            user_id: ID del usuario
            publication_id: ID de la publicación

        Returns:
            bool: True si ya reaccionó
        """
        reaction = await self.get_user_reaction(user_id, publication_id)
        return reaction is not None

    # ===== CONTEOS =====

    async def get_reaction_counts(self, publication_id: int) -> Dict[str, int]:
        """
        Obtiene el conteo de reacciones por emoji en una publicación.

        Args:
            publication_id: ID de la publicación

        Returns:
            Dict[str, int]: Diccionario {emoji: cantidad}
        """
        result = await self._session.execute(
            select(
                UserReaction.emoji,
                func.count(UserReaction.id).label('count')
            )
            .where(UserReaction.publication_id == publication_id)
            .group_by(UserReaction.emoji)
        )

        return {row.emoji: row.count for row in result.all()}

    async def get_total_reactions(self, publication_id: int) -> int:
        """
        Obtiene el total de reacciones en una publicación.

        Args:
            publication_id: ID de la publicación

        Returns:
            int: Total de reacciones
        """
        result = await self._session.execute(
            select(func.count(UserReaction.id))
            .where(UserReaction.publication_id == publication_id)
        )
        count = result.scalar()
        return count if count is not None else 0

    async def get_user_reaction_count(self, user_id: int) -> int:
        """
        Obtiene el total de reacciones de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            int: Total de reacciones realizadas
        """
        result = await self._session.execute(
            select(func.count(UserReaction.id))
            .where(UserReaction.user_id == user_id)
        )
        count = result.scalar()
        return count if count is not None else 0

    async def get_publication_reactions(
        self,
        publication_id: int,
        limit: int = 50
    ) -> List[UserReaction]:
        """
        Obtiene las reacciones de una publicación.

        Args:
            publication_id: ID de la publicación
            limit: Máximo de resultados

        Returns:
            List[UserReaction]: Lista de reacciones
        """
        result = await self._session.execute(
            select(UserReaction)
            .where(UserReaction.publication_id == publication_id)
            .order_by(desc(UserReaction.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    # ===== KEYBOARD GENERATION =====

    def generate_reaction_keyboard(
        self,
        publication_id: int,
        emojis: List[str],
        counts: Dict[str, int]
    ) -> InlineKeyboardMarkup:
        """
        Genera un keyboard inline con botones de reacción.

        Args:
            publication_id: ID de la publicación
            emojis: Lista de emojis disponibles
            counts: Diccionario de conteos por emoji

        Returns:
            InlineKeyboardMarkup: Keyboard con botones de reacción

        Formato callback: react:{publication_id}:{emoji_index}
        """
        builder = InlineKeyboardBuilder()

        # Crear botones en una fila
        buttons = []
        for index, emoji in enumerate(emojis):
            count = counts.get(emoji, 0)
            callback_data = f"react:{publication_id}:{index}"

            # Formato: "👍 5"
            label = f"{emoji} {count}" if count > 0 else emoji

            buttons.append(
                InlineKeyboardButton(
                    text=label,
                    callback_data=callback_data
                )
            )

        builder.row(*buttons)

        return builder.as_markup()

    def get_emoji_from_callback(self, emojis: List[str], callback_data: str) -> str:
        """
        Extrae el emoji del callback_data.

        Args:
            emojis: Lista de emojis disponibles
            callback_data: Callback data del botón

        Returns:
            str: Emoji correspondiente

        Raises:
            ValueError: Si el callback_data no tiene el formato correcto
        """
        try:
            parts = callback_data.split(":")
            if len(parts) != 3 or parts[0] != "react":
                raise ValueError("Formato inválido")

            emoji_index = int(parts[2])
            return emojis[emoji_index]

        except (ValueError, IndexError):
            raise ValueError("Callback data inválido")

    # ===== ESTADÍSTICAS =====

    async def get_most_reacted_publications(self, limit: int = 10) -> List[Publication]:
        """
        Obtiene las publicaciones con más reacciones.

        Args:
            limit: Máximo de resultados

        Returns:
            List[Publication]: Lista ordenada por cantidad de reacciones
        """
        # Subquery para contar reacciones
        reaction_count = (
            select(
                UserReaction.publication_id,
                func.count(UserReaction.id).label('count')
            )
            .group_by(UserReaction.publication_id)
            .subquery()
        )

        # Query principal
        result = await self._session.execute(
            select(Publication)
            .join(reaction_count, Publication.id == reaction_count.c.publication_id)
            .where(Publication.active == True)
            .order_by(desc(reaction_count.c.count))
            .limit(limit)
        )

        return list(result.scalars().all())

    async def get_user_reactions_in_channel(
        self,
        user_id: int,
        channel_id: str
    ) -> List[UserReaction]:
        """
        Obtiene todas las reacciones de un usuario en un canal.

        Args:
            user_id: ID del usuario
            channel_id: ID del canal

        Returns:
            List[UserReaction]: Lista de reacciones
        """
        result = await self._session.execute(
            select(UserReaction)
            .join(Publication, UserReaction.publication_id == Publication.id)
            .where(
                and_(
                    UserReaction.user_id == user_id,
                    Publication.channel_id == channel_id
                )
            )
            .order_by(desc(UserReaction.created_at))
        )
        return list(result.scalars().all())
