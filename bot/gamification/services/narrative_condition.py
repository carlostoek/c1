"""
Servicio para verificar condiciones narrativas en el sistema de gamificación.

Permite usar progreso narrativo como condiciones de desbloqueo para:
- Misiones
- Recompensas
- Niveles
- Items de tienda
"""
import logging
from typing import Dict, Any, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class NarrativeConditionService:
    """
    Servicio que verifica condiciones basadas en progreso narrativo.

    Condiciones soportadas:
    - narrative_chapter: Usuario completó capítulo específico
    - narrative_fragment: Usuario llegó a fragmento específico
    - narrative_decision: Usuario tomó decisión específica
    - archetype: Usuario tiene arquetipo específico
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa servicio.

        Args:
            session: Sesión async de SQLAlchemy
        """
        self._session = session
        self._progress_service = None

    async def _get_progress_service(self):
        """Lazy load del ProgressService."""
        if self._progress_service is None:
            try:
                from bot.narrative.services.progress import ProgressService
                self._progress_service = ProgressService(self._session)
            except ImportError:
                logger.warning("Módulo narrativa no disponible")
                return None
        return self._progress_service

    async def check_condition(
        self,
        user_id: int,
        condition: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Verifica si usuario cumple una condición narrativa.

        Args:
            user_id: ID del usuario
            condition: Diccionario con tipo y parámetros de condición
                {
                    "type": "narrative_chapter" | "narrative_fragment" |
                            "narrative_decision" | "archetype" | "multiple",
                    ...parámetros específicos...
                }

        Returns:
            Tuple[bool, str]: (cumple_condición, mensaje)
        """
        condition_type = condition.get("type")

        if condition_type == "narrative_chapter":
            return await self._check_chapter_completed(user_id, condition)

        elif condition_type == "narrative_fragment":
            return await self._check_fragment_visited(user_id, condition)

        elif condition_type == "narrative_decision":
            return await self._check_decision_taken(user_id, condition)

        elif condition_type == "archetype":
            return await self._check_archetype(user_id, condition)

        elif condition_type == "multiple":
            return await self._check_multiple_conditions(user_id, condition)

        return False, f"Tipo de condición no soportado: {condition_type}"

    async def _check_chapter_completed(
        self,
        user_id: int,
        condition: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Verifica si usuario completó un capítulo."""
        chapter_slug = condition.get("chapter_slug")
        if not chapter_slug:
            return False, "Falta chapter_slug en condición"

        progress_service = await self._get_progress_service()
        if not progress_service:
            return False, "Módulo narrativa no disponible"

        try:
            completed = await progress_service.has_completed_chapter(
                user_id=user_id,
                chapter_slug=chapter_slug
            )

            if completed:
                return True, f"Capítulo '{chapter_slug}' completado"
            return False, f"Aún no has completado el capítulo '{chapter_slug}'"

        except Exception as e:
            logger.error(f"Error verificando capítulo: {e}")
            return False, f"Error al verificar: {str(e)}"

    async def _check_fragment_visited(
        self,
        user_id: int,
        condition: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Verifica si usuario visitó un fragmento."""
        fragment_key = condition.get("fragment_key")
        if not fragment_key:
            return False, "Falta fragment_key en condición"

        progress_service = await self._get_progress_service()
        if not progress_service:
            return False, "Módulo narrativa no disponible"

        try:
            visited = await progress_service.has_visited_fragment(
                user_id=user_id,
                fragment_key=fragment_key
            )

            if visited:
                return True, f"Fragmento '{fragment_key}' visitado"
            return False, f"Aún no has llegado al fragmento '{fragment_key}'"

        except Exception as e:
            logger.error(f"Error verificando fragmento: {e}")
            return False, f"Error al verificar: {str(e)}"

    async def _check_decision_taken(
        self,
        user_id: int,
        condition: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Verifica si usuario tomó una decisión específica."""
        decision_key = condition.get("decision_key")
        if not decision_key:
            return False, "Falta decision_key en condición"

        progress_service = await self._get_progress_service()
        if not progress_service:
            return False, "Módulo narrativa no disponible"

        try:
            taken = await progress_service.has_taken_decision(
                user_id=user_id,
                decision_key=decision_key
            )

            if taken:
                return True, f"Decisión '{decision_key}' tomada"
            return False, f"Aún no has tomado la decisión '{decision_key}'"

        except Exception as e:
            logger.error(f"Error verificando decisión: {e}")
            return False, f"Error al verificar: {str(e)}"

    async def _check_archetype(
        self,
        user_id: int,
        condition: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Verifica si usuario tiene un arquetipo específico."""
        required_archetype = condition.get("archetype")
        if not required_archetype:
            return False, "Falta archetype en condición"

        progress_service = await self._get_progress_service()
        if not progress_service:
            return False, "Módulo narrativa no disponible"

        try:
            progress = await progress_service.get_progress(user_id)
            if not progress:
                return False, "No has iniciado la narrativa"

            user_archetype = progress.detected_archetype.value \
                if hasattr(progress.detected_archetype, 'value') \
                else str(progress.detected_archetype)

            if user_archetype == required_archetype:
                return True, f"Arquetipo '{required_archetype}' detectado"
            return False, f"Tu arquetipo es '{user_archetype}', se requiere '{required_archetype}'"

        except Exception as e:
            logger.error(f"Error verificando arquetipo: {e}")
            return False, f"Error al verificar: {str(e)}"

    async def _check_multiple_conditions(
        self,
        user_id: int,
        condition: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Verifica múltiples condiciones (todas deben cumplirse)."""
        conditions = condition.get("conditions", [])
        if not conditions:
            return False, "Lista de condiciones vacía"

        failed_messages = []

        for idx, sub_condition in enumerate(conditions):
            met, message = await self.check_condition(user_id, sub_condition)
            if not met:
                failed_messages.append(message)

        if failed_messages:
            return False, "; ".join(failed_messages)

        return True, "Todas las condiciones cumplidas"

    async def get_user_narrative_status(
        self,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene resumen del estado narrativo del usuario.

        Útil para mostrar en el wizard de misiones.

        Args:
            user_id: ID del usuario

        Returns:
            Dict con estado o None si no disponible
        """
        progress_service = await self._get_progress_service()
        if not progress_service:
            return None

        try:
            progress = await progress_service.get_progress(user_id)
            if not progress:
                return {
                    "has_started": False,
                    "archetype": None,
                    "chapters_completed": 0,
                    "current_fragment": None
                }

            return {
                "has_started": True,
                "archetype": progress.detected_archetype.value
                    if hasattr(progress.detected_archetype, 'value')
                    else str(progress.detected_archetype),
                "chapters_completed": progress.chapters_completed,
                "current_fragment": progress.current_fragment_key,
                "total_decisions": progress.total_decisions
            }

        except Exception as e:
            logger.error(f"Error obteniendo estado narrativo: {e}")
            return None

    async def get_available_chapters(self) -> list:
        """
        Obtiene lista de capítulos disponibles para condiciones.

        Returns:
            Lista de dict con slug y name de cada capítulo
        """
        try:
            from bot.narrative.services.chapter import ChapterService
            chapter_service = ChapterService(self._session)
            chapters = await chapter_service.get_all_chapters(active_only=True)

            return [
                {"slug": ch.slug, "name": ch.name}
                for ch in chapters
            ]

        except ImportError:
            logger.warning("ChapterService no disponible")
            return []
        except Exception as e:
            logger.error(f"Error obteniendo capítulos: {e}")
            return []
