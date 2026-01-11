"""
Servicio de gestión del progreso del usuario en la narrativa.

Rastrea posición actual, arquetipos detectados y estadísticas de progreso.
"""
import logging
from typing import Optional, Tuple
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.narrative.database import (
    NarrativeChapter,
    NarrativeFragment,
    UserNarrativeProgress,
    ArchetypeType,
)

logger = logging.getLogger(__name__)


class ProgressService:
    """
    Servicio de progreso del usuario.

    Métodos:
    - get_or_create_progress: Obtener o crear progreso del usuario
    - advance_to: Avanzar a fragmento específico
    - get_current_fragment: Obtener fragmento actual del usuario
    - complete_chapter: Marcar capítulo como completado
    - update_archetype: Actualizar arquetipo detectado
    - has_completed_chapter: Verificar si completó capítulo
    - has_visited_fragment: Verificar si visitó fragmento
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa servicio.

        Args:
            session: Sesión async de SQLAlchemy
        """
        self._session = session

    async def get_or_create_progress(
        self,
        user_id: int
    ) -> UserNarrativeProgress:
        """
        Obtiene o crea el progreso del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Progreso del usuario
        """
        stmt = select(UserNarrativeProgress).where(
            UserNarrativeProgress.user_id == user_id
        )
        result = await self._session.execute(stmt)
        progress = result.scalar_one_or_none()

        if not progress:
            # Crear nuevo progreso
            progress = UserNarrativeProgress(
                user_id=user_id,
                detected_archetype=ArchetypeType.UNKNOWN,
                archetype_confidence=0.0,
                total_decisions=0,
                chapters_completed=0
            )
            self._session.add(progress)
            await self._session.flush()
            await self._session.refresh(progress)

            logger.info(f"✅ Progreso creado para usuario {user_id}")
        else:
            logger.debug(f"📊 Progreso existente para usuario {user_id}")

        return progress

    async def advance_to(
        self,
        user_id: int,
        fragment_key: str,
        chapter_id: Optional[int] = None
    ) -> UserNarrativeProgress:
        """
        Avanza usuario a fragmento específico.

        Args:
            user_id: ID del usuario
            fragment_key: Key del fragmento destino
            chapter_id: ID del capítulo (opcional, si cambió de capítulo)

        Returns:
            Progreso actualizado
        """
        progress = await self.get_or_create_progress(user_id)

        # Actualizar posición
        progress.current_fragment_key = fragment_key
        if chapter_id is not None:
            progress.current_chapter_id = chapter_id

        # Actualizar timestamp
        progress.last_interaction = datetime.utcnow()

        await self._session.flush()
        await self._session.refresh(progress)

        logger.info(f"➡️ Usuario {user_id} avanzó a fragmento: {fragment_key}")

        return progress

    async def get_current_fragment(
        self,
        user_id: int
    ) -> Optional[str]:
        """
        Obtiene fragmento actual del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Fragment key actual o None si no ha empezado
        """
        progress = await self.get_or_create_progress(user_id)
        return progress.current_fragment_key

    async def complete_chapter(
        self,
        user_id: int,
        chapter_id: int
    ) -> UserNarrativeProgress:
        """
        Marca capítulo como completado.

        Args:
            user_id: ID del usuario
            chapter_id: ID del capítulo completado

        Returns:
            Progreso actualizado
        """
        progress = await self.get_or_create_progress(user_id)

        # Incrementar contador si no lo había completado antes
        # (esto es simplificado, en producción usaríamos tabla separada)
        progress.chapters_completed += 1
        progress.last_interaction = datetime.utcnow()

        await self._session.flush()
        await self._session.refresh(progress)

        logger.info(f"🎉 Usuario {user_id} completó capítulo {chapter_id}")

        return progress

    async def update_archetype(
        self,
        user_id: int,
        archetype: ArchetypeType,
        confidence: float
    ) -> UserNarrativeProgress:
        """
        Actualiza arquetipo detectado del usuario.

        Args:
            user_id: ID del usuario
            archetype: Tipo de arquetipo detectado
            confidence: Nivel de confianza (0.0 - 1.0)

        Returns:
            Progreso actualizado
        """
        progress = await self.get_or_create_progress(user_id)

        progress.detected_archetype = archetype
        progress.archetype_confidence = confidence

        await self._session.flush()
        await self._session.refresh(progress)

        logger.info(
            f"🎭 Usuario {user_id} → Arquetipo: {archetype.value} "
            f"(confianza: {confidence:.2f})"
        )

        return progress

    async def increment_decisions(
        self,
        user_id: int
    ) -> UserNarrativeProgress:
        """
        Incrementa contador de decisiones del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Progreso actualizado
        """
        progress = await self.get_or_create_progress(user_id)

        progress.total_decisions += 1
        progress.last_interaction = datetime.utcnow()

        await self._session.flush()
        await self._session.refresh(progress)

        logger.debug(f"📊 Usuario {user_id} → Total decisiones: {progress.total_decisions}")

        return progress

    async def has_completed_chapter(
        self,
        user_id: int,
        chapter_slug: str
    ) -> bool:
        """
        Verifica si usuario completó un capítulo.

        NOTA: Implementación simplificada. En producción se debería
        tener tabla separada para tracking de capítulos completados.

        Args:
            user_id: ID del usuario
            chapter_slug: Slug del capítulo

        Returns:
            True si completó el capítulo
        """
        progress = await self.get_or_create_progress(user_id)

        # Simplificación: asumimos que si completó al menos 1 capítulo
        # y actualmente está en otro, entonces completó el anterior
        # TODO: Mejorar esto con tabla dedicada
        return progress.chapters_completed > 0

    async def has_visited_fragment(
        self,
        user_id: int,
        fragment_key: str
    ) -> bool:
        """
        Verifica si usuario visitó un fragmento.

        NOTA: Implementación simplificada usando current_fragment_key.
        En producción se debería verificar en UserDecisionHistory.

        Args:
            user_id: ID del usuario
            fragment_key: Key del fragmento

        Returns:
            True si visitó el fragmento
        """
        from bot.narrative.database import UserDecisionHistory

        # Verificar en historial de decisiones
        stmt = select(UserDecisionHistory).where(
            UserDecisionHistory.user_id == user_id,
            UserDecisionHistory.fragment_key == fragment_key
        )
        result = await self._session.execute(stmt)
        history = result.scalar_one_or_none()

        return history is not None

    async def get_progress(self, user_id: int) -> Optional[UserNarrativeProgress]:
        """
        Obtiene progreso del usuario sin crear si no existe.

        Args:
            user_id: ID del usuario

        Returns:
            Progreso o None si no existe
        """
        stmt = select(UserNarrativeProgress).where(
            UserNarrativeProgress.user_id == user_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def reset_progress(self, user_id: int) -> bool:
        """
        Resetea progreso del usuario (para reiniciar historia).

        Args:
            user_id: ID del usuario

        Returns:
            True si se reseteó, False si no tenía progreso
        """
        progress = await self.get_progress(user_id)
        if not progress:
            logger.warning(f"⚠️ No hay progreso que resetear para usuario {user_id}")
            return False

        # Resetear a valores iniciales
        progress.current_chapter_id = None
        progress.current_fragment_key = None
        progress.detected_archetype = ArchetypeType.UNKNOWN
        progress.archetype_confidence = 0.0
        progress.total_decisions = 0
        progress.chapters_completed = 0
        progress.last_interaction = datetime.utcnow()

        await self._session.flush()

        logger.info(f"🔄 Progreso reseteado para usuario {user_id}")

        return True

    async def has_taken_decision(
        self,
        user_id: int,
        decision_key: str
    ) -> bool:
        """
        Verifica si usuario tomó una decisión específica.

        Args:
            user_id: ID del usuario
            decision_key: Key de la decisión

        Returns:
            True si tomó la decisión
        """
        from bot.narrative.database import UserDecisionHistory, FragmentDecision

        # Verificar si existe en el historial con el decision_key específico
        stmt = (
            select(UserDecisionHistory)
            .join(FragmentDecision, UserDecisionHistory.decision_id == FragmentDecision.id)
            .where(
                UserDecisionHistory.user_id == user_id,
                FragmentDecision.target_fragment_key == decision_key
            )
        )
        result = await self._session.execute(stmt)
        history = result.scalar_one_or_none()

        return history is not None

    async def advance_after_reaction(
        self,
        user_id: int,
        current_fragment_key: str,
        next_fragment_key: str
    ) -> UserNarrativeProgress:
        """
        Avanza narrativa después de reacción exitosa.

        Similar a advance_to() pero con logging específico para reacciones.

        Args:
            user_id: Usuario
            current_fragment_key: Fragmento actual (donde esperaba reacción)
            next_fragment_key: Fragmento siguiente

        Returns:
            Progreso actualizado
        """
        progress = await self.advance_to(
            user_id=user_id,
            fragment_key=next_fragment_key
        )

        logger.info(
            f"✅ Usuario {user_id} avanzó por reacción: "
            f"{current_fragment_key} → {next_fragment_key}"
        )

        return progress
