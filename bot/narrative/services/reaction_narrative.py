"""
Servicio de gestión de reacciones narrativas.

Responsabilidades:
- Crear tracking de espera de reacción
- Validar reacción narrativa
- Calcular tiempo de respuesta
- Integrar con arquetipos
- Avanzar narrativa automáticamente
"""
import logging
from typing import Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.narrative.database.models_immersive import NarrativeReactionWait
from bot.database.models import BroadcastMessage

logger = logging.getLogger(__name__)


class NarrativeReactionService:
    """Servicio de reacciones narrativas."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def start_reaction_wait(
        self,
        user_id: int,
        fragment_key: str,
        broadcast_message_id: int,
        next_fragment_key: str,
        required_emoji: Optional[str] = None,
        timeout_seconds: int = 120
    ) -> NarrativeReactionWait:
        """
        Inicia espera de reacción para usuario.

        Crea registro en BD para tracking persistente.

        Args:
            user_id: Usuario
            fragment_key: Fragmento actual
            broadcast_message_id: Mensaje de broadcasting
            next_fragment_key: Fragmento siguiente
            required_emoji: Emoji requerido (None = cualquiera)
            timeout_seconds: Timeout en segundos

        Returns:
            NarrativeReactionWait creado
        """
        # Eliminar wait previo si existe (usuario puede reintentar)
        await self.cancel_reaction_wait(user_id)

        # Crear nuevo wait
        expires_at = datetime.utcnow() + timedelta(seconds=timeout_seconds)

        wait = NarrativeReactionWait(
            user_id=user_id,
            fragment_key=fragment_key,
            broadcast_message_id=broadcast_message_id,
            required_emoji=required_emoji,
            started_at=datetime.utcnow(),
            expires_at=expires_at,
            next_fragment_key=next_fragment_key
        )

        self.session.add(wait)
        await self.session.flush()
        await self.session.refresh(wait)

        logger.info(
            f"🕐 Reacción narrativa iniciada: user={user_id}, "
            f"fragment={fragment_key}, timeout={timeout_seconds}s"
        )

        return wait

    async def get_active_wait(
        self,
        user_id: int
    ) -> Optional[NarrativeReactionWait]:
        """
        Obtiene wait activo del usuario.

        Returns:
            NarrativeReactionWait o None
        """
        stmt = select(NarrativeReactionWait).where(
            NarrativeReactionWait.user_id == user_id,
            NarrativeReactionWait.expires_at > datetime.utcnow()
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def validate_reaction(
        self,
        user_id: int,
        broadcast_message_id: int,
        emoji: str
    ) -> Tuple[bool, Optional[str], Optional[NarrativeReactionWait]]:
        """
        Valida si reacción corresponde a misión narrativa activa.

        Args:
            user_id: Usuario
            broadcast_message_id: Mensaje donde reaccionó
            emoji: Emoji usado

        Returns:
            (is_valid, error_message, wait_object)
        """
        # Obtener wait activo
        wait = await self.get_active_wait(user_id)

        if not wait:
            # No tiene misión activa
            return False, None, None

        # Validar mensaje correcto
        if wait.broadcast_message_id != broadcast_message_id:
            return False, "Reacción en mensaje incorrecto", wait

        # Validar emoji si es requerido
        if wait.required_emoji and wait.required_emoji != emoji:
            return (
                False,
                f"Emoji incorrecto (esperado: {wait.required_emoji})",
                wait
            )

        # Validación exitosa
        return True, None, wait

    async def calculate_response_time(
        self,
        wait: NarrativeReactionWait
    ) -> int:
        """
        Calcula tiempo de respuesta en segundos.

        Args:
            wait: Objeto de espera

        Returns:
            Segundos transcurridos
        """
        delta = datetime.utcnow() - wait.started_at
        return int(delta.total_seconds())

    async def complete_reaction_wait(
        self,
        user_id: int
    ) -> bool:
        """
        Completa y elimina wait activo.

        Llamar después de procesar reacción exitosa.

        Returns:
            True si se eliminó, False si no había wait
        """
        wait = await self.get_active_wait(user_id)

        if not wait:
            return False

        await self.session.delete(wait)
        await self.session.flush()

        logger.info(
            f"✅ Reacción narrativa completada: user={user_id}, "
            f"fragment={wait.fragment_key}"
        )

        return True

    async def cancel_reaction_wait(
        self,
        user_id: int
    ) -> bool:
        """
        Cancela wait activo (timeout o reinicio).

        Returns:
            True si se canceló, False si no había wait
        """
        stmt = select(NarrativeReactionWait).where(
            NarrativeReactionWait.user_id == user_id
        )

        result = await self.session.execute(stmt)
        wait = result.scalar_one_or_none()

        if not wait:
            return False

        await self.session.delete(wait)
        await self.session.flush()

        logger.warning(
            f"⚠️ Reacción narrativa cancelada: user={user_id}"
        )

        return True

    async def cleanup_expired_waits(self) -> int:
        """
        Limpia waits expirados (background task).

        Returns:
            Cantidad eliminada
        """
        stmt = select(NarrativeReactionWait).where(
            NarrativeReactionWait.expires_at <= datetime.utcnow()
        )

        result = await self.session.execute(stmt)
        expired = result.scalars().all()

        count = len(expired)

        for wait in expired:
            await self.session.delete(wait)

        await self.session.flush()

        if count > 0:
            logger.info(f"🧹 Limpió {count} waits expirados")

        return count
