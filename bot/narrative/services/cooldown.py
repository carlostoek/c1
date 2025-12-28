"""
Servicio de cooldowns narrativos.

Gestiona los tiempos de espera para acceder a fragmentos,
tomar decisiones y reintentar desafíos.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from bot.narrative.database.models_immersive import NarrativeCooldown
from bot.narrative.database.enums import CooldownType

logger = logging.getLogger(__name__)


class CooldownService:
    """
    Servicio para gestión de cooldowns narrativos.

    Tipos de cooldown:
    - FRAGMENT: Tiempo de espera para acceder a un fragmento
    - CHAPTER: Tiempo de espera para acceder a un capítulo
    - DECISION: Tiempo entre decisiones
    - CHALLENGE: Tiempo para reintentar un desafío
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio.

        Args:
            session: Sesión async de SQLAlchemy
        """
        self._session = session

    # ========================================
    # GESTIÓN DE COOLDOWNS
    # ========================================

    async def set_cooldown(
        self,
        user_id: int,
        cooldown_type: CooldownType,
        target_key: str,
        duration_seconds: int,
        narrative_message: Optional[str] = None
    ) -> NarrativeCooldown:
        """
        Establece un cooldown para un usuario.

        Si ya existe un cooldown para el mismo target, lo reemplaza.

        Args:
            user_id: ID del usuario
            cooldown_type: Tipo de cooldown
            target_key: Key del target (fragment_key, chapter_slug, etc.)
            duration_seconds: Duración en segundos
            narrative_message: Mensaje a mostrar mientras espera

        Returns:
            Cooldown creado/actualizado
        """
        # Limpiar cooldown existente si hay
        await self.clear_cooldown(user_id, cooldown_type, target_key)

        now = datetime.utcnow()
        cooldown = NarrativeCooldown(
            user_id=user_id,
            cooldown_type=cooldown_type,
            target_key=target_key,
            started_at=now,
            expires_at=now + timedelta(seconds=duration_seconds),
            narrative_message=narrative_message
        )
        self._session.add(cooldown)
        await self._session.flush()

        logger.info(
            f"Cooldown establecido: user={user_id}, type={cooldown_type.value}, "
            f"target={target_key}, duration={duration_seconds}s"
        )
        return cooldown

    async def check_cooldown(
        self,
        user_id: int,
        cooldown_type: CooldownType,
        target_key: str
    ) -> tuple[bool, Optional[NarrativeCooldown]]:
        """
        Verifica si hay un cooldown activo.

        Args:
            user_id: ID del usuario
            cooldown_type: Tipo de cooldown
            target_key: Key del target

        Returns:
            Tupla (está_en_cooldown, cooldown_activo)
        """
        cooldown = await self.get_cooldown(user_id, cooldown_type, target_key)

        if cooldown is None:
            return False, None

        if cooldown.is_expired:
            # Limpiar cooldown expirado
            await self.clear_cooldown(user_id, cooldown_type, target_key)
            return False, None

        return True, cooldown

    async def get_cooldown(
        self,
        user_id: int,
        cooldown_type: CooldownType,
        target_key: str
    ) -> Optional[NarrativeCooldown]:
        """
        Obtiene un cooldown específico.

        Args:
            user_id: ID del usuario
            cooldown_type: Tipo de cooldown
            target_key: Key del target

        Returns:
            Cooldown o None
        """
        stmt = select(NarrativeCooldown).where(
            and_(
                NarrativeCooldown.user_id == user_id,
                NarrativeCooldown.cooldown_type == cooldown_type,
                NarrativeCooldown.target_key == target_key
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def clear_cooldown(
        self,
        user_id: int,
        cooldown_type: CooldownType,
        target_key: str
    ) -> bool:
        """
        Elimina un cooldown.

        Args:
            user_id: ID del usuario
            cooldown_type: Tipo de cooldown
            target_key: Key del target

        Returns:
            True si se eliminó
        """
        stmt = delete(NarrativeCooldown).where(
            and_(
                NarrativeCooldown.user_id == user_id,
                NarrativeCooldown.cooldown_type == cooldown_type,
                NarrativeCooldown.target_key == target_key
            )
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0

    async def clear_all_cooldowns(
        self,
        user_id: int
    ) -> int:
        """
        Elimina todos los cooldowns de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Número de cooldowns eliminados
        """
        stmt = delete(NarrativeCooldown).where(
            NarrativeCooldown.user_id == user_id
        )
        result = await self._session.execute(stmt)
        return result.rowcount

    async def clear_expired_cooldowns(self) -> int:
        """
        Limpia todos los cooldowns expirados del sistema.

        Returns:
            Número de cooldowns eliminados
        """
        now = datetime.utcnow()
        stmt = delete(NarrativeCooldown).where(
            NarrativeCooldown.expires_at < now
        )
        result = await self._session.execute(stmt)
        count = result.rowcount
        if count > 0:
            logger.info(f"Limpiados {count} cooldowns expirados")
        return count

    # ========================================
    # CONSULTAS
    # ========================================

    async def get_active_cooldowns(
        self,
        user_id: int
    ) -> List[NarrativeCooldown]:
        """
        Obtiene todos los cooldowns activos de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Lista de cooldowns activos
        """
        now = datetime.utcnow()
        stmt = (
            select(NarrativeCooldown)
            .where(
                and_(
                    NarrativeCooldown.user_id == user_id,
                    NarrativeCooldown.expires_at > now
                )
            )
            .order_by(NarrativeCooldown.expires_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_remaining_time(
        self,
        user_id: int,
        cooldown_type: CooldownType,
        target_key: str
    ) -> int:
        """
        Obtiene el tiempo restante de un cooldown.

        Args:
            user_id: ID del usuario
            cooldown_type: Tipo de cooldown
            target_key: Key del target

        Returns:
            Segundos restantes (0 si no hay cooldown o expiró)
        """
        cooldown = await self.get_cooldown(user_id, cooldown_type, target_key)
        if cooldown is None:
            return 0
        return cooldown.remaining_seconds

    async def get_cooldown_info(
        self,
        user_id: int,
        cooldown_type: CooldownType,
        target_key: str
    ) -> Dict[str, Any]:
        """
        Obtiene información detallada de un cooldown.

        Args:
            user_id: ID del usuario
            cooldown_type: Tipo de cooldown
            target_key: Key del target

        Returns:
            Diccionario con información del cooldown
        """
        is_active, cooldown = await self.check_cooldown(user_id, cooldown_type, target_key)

        if not is_active:
            return {
                "is_active": False,
                "remaining_seconds": 0,
                "remaining_formatted": "",
                "message": None,
                "expires_at": None,
            }

        return {
            "is_active": True,
            "remaining_seconds": cooldown.remaining_seconds,
            "remaining_formatted": self._format_time(cooldown.remaining_seconds),
            "message": cooldown.narrative_message,
            "expires_at": cooldown.expires_at.isoformat(),
            "started_at": cooldown.started_at.isoformat(),
        }

    # ========================================
    # COOLDOWNS POR TIPO
    # ========================================

    async def set_fragment_cooldown(
        self,
        user_id: int,
        fragment_key: str,
        duration_seconds: int,
        message: Optional[str] = None
    ) -> NarrativeCooldown:
        """
        Establece cooldown para un fragmento.

        Args:
            user_id: ID del usuario
            fragment_key: Key del fragmento
            duration_seconds: Duración en segundos
            message: Mensaje narrativo

        Returns:
            Cooldown creado
        """
        default_message = message or "Diana necesita un momento para reflexionar..."
        return await self.set_cooldown(
            user_id,
            CooldownType.FRAGMENT,
            fragment_key,
            duration_seconds,
            default_message
        )

    async def set_chapter_cooldown(
        self,
        user_id: int,
        chapter_slug: str,
        duration_seconds: int,
        message: Optional[str] = None
    ) -> NarrativeCooldown:
        """
        Establece cooldown para un capítulo.

        Args:
            user_id: ID del usuario
            chapter_slug: Slug del capítulo
            duration_seconds: Duración en segundos
            message: Mensaje narrativo

        Returns:
            Cooldown creado
        """
        default_message = message or "Debes esperar antes de continuar con este capítulo..."
        return await self.set_cooldown(
            user_id,
            CooldownType.CHAPTER,
            chapter_slug,
            duration_seconds,
            default_message
        )

    async def set_decision_cooldown(
        self,
        user_id: int,
        duration_seconds: int = 30,
        message: Optional[str] = None
    ) -> NarrativeCooldown:
        """
        Establece cooldown global para decisiones.

        Args:
            user_id: ID del usuario
            duration_seconds: Duración en segundos
            message: Mensaje narrativo

        Returns:
            Cooldown creado
        """
        default_message = message or "Tómate un momento para pensar tu siguiente paso..."
        return await self.set_cooldown(
            user_id,
            CooldownType.DECISION,
            "global",
            duration_seconds,
            default_message
        )

    async def set_challenge_cooldown(
        self,
        user_id: int,
        challenge_id: int,
        duration_seconds: int,
        message: Optional[str] = None
    ) -> NarrativeCooldown:
        """
        Establece cooldown para reintentar un desafío.

        Args:
            user_id: ID del usuario
            challenge_id: ID del desafío
            duration_seconds: Duración en segundos
            message: Mensaje narrativo

        Returns:
            Cooldown creado
        """
        default_message = message or "Debes esperar antes de intentarlo nuevamente..."
        return await self.set_cooldown(
            user_id,
            CooldownType.CHALLENGE,
            str(challenge_id),
            duration_seconds,
            default_message
        )

    async def can_take_decision(
        self,
        user_id: int
    ) -> tuple[bool, int]:
        """
        Verifica si el usuario puede tomar una decisión.

        Args:
            user_id: ID del usuario

        Returns:
            Tupla (puede_decidir, segundos_restantes)
        """
        is_active, cooldown = await self.check_cooldown(
            user_id,
            CooldownType.DECISION,
            "global"
        )
        if is_active:
            return False, cooldown.remaining_seconds
        return True, 0

    async def can_access_fragment(
        self,
        user_id: int,
        fragment_key: str
    ) -> tuple[bool, int, Optional[str]]:
        """
        Verifica si el usuario puede acceder a un fragmento.

        Args:
            user_id: ID del usuario
            fragment_key: Key del fragmento

        Returns:
            Tupla (puede_acceder, segundos_restantes, mensaje)
        """
        is_active, cooldown = await self.check_cooldown(
            user_id,
            CooldownType.FRAGMENT,
            fragment_key
        )
        if is_active:
            return False, cooldown.remaining_seconds, cooldown.narrative_message
        return True, 0, None

    # ========================================
    # HELPERS
    # ========================================

    def _format_time(self, seconds: int) -> str:
        """Formatea segundos a string legible."""
        if seconds < 60:
            return f"{seconds} segundos"
        elif seconds < 3600:
            mins = seconds // 60
            secs = seconds % 60
            if secs == 0:
                return f"{mins} minutos"
            return f"{mins}m {secs}s"
        else:
            hours = seconds // 3600
            mins = (seconds % 3600) // 60
            if mins == 0:
                return f"{hours} horas"
            return f"{hours}h {mins}m"
