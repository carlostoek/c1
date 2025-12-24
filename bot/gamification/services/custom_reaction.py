"""Servicio de gestión de reacciones personalizadas en broadcasting.

Responsabilidades:
- Registrar reacciones de usuarios en mensajes de broadcasting
- Validar y prevenir reacciones duplicadas
- Otorgar besitos por reaccionar
- Actualizar estadísticas de mensajes
- Obtener reacciones de usuarios
"""

from typing import Optional, Dict, List
from datetime import datetime, UTC
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
import logging

from bot.gamification.database.models import CustomReaction, Reaction
from bot.database.models import BroadcastMessage
from bot.gamification.database.enums import TransactionType

logger = logging.getLogger(__name__)


class CustomReactionService:
    """Servicio de gestión de reacciones personalizadas."""

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio.

        Args:
            session: Sesión async de SQLAlchemy
        """
        self.session = session

    async def register_custom_reaction(
        self,
        broadcast_message_id: int,
        user_id: int,
        reaction_type_id: int,
        emoji: str
    ) -> Dict:
        """Registra reacción cuando usuario presiona botón.

        Args:
            broadcast_message_id: ID del mensaje de broadcasting
            user_id: ID del usuario que reacciona
            reaction_type_id: ID del tipo de reacción
            emoji: Emoji de la reacción

        Returns:
            {
                "success": True,
                "besitos_earned": 10,
                "total_besitos": 1245,
                "already_reacted": False,
                "multiplier_applied": 1.0
            }
        """
        # 1. Verificar si ya reaccionó con este emoji
        stmt = select(CustomReaction).where(
            CustomReaction.broadcast_message_id == broadcast_message_id,
            CustomReaction.user_id == user_id,
            CustomReaction.reaction_type_id == reaction_type_id
        )
        result = await self.session.execute(stmt)
        existing_reaction = result.scalar_one_or_none()

        if existing_reaction:
            logger.warning(
                f"User {user_id} already reacted with {emoji} "
                f"on message {broadcast_message_id}"
            )
            return {
                "success": False,
                "already_reacted": True,
                "besitos_earned": 0,
                "total_besitos": 0,
                "multiplier_applied": 1.0
            }

        # 2. Obtener ReactionType para saber besitos
        stmt = select(Reaction).where(Reaction.id == reaction_type_id)
        result = await self.session.execute(stmt)
        reaction_type = result.scalar_one_or_none()

        if not reaction_type or not reaction_type.active:
            logger.error(
                f"Reaction type {reaction_type_id} not found or inactive"
            )
            return {
                "success": False,
                "already_reacted": False,
                "besitos_earned": 0,
                "total_besitos": 0,
                "multiplier_applied": 1.0,
                "error": "Reaction type not found or inactive"
            }

        # 3. Calcular besitos (con multiplicador si aplica - futuro)
        besitos_value = reaction_type.besitos_value
        multiplier = 1.0  # Por ahora sin multiplicadores
        besitos_to_grant = int(besitos_value * multiplier)

        # 4. Crear CustomReaction
        try:
            custom_reaction = CustomReaction(
                broadcast_message_id=broadcast_message_id,
                user_id=user_id,
                reaction_type_id=reaction_type_id,
                emoji=emoji,
                besitos_earned=besitos_to_grant
            )
            self.session.add(custom_reaction)
            await self.session.flush()  # Para obtener el ID

            logger.info(
                f"User {user_id} reacted with {emoji} "
                f"on message {broadcast_message_id}, earning {besitos_to_grant} besitos"
            )

        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Failed to create CustomReaction: {e}")
            return {
                "success": False,
                "already_reacted": True,
                "besitos_earned": 0,
                "total_besitos": 0,
                "multiplier_applied": multiplier
            }

        # 5. Otorgar besitos via BesitoService
        from bot.gamification.services.besito import BesitoService
        besito_service = BesitoService(self.session)

        await besito_service.grant_besitos(
            user_id=user_id,
            amount=besitos_to_grant,
            transaction_type=TransactionType.REACTION_CUSTOM,
            description=f"Reacción {emoji} en broadcast {broadcast_message_id}",
            reference_id=custom_reaction.id
        )

        # Obtener total de besitos después de otorgar
        total_besitos = await besito_service.get_balance(user_id)

        # 6. Actualizar stats del mensaje
        await self._update_message_stats(broadcast_message_id)

        # 7. Commit de todos los cambios
        await self.session.commit()

        # 8. Retornar resultado
        return {
            "success": True,
            "already_reacted": False,
            "besitos_earned": besitos_to_grant,
            "total_besitos": total_besitos,
            "multiplier_applied": multiplier
        }

    async def get_user_reactions_for_message(
        self,
        broadcast_message_id: int,
        user_id: int
    ) -> List[int]:
        """Retorna IDs de reaction_types que el usuario ya usó.

        Para marcar botones como "ya reaccionado".

        Args:
            broadcast_message_id: ID del mensaje de broadcasting
            user_id: ID del usuario

        Returns:
            Lista de reaction_type_ids que el usuario ya usó
        """
        stmt = select(CustomReaction.reaction_type_id).where(
            CustomReaction.broadcast_message_id == broadcast_message_id,
            CustomReaction.user_id == user_id
        )
        result = await self.session.execute(stmt)
        reaction_ids = [row[0] for row in result.all()]

        logger.debug(
            f"User {user_id} has {len(reaction_ids)} reactions "
            f"on message {broadcast_message_id}"
        )

        return reaction_ids

    async def get_message_reaction_stats(
        self,
        broadcast_message_id: int
    ) -> Dict[str, int]:
        """Stats de reacciones de un mensaje.

        Returns:
            {
                "👍": 45,
                "❤️": 32,
                "🔥": 28
            }
        """
        stmt = select(
            CustomReaction.emoji,
            func.count(CustomReaction.id).label("count")
        ).where(
            CustomReaction.broadcast_message_id == broadcast_message_id
        ).group_by(CustomReaction.emoji)

        result = await self.session.execute(stmt)
        stats = {row.emoji: row.count for row in result.all()}

        logger.debug(
            f"Message {broadcast_message_id} has {len(stats)} different reactions"
        )

        return stats

    async def get_message_reaction_stats_by_type(
        self,
        broadcast_message_id: int
    ) -> Dict[int, int]:
        """Stats de reacciones por reaction_type_id.

        Args:
            broadcast_message_id: ID del mensaje de broadcasting

        Returns:
            {1: 45, 2: 33, 3: 28}  # reaction_type_id → count
        """
        stmt = select(
            CustomReaction.reaction_type_id,
            func.count(CustomReaction.id).label("count")
        ).where(
            CustomReaction.broadcast_message_id == broadcast_message_id
        ).group_by(CustomReaction.reaction_type_id)

        result = await self.session.execute(stmt)
        stats = {row.reaction_type_id: row.count for row in result.all()}

        return stats

    async def _update_message_stats(self, broadcast_message_id: int):
        """Actualiza cache de stats en BroadcastMessage.

        Args:
            broadcast_message_id: ID del mensaje de broadcasting
        """
        # Obtener mensaje
        stmt = select(BroadcastMessage).where(
            BroadcastMessage.id == broadcast_message_id
        )
        result = await self.session.execute(stmt)
        broadcast_msg = result.scalar_one_or_none()

        if not broadcast_msg:
            logger.warning(
                f"BroadcastMessage {broadcast_message_id} not found for stats update"
            )
            return

        # Calcular total de reacciones
        stmt_total = select(func.count(CustomReaction.id)).where(
            CustomReaction.broadcast_message_id == broadcast_message_id
        )
        result = await self.session.execute(stmt_total)
        total_reactions = result.scalar() or 0

        # Calcular usuarios únicos que reaccionaron
        stmt_unique = select(func.count(func.distinct(CustomReaction.user_id))).where(
            CustomReaction.broadcast_message_id == broadcast_message_id
        )
        result = await self.session.execute(stmt_unique)
        unique_reactors = result.scalar() or 0

        # Actualizar cache
        broadcast_msg.total_reactions = total_reactions
        broadcast_msg.unique_reactors = unique_reactors

        logger.debug(
            f"Updated stats for message {broadcast_message_id}: "
            f"{total_reactions} reactions, {unique_reactors} unique users"
        )

        # No hacemos commit aquí, se hace en el método que llama
