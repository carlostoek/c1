"""
Servicio de procesamiento de decisiones del usuario.

Maneja la lógica de tomar decisiones, validaciones, costos/recompensas,
y registro en historial.
"""
import logging
from typing import List, Tuple, Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.narrative.database import (
    FragmentDecision,
    UserDecisionHistory,
    NarrativeFragment,
)

logger = logging.getLogger(__name__)


class DecisionService:
    """
    Servicio de procesamiento de decisiones.

    Métodos CRUD:
    - create_decision: Crear nueva decisión
    - update_decision: Actualizar decisión existente
    - delete_decision: Eliminar decisión (soft delete)
    - get_decision_by_id: Obtener decisión por ID
    - get_decisions_by_fragment: Obtener decisiones de un fragmento

    Métodos de Procesamiento:
    - get_available_decisions: Obtener decisiones disponibles
    - process_decision: Procesar decisión del usuario
    - record_decision: Registrar decisión en historial
    - can_afford_decision: Verificar si usuario puede pagar decisión
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa servicio.

        Args:
            session: Sesión async de SQLAlchemy
        """
        self._session = session

    async def get_available_decisions(
        self,
        fragment_key: str,
        user_id: Optional[int] = None
    ) -> List[FragmentDecision]:
        """
        Obtiene decisiones disponibles para un fragmento.

        Args:
            fragment_key: Key del fragmento
            user_id: ID del usuario (para validar besitos si aplica)

        Returns:
            Lista de decisiones disponibles
        """
        from bot.narrative.services.fragment import FragmentService

        fragment_service = FragmentService(self._session)
        fragment = await fragment_service.get_fragment(
            fragment_key,
            load_decisions=True
        )

        if not fragment:
            logger.warning(f"⚠️ Fragmento no encontrado: {fragment_key}")
            return []

        # Filtrar decisiones activas
        decisions = [d for d in fragment.decisions if d.is_active]

        # Ordenar por order
        decisions.sort(key=lambda d: d.order)

        logger.debug(
            f"📋 Decisiones disponibles para {fragment_key}: {len(decisions)}"
        )

        return decisions

    async def process_decision(
        self,
        user_id: int,
        decision_id: int,
        response_time: Optional[int] = None
    ) -> Tuple[bool, str, Optional[NarrativeFragment]]:
        """
        Procesa decisión del usuario.

        Este método:
        1. Valida que la decisión existe
        2. Verifica si hay costo en besitos (y si usuario puede pagar)
        3. Cobra besitos si aplica
        4. Otorga besitos si aplica
        5. Registra decisión en historial
        6. Actualiza progreso del usuario
        7. Retorna fragmento destino

        Args:
            user_id: ID del usuario
            decision_id: ID de la decisión tomada
            response_time: Tiempo de respuesta en segundos (para arquetipos)

        Returns:
            Tupla (success, message, next_fragment)
        """
        # Obtener decisión
        decision = await self.get_decision_by_id(decision_id)
        if not decision:
            return False, "❌ Decisión no válida", None

        # Verificar si está activa
        if not decision.is_active:
            return False, "❌ Esta decisión no está disponible", None

        # Verificar costo en besitos
        if decision.besitos_cost > 0:
            can_afford, balance = await self.can_afford_decision(user_id, decision)
            if not can_afford:
                return (
                    False,
                    f"❌ Necesitas {decision.besitos_cost} besitos (tienes {balance})",
                    None
                )

            # Cobrar besitos
            await self._deduct_besitos(user_id, decision.besitos_cost)
            logger.info(
                f"💰 Usuario {user_id} pagó {decision.besitos_cost} besitos"
            )

        # Otorgar besitos si aplica
        if decision.grants_besitos > 0:
            await self._grant_besitos(user_id, decision.grants_besitos)
            logger.info(
                f"💝 Usuario {user_id} recibió {decision.grants_besitos} besitos"
            )

        # Registrar decisión en historial
        await self.record_decision(
            user_id=user_id,
            decision=decision,
            response_time=response_time
        )

        # Actualizar progreso
        from bot.narrative.services.progress import ProgressService
        from bot.narrative.services.fragment import FragmentService

        progress_service = ProgressService(self._session)
        await progress_service.increment_decisions(user_id)

        # Obtener fragmento destino
        fragment_service = FragmentService(self._session)
        next_fragment = await fragment_service.get_fragment(
            decision.target_fragment_key,
            load_decisions=True
        )

        if not next_fragment:
            return (
                False,
                f"❌ Error: fragmento destino '{decision.target_fragment_key}' no existe",
                None
            )

        # Avanzar usuario al nuevo fragmento
        await progress_service.advance_to(
            user_id=user_id,
            fragment_key=next_fragment.fragment_key,
            chapter_id=next_fragment.chapter_id
        )

        # Establecer cooldown para fragmentos intensos
        await self._apply_fragment_cooldown(user_id, next_fragment)

        # Verificar si completó capítulo y aplicar cooldown
        if next_fragment.is_ending:
            await self._apply_chapter_completion_cooldown(user_id, next_fragment.chapter_id)

        logger.info(
            f"✅ Usuario {user_id} procesó decisión {decision_id} "
            f"→ {next_fragment.fragment_key}"
        )

        return True, "✅ Decisión procesada", next_fragment

    async def record_decision(
        self,
        user_id: int,
        decision: FragmentDecision,
        response_time: Optional[int] = None
    ) -> UserDecisionHistory:
        """
        Registra decisión en historial.

        Args:
            user_id: ID del usuario
            decision: Decisión tomada
            response_time: Tiempo de respuesta en segundos

        Returns:
            Registro de historial creado
        """
        # Obtener fragment_key del fragmento padre
        from bot.narrative.database import NarrativeFragment

        stmt = select(NarrativeFragment).where(
            NarrativeFragment.id == decision.fragment_id
        )
        result = await self._session.execute(stmt)
        fragment = result.scalar_one()

        history = UserDecisionHistory(
            user_id=user_id,
            fragment_key=fragment.fragment_key,
            decision_id=decision.id,
            response_time_seconds=response_time
        )

        self._session.add(history)
        await self._session.flush()
        await self._session.refresh(history)

        logger.debug(
            f"📝 Decisión registrada: user={user_id}, "
            f"fragment={fragment.fragment_key}, time={response_time}s"
        )

        return history

    async def get_decision_by_id(
        self,
        decision_id: int
    ) -> Optional[FragmentDecision]:
        """
        Obtiene decisión por ID.

        Args:
            decision_id: ID de la decisión

        Returns:
            Decisión o None si no existe
        """
        stmt = select(FragmentDecision).where(
            FragmentDecision.id == decision_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def can_afford_decision(
        self,
        user_id: int,
        decision: FragmentDecision
    ) -> Tuple[bool, int]:
        """
        Verifica si usuario puede pagar decisión.

        Args:
            user_id: ID del usuario
            decision: Decisión a validar

        Returns:
            Tupla (puede_pagar, balance_actual)
        """
        if decision.besitos_cost == 0:
            return True, 0

        # Obtener balance de besitos del usuario
        balance = await self._get_besitos_balance(user_id)

        can_afford = balance >= decision.besitos_cost

        return can_afford, balance

    async def _get_besitos_balance(self, user_id: int) -> int:
        """
        Obtiene balance de besitos del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Balance de besitos
        """
        try:
            from bot.gamification.services.container import get_container

            gamification = get_container()
            user_gamif = await gamification.user_gamification.get_or_create(user_id)
            return user_gamif.total_besitos
        except Exception as e:
            logger.error(f"❌ Error obteniendo balance de besitos: {e}")
            return 0

    async def _deduct_besitos(self, user_id: int, amount: int) -> None:
        """
        Deduce besitos del usuario.

        Args:
            user_id: ID del usuario
            amount: Cantidad a deducir
        """
        try:
            from bot.gamification.services.container import get_container
            from bot.gamification.database.enums import TransactionType

            gamification = get_container()
            await gamification.besito.deduct_besitos(
                user_id=user_id,
                amount=amount,
                reason="Decisión narrativa",
                transaction_type=TransactionType.PURCHASE
            )
        except Exception as e:
            logger.error(f"❌ Error deduciendo besitos: {e}")

    async def _grant_besitos(self, user_id: int, amount: int) -> None:
        """
        Otorga besitos al usuario.

        Args:
            user_id: ID del usuario
            amount: Cantidad a otorgar
        """
        try:
            from bot.gamification.services.container import get_container
            from bot.gamification.database.enums import TransactionType

            gamification = get_container()
            await gamification.besito.grant_besitos(
                user_id=user_id,
                amount=amount,
                reason="Recompensa de decisión narrativa",
                transaction_type=TransactionType.ADMIN_GRANT
            )
        except Exception as e:
            logger.error(f"❌ Error otorgando besitos: {e}")

    # ========================================
    # MÉTODOS CRUD
    # ========================================

    async def create_decision(
        self,
        fragment_id: int,
        button_text: str,
        target_fragment_key: str,
        order: int = 0,
        button_emoji: Optional[str] = None,
        besitos_cost: int = 0,
        grants_besitos: int = 0,
        affects_archetype: Optional[str] = None
    ) -> FragmentDecision:
        """
        Crea nueva decisión para un fragmento.

        Args:
            fragment_id: ID del fragmento padre
            button_text: Texto del botón
            target_fragment_key: Key del fragmento destino
            order: Orden de presentación (default 0)
            button_emoji: Emoji opcional para el botón
            besitos_cost: Costo en besitos (default 0)
            grants_besitos: Besitos a otorgar (default 0)
            affects_archetype: Arquetipo afectado (opcional)

        Returns:
            Decisión creada
        """
        decision = FragmentDecision(
            fragment_id=fragment_id,
            button_text=button_text,
            target_fragment_key=target_fragment_key,
            order=order,
            button_emoji=button_emoji,
            besitos_cost=besitos_cost,
            grants_besitos=grants_besitos,
            affects_archetype=affects_archetype,
            is_active=True
        )

        self._session.add(decision)
        await self._session.flush()
        await self._session.refresh(decision)

        logger.info(
            f"✅ Decisión creada: '{button_text}' → {target_fragment_key}"
        )

        return decision

    async def update_decision(
        self,
        decision_id: int,
        button_text: Optional[str] = None,
        target_fragment_key: Optional[str] = None,
        order: Optional[int] = None,
        button_emoji: Optional[str] = None,
        besitos_cost: Optional[int] = None,
        grants_besitos: Optional[int] = None,
        affects_archetype: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[FragmentDecision]:
        """
        Actualiza decisión existente.

        Args:
            decision_id: ID de la decisión
            button_text: Nuevo texto del botón
            target_fragment_key: Nuevo fragmento destino
            order: Nuevo orden
            button_emoji: Nuevo emoji
            besitos_cost: Nuevo costo
            grants_besitos: Nuevos besitos a otorgar
            affects_archetype: Nuevo arquetipo afectado
            is_active: Nuevo estado activo

        Returns:
            Decisión actualizada o None si no existe
        """
        decision = await self.get_decision_by_id(decision_id)
        if not decision:
            logger.warning(f"⚠️ Decisión no encontrada: {decision_id}")
            return None

        if button_text is not None:
            decision.button_text = button_text
        if target_fragment_key is not None:
            decision.target_fragment_key = target_fragment_key
        if order is not None:
            decision.order = order
        if button_emoji is not None:
            decision.button_emoji = button_emoji if button_emoji != "" else None
        if besitos_cost is not None:
            decision.besitos_cost = besitos_cost
        if grants_besitos is not None:
            decision.grants_besitos = grants_besitos
        if affects_archetype is not None:
            decision.affects_archetype = affects_archetype if affects_archetype != "" else None
        if is_active is not None:
            decision.is_active = is_active

        await self._session.flush()
        await self._session.refresh(decision)

        logger.info(f"✅ Decisión actualizada: ID={decision_id}")

        return decision

    async def delete_decision(self, decision_id: int) -> bool:
        """
        Elimina decisión (soft delete).

        Args:
            decision_id: ID de la decisión

        Returns:
            True si se eliminó, False si no existía
        """
        decision = await self.get_decision_by_id(decision_id)
        if not decision:
            logger.warning(f"⚠️ Decisión no encontrada: {decision_id}")
            return False

        decision.is_active = False
        await self._session.flush()

        logger.info(f"🗑️ Decisión eliminada (soft): ID={decision_id}")

        return True

    async def get_decisions_by_fragment(
        self,
        fragment_id: int,
        active_only: bool = True
    ) -> List[FragmentDecision]:
        """
        Obtiene todas las decisiones de un fragmento.

        Args:
            fragment_id: ID del fragmento
            active_only: Si True, solo retorna decisiones activas

        Returns:
            Lista de decisiones ordenadas por order
        """
        stmt = select(FragmentDecision).where(
            FragmentDecision.fragment_id == fragment_id
        )

        if active_only:
            stmt = stmt.where(FragmentDecision.is_active == True)

        stmt = stmt.order_by(FragmentDecision.order)

        result = await self._session.execute(stmt)
        decisions = list(result.scalars().all())

        logger.debug(
            f"📋 Decisiones para fragment_id={fragment_id}: {len(decisions)}"
        )

        return decisions

    # ========================================
    # MÉTODOS DE COOLDOWN
    # ========================================

    async def _apply_fragment_cooldown(
        self,
        user_id: int,
        fragment: NarrativeFragment
    ) -> None:
        """
        Aplica cooldown si el fragmento es intenso.

        Args:
            user_id: ID del usuario
            fragment: Fragmento al que avanzó
        """
        from bot.narrative.services.cooldown import CooldownService
        from bot.narrative.database.enums import CooldownType
        from bot.narrative.config import NarrativeConfig

        # Verificar si el fragmento es intenso (basado en visual_hint)
        is_intense = (
            fragment.visual_hint
            and any(
                keyword in fragment.visual_hint.lower()
                for keyword in ["intense", "climax", "revelation", "critical"]
            )
        )

        if is_intense:
            cooldown_service = CooldownService(self._session)
            await cooldown_service.set_cooldown(
                user_id=user_id,
                cooldown_type=CooldownType.FRAGMENT,
                target_key=fragment.fragment_key,
                duration_seconds=NarrativeConfig.INTENSE_FRAGMENT_COOLDOWN_SECONDS,
                message=NarrativeConfig.get_cooldown_message("fragment")
            )
            logger.info(
                f"⏳ Cooldown de fragmento intenso aplicado: "
                f"{NarrativeConfig.INTENSE_FRAGMENT_COOLDOWN_SECONDS}s para {fragment.fragment_key}"
            )

    async def _apply_chapter_completion_cooldown(
        self,
        user_id: int,
        chapter_id: int
    ) -> None:
        """
        Aplica cooldown al completar un capítulo.

        Args:
            user_id: ID del usuario
            chapter_id: ID del capítulo completado
        """
        from bot.narrative.services.cooldown import CooldownService
        from bot.narrative.database.enums import CooldownType
        from bot.narrative.config import NarrativeConfig

        cooldown_service = CooldownService(self._session)
        await cooldown_service.set_cooldown(
            user_id=user_id,
            cooldown_type=CooldownType.CHAPTER,
            target_key=f"chapter_{chapter_id}",
            duration_seconds=NarrativeConfig.CHAPTER_COMPLETION_COOLDOWN_SECONDS,
            message=NarrativeConfig.get_cooldown_message("chapter")
        )
        logger.info(
            f"🎉 Cooldown de completado de capítulo aplicado: "
            f"{NarrativeConfig.CHAPTER_COMPLETION_COOLDOWN_SECONDS}s para capítulo {chapter_id}"
        )
