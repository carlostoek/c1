"""
Configuración del sistema de detección de arquetipos (FASE 3).

Define umbrales, pesos y configuraciones para el algoritmo de detección
de arquetipos basado en señales de comportamiento del usuario.

Author: Sistema de Gamificación
Version: 1.0
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


# =============================================================================
# 1. CONFIGURACIÓN GENERAL
# =============================================================================

class ArchetypeDetectionConfig:
    """Configuración global del sistema de detección de arquetipos."""

    # Umbrales de detección
    MIN_INTERACTIONS_FOR_DETECTION = 25      # Interacciones mínimas para detectar
    MIN_INTERACTIONS_FOR_REEVALUATION = 50   # Interacciones para re-evaluar
    MIN_CONFIDENCE_THRESHOLD = 0.35          # Confianza mínima (0-1)

    # Timing de re-evaluación
    REEVALUATION_DAYS = 7                     # Días para re-evaluar automáticamente
    REEVALUATION_INTERACTIONS = 50            # Interacciones para re-evaluar

    # Configuración de sesión
    SESSION_TIMEOUT_MINUTES = 30              # Minutos para considerar fin de sesión
    INACTIVITY_DAYS = 7                       # Días para considerar inactividad

    # Pesos por defecto (ajustables sin deploy)
    EXPLORER_WEIGHTS: Dict[str, float] = {
        "completion_rate": 0.25,
        "easter_eggs": 0.20,
        "time_on_content": 0.20,
        "revisits": 0.15,
        "unique_content": 0.20
    }

    DIRECT_WEIGHTS: Dict[str, float] = {
        "time_to_click": 0.30,
        "decision_time": 0.25,
        "actions_per_session": 0.20,
        "direct_nav": 0.15,
        "session_duration": 0.10
    }

    ROMANTIC_WEIGHTS: Dict[str, float] = {
        "emotional_views": 0.30,
        "personal_stories": 0.25,
        "repeat_visits": 0.20,
        "mnemonics": 0.15,
        "likes_ratio": 0.10
    }

    ANALYTICAL_WEIGHTS: Dict[str, float] = {
        "quiz_scores": 0.30,
        "quiz_completion": 0.20,
        "systematic": 0.20,
        "details": 0.15,
        "info_requests": 0.15
    }

    PERSISTENT_WEIGHTS: Dict[str, float] = {
        "returns": 0.30,
        "retries": 0.25,
        "completed_flows": 0.25,
        "streak_restarts": 0.10,
        "account_age": 0.10
    }

    PATIENT_WEIGHTS: Dict[str, float] = {
        "slow_decisions": 0.25,
        "no_skips": 0.20,
        "current_streak": 0.25,
        "best_streak": 0.15,
        "consistency": 0.15
    }

    # Tags de contenido para detección ROMANTIC
    EMOTIONAL_CONTENT_TAGS: List[str] = [
        "emotional",
        "personal",
        "vulnerable",
        "intimate",
        "diary",
        "letter",
        "confession",
        "memory",
        "diana_story"
    ]

    INFORMATIONAL_CONTENT_TAGS: List[str] = [
        "informational",
        "instructional",
        "transactional"
    ]

    # Palabras emocionales (para contenido futuro si se necesita)
    EMOTIONAL_WORDS: set[str] = {
        # Positivas intensas
        "amor", "amo", "quiero", "adoro", "deseo", "anhelo", "sueño",
        "pasión", "corazón", "alma", "sentir", "siento",

        # Conexión
        "conexión", "conectar", "especial", "único", "única", "íntimo",
        "cercano", "profundo", "verdadero", "auténtico", "genuino",

        # Vulnerabilidad
        "miedo", "temo", "vulnerable", "abierto", "honesto", "sincero",
        "confiar", "confianza", "entrega", "rendirme",

        # Intensidad
        "intenso", "increíble", "maravilloso", "hermoso", "perfecto",
        "mágico", "extraordinario", "inolvidable",

        # Relacionales
        "nosotros", "juntos", "compartir", "unir", "pertenecer",
        "acompañar", "entender", "comprender"
    }

    @classmethod
    def get_weights(cls, archetype: str) -> Dict[str, float]:
        """Obtiene pesos para un arquetipo específico."""
        weights_map = {
            "EXPLORER": cls.EXPLORER_WEIGHTS,
            "DIRECT": cls.DIRECT_WEIGHTS,
            "ROMANTIC": cls.ROMANTIC_WEIGHTS,
            "ANALYTICAL": cls.ANALYTICAL_WEIGHTS,
            "PERSISTENT": cls.PERSISTENT_WEIGHTS,
            "PATIENT": cls.PATIENT_WEIGHTS,
        }
        return weights_map.get(archetype, {})

    @classmethod
    def is_emotional_content(cls, tags: List[str]) -> bool:
        """Determina si el contenido es emocional basado en tags."""
        return any(tag in cls.EMOTIONAL_CONTENT_TAGS for tag in tags)

    @classmethod
    def is_informational_content(cls, tags: List[str]) -> bool:
        """Determina si el contenido es informativo basado en tags."""
        return any(tag in cls.INFORMATIONAL_CONTENT_TAGS for tag in tags)


# =============================================================================
# 2. RANGOS DE NORMALIZACIÓN
# =============================================================================

class NormalizationRanges:
    """Rangos mínimos y máximos para normalizar métricas."""

    # EXPLORER
    CONTENT_COMPLETION_RATE = (0.1, 0.8)
    EASTER_EGGS_FOUND = (0, 10)
    AVG_TIME_ON_CONTENT = (30, 180)
    REVISITS_OLD_CONTENT = (0, 20)
    UNIQUE_CONTENT_PER_SESSION = (2, 8)

    # DIRECT
    AVG_TIME_TO_CLICK = (1, 10)
    AVG_DECISION_TIME = (5, 45)
    ACTIONS_PER_SESSION = (3, 15)
    DIRECT_NAVIGATION_RATIO = (0.6, 1.0)
    AVG_SESSION_DURATION = (60, 600)

    # ROMANTIC
    EMOTIONAL_CONTENT_VIEWS = (5, 30)
    PERSONAL_STORIES_ACCESSED = (2, 15)
    REPEAT_EMOTIONAL_VISITS = (3, 20)
    DIANA_MNEMONICS_INTERACTIONS = (1, 10)
    LIKES_VS_SAVES_RATIO = (0.3, 0.8)

    # ANALYTICAL
    EVALUATION_SCORES_AVG = (60, 95)
    EVALUATION_COMPLETION_RATE = (0.7, 1.0)
    SYSTEMATIC_EXPLORATION = (0.6, 0.95)
    DETAILS_VIEWED = (5, 30)
    INFO_REQUESTS = (2, 15)

    # PERSISTENT
    RETURN_AFTER_INACTIVITY = (0, 5)
    RETRY_FAILED_ACTIONS = (0, 10)
    INCOMPLETE_FLOWS_COMPLETED = (0, 5)
    STREAK_RESTARTS = (0, 5)
    ACCOUNT_AGE_DAYS = (30, 365)

    # PATIENT
    SLOW_DECISION_COUNT = (3, 15)
    SKIP_ACTIONS_USED = (0, 5)  # Invertido: menos es mejor
    CURRENT_STREAK = (7, 60)
    BEST_STREAK = (14, 100)
    SESSION_CONSISTENCY = (0.7, 0.95)


# =============================================================================
# 3. FUNCIONES DE AYUDA
# =============================================================================

def normalize(value: float, min_val: float, max_val: float) -> float:
    """
    Normaliza un valor al rango 0-1.

    Args:
        value: Valor a normalizar
        min_val: Valor mínimo esperado
        max_val: Valor máximo esperado

    Returns:
        Valor normalizado entre 0 y 1
    """
    if min_val >= max_val:
        return 0.0

    try:
        if value <= min_val:
            return 0.0
        if value >= max_val:
            return 1.0
        return (value - min_val) / (max_val - min_val)
    except (TypeError, ValueError):
        return 0.0


def normalize_inverted(value: float, min_val: float, max_val: float) -> float:
    """
    Normaliza un valor al rango 0-1 de forma invertida.

    Útil para métricas donde "menos es mejor" (ej: skips usados).

    Args:
        value: Valor a normalizar
        min_val: Valor mínimo esperado
        max_val: Valor máximo esperado

    Returns:
        Valor normalizado entre 0 y 1 (invertido)
    """
    return 1.0 - normalize(value, min_val, max_val)


# =============================================================================
# 4. DEFINICIONES DE SCORES
# =============================================================================

class ScoreDefinitions:
    """
    Definiciones de fórmulas de scoring para cada arquetipo.

    CORREGIDO para FASE 3 - No depende de TEXT_RESPONSE,
    sino de interacciones reales con botones y navegación.
    """

    @staticmethod
    def calculate_explorer_score(signals: Dict[str, Any]) -> float:
        """Calcula score EXPLORER basado en métricas de exploración."""
        weights = ArchetypeDetectionConfig.EXPLORER_WEIGHTS
        ranges = NormalizationRanges

        # Obtener valores (con defaults a 0 si no existen)
        completion_rate = signals.get("content_completion_rate", 0.0) / 100.0
        easter_eggs = signals.get("easter_eggs_found", 0)
        time_on_content = signals.get("avg_time_on_content", 0.0) / 100.0
        revisits = signals.get("revisits_old_content", 0)
        unique_content = signals.get("unique_content_per_session", 0.0) / 100.0

        # Calcular score
        score = (
            normalize(completion_rate, *ranges.CONTENT_COMPLETION_RATE) * weights["completion_rate"] +
            normalize(easter_eggs, *ranges.EASTER_EGGS_FOUND) * weights["easter_eggs"] +
            normalize(time_on_content, *ranges.AVG_TIME_ON_CONTENT) * weights["time_on_content"] +
            normalize(revisits, *ranges.REVISITS_OLD_CONTENT) * weights["revisits"] +
            normalize(unique_content, *ranges.UNIQUE_CONTENT_PER_SESSION) * weights["unique_content"]
        )

        return min(1.0, max(0.0, score))

    @staticmethod
    def calculate_direct_score(signals: Dict[str, Any]) -> float:
        """Calcula score DIRECT basado en velocidad de interacción."""
        weights = ArchetypeDetectionConfig.DIRECT_WEIGHTS
        ranges = NormalizationRanges

        time_to_click = signals.get("avg_time_to_click", 0.0) / 100.0
        decision_time = signals.get("avg_decision_time", 0.0) / 100.0
        actions_per_session = signals.get("actions_per_session", 0.0) / 100.0
        direct_nav = signals.get("direct_navigation_ratio", 0.0) / 100.0
        session_duration = signals.get("avg_session_duration", 0.0) / 100.0

        score = (
            normalize(time_to_click, *ranges.AVG_TIME_TO_CLICK) * weights["time_to_click"] +
            (1 - normalize(decision_time, *ranges.AVG_DECISION_TIME)) * weights["decision_time"] +
            normalize(actions_per_session, *ranges.ACTIONS_PER_SESSION) * weights["actions_per_session"] +
            normalize(direct_nav, *ranges.DIRECT_NAVIGATION_RATIO) * weights["direct_nav"] +
            (1 - normalize(session_duration, *ranges.AVG_SESSION_DURATION)) * weights["session_duration"]
        )

        return min(1.0, max(0.0, score))

    @staticmethod
    def calculate_romantic_score(signals: Dict[str, Any]) -> float:
        """Calcula score ROMANTIC basado en contenido emocional consumido."""
        weights = ArchetypeDetectionConfig.ROMANTIC_WEIGHTS
        ranges = NormalizationRanges

        emotional_views = signals.get("emotional_content_views", 0)
        personal_stories = signals.get("personal_stories_accessed", 0)
        repeat_visits = signals.get("repeat_emotional_visits", 0)
        mnemonics = signals.get("diana_mnemonics_interactions", 0)
        likes_ratio = signals.get("likes_vs_saves_ratio", 0.0) / 100.0

        score = (
            normalize(emotional_views, *ranges.EMOTIONAL_CONTENT_VIEWS) * weights["emotional_views"] +
            normalize(personal_stories, *ranges.PERSONAL_STORIES_ACCESSED) * weights["personal_stories"] +
            normalize(repeat_visits, *ranges.REPEAT_EMOTIONAL_VISITS) * weights["repeat_visits"] +
            normalize(mnemonics, *ranges.DIANA_MNEMONICS_INTERACTIONS) * weights["mnemonics"] +
            normalize(likes_ratio, *ranges.LIKES_VS_SAVES_RATIO) * weights["likes_ratio"]
        )

        return min(1.0, max(0.0, score))

    @staticmethod
    def calculate_analytical_score(signals: Dict[str, Any]) -> float:
        """Calcula score ANALYTICAL basado en análisis y evaluaciones."""
        weights = ArchetypeDetectionConfig.ANALYTICAL_WEIGHTS
        ranges = NormalizationRanges

        eval_scores = signals.get("evaluation_scores_avg", 0.0) / 100.0
        eval_completion = signals.get("evaluation_completion_rate", 0.0) / 100.0
        systematic = signals.get("systematic_exploration", 0.0) / 100.0
        details = signals.get("details_viewed", 0)
        info_requests = signals.get("info_requests", 0)

        score = (
            normalize(eval_scores, *ranges.EVALUATION_SCORES_AVG) * weights["quiz_scores"] +
            normalize(eval_completion, *ranges.EVALUATION_COMPLETION_RATE) * weights["quiz_completion"] +
            normalize(systematic, *ranges.SYSTEMATIC_EXPLORATION) * weights["systematic"] +
            normalize(details, *ranges.DETAILS_VIEWED) * weights["details"] +
            normalize(info_requests, *ranges.INFO_REQUESTS) * weights["info_requests"]
        )

        return min(1.0, max(0.0, score))

    @staticmethod
    def calculate_persistent_score(signals: Dict[str, Any]) -> float:
        """Calcula score PERSISTENT basado en retorno y persistencia."""
        weights = ArchetypeDetectionConfig.PERSISTENT_WEIGHTS
        ranges = NormalizationRanges

        returns = signals.get("return_after_inactivity", 0)
        retries = signals.get("retry_failed_actions", 0)
        completed_flows = signals.get("incomplete_flows_completed", 0)
        streak_restarts = signals.get("streak_restarts", 0)
        account_age = signals.get("account_age_days", 0)

        score = (
            normalize(returns, *ranges.RETURN_AFTER_INACTIVITY) * weights["returns"] +
            normalize(retries, *ranges.RETRY_FAILED_ACTIONS) * weights["retries"] +
            normalize(completed_flows, *ranges.INCOMPLETE_FLOWS_COMPLETED) * weights["completed_flows"] +
            normalize(streak_restarts, *ranges.STREAK_RESTARTS) * weights["streak_restarts"] +
            normalize(account_age, *ranges.ACCOUNT_AGE_DAYS) * weights["account_age"]
        )

        return min(1.0, max(0.0, score))

    @staticmethod
    def calculate_patient_score(signals: Dict[str, Any]) -> float:
        """Calcula score PATIENT basado en paciencia y consistencia."""
        weights = ArchetypeDetectionConfig.PATIENT_WEIGHTS
        ranges = NormalizationRanges

        slow_decisions = signals.get("slow_decision_count", 0)
        skips = signals.get("skip_actions_used", 0)
        current_streak = signals.get("current_streak", 0)
        best_streak = signals.get("best_streak", 0)
        consistency = signals.get("session_consistency", 0.0) / 100.0

        score = (
            normalize(slow_decisions, *ranges.SLOW_DECISION_COUNT) * weights["slow_decisions"] +
            normalize_inverted(skips, *ranges.SKIP_ACTIONS_USED) * weights["no_skips"] +
            normalize(current_streak, *ranges.CURRENT_STREAK) * weights["current_streak"] +
            normalize(best_streak, *ranges.BEST_STREAK) * weights["best_streak"] +
            normalize(consistency, *ranges.SESSION_CONSISTENCY) * weights["consistency"]
        )

        return min(1.0, max(0.0, score))

    @classmethod
    def calculate_all_scores(cls, signals: Dict[str, Any]) -> Dict[str, float]:
        """Calcula scores de todos los arquetipos."""
        return {
            "EXPLORER": cls.calculate_explorer_score(signals),
            "DIRECT": cls.calculate_direct_score(signals),
            "ROMANTIC": cls.calculate_romantic_score(signals),
            "ANALYTICAL": cls.calculate_analytical_score(signals),
            "PERSISTENT": cls.calculate_persistent_score(signals),
            "PATIENT": cls.calculate_patient_score(signals),
        }


# =============================================================================
# 5. DATA CLASSES
# =============================================================================

@dataclass
class ArchetypeResult:
    """Resultado de la detección de arquetipo."""

    archetype: Optional[str]  # Arquetipo detectado o None
    confidence: float  # Confianza de la detección (0-1)
    scores: Dict[str, float]  # Scores de todos los arquetipos (0-1)
    reason: str  # Razón del resultado ("detected", "insufficient_data", "low_confidence")
    interactions_count: int  # Total de interacciones consideradas
    detected_at: Optional[str] = None  # Timestamp ISO de detección (opcional)


@dataclass
class ArchetypeInsights:
    """Insights detallados del arquetipo del usuario."""

    archetype: Optional[str]
    confidence: float
    top_3_archetypes: List[tuple[str, float]]  # [(archetype, score), ...]
    top_signals: List[tuple[str, str]]  # [(signal_name, description), ...]
    recommendations: List[str]  # Recomendaciones basadas en arquetipo
