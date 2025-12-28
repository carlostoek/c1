"""
Servicio de variantes de fragmentos.

Gestiona las versiones alternativas de contenido de fragmentos
basadas en el contexto del usuario (visitas, pistas, arquetipo, etc.).
"""
import logging
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from bot.narrative.database.models_immersive import FragmentVariant, UserFragmentVisit
from bot.narrative.database.models import NarrativeFragment
from bot.narrative.database.enums import VariantConditionType, ArchetypeType

logger = logging.getLogger(__name__)


class VariantService:
    """
    Servicio para gestión de variantes de fragmentos.

    Cada fragmento puede tener múltiples variantes que se activan
    dependiendo del contexto del usuario:
    - Número de visitas al fragmento
    - Posesión de pistas específicas
    - Arquetipo del usuario
    - Hora del día
    - Días desde que inició la historia
    - Decisiones tomadas previamente
    - Capítulos completados
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio.

        Args:
            session: Sesión async de SQLAlchemy
        """
        self._session = session

    # ========================================
    # RESOLUCIÓN DE VARIANTES
    # ========================================

    async def resolve_variant(
        self,
        fragment_key: str,
        user_context: Dict[str, Any]
    ) -> Optional[FragmentVariant]:
        """
        Resuelve qué variante aplicar para un fragmento dado el contexto.

        Las variantes se evalúan en orden de prioridad (mayor primero).
        La primera variante cuya condición se cumpla es la que se aplica.

        Args:
            fragment_key: Key del fragmento
            user_context: Contexto del usuario con:
                - user_id: int
                - visit_count: int (visitas a este fragmento)
                - clues: List[str] (slugs de pistas que tiene)
                - archetype: str (arquetipo detectado)
                - decisions: List[str] (fragment_keys donde tomó decisiones)
                - completed_chapters: List[str] (slugs de capítulos completados)
                - started_at: datetime (cuándo inició la historia)

        Returns:
            Variante activa o None si ninguna aplica
        """
        variants = await self.get_variants_for_fragment(fragment_key)

        if not variants:
            return None

        # Evaluar en orden de prioridad (mayor primero)
        for variant in sorted(variants, key=lambda v: v.priority, reverse=True):
            if await self._evaluate_condition(variant, user_context):
                logger.debug(f"Variante activa: {variant.variant_key} para {fragment_key}")
                return variant

        return None

    async def apply_variant(
        self,
        fragment: NarrativeFragment,
        variant: Optional[FragmentVariant]
    ) -> Dict[str, Any]:
        """
        Aplica una variante a un fragmento, mezclando contenidos.

        Args:
            fragment: Fragmento base
            variant: Variante a aplicar (o None)

        Returns:
            Diccionario con el fragmento resultante
        """
        result = {
            "fragment_key": fragment.fragment_key,
            "title": fragment.title,
            "speaker": fragment.speaker,
            "content": fragment.content,
            "visual_hint": fragment.visual_hint,
            "media_file_id": fragment.media_file_id,
            "variant_applied": None,
            "additional_decisions": [],
        }

        if variant:
            # Aplicar overrides
            if variant.content_override:
                result["content"] = variant.content_override
            if variant.speaker_override:
                result["speaker"] = variant.speaker_override
            if variant.visual_hint_override:
                result["visual_hint"] = variant.visual_hint_override
            if variant.media_file_id_override:
                result["media_file_id"] = variant.media_file_id_override
            if variant.additional_decisions:
                try:
                    result["additional_decisions"] = json.loads(variant.additional_decisions)
                except json.JSONDecodeError:
                    pass

            result["variant_applied"] = variant.variant_key

        return result

    # ========================================
    # EVALUACIÓN DE CONDICIONES
    # ========================================

    async def _evaluate_condition(
        self,
        variant: FragmentVariant,
        context: Dict[str, Any]
    ) -> bool:
        """
        Evalúa si una condición de variante se cumple.

        Args:
            variant: Variante a evaluar
            context: Contexto del usuario

        Returns:
            True si la condición se cumple
        """
        condition_type = variant.condition_type
        value = variant.condition_value

        try:
            if condition_type == VariantConditionType.FIRST_VISIT:
                # Especial: primera visita
                return context.get("visit_count", 0) == 1

            elif condition_type == VariantConditionType.RETURN_VISIT:
                # Visita de retorno (>= 2)
                return context.get("visit_count", 0) >= 2

            elif condition_type == VariantConditionType.VISIT_COUNT:
                # Número exacto o mínimo de visitas
                # Formato: ">=3" o "3" o "==3"
                return self._compare_value(context.get("visit_count", 0), value)

            elif condition_type == VariantConditionType.HAS_CLUE:
                # Tiene pista específica
                clues = context.get("clues", [])
                return value in clues

            elif condition_type == VariantConditionType.ARCHETYPE:
                # Arquetipo específico
                return context.get("archetype", "unknown") == value

            elif condition_type == VariantConditionType.TIME_OF_DAY:
                # Hora del día: morning (6-12), afternoon (12-18), night (18-6)
                hour = datetime.utcnow().hour
                if value == "morning":
                    return 6 <= hour < 12
                elif value == "afternoon":
                    return 12 <= hour < 18
                elif value == "night":
                    return hour >= 18 or hour < 6
                return False

            elif condition_type == VariantConditionType.DAYS_SINCE_START:
                # Días desde inicio de historia
                started_at = context.get("started_at")
                if started_at:
                    days = (datetime.utcnow() - started_at).days
                    return self._compare_value(days, value)
                return False

            elif condition_type == VariantConditionType.DECISION_TAKEN:
                # Tomó decisión en fragmento específico
                decisions = context.get("decisions", [])
                return value in decisions

            elif condition_type == VariantConditionType.CHAPTER_COMPLETE:
                # Completó capítulo específico
                completed = context.get("completed_chapters", [])
                return value in completed

            else:
                logger.warning(f"Tipo de condición desconocido: {condition_type}")
                return False

        except Exception as e:
            logger.error(f"Error evaluando condición {condition_type}: {e}")
            return False

    def _compare_value(self, actual: int, expected: str) -> bool:
        """
        Compara un valor con una expresión.

        Soporta: ">=3", "<=3", "==3", ">3", "<3", "3" (equivale a >=)
        """
        expected = expected.strip()

        try:
            if expected.startswith(">="):
                return actual >= int(expected[2:])
            elif expected.startswith("<="):
                return actual <= int(expected[2:])
            elif expected.startswith("=="):
                return actual == int(expected[2:])
            elif expected.startswith(">"):
                return actual > int(expected[1:])
            elif expected.startswith("<"):
                return actual < int(expected[1:])
            else:
                # Por defecto, >=
                return actual >= int(expected)
        except ValueError:
            return False

    # ========================================
    # CRUD DE VARIANTES
    # ========================================

    async def get_variants_for_fragment(
        self,
        fragment_key: str,
        active_only: bool = True
    ) -> List[FragmentVariant]:
        """
        Obtiene todas las variantes de un fragmento.

        Args:
            fragment_key: Key del fragmento
            active_only: Solo variantes activas

        Returns:
            Lista de variantes
        """
        stmt = select(FragmentVariant).where(
            FragmentVariant.fragment_key == fragment_key
        )
        if active_only:
            stmt = stmt.where(FragmentVariant.is_active == True)

        stmt = stmt.order_by(FragmentVariant.priority.desc())

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_variant(
        self,
        fragment_key: str,
        variant_key: str,
        condition_type: VariantConditionType,
        condition_value: str,
        priority: int = 0,
        content_override: Optional[str] = None,
        speaker_override: Optional[str] = None,
        visual_hint_override: Optional[str] = None,
        additional_decisions: Optional[List[Dict]] = None
    ) -> FragmentVariant:
        """
        Crea una nueva variante para un fragmento.

        Args:
            fragment_key: Key del fragmento
            variant_key: Identificador de la variante
            condition_type: Tipo de condición
            condition_value: Valor de la condición
            priority: Prioridad (mayor = evaluar primero)
            content_override: Contenido alternativo
            speaker_override: Hablante alternativo
            visual_hint_override: Visual hint alternativo
            additional_decisions: Decisiones adicionales (JSON)

        Returns:
            Variante creada
        """
        variant = FragmentVariant(
            fragment_key=fragment_key,
            variant_key=variant_key,
            condition_type=condition_type,
            condition_value=condition_value,
            priority=priority,
            content_override=content_override,
            speaker_override=speaker_override,
            visual_hint_override=visual_hint_override,
            additional_decisions=json.dumps(additional_decisions) if additional_decisions else None,
            is_active=True,
            created_at=datetime.utcnow()
        )
        self._session.add(variant)
        await self._session.flush()

        logger.info(f"Variante creada: {variant_key} para {fragment_key}")
        return variant

    async def get_variant(
        self,
        fragment_key: str,
        variant_key: str
    ) -> Optional[FragmentVariant]:
        """
        Obtiene una variante específica.

        Args:
            fragment_key: Key del fragmento
            variant_key: Key de la variante

        Returns:
            Variante o None
        """
        stmt = select(FragmentVariant).where(
            and_(
                FragmentVariant.fragment_key == fragment_key,
                FragmentVariant.variant_key == variant_key
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_variant(
        self,
        fragment_key: str,
        variant_key: str,
        **updates
    ) -> Optional[FragmentVariant]:
        """
        Actualiza una variante.

        Args:
            fragment_key: Key del fragmento
            variant_key: Key de la variante
            **updates: Campos a actualizar

        Returns:
            Variante actualizada o None
        """
        variant = await self.get_variant(fragment_key, variant_key)
        if variant is None:
            return None

        for key, value in updates.items():
            if hasattr(variant, key):
                if key == "additional_decisions" and isinstance(value, list):
                    value = json.dumps(value)
                setattr(variant, key, value)

        await self._session.flush()
        return variant

    async def delete_variant(
        self,
        fragment_key: str,
        variant_key: str
    ) -> bool:
        """
        Elimina una variante.

        Args:
            fragment_key: Key del fragmento
            variant_key: Key de la variante

        Returns:
            True si se eliminó
        """
        stmt = delete(FragmentVariant).where(
            and_(
                FragmentVariant.fragment_key == fragment_key,
                FragmentVariant.variant_key == variant_key
            )
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0

    async def toggle_variant(
        self,
        fragment_key: str,
        variant_key: str
    ) -> Optional[bool]:
        """
        Activa/desactiva una variante.

        Args:
            fragment_key: Key del fragmento
            variant_key: Key de la variante

        Returns:
            Nuevo estado o None si no existe
        """
        variant = await self.get_variant(fragment_key, variant_key)
        if variant is None:
            return None

        variant.is_active = not variant.is_active
        await self._session.flush()
        return variant.is_active

    # ========================================
    # UTILIDADES
    # ========================================

    async def get_fragment_with_variant(
        self,
        fragment_key: str,
        user_context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene un fragmento con su variante aplicada.

        Combina la obtención del fragmento, resolución de variante
        y aplicación del contenido.

        Args:
            fragment_key: Key del fragmento
            user_context: Contexto del usuario

        Returns:
            Fragmento con variante aplicada o None
        """
        # Obtener fragmento base
        stmt = select(NarrativeFragment).where(
            NarrativeFragment.fragment_key == fragment_key
        )
        result = await self._session.execute(stmt)
        fragment = result.scalar_one_or_none()

        if fragment is None:
            return None

        # Resolver variante
        variant = await self.resolve_variant(fragment_key, user_context)

        # Aplicar variante
        return await self.apply_variant(fragment, variant)

    async def build_user_context(
        self,
        user_id: int,
        fragment_key: str
    ) -> Dict[str, Any]:
        """
        Construye el contexto del usuario para evaluación de variantes.

        Este método debería ser llamado por el handler antes de
        resolver variantes. Requiere acceso a otros servicios.

        Args:
            user_id: ID del usuario
            fragment_key: Key del fragmento actual

        Returns:
            Contexto del usuario
        """
        # Este es un stub - el contexto completo se construye
        # en el handler/orchestrator que tiene acceso a todos los servicios
        context = {
            "user_id": user_id,
            "visit_count": 0,
            "clues": [],
            "archetype": "unknown",
            "decisions": [],
            "completed_chapters": [],
            "started_at": None,
        }

        # Obtener visitas a este fragmento
        stmt = select(UserFragmentVisit).where(
            and_(
                UserFragmentVisit.user_id == user_id,
                UserFragmentVisit.fragment_key == fragment_key
            )
        )
        result = await self._session.execute(stmt)
        visit = result.scalar_one_or_none()
        if visit:
            context["visit_count"] = visit.visit_count

        return context
