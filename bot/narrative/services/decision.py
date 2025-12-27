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

    Métodos:
    - get_available_decisions: Obtener decisiones disponibles
    - process_decision: Procesar decisión del usuario
    - record_decision: Registrar decisión en historial
    - get_decision_by_id: Obtener decisión por ID
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
