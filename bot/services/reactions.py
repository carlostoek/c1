"""
Reaction Service - Gestión de sistema de reacciones.

Proporciona métodos para:
- CRUD de configuración de reacciones
- Gestión de reacciones de usuarios
- Contadores y analytics
"""
import logging
from typing import List, Optional, Dict
from datetime import datetime, timezone

from sqlalchemy import select, func, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from bot.database.models import ReactionConfig, MessageReaction

logger = logging.getLogger(__name__)


class ReactionService:
    """
    Servicio para gestionar sistema de reacciones inline.

    Responsabilidades:
    - CRUD de configuración de reacciones
    - Gestión de reacciones de usuarios a mensajes
    - Validaciones de negocio (límites, unicidad)
    - Analytics y contadores
    """

    # Constantes
    MAX_ACTIVE_REACTIONS = 6  # Límite de Telegram para botones inline

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio de reacciones.

        Args:
            session: Sesión async de SQLAlchemy
        """
        self.session = session
        self._logger = logging.getLogger(__name__)

    # ===== CRUD CONFIGURACIONES =====

    async def get_active_reactions(self) -> List[ReactionConfig]:
        """
        Obtiene todas las reacciones activas.

        Returns:
            Lista de ReactionConfig activas, ordenadas por created_at ASC

        Example:
            >>> reactions = await service.get_active_reactions()
            >>> print(f"Hay {len(reactions)} reacciones activas")
        """
        try:
            result = await self.session.execute(
                select(ReactionConfig)
                .where(ReactionConfig.active == True)
                .order_by(ReactionConfig.created_at.asc())
            )
            reactions = result.scalars().all()

            logger.debug(f"📊 Obtenidas {len(reactions)} reacciones activas")
            return list(reactions)

        except Exception as e:
            logger.error(f"❌ Error obteniendo reacciones activas: {e}", exc_info=True)
            return []

    async def get_all_reactions(self, include_inactive: bool = True) -> List[ReactionConfig]:
        """
        Obtiene todas las reacciones (activas e inactivas).

        Args:
            include_inactive: Si True, incluye reacciones inactivas

        Returns:
            Lista de todas las ReactionConfig
        """
        try:
            query = select(ReactionConfig)

            if not include_inactive:
                query = query.where(ReactionConfig.active == True)

            query = query.order_by(ReactionConfig.created_at.asc())

            result = await self.session.execute(query)
            reactions = result.scalars().all()

            logger.debug(f"📊 Obtenidas {len(reactions)} reacciones totales")
            return list(reactions)

        except Exception as e:
            logger.error(f"❌ Error obteniendo todas las reacciones: {e}", exc_info=True)
            return []

    async def get_reaction_by_id(self, reaction_id: int) -> Optional[ReactionConfig]:
        """
        Obtiene una reacción por su ID.

        Args:
            reaction_id: ID de la reacción

        Returns:
            ReactionConfig o None si no existe
        """
        try:
            result = await self.session.execute(
                select(ReactionConfig).where(ReactionConfig.id == reaction_id)
            )
            reaction = result.scalar_one_or_none()

            if reaction:
                logger.debug(f"✅ Reacción ID {reaction_id} encontrada: {reaction.emoji}")
            else:
                logger.warning(f"⚠️ Reacción ID {reaction_id} no existe")

            return reaction

        except Exception as e:
            logger.error(f"❌ Error obteniendo reacción {reaction_id}: {e}", exc_info=True)
            return None

    async def get_reaction_by_emoji(self, emoji: str) -> Optional[ReactionConfig]:
        """
        Obtiene una reacción por su emoji.

        Args:
            emoji: Emoji a buscar

        Returns:
            ReactionConfig o None si no existe
        """
        try:
            result = await self.session.execute(
                select(ReactionConfig).where(ReactionConfig.emoji == emoji)
            )
            reaction = result.scalar_one_or_none()

            if reaction:
                logger.debug(f"✅ Reacción '{emoji}' encontrada")

            return reaction

        except Exception as e:
            logger.error(f"❌ Error obteniendo reacción por emoji '{emoji}': {e}", exc_info=True)
            return None

    async def create_reaction(
        self,
        emoji: str,
        label: str,
        besitos_reward: int
    ) -> Optional[ReactionConfig]:
        """
        Crea una nueva configuración de reacción.

        Args:
            emoji: Emoji Unicode (ej: "❤️", "👍", "🔥")
            label: Label descriptivo (ej: "Me encanta", "Me gusta")
            besitos_reward: Cantidad de besitos a otorgar (>= 1)

        Returns:
            ReactionConfig creada o None si falla

        Note:
            Valida que besitos_reward >= 1, label <= 50 caracteres
            y que haya < 6 reacciones activas.

        Example:
            >>> reaction = await service.create_reaction("❤️", "Me encanta", 5)
            >>> if reaction:
            >>>     print(f"Reacción {reaction.emoji} creada con {reaction.besitos_reward} besitos")
        """
        try:
            # Validación: besitos >= 1
            if besitos_reward < 1:
                logger.warning(f"⚠️ Intento de crear reacción con besitos < 1: {besitos_reward}")
                return None

            # Validación: label <= 50
            if len(label) > 50:
                logger.warning(f"⚠️ Label muy largo: {len(label)} caracteres")
                return None

            # Validación: límite de reacciones activas
            active_count = await self.count_active_reactions()
            if active_count >= self.MAX_ACTIVE_REACTIONS:
                logger.warning(
                    f"⚠️ Límite de reacciones activas alcanzado ({self.MAX_ACTIVE_REACTIONS})"
                )
                return None

            # Crear reacción
            reaction = ReactionConfig(
                emoji=emoji,
                label=label,
                besitos_reward=besitos_reward,
                active=True
            )

            self.session.add(reaction)
            await self.session.flush()  # Para obtener el ID
            await self.session.refresh(reaction)

            logger.info(
                f"✅ Reacción creada: {reaction.emoji} '{reaction.label}' "
                f"({reaction.besitos_reward} besitos)"
            )

            return reaction

        except IntegrityError as e:
            await self.session.rollback()
            logger.warning(f"⚠️ Error de integridad al crear reacción '{emoji}': {e}")
            return None
        except Exception as e:
            await self.session.rollback()
            logger.error(f"❌ Error creando reacción '{emoji}': {e}", exc_info=True)
            return None

    async def update_reaction(
        self,
        reaction_id: int,
        label: Optional[str] = None,
        besitos_reward: Optional[int] = None,
        active: Optional[bool] = None
    ) -> Optional[ReactionConfig]:
        """
        Actualiza una reacción existente.

        Args:
            reaction_id: ID de la reacción a actualizar
            label: Nuevo label (opcional)
            besitos_reward: Nuevo puntaje (opcional, >= 1)
            active: Nuevo estado activo/inactivo (opcional)

        Returns:
            ReactionConfig actualizada o None si falla

        Note:
            No se permite cambiar el emoji (es único e inmutable).
            Para cambiar emoji, eliminar y crear nueva reacción.

            Si se intenta activar una reacción y hay 6 activas,
            rechaza la actualización.
        """
        try:
            reaction = await self.get_reaction_by_id(reaction_id)
            if not reaction:
                logger.warning(f"⚠️ No se puede actualizar: reacción {reaction_id} no existe")
                return None

            # Aplicar cambios
            updated = False

            if label is not None:
                if len(label) > 50:
                    logger.warning(f"⚠️ Label muy largo: {len(label)} caracteres")
                    return None
                reaction.label = label
                updated = True

            if besitos_reward is not None:
                if besitos_reward < 1:
                    logger.warning(f"⚠️ Besitos reward inválido: {besitos_reward}")
                    return None
                reaction.besitos_reward = besitos_reward
                updated = True

            if active is not None:
                # Verificar límite si se está activando
                if active and not reaction.active:
                    active_count = await self.count_active_reactions()
                    if active_count >= self.MAX_ACTIVE_REACTIONS:
                        logger.warning(
                            f"⚠️ No se puede activar: límite de {self.MAX_ACTIVE_REACTIONS} alcanzado"
                        )
                        return None

                reaction.active = active
                updated = True

            if updated:
                reaction.updated_at = datetime.now(timezone.utc)
                await self.session.flush()
                await self.session.refresh(reaction)

                logger.info(
                    f"✅ Reacción {reaction_id} actualizada: {reaction.emoji} '{reaction.label}'"
                )

            return reaction

        except Exception as e:
            await self.session.rollback()
            logger.error(f"❌ Error actualizando reacción {reaction_id}: {e}", exc_info=True)
            return None

    async def delete_reaction(self, reaction_id: int) -> bool:
        """
        Elimina una reacción (solo si no tiene histórico).

        Args:
            reaction_id: ID de la reacción a eliminar

        Returns:
            True si se eliminó exitosamente, False si falla

        Note:
            Si la reacción tiene histórico de uso (MessageReaction),
            se DESACTIVA en lugar de eliminar para mantener integridad.
        """
        try:
            reaction = await self.get_reaction_by_id(reaction_id)
            if not reaction:
                logger.warning(f"⚠️ No se puede eliminar: reacción {reaction_id} no existe")
                return False

            # Verificar si tiene histórico
            result = await self.session.execute(
                select(func.count(MessageReaction.id))
                .where(MessageReaction.emoji == reaction.emoji)
            )
            usage_count = result.scalar()

            if usage_count > 0:
                # Tiene histórico: desactivar en lugar de eliminar
                logger.info(
                    f"⚠️ Reacción {reaction_id} tiene {usage_count} usos. "
                    f"Desactivando en lugar de eliminar."
                )
                reaction.active = False
                await self.session.flush()
                return True

            # Sin histórico: eliminar completamente
            await self.session.delete(reaction)
            await self.session.flush()

            logger.info(f"✅ Reacción {reaction_id} ({reaction.emoji}) eliminada")
            return True

        except Exception as e:
            await self.session.rollback()
            logger.error(f"❌ Error eliminando reacción {reaction_id}: {e}", exc_info=True)
            return False

    async def count_active_reactions(self) -> int:
        """
        Cuenta cuántas reacciones activas hay.

        Returns:
            Número de reacciones activas
        """
        try:
            result = await self.session.execute(
                select(func.count(ReactionConfig.id))
                .where(ReactionConfig.active == True)
            )
            count = result.scalar()
            return count or 0

        except Exception as e:
            logger.error(f"❌ Error contando reacciones activas: {e}", exc_info=True)
            return 0

    # ===== GESTIÓN DE REACCIONES DE USUARIOS =====

    async def record_user_reaction(
        self,
        channel_id: int,
        message_id: int,
        user_id: int,
        emoji: str
    ) -> Optional[MessageReaction]:
        """
        Registra o actualiza una reacción de usuario.

        Si el usuario ya reaccionó al mensaje:
        - Actualiza el emoji y besitos_awarded
        - Retorna la reacción actualizada

        Si es primera reacción:
        - Crea nueva entrada
        - Retorna la reacción creada

        Args:
            channel_id: ID del canal de Telegram
            message_id: ID del mensaje de Telegram
            user_id: ID del usuario que reacciona
            emoji: Emoji seleccionado

        Returns:
            MessageReaction creada/actualizada o None si falla

        Example:
            >>> reaction = await service.record_user_reaction(
            ...     channel_id=-1001234567890,
            ...     message_id=12345,
            ...     user_id=987654321,
            ...     emoji="❤️"
            ... )
            >>> print(f"Reacción registrada: {reaction.emoji}")
        """
        try:
            # Obtener configuración del emoji para saber besitos
            reaction_config = await self.get_reaction_by_emoji(emoji)
            if not reaction_config:
                logger.warning(f"⚠️ Emoji '{emoji}' no configurado como reacción")
                return None

            if not reaction_config.active:
                logger.warning(f"⚠️ Emoji '{emoji}' está desactivado")
                return None

            # Verificar si usuario ya reaccionó a este mensaje
            result = await self.session.execute(
                select(MessageReaction).where(
                    and_(
                        MessageReaction.channel_id == channel_id,
                        MessageReaction.message_id == message_id,
                        MessageReaction.user_id == user_id
                    )
                )
            )
            existing_reaction = result.scalar_one_or_none()

            if existing_reaction:
                # Ya reaccionó: actualizar emoji y besitos
                old_emoji = existing_reaction.emoji
                existing_reaction.emoji = emoji
                existing_reaction.besitos_awarded = reaction_config.besitos_reward

                await self.session.flush()
                await self.session.refresh(existing_reaction)

                logger.info(
                    f"✅ Reacción actualizada: user {user_id} cambió de '{old_emoji}' "
                    f"a '{emoji}' en msg {message_id}"
                )

                return existing_reaction
            else:
                # Primera reacción: crear nueva
                new_reaction = MessageReaction(
                    channel_id=channel_id,
                    message_id=message_id,
                    user_id=user_id,
                    emoji=emoji,
                    besitos_awarded=reaction_config.besitos_reward
                )

                self.session.add(new_reaction)
                await self.session.flush()
                await self.session.refresh(new_reaction)

                logger.info(
                    f"✅ Nueva reacción: user {user_id} reaccionó con '{emoji}' "
                    f"en msg {message_id} (+{reaction_config.besitos_reward} besitos)"
                )

                return new_reaction

        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"❌ Error registrando reacción: user {user_id}, msg {message_id}, "
                f"emoji '{emoji}': {e}",
                exc_info=True
            )
            return None

    async def get_user_reaction(
        self,
        channel_id: int,
        message_id: int,
        user_id: int
    ) -> Optional[MessageReaction]:
        """
        Obtiene la reacción de un usuario a un mensaje específico.

        Args:
            channel_id: ID del canal
            message_id: ID del mensaje
            user_id: ID del usuario

        Returns:
            MessageReaction o None si no ha reaccionado
        """
        try:
            result = await self.session.execute(
                select(MessageReaction).where(
                    and_(
                        MessageReaction.channel_id == channel_id,
                        MessageReaction.message_id == message_id,
                        MessageReaction.user_id == user_id
                    )
                )
            )
            reaction = result.scalar_one_or_none()

            if reaction:
                logger.debug(
                    f"✅ Reacción encontrada: user {user_id} → '{reaction.emoji}' "
                    f"en msg {message_id}"
                )
            else:
                logger.debug(f"ℹ️ User {user_id} no ha reaccionado a msg {message_id}")

            return reaction

        except Exception as e:
            logger.error(
                f"❌ Error obteniendo reacción: user {user_id}, msg {message_id}: {e}",
                exc_info=True
            )
            return None

    async def has_user_reacted(
        self,
        channel_id: int,
        message_id: int,
        user_id: int
    ) -> bool:
        """
        Verifica si un usuario ha reaccionado a un mensaje.

        Args:
            channel_id: ID del canal
            message_id: ID del mensaje
            user_id: ID del usuario

        Returns:
            True si ha reaccionado, False si no
        """
        reaction = await self.get_user_reaction(channel_id, message_id, user_id)
        return reaction is not None

    async def remove_user_reaction(
        self,
        channel_id: int,
        message_id: int,
        user_id: int
    ) -> bool:
        """
        Elimina la reacción de un usuario a un mensaje.

        Args:
            channel_id: ID del canal
            message_id: ID del mensaje
            user_id: ID del usuario

        Returns:
            True si se eliminó, False si no existía o falló
        """
        try:
            result = await self.session.execute(
                delete(MessageReaction).where(
                    and_(
                        MessageReaction.channel_id == channel_id,
                        MessageReaction.message_id == message_id,
                        MessageReaction.user_id == user_id
                    )
                )
            )

            deleted_count = result.rowcount

            if deleted_count > 0:
                await self.session.flush()
                logger.info(
                    f"✅ Reacción eliminada: user {user_id} en msg {message_id}"
                )
                return True
            else:
                logger.warning(
                    f"⚠️ No se eliminó nada: user {user_id} no tenía reacción "
                    f"en msg {message_id}"
                )
                return False

        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"❌ Error eliminando reacción: user {user_id}, msg {message_id}: {e}",
                exc_info=True
            )
            return False

    # ===== CONTADORES Y ANALYTICS =====

    async def get_message_reaction_counts(
        self,
        channel_id: int,
        message_id: int
    ) -> Dict[str, int]:
        """
        Obtiene contadores de reacciones para un mensaje.

        Args:
            channel_id: ID del canal
            message_id: ID del mensaje

        Returns:
            Dict con emojis como keys y conteos como value
            Ejemplo: {"❤️": 45, "👍": 23, "🔥": 12}

        Example:
            >>> counts = await service.get_message_reaction_counts(-1001234, 12345)
            >>> print(f"❤️ tiene {counts.get('❤️', 0)} reacciones")
        """
        try:
            result = await self.session.execute(
                select(
                    MessageReaction.emoji,
                    func.count(MessageReaction.id).label('count')
                )
                .where(
                    and_(
                        MessageReaction.channel_id == channel_id,
                        MessageReaction.message_id == message_id
                    )
                )
                .group_by(MessageReaction.emoji)
            )

            counts = {row.emoji: row.count for row in result}

            logger.debug(
                f"📊 Contadores msg {message_id}: {len(counts)} emojis diferentes, "
                f"{sum(counts.values())} reacciones totales"
            )

            return counts

        except Exception as e:
            logger.error(
                f"❌ Error obteniendo contadores: msg {message_id}: {e}",
                exc_info=True
            )
            return {}

    async def get_message_total_reactions(
        self,
        channel_id: int,
        message_id: int
    ) -> int:
        """
        Obtiene el total de reacciones (usuarios únicos) de un mensaje.

        Args:
            channel_id: ID del canal
            message_id: ID del mensaje

        Returns:
            Número total de usuarios que han reaccionado
        """
        try:
            result = await self.session.execute(
                select(func.count(MessageReaction.id))
                .where(
                    and_(
                        MessageReaction.channel_id == channel_id,
                        MessageReaction.message_id == message_id
                    )
                )
            )

            total = result.scalar()
            logger.debug(f"📊 Msg {message_id} tiene {total} reacciones totales")

            return total or 0

        except Exception as e:
            logger.error(
                f"❌ Error contando reacciones totales: msg {message_id}: {e}",
                exc_info=True
            )
            return 0

    async def get_user_total_reactions(
        self,
        user_id: int,
        channel_id: Optional[int] = None
    ) -> int:
        """
        Obtiene el total de reacciones hechas por un usuario.

        Args:
            user_id: ID del usuario
            channel_id: ID del canal (opcional, None = todos los canales)

        Returns:
            Número total de reacciones del usuario
        """
        try:
            query = select(func.count(MessageReaction.id)).where(
                MessageReaction.user_id == user_id
            )

            if channel_id is not None:
                query = query.where(MessageReaction.channel_id == channel_id)

            result = await self.session.execute(query)
            total = result.scalar()

            logger.debug(
                f"📊 User {user_id} tiene {total} reacciones "
                f"{'en total' if channel_id is None else f'en canal {channel_id}'}"
            )

            return total or 0

        except Exception as e:
            logger.error(
                f"❌ Error contando reacciones de user {user_id}: {e}",
                exc_info=True
            )
            return 0

    async def get_top_reacted_messages(
        self,
        channel_id: int,
        limit: int = 10
    ) -> List[tuple[int, int]]:
        """
        Obtiene los mensajes con más reacciones en un canal.

        Args:
            channel_id: ID del canal
            limit: Número máximo de mensajes a retornar

        Returns:
            Lista de tuplas (message_id, reaction_count) ordenada DESC

        Example:
            >>> top = await service.get_top_reacted_messages(-1001234, limit=5)
            >>> for msg_id, count in top:
            ...     print(f"Mensaje {msg_id}: {count} reacciones")
        """
        try:
            result = await self.session.execute(
                select(
                    MessageReaction.message_id,
                    func.count(MessageReaction.id).label('reaction_count')
                )
                .where(MessageReaction.channel_id == channel_id)
                .group_by(MessageReaction.message_id)
                .order_by(func.count(MessageReaction.id).desc())
                .limit(limit)
            )

            top_messages = [(row.message_id, row.reaction_count) for row in result]

            logger.debug(
                f"📊 Top {len(top_messages)} mensajes más reaccionados en canal {channel_id}"
            )

            return top_messages

        except Exception as e:
            logger.error(
                f"❌ Error obteniendo top mensajes: canal {channel_id}: {e}",
                exc_info=True
            )
            return []

    async def get_most_used_emoji(
        self,
        channel_id: Optional[int] = None
    ) -> Optional[tuple[str, int]]:
        """
        Obtiene el emoji más usado.

        Args:
            channel_id: ID del canal (opcional, None = todos los canales)

        Returns:
            Tupla (emoji, count) o None si no hay reacciones

        Example:
            >>> most_used = await service.get_most_used_emoji()
            >>> if most_used:
            ...     emoji, count = most_used
            ...     print(f"Emoji más usado: {emoji} con {count} usos")
        """
        try:
            query = select(
                MessageReaction.emoji,
                func.count(MessageReaction.id).label('count')
            )

            if channel_id is not None:
                query = query.where(MessageReaction.channel_id == channel_id)

            query = query.group_by(MessageReaction.emoji).order_by(
                func.count(MessageReaction.id).desc()
            ).limit(1)

            result = await self.session.execute(query)
            row = result.first()

            if row:
                logger.debug(
                    f"📊 Emoji más usado: '{row.emoji}' con {row.count} usos"
                )
                return (row.emoji, row.count)
            else:
                logger.debug("ℹ️ No hay reacciones registradas")
                return None

        except Exception as e:
            logger.error(f"❌ Error obteniendo emoji más usado: {e}", exc_info=True)
            return None
