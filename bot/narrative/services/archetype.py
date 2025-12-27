"""
Servicio de detección de arquetipos de usuario.

Analiza patrones de respuesta del usuario para determinar su arquetipo
(IMPULSIVE, CONTEMPLATIVE, SILENT) y adaptar la narrativa.
"""
import logging
from typing import Optional, Tuple, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.narrative.database import (
    UserNarrativeProgress,
    UserDecisionHistory,
    ArchetypeType,
)

logger = logging.getLogger(__name__)


# Umbrales de tiempo para clasificación (segundos)
IMPULSIVE_THRESHOLD = 5      # < 5s = Impulsivo
CONTEMPLATIVE_THRESHOLD = 30  # > 30s = Contemplativo
SILENT_THRESHOLD = 120        # > 120s = Silencioso (timeout)

# Decisiones mínimas para confianza
MIN_DECISIONS_FOR_DETECTION = 3      # Mínimo para detección básica
MIN_DECISIONS_FOR_HIGH_CONFIDENCE = 10  # Para alta confianza


class ArchetypeService:
    """
    Servicio de detección y gestión de arquetipos.

    Métodos:
    - analyze_and_update: Analiza comportamiento y actualiza arquetipo
    - get_archetype: Obtiene arquetipo actual del usuario
    - classify_response_time: Clasifica tiempo de respuesta en arquetipo
    - calculate_confidence: Calcula confianza de la detección
    - get_response_time_stats: Obtiene estadísticas de tiempos
    - should_update_archetype: Verifica si debe actualizar
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa servicio.

        Args:
            session: Sesión async de SQLAlchemy
        """
        self._session = session

    async def analyze_and_update(
        self,
        user_id: int,
        force: bool = False
    ) -> Tuple[ArchetypeType, float]:
        """
        Analiza comportamiento del usuario y actualiza su arquetipo.

        Este método:
        1. Obtiene historial de decisiones
        2. Calcula promedio de tiempos de respuesta
        3. Clasifica en arquetipo según umbrales
        4. Calcula nivel de confianza
        5. Actualiza progreso si cambió o si force=True

        Args:
            user_id: ID del usuario
            force: Forzar actualización aunque no haya cambios

        Returns:
            Tupla (arquetipo_detectado, confianza)
        """
        # Obtener estadísticas de tiempos
        stats = await self.get_response_time_stats(user_id)

        if stats['total_decisions'] == 0:
            logger.debug(f"📊 Usuario {user_id} sin decisiones, arquetipo UNKNOWN")
            return ArchetypeType.UNKNOWN, 0.0

        # Clasificar según promedio
        avg_time = stats['avg_response_time']
        archetype = self.classify_response_time(avg_time)

        # Calcular confianza
        confidence = self.calculate_confidence(
            total_decisions=stats['total_decisions'],
            avg_time=avg_time,
            archetype=archetype
        )

        # Verificar si debe actualizar
        should_update = await self.should_update_archetype(
            user_id=user_id,
            new_archetype=archetype,
            new_confidence=confidence
        )

        if should_update or force:
            # Actualizar progreso
            from bot.narrative.services.progress import ProgressService

            progress_service = ProgressService(self._session)
            await progress_service.update_archetype(
                user_id=user_id,
                archetype=archetype,
                confidence=confidence
            )

            logger.info(
                f"🎭 Arquetipo actualizado: user={user_id}, "
                f"archetype={archetype.value}, confidence={confidence:.2f}, "
                f"avg_time={avg_time:.1f}s, decisions={stats['total_decisions']}"
            )
        else:
            logger.debug(
                f"📊 Sin cambio en arquetipo: user={user_id}, "
                f"archetype={archetype.value}"
            )

        return archetype, confidence

    async def get_archetype(
        self,
        user_id: int
    ) -> Tuple[ArchetypeType, float]:
        """
        Obtiene arquetipo actual del usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Tupla (arquetipo, confianza)
        """
        stmt = select(UserNarrativeProgress).where(
            UserNarrativeProgress.user_id == user_id
        )
        result = await self._session.execute(stmt)
        progress = result.scalar_one_or_none()

        if not progress:
            return ArchetypeType.UNKNOWN, 0.0

        return progress.detected_archetype, progress.archetype_confidence

    def classify_response_time(self, avg_time: float) -> ArchetypeType:
        """
        Clasifica tiempo de respuesta en arquetipo.

        Umbrales:
        - < 5s: IMPULSIVE (reacciona rápido)
        - 5-30s: En transición, prioriza CONTEMPLATIVE si > 15s
        - > 30s: CONTEMPLATIVE (toma su tiempo)
        - > 120s: SILENT (no reacciona, timeout)

        Args:
            avg_time: Tiempo promedio de respuesta (segundos)

        Returns:
            Arquetipo clasificado
        """
        if avg_time >= SILENT_THRESHOLD:
            return ArchetypeType.SILENT
        elif avg_time >= CONTEMPLATIVE_THRESHOLD:
            return ArchetypeType.CONTEMPLATIVE
        elif avg_time < IMPULSIVE_THRESHOLD:
            return ArchetypeType.IMPULSIVE
        else:
            # Zona intermedia (5-30s): priorizar CONTEMPLATIVE si > 15s
            return (
                ArchetypeType.CONTEMPLATIVE if avg_time > 15
                else ArchetypeType.IMPULSIVE
            )

    def calculate_confidence(
        self,
        total_decisions: int,
        avg_time: float,
        archetype: ArchetypeType
    ) -> float:
        """
        Calcula nivel de confianza de la detección.

        Factores:
        1. Cantidad de decisiones (más decisiones = más confianza)
        2. Qué tan clara es la clasificación (cerca del umbral = menos confianza)

        Args:
            total_decisions: Total de decisiones tomadas
            avg_time: Tiempo promedio de respuesta
            archetype: Arquetipo detectado

        Returns:
            Confianza (0.0 - 1.0)
        """
        if total_decisions == 0:
            return 0.0

        # Factor 1: Confianza basada en cantidad de decisiones
        # 0-2 decisiones: 0.2-0.4
        # 3-9 decisiones: 0.5-0.7
        # 10+ decisiones: 0.8-1.0
        if total_decisions < MIN_DECISIONS_FOR_DETECTION:
            decision_confidence = 0.2 + (total_decisions * 0.1)
        elif total_decisions < MIN_DECISIONS_FOR_HIGH_CONFIDENCE:
            decision_confidence = 0.5 + ((total_decisions - 3) * 0.03)
        else:
            decision_confidence = min(0.8 + ((total_decisions - 10) * 0.02), 1.0)

        # Factor 2: Confianza basada en claridad de clasificación
        # Qué tan lejos está de los umbrales
        if archetype == ArchetypeType.IMPULSIVE:
            # Más lejos de 5s = más confianza
            # 0-2s = alta confianza (0.9)
            # 3-4s = media confianza (0.7)
            clarity_confidence = max(0.6, 1.0 - (avg_time / 10))

        elif archetype == ArchetypeType.CONTEMPLATIVE:
            # 30-60s = media confianza (0.8)
            # 60-120s = alta confianza (0.9)
            if avg_time < 60:
                clarity_confidence = 0.7 + (avg_time - 30) / 150
            else:
                clarity_confidence = 0.85

        elif archetype == ArchetypeType.SILENT:
            # > 120s = muy alta confianza (0.95)
            clarity_confidence = 0.95

        else:
            # UNKNOWN
            clarity_confidence = 0.3

        # Confianza final: promedio ponderado
        # 70% decisiones, 30% claridad
        final_confidence = (decision_confidence * 0.7) + (clarity_confidence * 0.3)

        return min(max(final_confidence, 0.0), 1.0)

    async def get_response_time_stats(
        self,
        user_id: int
    ) -> dict:
        """
        Obtiene estadísticas de tiempos de respuesta.

        Args:
            user_id: ID del usuario

        Returns:
            Dict con:
            - total_decisions: Total de decisiones
            - avg_response_time: Tiempo promedio (segundos)
            - min_response_time: Tiempo mínimo
            - max_response_time: Tiempo máximo
            - decisions_with_time: Decisiones con tiempo registrado
        """
        # Obtener decisiones con tiempo de respuesta
        stmt = select(
            func.count(UserDecisionHistory.id).label('total'),
            func.avg(UserDecisionHistory.response_time_seconds).label('avg_time'),
            func.min(UserDecisionHistory.response_time_seconds).label('min_time'),
            func.max(UserDecisionHistory.response_time_seconds).label('max_time'),
            func.count(UserDecisionHistory.response_time_seconds).label('with_time')
        ).where(
            UserDecisionHistory.user_id == user_id
        )

        result = await self._session.execute(stmt)
        row = result.one()

        return {
            'total_decisions': row.total or 0,
            'avg_response_time': float(row.avg_time or 0),
            'min_response_time': float(row.min_time or 0),
            'max_response_time': float(row.max_time or 0),
            'decisions_with_time': row.with_time or 0
        }

    async def should_update_archetype(
        self,
        user_id: int,
        new_archetype: ArchetypeType,
        new_confidence: float
    ) -> bool:
        """
        Verifica si debe actualizar el arquetipo.

        Actualiza si:
        1. Arquetipo cambió
        2. Confianza aumentó significativamente (>0.1)
        3. No hay arquetipo registrado

        Args:
            user_id: ID del usuario
            new_archetype: Nuevo arquetipo detectado
            new_confidence: Nueva confianza

        Returns:
            True si debe actualizar
        """
        current_archetype, current_confidence = await self.get_archetype(user_id)

        # Si no hay arquetipo, actualizar
        if current_archetype == ArchetypeType.UNKNOWN:
            return True

        # Si arquetipo cambió, actualizar
        if new_archetype != current_archetype:
            return True

        # Si confianza aumentó significativamente, actualizar
        if new_confidence - current_confidence > 0.1:
            return True

        return False

    async def get_decision_history(
        self,
        user_id: int,
        limit: int = 20
    ) -> List[UserDecisionHistory]:
        """
        Obtiene historial de decisiones del usuario.

        Args:
            user_id: ID del usuario
            limit: Máximo de decisiones a retornar

        Returns:
            Lista de decisiones (más recientes primero)
        """
        stmt = (
            select(UserDecisionHistory)
            .where(UserDecisionHistory.user_id == user_id)
            .order_by(UserDecisionHistory.decided_at.desc())
            .limit(limit)
        )

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_archetype_distribution(self) -> dict:
        """
        Obtiene distribución de arquetipos entre todos los usuarios.

        Returns:
            Dict con conteo por arquetipo:
            {
                'impulsive': 10,
                'contemplative': 5,
                'silent': 2,
                'unknown': 3
            }
        """
        stmt = (
            select(
                UserNarrativeProgress.detected_archetype,
                func.count(UserNarrativeProgress.id).label('count')
            )
            .group_by(UserNarrativeProgress.detected_archetype)
        )

        result = await self._session.execute(stmt)
        rows = result.all()

        distribution = {
            'impulsive': 0,
            'contemplative': 0,
            'silent': 0,
            'unknown': 0
        }

        for row in rows:
            archetype_value = row.detected_archetype.value
            distribution[archetype_value] = row.count

        return distribution
