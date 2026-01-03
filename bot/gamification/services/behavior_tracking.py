"""
Servicio de tracking de comportamiento para detección de arquetipos (FASE 3).

Registra interacciones del usuario y actualiza las señales de comportamiento
que se utilizan para detectar su arquetipo.

Este servicio está CORREGIDO para no depender de TEXT_RESPONSE,
sino de interacciones reales con botones y navegación.

Author: Sistema de Gamificación
Version: 1.0
"""

import logging
import json
from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any, List
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.gamification.database.models import UserBehaviorSignals, UserGamification, DailyGiftClaim
from bot.gamification.database.enums import InteractionType
from bot.gamification.config.archetype_detection import (
    ArchetypeDetectionConfig,
    normalize
)

logger = logging.getLogger(__name__)


class BehaviorTrackingService:
    """
    Servicio de tracking de comportamiento del usuario.

    Registra cada interacción relevante y actualiza las señales
    acumuladas que luego se utilizan para detectar el arquetipo.
    """

    def __init__(self, session: AsyncSession):
        """Inicializa el servicio con una sesión de base de datos."""
        self.session = session

    # ============================================================
    # MÉTODOS PRINCIPALES DE TRACKING
    # ============================================================

    async def track_button_click(
        self,
        user_id: int,
        button_id: str,
        context: str,
        time_to_click: float,
        is_exploration: bool = False,
        is_direct_action: bool = False,
    ) -> None:
        """
        Registra un click en botón inline.

        Args:
            user_id: ID del usuario
            button_id: ID del botón clickeado
            context: Contexto dónde estaba el botón
            time_to_click: Segundos desde que se mostró el botón
            is_exploration: Si es navegación exploratoria
            is_direct_action: Si es acción directa al objetivo
        """
        signals = await self._get_or_create_signals(user_id)

        # Actualizar métricas generales
        signals.total_interactions += 1
        signals.last_interaction_at = datetime.now(UTC)

        # Actualizar métricas de velocidad
        current_avg = signals.avg_time_to_click / 100.0
        signals.avg_time_to_click = self._update_average(
            current_avg, signals.total_interactions, time_to_click
        )

        # Contar acciones rápidas (<3 segundos)
        if time_to_click < 3.0:
            signals.quick_actions_count += 1

        # Actualizar navegación directa
        if is_direct_action:
            current_ratio = signals.direct_navigation_ratio / 100.0
            signals.direct_navigation_ratio = self._update_ratio(
                current_ratio, True
            ) * 100

        # Actualizar exploración
        if is_exploration:
            signals.content_sections_visited += 1

        await self.session.commit()

    async def track_content_interaction(
        self,
        user_id: int,
        content_id: str,
        content_type: str,
        interaction_type: str,
        time_spent: float = 0.0,
        completion: float = 0.0,
        is_emotional: bool = False,
        is_personal: bool = False,
        is_revisit: bool = False,
        tags: Optional[List[str]] = None,
    ) -> None:
        """
        Registra interacción con contenido narrativo.

        Args:
            user_id: ID del usuario
            content_id: ID del contenido
            content_type: Tipo de contenido ("story", "profile", "shop", etc.)
            interaction_type: Tipo de interacción ("view", "complete", "revisit", "easter_egg")
            time_spent: Segundos en el contenido
            completion: Qué tanto completó (0-1)
            is_emotional: Si es contenido emocional/personal
            is_personal: Si es sobre Diana personalmente
            is_revisit: Si es revisita de contenido antiguo
            tags: Tags del contenido para clasificación
        """
        signals = await self._get_or_create_signals(user_id)

        tags = tags or []

        # Actualizar métricas generales
        signals.total_interactions += 1
        signals.last_interaction_at = datetime.now(UTC)

        # Actualizar tiempo promedio en contenido
        if time_spent > 0:
            current_avg = signals.avg_time_on_content / 100.0
            signals.avg_time_on_content = self._update_average(
                current_avg, signals.total_interactions, time_spent
            ) * 100

        # Actualizar contenido completado
        if completion > 0:
            current_completion = signals.content_completion_rate / 100.0
            signals.content_completion_rate = self._update_average(
                current_completion, signals.total_interactions, completion
            ) * 100

        # Detectar y actualizar contenido emocional/personal
        if is_emotional or ArchetypeDetectionConfig.is_emotional_content(tags):
            signals.emotional_content_views += 1

            if is_revisit:
                signals.repeat_emotional_visits += 1

        if is_personal or "personal" in tags or "diana_story" in tags:
            signals.personal_stories_accessed += 1

        # Si es memento/referencia a Diana
        if "mnemonic" in tags or "memento" in tags:
            signals.diana_mnemonics_interactions += 1

        # Si es revisita de contenido antiguo
        if is_revisit:
            signals.revisits_old_content += 1

        # Si encontró easter egg
        if interaction_type == "easter_egg" or "easter_egg" in tags:
            signals.easter_eggs_found += 1

        # Si expandió detalles
        if interaction_type == "details_expanded":
            signals.details_viewed += 1

        await self.session.commit()

    async def track_decision(
        self,
        user_id: int,
        decision_id: str,
        time_to_decide: float,
        options_available: int,
        decision_type: str = "narrative",
        is_systematic: bool = False,
        is_emotional: bool = False,
    ) -> None:
        """
        Registra una decisión narrativa tomada por el usuario.

        Args:
            user_id: ID del usuario
            decision_id: ID de la decisión
            time_to_decide: Segundos para tomar decisión
            options_available: Cantidad de opciones disponibles
            decision_type: Tipo de decisión ("narrative", "choice", "path")
            is_systematic: Si siguió patrón lógico
            is_emotional: Si la elección fue emocional
        """
        signals = await self._get_or_create_signals(user_id)

        # Actualizar métricas generales
        signals.total_interactions += 1
        signals.last_interaction_at = datetime.now(UTC)

        # Actualizar tiempo promedio de decisión
        current_avg = signals.avg_decision_time / 100.0
        signals.avg_decision_time = self._update_average(
            current_avg, signals.total_interactions, time_to_decide
        ) * 100

        # Contar decisiones lentas (>30 segundos)
        if time_to_decide > 30:
            signals.slow_decision_count += 1

        # Actualizar exploración sistemática
        if is_systematic:
            current_systematic = signals.systematic_exploration / 100.0
            signals.systematic_exploration = self._update_ratio(
                current_systematic, True
            ) * 100

        # Si fue decisión emocional, contar como interacción emocional
        if is_emotional:
            signals.emotional_content_views += 1

        await self.session.commit()

    async def track_session(
        self,
        user_id: int,
        session_type: str,
        duration: float = 0.0,
        actions_count: int = 1,
        navigation_depth: int = 1,
        is_return: bool = False,
    ) -> None:
        """
        Registra información de sesión del usuario.

        Args:
            user_id: ID del usuario
            session_type: Tipo de sesión ("start", "end", "return")
            duration: Duración de sesión en segundos
            actions_count: Cantidad de acciones en la sesión
            navigation_depth: Profundidad de navegación alcanzada
            is_return: Si es retorno después de inactividad
        """
        signals = await self._get_or_create_signals(user_id)

        now = datetime.now(UTC)

        if session_type == "start":
            # Nueva sesión
            signals.total_sessions += 1
            signals.first_interaction_at = signals.first_interaction_at or now
            signals.last_interaction_at = now

            # Actualizar profundidad máxima
            if navigation_depth > signals.explore_depth:
                signals.explore_depth = navigation_depth

        elif session_type == "end":
            # Fin de sesión - actualizar duración promedio
            if duration > 0:
                current_avg = signals.avg_session_duration / 100.0
                signals.avg_session_duration = self._update_average(
                    current_avg, signals.total_sessions, duration
                ) * 100

            # Actualizar acciones por sesión
            if actions_count > 0:
                current_avg = signals.actions_per_session / 100.0
                signals.actions_per_session = self._update_average(
                    current_avg, signals.total_sessions, actions_count
                ) * 100

        elif session_type == "return":
            # Retorno después de inactividad
            signals.return_after_inactivity += 1
            signals.last_interaction_at = now

            # Calcular return_rate
            if signals.total_sessions > 0:
                signals.return_rate = (
                    signals.return_after_inactivity / signals.total_sessions
                ) * 100

        await self.session.commit()

    async def track_skip_action(self, user_id: int) -> None:
        """Registra que el usuario usó 'saltar'."""
        signals = await self._get_or_create_signals(user_id)
        signals.skip_actions_used += 1
        signals.skips_explanation += 1
        await self.session.commit()

    async def track_retry_action(self, user_id: int) -> None:
        """Registra que el usuario reintentó una acción fallida."""
        signals = await self._get_or_create_signals(user_id)
        signals.retry_failed_actions += 1
        await self.session.commit()

    async def track_info_request(self, user_id: int) -> None:
        """Registra que el usuario pidió más información."""
        signals = await self._get_or_create_signals(user_id)
        signals.info_requests += 1
        await self.session.commit()

    async def track_quiz(
        self,
        user_id: int,
        score: float,
        is_completed: bool,
        questions_count: int = 1,
    ) -> None:
        """
        Registra resultado de evaluación/quiz.

        Args:
            user_id: ID del usuario
            score: Score obtenido (0-100)
            is_completed: Si completó la evaluación
            questions_count: Cantidad de preguntas
        """
        signals = await self._get_or_create_signals(user_id)

        # Actualizar promedio de scores
        if score > 0:
            current_avg = signals.evaluation_scores_avg / 100.0
            signals.evaluation_scores_avg = self._update_average(
                current_avg, signals.total_interactions, score / 100.0
            ) * 100

        # Actualizar rate de completación
        current_rate = signals.evaluation_completion_rate / 100.0
        signals.evaluation_completion_rate = self._update_average(
            current_rate, signals.total_interactions, 1.0 if is_completed else 0.0
        ) * 100

        await self.session.commit()

    async def sync_streak_data(self, user_id: int) -> None:
        """
        Sincroniza datos de racha desde DailyGiftClaim.

        Llamar periódicamente para mantener UserBehaviorSignals actualizado
        con los datos más recientes de rachas.
        """
        # Obtener datos de DailyGiftClaim
        stmt = select(DailyGiftClaim).where(DailyGiftClaim.user_id == user_id)
        result = await self.session.execute(stmt)
        daily_gift = result.scalar_one_or_none()

        if daily_gift:
            signals = await self._get_or_create_signals(user_id)

            # Sincronizar rachas
            signals.current_streak = daily_gift.current_streak
            signals.best_streak = daily_gift.longest_streak

            await self.session.commit()

    # ============================================================
    # MÉTODOS DE OBTENCIÓN DE SEÑALES
    # ============================================================

    async def get_behavior_signals(self, user_id: int) -> Optional[UserBehaviorSignals]:
        """
        Obtiene las señales de comportamiento de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Instancia de UserBehaviorSignals o None si no existe
        """
        stmt = select(UserBehaviorSignals).where(
            UserBehaviorSignals.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_signals_as_dict(self, user_id: int) -> Dict[str, Any]:
        """
        Obtiene las señales como diccionario para cálculos de scoring.

        Args:
            user_id: ID del usuario

        Returns:
            Diccionario con todas las métricas del usuario
        """
        signals = await self.get_behavior_signals(user_id)

        if not signals:
            return {}

        return {
            # Exploration
            "content_sections_visited": signals.content_sections_visited,
            "content_completion_rate": signals.content_completion_rate,
            "easter_eggs_found": signals.easter_eggs_found,
            "avg_time_on_content": signals.avg_time_on_content,
            "revisits_old_content": signals.revisits_old_content,
            "unique_content_per_session": signals.unique_content_per_session,
            "explore_depth": signals.explore_depth,

            # Speed/Efficiency
            "avg_time_to_click": signals.avg_time_to_click,
            "avg_decision_time": signals.avg_decision_time,
            "actions_per_session": signals.actions_per_session,
            "quick_actions_count": signals.quick_actions_count,
            "direct_navigation_ratio": signals.direct_navigation_ratio,
            "skips_explanation": signals.skips_explanation,

            # Emotional
            "emotional_content_views": signals.emotional_content_views,
            "personal_stories_accessed": signals.personal_stories_accessed,
            "likes_vs_saves_ratio": signals.likes_vs_saves_ratio,
            "repeat_emotional_visits": signals.repeat_emotional_visits,
            "diana_mnemonics_interactions": signals.diana_mnemonics_interactions,

            # Analysis
            "evaluation_scores_avg": signals.evaluation_scores_avg,
            "evaluation_completion_rate": signals.evaluation_completion_rate,
            "info_requests": signals.info_requests,
            "systematic_exploration": signals.systematic_exploration,
            "details_viewed": signals.details_viewed,
            "puzzle_completion_time": signals.puzzle_completion_time,

            # Persistence
            "return_after_inactivity": signals.return_after_inactivity,
            "retry_failed_actions": signals.retry_failed_actions,
            "incomplete_flows_completed": signals.incomplete_flows_completed,
            "account_age_days": signals.account_age_days,
            "return_rate": signals.return_rate,
            "streak_restarts": signals.streak_restarts,

            # Patience
            "skip_actions_used": signals.skip_actions_used,
            "current_streak": signals.current_streak,
            "best_streak": signals.best_streak,
            "avg_session_duration": signals.avg_session_duration,
            "session_consistency": signals.session_consistency,
            "slow_decision_count": signals.slow_decision_count,

            # General
            "total_interactions": signals.total_interactions,
            "total_sessions": signals.total_sessions,
        }

    # ============================================================
    # MÉTODOS PRIVADOS
    # ============================================================

    async def _get_or_create_signals(self, user_id: int) -> UserBehaviorSignals:
        """
        Obtiene o crea las señales de comportamiento para un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            Instancia de UserBehaviorSignals
        """
        signals = await self.get_behavior_signals(user_id)

        if not signals:
            # Crear nuevas señales
            signals = UserBehaviorSignals(user_id=user_id)
            self.session.add(signals)
            await self.session.flush()  # Para obtener el ID sin hacer commit aún

        return signals

    @staticmethod
    def _update_average(
        current_avg: float,
        count: int,
        new_value: float,
    ) -> float:
        """Actualiza un promedio incrementalmente."""
        if count <= 0:
            return new_value * 100  # Convertir a entero*100

        # Fórmula de promedio incremental
        return ((current_avg * (count - 1)) + new_value) / count * 100

    @staticmethod
    def _update_ratio(current_ratio: float, is_positive: bool) -> float:
        """Actualiza un ratio (0-1) incrementalmente."""
        alpha = 0.1  # Factor de suavizado

        if is_positive:
            return current_ratio + (alpha * (1.0 - current_ratio))
        else:
            return current_ratio + (alpha * (0.0 - current_ratio))
