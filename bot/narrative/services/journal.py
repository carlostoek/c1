"""
Servicio del Diario de Viaje.

Proporciona información de navegación y progreso narrativo:
- Estado de fragmentos (visitado/bloqueado/disponible)
- Progreso por capítulo
- Pistas encontradas y faltantes
- Fragmentos accesibles para navegación rápida
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from sqlalchemy import select, and_, func, case, outerjoin
from sqlalchemy.ext.asyncio import AsyncSession

from bot.narrative.database.models import (
    NarrativeChapter,
    NarrativeFragment,
    FragmentRequirement,
    UserNarrativeProgress,
)
from bot.narrative.database.models_immersive import (
    UserFragmentVisit,
    ChapterCompletion,
)
from bot.narrative.database.enums import ChapterType

logger = logging.getLogger(__name__)


class FragmentStatus:
    """Estados posibles de un fragmento para el usuario."""
    VISITED = "visited"      # Ya visitado
    AVAILABLE = "available"  # Accesible (requisitos cumplidos)
    LOCKED = "locked"        # Bloqueado (requisitos no cumplidos)
    CURRENT = "current"      # Posición actual del usuario


class JournalService:
    """
    Servicio para el Diario de Viaje del usuario.

    Proporciona:
    - Vista de progreso por capítulo
    - Estado de fragmentos
    - Navegación rápida
    - Resumen de pistas
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio.

        Args:
            session: Sesión async de SQLAlchemy
        """
        self._session = session

    # ========================================
    # PROGRESO POR CAPÍTULO
    # ========================================

    async def get_chapter_progress(
        self,
        user_id: int,
        chapter_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene progreso del usuario por capítulo.

        Args:
            user_id: ID del usuario
            chapter_id: ID de capítulo específico (opcional)

        Returns:
            Lista de capítulos con progreso
        """
        # Optimized query using GROUP BY and JOINs to avoid N+1 queries
        # Build subquery for fragment counts
        frag_counts = (
            select(
                NarrativeFragment.chapter_id,
                func.count(NarrativeFragment.id).label('total_fragments')
            )
            .where(NarrativeFragment.is_active == True)
            .group_by(NarrativeFragment.chapter_id)
            .subquery()
        )

        # Build subquery for visited fragment counts
        visit_counts = (
            select(
                NarrativeFragment.chapter_id,
                func.count(func.distinct(UserFragmentVisit.fragment_key)).label('visited_fragments')
            )
            .select_from(UserFragmentVisit)
            .join(
                NarrativeFragment,
                UserFragmentVisit.fragment_key == NarrativeFragment.fragment_key
            )
            .where(UserFragmentVisit.user_id == user_id)
            .group_by(NarrativeFragment.chapter_id)
            .subquery()
        )

        # Main query joining everything together
        stmt = (
            select(
                NarrativeChapter,
                func.coalesce(frag_counts.c.total_fragments, 0).label('total_fragments'),
                func.coalesce(visit_counts.c.visited_fragments, 0).label('visited_fragments'),
                ChapterCompletion.completed_at
            )
            .outerjoin(frag_counts, NarrativeChapter.id == frag_counts.c.chapter_id)
            .outerjoin(visit_counts, NarrativeChapter.id == visit_counts.c.chapter_id)
            .outerjoin(
                ChapterCompletion,
                and_(
                    ChapterCompletion.user_id == user_id,
                    ChapterCompletion.chapter_slug == NarrativeChapter.slug
                )
            )
            .where(NarrativeChapter.is_active == True)
            .order_by(NarrativeChapter.order)
        )

        if chapter_id:
            stmt = stmt.where(NarrativeChapter.id == chapter_id)

        result = await self._session.execute(stmt)
        rows = result.all()

        progress_list = []
        for row in rows:
            chapter = row[0]
            total_fragments = row[1]
            visited_fragments = row[2]
            completed_at = row[3]

            progress_list.append({
                "chapter_id": chapter.id,
                "chapter_slug": chapter.slug,
                "chapter_name": chapter.name,
                "chapter_type": chapter.chapter_type.value,
                "description": chapter.description,
                "total_fragments": total_fragments,
                "visited_fragments": visited_fragments,
                "completion_percent": round(
                    (visited_fragments / total_fragments * 100) if total_fragments > 0 else 0,
                    1
                ),
                "is_completed": completed_at is not None,
                "completed_at": completed_at,
            })

        return progress_list

    async def _get_chapter_completion(
        self,
        user_id: int,
        chapter_slug: str
    ) -> Optional[ChapterCompletion]:
        """Obtiene registro de completación de capítulo."""
        stmt = select(ChapterCompletion).where(
            and_(
                ChapterCompletion.user_id == user_id,
                ChapterCompletion.chapter_slug == chapter_slug
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    # ========================================
    # ESTADO DE FRAGMENTOS
    # ========================================

    async def get_fragment_status(
        self,
        user_id: int,
        fragment_key: str
    ) -> str:
        """
        Obtiene el estado de un fragmento para el usuario.

        Args:
            user_id: ID del usuario
            fragment_key: Key del fragmento

        Returns:
            Estado: visited, available, locked, current
        """
        # Verificar si es posición actual
        progress = await self._get_user_progress(user_id)
        if progress and progress.current_fragment_key == fragment_key:
            return FragmentStatus.CURRENT

        # Verificar si visitado
        if await self._has_visited(user_id, fragment_key):
            return FragmentStatus.VISITED

        # Verificar requisitos
        is_accessible = await self._check_fragment_accessible(user_id, fragment_key)
        if is_accessible:
            return FragmentStatus.AVAILABLE

        return FragmentStatus.LOCKED

    async def get_fragments_by_status(
        self,
        user_id: int,
        chapter_id: int,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene fragmentos de un capítulo agrupados por estado.

        Args:
            user_id: ID del usuario
            chapter_id: ID del capítulo
            status: Filtrar por estado específico (opcional)

        Returns:
            Lista de fragmentos con su estado
        """
        # Obtener fragmentos del capítulo
        stmt = select(NarrativeFragment).where(
            and_(
                NarrativeFragment.chapter_id == chapter_id,
                NarrativeFragment.is_active == True
            )
        ).order_by(NarrativeFragment.order)

        result = await self._session.execute(stmt)
        fragments = list(result.scalars().all())

        fragment_list = []
        for fragment in fragments:
            frag_status = await self.get_fragment_status(user_id, fragment.fragment_key)

            if status and frag_status != status:
                continue

            # Obtener info de visita si existe
            visit = await self._get_visit(user_id, fragment.fragment_key)

            fragment_list.append({
                "fragment_key": fragment.fragment_key,
                "title": fragment.title,
                "speaker": fragment.speaker,
                "is_entry_point": fragment.is_entry_point,
                "is_ending": fragment.is_ending,
                "status": frag_status,
                "visit_count": visit.visit_count if visit else 0,
                "last_visit": visit.last_visit if visit else None,
                "time_spent": visit.total_time_seconds if visit else 0,
            })

        return fragment_list

    async def get_accessible_fragments(
        self,
        user_id: int,
        chapter_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene fragmentos accesibles para navegación rápida.

        Args:
            user_id: ID del usuario
            chapter_id: Filtrar por capítulo (opcional)

        Returns:
            Lista de fragmentos visitados/disponibles
        """
        # Obtener todos los fragmentos visitados
        stmt = (
            select(UserFragmentVisit)
            .where(UserFragmentVisit.user_id == user_id)
            .order_by(UserFragmentVisit.last_visit.desc())
        )
        result = await self._session.execute(stmt)
        visits = list(result.scalars().all())

        accessible = []
        for visit in visits:
            # Obtener info del fragmento
            frag_stmt = select(NarrativeFragment).where(
                NarrativeFragment.fragment_key == visit.fragment_key
            )
            frag_result = await self._session.execute(frag_stmt)
            fragment = frag_result.scalar_one_or_none()

            if not fragment or not fragment.is_active:
                continue

            if chapter_id and fragment.chapter_id != chapter_id:
                continue

            # Obtener nombre del capítulo
            chapter = await self._session.get(NarrativeChapter, fragment.chapter_id)

            accessible.append({
                "fragment_key": fragment.fragment_key,
                "title": fragment.title,
                "speaker": fragment.speaker,
                "chapter_id": fragment.chapter_id,
                "chapter_name": chapter.name if chapter else "Desconocido",
                "visit_count": visit.visit_count,
                "last_visit": visit.last_visit,
            })

        return accessible

    async def get_blocked_fragments_with_reasons(
        self,
        user_id: int,
        chapter_id: int
    ) -> List[Dict[str, Any]]:
        """
        Obtiene fragmentos bloqueados con sus razones.

        Args:
            user_id: ID del usuario
            chapter_id: ID del capítulo

        Returns:
            Lista de fragmentos bloqueados con razones
        """
        fragments = await self.get_fragments_by_status(
            user_id, chapter_id, status=FragmentStatus.LOCKED
        )

        blocked_list = []
        for frag in fragments:
            # Obtener requisitos del fragmento
            reasons = await self._get_blocking_reasons(user_id, frag["fragment_key"])

            blocked_list.append({
                **frag,
                "blocking_reasons": reasons,
            })

        return blocked_list

    # ========================================
    # RESUMEN DE PISTAS
    # ========================================

    async def get_clues_summary(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Obtiene resumen de pistas del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Resumen con pistas encontradas y faltantes
        """
        from bot.narrative.services.clue import ClueService

        clue_service = ClueService(self._session)
        progress = await clue_service.get_clue_progress(user_id)

        return progress

    # ========================================
    # HELPERS PRIVADOS
    # ========================================

    async def _get_user_progress(
        self,
        user_id: int
    ) -> Optional[UserNarrativeProgress]:
        """Obtiene progreso del usuario."""
        stmt = select(UserNarrativeProgress).where(
            UserNarrativeProgress.user_id == user_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def _has_visited(
        self,
        user_id: int,
        fragment_key: str
    ) -> bool:
        """Verifica si el usuario visitó un fragmento."""
        stmt = select(UserFragmentVisit).where(
            and_(
                UserFragmentVisit.user_id == user_id,
                UserFragmentVisit.fragment_key == fragment_key
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def _get_visit(
        self,
        user_id: int,
        fragment_key: str
    ) -> Optional[UserFragmentVisit]:
        """Obtiene registro de visita."""
        stmt = select(UserFragmentVisit).where(
            and_(
                UserFragmentVisit.user_id == user_id,
                UserFragmentVisit.fragment_key == fragment_key
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def _check_fragment_accessible(
        self,
        user_id: int,
        fragment_key: str
    ) -> bool:
        """
        Verifica si el fragmento es accesible para el usuario.

        Utiliza RequirementsService para validar todos los requisitos.
        """
        # Usar RequirementsService para validar requisitos
        from bot.narrative.services.requirements import RequirementsService

        requirements_service = RequirementsService(self._session)
        can_access, _ = await requirements_service.can_access_fragment(
            user_id=user_id,
            fragment_key=fragment_key
        )

        return can_access

    async def _get_blocking_reasons(
        self,
        user_id: int,
        fragment_key: str
    ) -> List[str]:
        """Obtiene razones de bloqueo de un fragmento."""
        reasons = []

        # Obtener fragmento
        stmt = select(NarrativeFragment).where(
            NarrativeFragment.fragment_key == fragment_key
        )
        result = await self._session.execute(stmt)
        fragment = result.scalar_one_or_none()

        if not fragment:
            return ["Fragmento no encontrado"]

        # Obtener requisitos
        req_stmt = select(FragmentRequirement).where(
            FragmentRequirement.fragment_id == fragment.id
        )
        req_result = await self._session.execute(req_stmt)
        requirements = list(req_result.scalars().all())

        for req in requirements:
            # Formatear razón según tipo
            reason = f"Requiere: {req.requirement_type.value}"
            if req.requirement_value:
                reason += f" ({req.requirement_value})"
            reasons.append(reason)

        return reasons if reasons else ["Requisitos desconocidos"]

    # ========================================
    # ESTADÍSTICAS GENERALES
    # ========================================

    async def get_journey_stats(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas completas del viaje del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Estadísticas completas
        """
        # Capítulos
        chapter_progress = await self.get_chapter_progress(user_id)
        total_chapters = len(chapter_progress)
        completed_chapters = sum(1 for c in chapter_progress if c["is_completed"])

        # Fragmentos visitados
        visit_stmt = select(func.count()).where(
            UserFragmentVisit.user_id == user_id
        )
        visit_result = await self._session.execute(visit_stmt)
        fragments_visited = visit_result.scalar() or 0

        # Tiempo total
        time_stmt = select(func.sum(UserFragmentVisit.total_time_seconds)).where(
            UserFragmentVisit.user_id == user_id
        )
        time_result = await self._session.execute(time_stmt)
        total_time = time_result.scalar() or 0

        # Pistas
        clues_summary = await self.get_clues_summary(user_id)

        return {
            "total_chapters": total_chapters,
            "completed_chapters": completed_chapters,
            "chapter_progress_percent": round(
                (completed_chapters / total_chapters * 100) if total_chapters > 0 else 0,
                1
            ),
            "fragments_visited": fragments_visited,
            "total_time_seconds": total_time,
            "total_time_formatted": self._format_time(total_time),
            "clues_found": clues_summary.get("found_clues", 0),
            "clues_total": clues_summary.get("total_clues", 0),
            "clue_completion_percent": clues_summary.get("completion_percent", 0),
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
