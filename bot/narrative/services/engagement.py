"""
Servicio de engagement narrativo.

Gestiona el tracking de visitas, tiempo de lectura y engagement
del usuario con los fragmentos narrativos.
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from bot.narrative.database.models_immersive import (
    UserFragmentVisit,
    ChapterCompletion,
    DailyNarrativeLimit,
)

logger = logging.getLogger(__name__)


class EngagementService:
    """
    Servicio para tracking de engagement narrativo.

    Gestiona:
    - Registro de visitas a fragmentos
    - Tracking de tiempo de lectura
    - Capítulos completados
    - Límites diarios de navegación
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio.

        Args:
            session: Sesión async de SQLAlchemy
        """
        self._session = session

    # ========================================
    # VISITAS A FRAGMENTOS
    # ========================================

    async def record_visit(
        self,
        user_id: int,
        fragment_key: str
    ) -> UserFragmentVisit:
        """
        Registra una visita a un fragmento.

        Si es la primera visita, crea el registro.
        Si ya existe, incrementa el contador.

        Args:
            user_id: ID del usuario
            fragment_key: Key del fragmento visitado

        Returns:
            Registro de visita actualizado
        """
        visit = await self.get_visit(user_id, fragment_key)

        if visit is None:
            # Primera visita
            visit = UserFragmentVisit(
                user_id=user_id,
                fragment_key=fragment_key,
                visit_count=1,
                first_visit=datetime.utcnow(),
                last_visit=datetime.utcnow(),
                total_time_seconds=0,
                reading_started_at=datetime.utcnow()
            )
            self._session.add(visit)
            logger.info(f"Primera visita: user={user_id}, fragment={fragment_key}")
        else:
            # Visita de retorno
            visit.visit_count += 1
            visit.last_visit = datetime.utcnow()
            visit.reading_started_at = datetime.utcnow()
            logger.debug(f"Visita #{visit.visit_count}: user={user_id}, fragment={fragment_key}")

        await self._session.flush()
        return visit

    async def get_visit(
        self,
        user_id: int,
        fragment_key: str
    ) -> Optional[UserFragmentVisit]:
        """
        Obtiene el registro de visita de un usuario a un fragmento.

        Args:
            user_id: ID del usuario
            fragment_key: Key del fragmento

        Returns:
            Registro de visita o None
        """
        stmt = select(UserFragmentVisit).where(
            and_(
                UserFragmentVisit.user_id == user_id,
                UserFragmentVisit.fragment_key == fragment_key
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_visit_count(
        self,
        user_id: int,
        fragment_key: str
    ) -> int:
        """
        Obtiene el número de visitas a un fragmento.

        Args:
            user_id: ID del usuario
            fragment_key: Key del fragmento

        Returns:
            Número de visitas (0 si nunca visitó)
        """
        visit = await self.get_visit(user_id, fragment_key)
        return visit.visit_count if visit else 0

    async def has_visited(
        self,
        user_id: int,
        fragment_key: str
    ) -> bool:
        """
        Verifica si el usuario ha visitado un fragmento.

        Args:
            user_id: ID del usuario
            fragment_key: Key del fragmento

        Returns:
            True si ha visitado al menos una vez
        """
        count = await self.get_visit_count(user_id, fragment_key)
        return count > 0

    async def get_all_visits(
        self,
        user_id: int,
        limit: int = 50
    ) -> List[UserFragmentVisit]:
        """
        Obtiene todas las visitas de un usuario.

        Args:
            user_id: ID del usuario
            limit: Máximo de registros

        Returns:
            Lista de visitas ordenadas por última visita
        """
        stmt = (
            select(UserFragmentVisit)
            .where(UserFragmentVisit.user_id == user_id)
            .order_by(UserFragmentVisit.last_visit.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ========================================
    # TIEMPO DE LECTURA
    # ========================================

    async def start_reading(
        self,
        user_id: int,
        fragment_key: str
    ) -> None:
        """
        Marca el inicio de lectura de un fragmento.

        Args:
            user_id: ID del usuario
            fragment_key: Key del fragmento
        """
        visit = await self.get_visit(user_id, fragment_key)
        if visit:
            visit.reading_started_at = datetime.utcnow()
            await self._session.flush()

    async def stop_reading(
        self,
        user_id: int,
        fragment_key: str
    ) -> int:
        """
        Finaliza lectura y acumula tiempo.

        Args:
            user_id: ID del usuario
            fragment_key: Key del fragmento

        Returns:
            Segundos de lectura acumulados en esta sesión
        """
        visit = await self.get_visit(user_id, fragment_key)
        if visit and visit.reading_started_at:
            elapsed = (datetime.utcnow() - visit.reading_started_at).total_seconds()
            elapsed_int = int(elapsed)
            visit.total_time_seconds += elapsed_int
            visit.reading_started_at = None
            await self._session.flush()
            return elapsed_int
        return 0

    async def get_time_spent(
        self,
        user_id: int,
        fragment_key: str
    ) -> int:
        """
        Obtiene tiempo total en un fragmento.

        Args:
            user_id: ID del usuario
            fragment_key: Key del fragmento

        Returns:
            Segundos totales acumulados
        """
        visit = await self.get_visit(user_id, fragment_key)
        return visit.total_time_seconds if visit else 0

    # ========================================
    # CAPÍTULOS COMPLETADOS
    # ========================================

    async def complete_chapter(
        self,
        user_id: int,
        chapter_slug: str,
        fragments_visited: int = 0,
        decisions_made: int = 0,
        total_time_seconds: int = 0,
        clues_found: int = 0,
        chapter_archetype: Optional[str] = None
    ) -> ChapterCompletion:
        """
        Marca un capítulo como completado.

        Args:
            user_id: ID del usuario
            chapter_slug: Slug del capítulo
            fragments_visited: Fragmentos visitados
            decisions_made: Decisiones tomadas
            total_time_seconds: Tiempo total en segundos
            clues_found: Pistas encontradas
            chapter_archetype: Arquetipo predominante

        Returns:
            Registro de completación
        """
        # Verificar si ya existe
        existing = await self.get_chapter_completion(user_id, chapter_slug)
        if existing:
            logger.warning(f"Capítulo ya completado: user={user_id}, chapter={chapter_slug}")
            return existing

        completion = ChapterCompletion(
            user_id=user_id,
            chapter_slug=chapter_slug,
            completed_at=datetime.utcnow(),
            fragments_visited=fragments_visited,
            decisions_made=decisions_made,
            total_time_seconds=total_time_seconds,
            clues_found=clues_found,
            chapter_archetype=chapter_archetype
        )
        self._session.add(completion)
        await self._session.flush()

        logger.info(f"Capítulo completado: user={user_id}, chapter={chapter_slug}")
        return completion

    async def get_chapter_completion(
        self,
        user_id: int,
        chapter_slug: str
    ) -> Optional[ChapterCompletion]:
        """
        Obtiene registro de completación de capítulo.

        Args:
            user_id: ID del usuario
            chapter_slug: Slug del capítulo

        Returns:
            Registro de completación o None
        """
        stmt = select(ChapterCompletion).where(
            and_(
                ChapterCompletion.user_id == user_id,
                ChapterCompletion.chapter_slug == chapter_slug
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def has_completed_chapter(
        self,
        user_id: int,
        chapter_slug: str
    ) -> bool:
        """
        Verifica si el usuario completó un capítulo.

        Args:
            user_id: ID del usuario
            chapter_slug: Slug del capítulo

        Returns:
            True si completó el capítulo
        """
        completion = await self.get_chapter_completion(user_id, chapter_slug)
        return completion is not None

    async def get_completed_chapters(
        self,
        user_id: int
    ) -> List[ChapterCompletion]:
        """
        Obtiene todos los capítulos completados por un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Lista de completaciones
        """
        stmt = (
            select(ChapterCompletion)
            .where(ChapterCompletion.user_id == user_id)
            .order_by(ChapterCompletion.completed_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    # ========================================
    # LÍMITES DIARIOS
    # ========================================

    async def get_or_create_daily_limit(
        self,
        user_id: int
    ) -> DailyNarrativeLimit:
        """
        Obtiene o crea límites diarios para usuario.

        Si el registro existe pero es de otro día, resetea contadores.

        Args:
            user_id: ID del usuario

        Returns:
            Registro de límites diarios
        """
        stmt = select(DailyNarrativeLimit).where(
            DailyNarrativeLimit.user_id == user_id
        )
        result = await self._session.execute(stmt)
        limit = result.scalar_one_or_none()

        today = datetime.utcnow().date()

        if limit is None:
            # Crear nuevo
            limit = DailyNarrativeLimit(
                user_id=user_id,
                limit_date=datetime.utcnow(),
                fragments_viewed=0,
                decisions_made=0,
                challenges_attempted=0
            )
            self._session.add(limit)
        elif limit.limit_date.date() != today:
            # Resetear para nuevo día
            limit.limit_date = datetime.utcnow()
            limit.fragments_viewed = 0
            limit.decisions_made = 0
            limit.challenges_attempted = 0
            logger.debug(f"Reset límites diarios: user={user_id}")

        await self._session.flush()
        return limit

    async def increment_fragments_viewed(
        self,
        user_id: int
    ) -> tuple[int, int]:
        """
        Incrementa contador de fragmentos vistos.

        Args:
            user_id: ID del usuario

        Returns:
            Tupla (fragmentos_vistos, máximo_permitido)
        """
        limit = await self.get_or_create_daily_limit(user_id)
        limit.fragments_viewed += 1
        await self._session.flush()

        max_allowed = limit.max_fragments_per_day or 999  # None = sin límite
        return limit.fragments_viewed, max_allowed

    async def increment_decisions_made(
        self,
        user_id: int
    ) -> tuple[int, int]:
        """
        Incrementa contador de decisiones tomadas.

        Args:
            user_id: ID del usuario

        Returns:
            Tupla (decisiones_tomadas, máximo_permitido)
        """
        limit = await self.get_or_create_daily_limit(user_id)
        limit.decisions_made += 1
        await self._session.flush()

        max_allowed = limit.max_decisions_per_day or 999
        return limit.decisions_made, max_allowed

    async def check_daily_limit(
        self,
        user_id: int,
        limit_type: str = "fragments"
    ) -> tuple[bool, int, int]:
        """
        Verifica si el usuario alcanzó su límite diario.

        Args:
            user_id: ID del usuario
            limit_type: "fragments" o "decisions"

        Returns:
            Tupla (puede_continuar, usado, máximo)
        """
        limit = await self.get_or_create_daily_limit(user_id)

        if limit_type == "fragments":
            used = limit.fragments_viewed
            max_limit = limit.max_fragments_per_day
        else:
            used = limit.decisions_made
            max_limit = limit.max_decisions_per_day

        if max_limit is None:
            return True, used, 999

        return used < max_limit, used, max_limit

    # ========================================
    # ESTADÍSTICAS
    # ========================================

    async def get_user_stats(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas de engagement del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Diccionario con estadísticas
        """
        visits = await self.get_all_visits(user_id, limit=1000)
        completions = await self.get_completed_chapters(user_id)

        total_time = sum(v.total_time_seconds for v in visits)
        total_visits = sum(v.visit_count for v in visits)

        return {
            "fragments_discovered": len(visits),
            "total_visits": total_visits,
            "total_time_seconds": total_time,
            "total_time_formatted": self._format_time(total_time),
            "chapters_completed": len(completions),
            "completed_chapters": [c.chapter_slug for c in completions],
            "most_visited": max(visits, key=lambda v: v.visit_count).fragment_key if visits else None,
        }

    def _format_time(self, seconds: int) -> str:
        """Formatea segundos a string legible."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m {seconds % 60}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
