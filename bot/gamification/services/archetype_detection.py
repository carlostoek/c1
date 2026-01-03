"""
Servicio de detección de arquetipos de usuario (FASE 3).

Analiza las señales de comportamiento y determina el arquetipo del usuario.

Este servicio está CORREGIDO para usar el algoritmo basado en interacciones
reales con botones y navegación, no en TEXT_RESPONSE.

Author: Sistema de Gamificación
Version: 1.0
"""

import logging
import json
from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.gamification.database.models import UserBehaviorSignals, UserGamification
from bot.gamification.config.archetype_detection import (
    ArchetypeDetectionConfig,
    ScoreDefinitions,
    ArchetypeResult,
    ArchetypeInsights,
)
from bot.gamification.services.behavior_tracking import BehaviorTrackingService

logger = logging.getLogger(__name__)


class ArchetypeDetectionService:
    """
    Servicio de detección de arquetipos de usuario.

    Analiza las señales de comportamiento acumuladas y determina
    el arquetipo dominante del usuario.
    """

    def __init__(self, session: AsyncSession):
        """Inicializa el servicio con una sesión de base de datos."""
        self.session = session
        self.tracking = BehaviorTrackingService(session)

    # ============================================================
    # MÉTODOS PRINCIPALES DE DETECCIÓN
    # ============================================================

    async def detect_archetype(
        self,
        user_id: int,
        force: bool = False,
    ) -> ArchetypeResult:
        """
        Ejecuta la detección completa de arquetipo para un usuario.

        Args:
            user_id: ID del usuario
            force: Si es True, fuerza re-evaluación ignorando caché

        Returns:
            ArchetypeResult con el resultado de la detección
        """
        # Obtener señales de comportamiento
        signals_dict = await self.tracking.get_signals_as_dict(user_id)

        if not signals_dict:
            return ArchetypeResult(
                archetype=None,
                confidence=0.0,
                scores={},
                reason="no_signals",
                interactions_count=0,
            )

        interactions_count = signals_dict.get("total_interactions", 0)

        # Verificar si hay suficientes interacciones
        if not force and interactions_count < ArchetypeDetectionConfig.MIN_INTERACTIONS_FOR_DETECTION:
            return ArchetypeResult(
                archetype=None,
                confidence=0.0,
                scores={},
                reason="insufficient_data",
                interactions_count=interactions_count,
            )

        # Calcular scores para cada arquetipo
        scores = ScoreDefinitions.calculate_all_scores(signals_dict)

        # Convertir a escala 0-100
        scores_100 = {k: v * 100 for k, v in scores.items()}

        # Determinar arquetipo dominante
        sorted_scores = sorted(scores_100.items(), key=lambda x: x[1], reverse=True)
        top_archetype = sorted_scores[0][0]
        top_score = sorted_scores[0][1]
        second_score = sorted_scores[1][1] if len(sorted_scores) > 1 else 0

        # Calcular confianza
        confidence = (top_score - second_score) + (top_score * 0.3)
        confidence = min(100.0, max(0.0, confidence)) / 100.0

        # Verificar umbral mínimo de confianza
        if confidence < ArchetypeDetectionConfig.MIN_CONFIDENCE_THRESHOLD:
            return ArchetypeResult(
                archetype=None,
                confidence=confidence,
                scores=scores_100,
                reason="low_confidence",
                interactions_count=interactions_count,
            )

        # Guardar resultado en BD
        await self._save_archetype_result(
            user_id=user_id,
            archetype=top_archetype,
            confidence=confidence,
            scores=scores_100,
        )

        return ArchetypeResult(
            archetype=top_archetype,
            confidence=confidence,
            scores=scores_100,
            reason="detected",
            interactions_count=interactions_count,
            detected_at=datetime.now(UTC).isoformat(),
        )

    async def get_archetype(self, user_id: int) -> Optional[str]:
        """
        Obtiene el arquetipo actual de un usuario (desde BD, no recalcula).

        Args:
            user_id: ID del usuario

        Returns:
            Nombre del arquetipo o None si no está detectado
        """
        stmt = select(UserGamification).where(
            UserGamification.user_id == user_id
        )
        result = await self.session.execute(stmt)
        user_gamif = result.scalar_one_or_none()

        if not user_gamif:
            return None

        return user_gamif.archetype

    async def get_archetype_scores(self, user_id: int) -> Dict[str, float]:
        """
        Obtiene los scores de arquetipo de un usuario (desde BD).

        Args:
            user_id: ID del usuario

        Returns:
            Diccionario con scores o vacío si no existen
        """
        stmt = select(UserGamification).where(
            UserGamification.user_id == user_id
        )
        result = await self.session.execute(stmt)
        user_gamif = result.scalar_one_or_none()

        if not user_gamif or not user_gamif.archetype_scores:
            return {}

        try:
            return json.loads(user_gamif.archetype_scores)
        except (json.JSONDecodeError, TypeError):
            return {}

    async def should_reevaluate(self, user_id: int) -> bool:
        """
        Determina si es momento de re-evaluar el arquetipo de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            True si debe re-evaluarse, False en caso contrario
        """
        stmt = select(UserGamification).where(
            UserGamification.user_id == user_id
        )
        result = await self.session.execute(stmt)
        user_gamif = result.scalar_one_or_none()

        # Si nunca ha sido evaluado, sí re-evaluar
        if not user_gamif or not user_gamif.archetype:
            return True

        # Obtener señales actuales
        signals = await self.tracking.get_behavior_signals(user_id)
        if not signals:
            return False

        # Verificar si han pasado suficientes días
        if user_gamif.archetype_detected_at:
            days_since_detection = (
                datetime.now(UTC) - user_gamif.archetype_detected_at
            ).days

            if days_since_detection >= ArchetypeDetectionConfig.REEVALUATION_DAYS:
                return True

        # Verificar si hay suficientes interacciones nuevas
        # (Estimación simple - idealmente guardaríamos el conteo en detección)
        if signals.total_interactions >= ArchetypeDetectionConfig.REEVALUATION_INTERACTIONS:
            return True

        # Verificar si la confianza es baja
        if user_gamif.archetype_confidence < 50:  # < 0.5
            return True

        return False

    async def force_reevaluation(self, user_id: int) -> ArchetypeResult:
        """
        Fuerza la re-evaluación del arquetipo de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            ArchetypeResult con el resultado de la re-evaluación
        """
        return await self.detect_archetype(user_id, force=True)

    async def get_archetype_insights(
        self,
        user_id: int,
    ) -> Optional[ArchetypeInsights]:
        """
        Retorna información detallada del arquetipo para UI/admin.

        Args:
            user_id: ID del usuario

        Returns:
            ArchetypeInsights con información detallada o None
        """
        # Obtener datos de BD
        stmt = select(UserGamification).where(
            UserGamification.user_id == user_id
        )
        result = await self.session.execute(stmt)
        user_gamif = result.scalar_one_or_none()

        if not user_gamif:
            return None

        archetype = user_gamif.archetype
        confidence = user_gamif.archetype_confidence / 100.0

        # Obtener scores
        scores = await self.get_archetype_scores(user_id)
        if not scores:
            return None

        # Top 3 arquetipos
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_3 = sorted_scores[:3]

        # Top señales (las que más contribuyen al arquetipo detectado)
        top_signals = self._get_top_signals(archetype, scores)

        # Recomendaciones basadas en arquetipo
        recommendations = self._get_recommendations(archetype)

        return ArchetypeInsights(
            archetype=archetype,
            confidence=confidence,
            top_3_archetypes=top_3,
            top_signals=top_signals,
            recommendations=recommendations,
        )

    # ============================================================
    # MÉTODOS PRIVADOS
    # ============================================================

    async def _save_archetype_result(
        self,
        user_id: int,
        archetype: str,
        confidence: float,
        scores: Dict[str, float],
    ) -> None:
        """
        Guarda el resultado de la detección en BD.

        Args:
            user_id: ID del usuario
            archetype: Arquetipo detectado
            confidence: Confianza de la detección (0-1)
            scores: Scores de todos los arquetipos (0-100)
        """
        # Obtener o crear UserGamification
        stmt = select(UserGamification).where(
            UserGamification.user_id == user_id
        )
        result = await self.session.execute(stmt)
        user_gamif = result.scalar_one_or_none()

        if not user_gamif:
            user_gamif = UserGamification(user_id=user_id)
            self.session.add(user_gamif)
            await self.session.flush()

        # Actualizar campos
        user_gamif.archetype = archetype
        user_gamif.archetype_confidence = int(confidence * 100)
        user_gamif.archetype_scores = json.dumps(scores)
        user_gamif.archetype_detected_at = datetime.now(UTC)
        user_gamif.archetype_version = 1  # Versión del algoritmo

        await self.session.commit()

    def _get_top_signals(
        self,
        archetype: str,
        scores: Dict[str, float],
    ) -> List[tuple[str, str]]:
        """
        Obtiene las señales que más contribuyen al arquetipo detectado.

        Args:
            archetype: Arquetipo detectado
            scores: Scores de todos los arquetipos

        Returns:
            Lista de tuplas (signal_name, description)
        """
        # Mapeo de señales clave por arquetipo
        key_signals = {
            "EXPLORER": [
                ("easter_eggs_found", "Easter eggs encontrados"),
                ("content_completion_rate", "Tasa de contenido completado"),
                ("revisits_old_content", "Revisitas a contenido antiguo"),
            ],
            "DIRECT": [
                ("avg_time_to_click", "Velocidad de click"),
                ("avg_decision_time", "Tiempo de decisión"),
                ("direct_navigation_ratio", "Navegación directa"),
            ],
            "ROMANTIC": [
                ("emotional_content_views", "Vistas de contenido emotivo"),
                ("personal_stories_accessed", "Historias personales accedidas"),
                ("repeat_emotional_visits", "Revisitas emotivas"),
            ],
            "ANALYTICAL": [
                ("evaluation_scores_avg", "Scores en evaluaciones"),
                ("systematic_exploration", "Exploración sistemática"),
                ("details_viewed", "Detalles expandidos"),
            ],
            "PERSISTENT": [
                ("return_after_inactivity", "Retornos tras inactividad"),
                ("retry_failed_actions", "Reintentos de acciones"),
                ("account_age_days", "Antigüedad de cuenta"),
            ],
            "PATIENT": [
                ("slow_decision_count", "Decisiones lentas"),
                ("current_streak", "Racha actual"),
                ("session_consistency", "Consistencia de sesiones"),
            ],
        }

        return key_signals.get(archetype, [])

    def _get_recommendations(self, archetype: str) -> List[str]:
        """
        Obtiene recomendaciones basadas en el arquetipo detectado.

        Args:
            archetype: Arquetipo detectado

        Returns:
            Lista de recomendaciones
        """
        recommendations_map = {
            "EXPLORER": [
                "Ofrecer contenido con capas y secrets",
                "Desafiar con easter eggs ocultos",
                "Premiar la exploración exhaustiva",
            ],
            "DIRECT": [
                "Ser conciso y directo en mensajes",
                "Evitar rodeos y explicaciones largas",
                "Ofrecer acciones claras y medibles",
            ],
            "ROMANTIC": [
                "Personalizar mensajes con tono emotivo",
                "Compartir contenido sentimental de Diana",
                "Reconocer su sensibilidad",
            ],
            "ANALYTICAL": [
                "Proporcionar datos y análisis",
                "Desafiar con puzzles y enigmas",
                "Reconocer su capacidad intelectual",
            ],
            "PERSISTENT": [
                "Recompensar la constancia",
                "Ofrecer contenido progresivo",
                "Reconocer su dedicación",
            ],
            "PATIENT": [
                "No presionar por resultados rápidos",
                "Recompensar la consistencia",
                "Ofrecer contenido que se revela lentamente",
            ],
        }

        return recommendations_map.get(archetype, [])
