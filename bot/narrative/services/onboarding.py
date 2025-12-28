"""
Servicio de gestión del onboarding narrativo.

Maneja el flujo de introducción de nuevos usuarios al sistema narrativo,
incluyendo detección de arquetipo y otorgamiento de besitos iniciales.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.narrative.database.onboarding_models import (
    UserOnboardingProgress,
    OnboardingFragment,
)
from bot.narrative.database.enums import ArchetypeType

logger = logging.getLogger(__name__)


class OnboardingService:
    """
    Servicio de onboarding narrativo.

    Gestiona el flujo de introducción de nuevos usuarios:
    - Tracking de progreso a través de 5 pasos
    - Detección de arquetipo basada en decisiones
    - Otorgamiento de besitos de bienvenida
    - Validación de completación

    Métodos:
    - get_or_create_progress: Obtener o crear progreso de onboarding
    - mark_onboarding_started: Marcar inicio del onboarding
    - mark_onboarding_completed: Marcar completación
    - update_step: Avanzar al siguiente paso
    - record_decision: Registrar decisión y actualizar arquetipo
    - grant_welcome_besitos: Otorgar besitos de bienvenida
    - has_completed_onboarding: Verificar si completó
    - get_fragment: Obtener fragmento por paso
    - get_all_fragments: Obtener todos los fragmentos
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
    ) -> UserOnboardingProgress:
        """
        Obtiene o crea el progreso de onboarding del usuario.

        Args:
            user_id: ID del usuario de Telegram

        Returns:
            Progreso de onboarding del usuario
        """
        stmt = select(UserOnboardingProgress).where(
            UserOnboardingProgress.user_id == user_id
        )
        result = await self._session.execute(stmt)
        progress = result.scalar_one_or_none()

        if not progress:
            progress = UserOnboardingProgress(
                user_id=user_id,
                started=False,
                completed=False,
                current_step=0,
                archetype_scores=json.dumps({
                    "IMPULSIVE": 0,
                    "CONTEMPLATIVE": 0,
                    "SILENT": 0
                }),
                decisions_made=json.dumps([]),
                besitos_granted=0,
                created_at=datetime.now(timezone.utc)
            )
            self._session.add(progress)
            await self._session.flush()
            await self._session.refresh(progress)
            logger.info(f"✅ Progreso de onboarding creado para usuario {user_id}")
        else:
            logger.debug(f"📊 Progreso de onboarding existente para usuario {user_id}")

        return progress

    async def mark_onboarding_started(self, user_id: int) -> UserOnboardingProgress:
        """
        Marca el onboarding como iniciado.

        Args:
            user_id: ID del usuario

        Returns:
            Progreso actualizado
        """
        progress = await self.get_or_create_progress(user_id)

        if not progress.started:
            progress.started = True
            progress.current_step = 1
            progress.started_at = datetime.now(timezone.utc)
            await self._session.flush()
            logger.info(f"🎬 Onboarding iniciado para usuario {user_id}")

        return progress

    async def mark_onboarding_completed(self, user_id: int) -> UserOnboardingProgress:
        """
        Marca el onboarding como completado.

        Args:
            user_id: ID del usuario

        Returns:
            Progreso actualizado
        """
        progress = await self.get_or_create_progress(user_id)

        progress.completed = True
        progress.current_step = 5
        progress.completed_at = datetime.now(timezone.utc)
        await self._session.flush()

        logger.info(f"🎉 Onboarding completado para usuario {user_id}")
        return progress

    async def update_step(self, user_id: int, step: int) -> UserOnboardingProgress:
        """
        Actualiza el paso actual del onboarding.

        Args:
            user_id: ID del usuario
            step: Número de paso (1-5)

        Returns:
            Progreso actualizado
        """
        progress = await self.get_or_create_progress(user_id)

        if 1 <= step <= 5:
            progress.current_step = step
            await self._session.flush()
            logger.debug(f"📍 Usuario {user_id} avanzó al paso {step}")

        return progress

    async def record_decision(
        self,
        user_id: int,
        step: int,
        choice_index: int,
        archetype_hint: Optional[str] = None
    ) -> UserOnboardingProgress:
        """
        Registra una decisión tomada durante el onboarding.

        Args:
            user_id: ID del usuario
            step: Paso donde se tomó la decisión
            choice_index: Índice de la opción elegida
            archetype_hint: Arquetipo asociado a la decisión (IMPULSIVE, CONTEMPLATIVE, SILENT)

        Returns:
            Progreso actualizado
        """
        progress = await self.get_or_create_progress(user_id)

        # Registrar decisión
        decisions = json.loads(progress.decisions_made or "[]")
        decisions.append({
            "step": step,
            "choice": choice_index,
            "archetype": archetype_hint,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        progress.decisions_made = json.dumps(decisions)

        # Actualizar puntuaciones de arquetipo
        if archetype_hint and archetype_hint in ["IMPULSIVE", "CONTEMPLATIVE", "SILENT"]:
            scores = json.loads(progress.archetype_scores or "{}")
            scores[archetype_hint] = scores.get(archetype_hint, 0) + 5
            progress.archetype_scores = json.dumps(scores)

        await self._session.flush()
        logger.debug(
            f"📝 Usuario {user_id} tomó decisión en paso {step}: "
            f"opción {choice_index}, arquetipo hint: {archetype_hint}"
        )

        return progress

    async def grant_welcome_besitos(
        self,
        user_id: int,
        amount: int = 30
    ) -> int:
        """
        Otorga besitos de bienvenida al usuario.

        Args:
            user_id: ID del usuario
            amount: Cantidad de besitos a otorgar (default: 30)

        Returns:
            Cantidad de besitos otorgados
        """
        progress = await self.get_or_create_progress(user_id)

        # Evitar doble otorgamiento
        if progress.besitos_granted > 0:
            logger.warning(
                f"⚠️ Usuario {user_id} ya recibió {progress.besitos_granted} besitos"
            )
            return 0

        progress.besitos_granted = amount
        await self._session.flush()

        # Otorgar besitos reales usando el servicio de gamificación
        try:
            from bot.gamification.services.container import GamificationContainer
            gamification = GamificationContainer(self._session)
            await gamification.besitos.add_besitos(
                user_id=user_id,
                amount=amount,
                reason="Bienvenida al sistema narrativo"
            )
            logger.info(f"🎁 {amount} besitos de bienvenida otorgados a usuario {user_id}")
        except Exception as e:
            logger.warning(f"⚠️ No se pudieron otorgar besitos: {e}")

        return amount

    async def has_completed_onboarding(self, user_id: int) -> bool:
        """
        Verifica si el usuario completó el onboarding.

        Args:
            user_id: ID del usuario

        Returns:
            True si completó, False si no
        """
        stmt = select(UserOnboardingProgress).where(
            UserOnboardingProgress.user_id == user_id,
            UserOnboardingProgress.completed == True
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_detected_archetype(self, user_id: int) -> Optional[ArchetypeType]:
        """
        Obtiene el arquetipo detectado durante el onboarding.

        Args:
            user_id: ID del usuario

        Returns:
            Arquetipo con mayor puntuación, o None si no hay datos
        """
        progress = await self.get_or_create_progress(user_id)

        scores = json.loads(progress.archetype_scores or "{}")
        if not scores:
            return None

        # Encontrar arquetipo con mayor puntuación
        max_archetype = max(scores, key=lambda k: scores[k])
        max_score = scores[max_archetype]

        if max_score == 0:
            return ArchetypeType.UNKNOWN

        try:
            return ArchetypeType[max_archetype]
        except KeyError:
            return ArchetypeType.UNKNOWN

    async def get_fragment(self, step: int) -> Optional[OnboardingFragment]:
        """
        Obtiene el fragmento de onboarding para un paso específico.

        Args:
            step: Número de paso (1-5)

        Returns:
            Fragmento de onboarding o None si no existe
        """
        stmt = select(OnboardingFragment).where(
            OnboardingFragment.step == step,
            OnboardingFragment.is_active == True
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_fragments(self) -> List[OnboardingFragment]:
        """
        Obtiene todos los fragmentos de onboarding activos.

        Returns:
            Lista de fragmentos ordenados por paso
        """
        stmt = (
            select(OnboardingFragment)
            .where(OnboardingFragment.is_active == True)
            .order_by(OnboardingFragment.step)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    def parse_decisions(self, fragment: OnboardingFragment) -> List[Dict[str, Any]]:
        """
        Parsea las decisiones de un fragmento.

        Args:
            fragment: Fragmento de onboarding

        Returns:
            Lista de decisiones como diccionarios
        """
        if not fragment.decisions:
            return []

        try:
            return json.loads(fragment.decisions)
        except json.JSONDecodeError:
            logger.error(f"❌ Error parseando decisiones del paso {fragment.step}")
            return []

    async def get_onboarding_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Obtiene un resumen del estado de onboarding del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Diccionario con resumen de estado
        """
        progress = await self.get_or_create_progress(user_id)
        archetype = await self.get_detected_archetype(user_id)

        return {
            "user_id": user_id,
            "started": progress.started,
            "completed": progress.completed,
            "current_step": progress.current_step,
            "progress_percent": progress.progress_percent,
            "besitos_granted": progress.besitos_granted,
            "detected_archetype": archetype.value if archetype else None,
            "decisions_count": len(json.loads(progress.decisions_made or "[]")),
            "started_at": progress.started_at.isoformat() if progress.started_at else None,
            "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
        }
