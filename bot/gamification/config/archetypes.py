"""
Sistema Expandido de Arquetipos de Usuario

Expande el sistema básico de 3 arquetipos (IMPULSIVE, CONTEMPLATIVE, SILENT)
a 6 arquetipos detallados para una personalización más precisa del contenido.

Este archivo es solo configuración. NO modifica modelos de BD existentes.
Las migraciones de enums se harán en fases posteriores.

Author: Sistema de Gamificación
Version: 1.0
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


# =============================================================================
# 1. ENUM EXPANDED ARCHETYPE
# =============================================================================

class ExpandedArchetype(str, Enum):
    """
    Arquetipos expandidos de usuario para detección de comportamiento.

    Expande los 3 arquetipos básicos a 6 más específicos:
    - EXPLORER: Busca cada detalle, explora todo
    - DIRECT: Respuestas concisas, decisiones rápidas
    - ROMANTIC: Búsqueda de conexión emocional
    - ANALYTICAL: Comprensión intelectual, pregunta
    - PERSISTENT: No se rinde, reintenta
    - PATIENT: Procesa profundamente, toma tiempo

    Compatibilidad con sistema antiguo:
    - IMPULSIVE → Puede mapearse a DIRECT o EXPLORER
    - CONTEMPLATIVE → Puede mapearse a ANALYTICAL o PATIENT
    - SILENT → Requiere más datos para clasificar
    """

    EXPLORER = "explorer"      # Busca cada detalle
    DIRECT = "direct"          # Respuestas concisas, rápido
    ROMANTIC = "romantic"      # Conexión emocional
    ANALYTICAL = "analytical"  # Comprensión intelectual
    PERSISTENT = "persistent"  # No se rinde, reintenta
    PATIENT = "patient"        # Procesa profundamente


# =============================================================================
# 2. CLASE ARCHETYPE DETECTION RULES
# =============================================================================

@dataclass
class DetectionRule:
    """
    Regla individual de detección para un arquetipo.

    Attributes:
        name: Nombre descriptivo de la regla
        condition: Condición a evaluar (diccionario con criterios)
        weight: Peso de esta regla en el score total (0-1)
        description: Explicación de qué detecta esta regla
    """

    name: str
    condition: Dict[str, Any]
    weight: float
    description: str


class ArchetypeDetectionRules:
    """
    Reglas de detección para cada arquetipo expandido.

    Cada arquetipo tiene múltiples reglas que se evalúan
    contra los datos del usuario para calcular un score 0-100.
    """

    # -------------------------------------------------------------------------
    # EXPLORER: Busca cada detalle
    # -------------------------------------------------------------------------
    EXPLORER_RULES = [
        DetectionRule(
            name="high_content_view_percentage",
            condition={
                "metric": "content_view_percentage",
                "operator": ">",
                "value": 0.8
            },
            weight=0.3,
            description="Ve más del 80% del contenido disponible"
        ),
        DetectionRule(
            name="found_easter_eggs",
            condition={
                "metric": "easter_eggs_found",
                "operator": ">",
                "value": 0
            },
            weight=0.3,
            description="Ha encontrado contenido oculto"
        ),
        DetectionRule(
            name="high_time_per_content",
            condition={
                "metric": "avg_time_per_content_seconds",
                "operator": ">",
                "value": 30
            },
            weight=0.2,
            description="Tiempo alto en cada contenido (>30s)"
        ),
        DetectionRule(
            name="revisits_content",
            condition={
                "metric": "revisits_content",
                "operator": "==",
                "value": True
            },
            weight=0.2,
            description="Vuelve a ver contenido previo"
        ),
    ]

    # -------------------------------------------------------------------------
    # DIRECT: Respuestas concisas y rápidas
    # -------------------------------------------------------------------------
    DIRECT_RULES = [
        DetectionRule(
            name="short_responses",
            condition={
                "metric": "avg_response_length_words",
                "operator": "<",
                "value": 10
            },
            weight=0.3,
            description="Respuestas cortas (<10 palabras)"
        ),
        DetectionRule(
            name="fast_decisions",
            condition={
                "metric": "avg_decision_time_seconds",
                "operator": "<",
                "value": 5
            },
            weight=0.3,
            description="Decide rápido (<5 segundos)"
        ),
        DetectionRule(
            name="skips_optional",
            condition={
                "metric": "skips_optional_content",
                "operator": "==",
                "value": True
            },
            weight=0.2,
            description="Salta contenido opcional"
        ),
        DetectionRule(
            name="linear_navigation",
            condition={
                "metric": "linear_navigation_ratio",
                "operator": ">",
                "value": 0.8
            },
            weight=0.2,
            description="Navegación lineal (>80%)"
        ),
    ]

    # -------------------------------------------------------------------------
    # ROMANTIC: Búsqueda de conexión emocional
    # -------------------------------------------------------------------------
    ROMANTIC_RULES = [
        DetectionRule(
            name="emotional_language",
            condition={
                "metric": "uses_emotional_language",
                "operator": "==",
                "value": True
            },
            weight=0.3,
            description="Usa lenguaje emocional"
        ),
        DetectionRule(
            name="long_responses",
            condition={
                "metric": "avg_response_length_words",
                "operator": ">",
                "value": 30
            },
            weight=0.25,
            description="Respuestas elaboradas (>30 palabras)"
        ),
        DetectionRule(
            name="reacts_to_emotional",
            condition={
                "metric": "reacts_to_emotional_content",
                "operator": "==",
                "value": True
            },
            weight=0.25,
            description="Reacciona a contenido sentimental"
        ),
        DetectionRule(
            name="uses_adjectives",
            condition={
                "metric": "adjective_frequency",
                "operator": ">",
                "value": 0.15
            },
            weight=0.2,
            description="Alta frecuencia de adjetivos (>15%)"
        ),
    ]

    # -------------------------------------------------------------------------
    # ANALYTICAL: Comprensión intelectual
    # -------------------------------------------------------------------------
    ANALYTICAL_RULES = [
        DetectionRule(
            name="asks_questions",
            condition={
                "metric": "asks_questions",
                "operator": "==",
                "value": True
            },
            weight=0.3,
            description="Hace preguntas en sus respuestas"
        ),
        DetectionRule(
            name="high_evaluation_scores",
            condition={
                "metric": "avg_evaluation_score_percent",
                "operator": ">",
                "value": 80
            },
            weight=0.3,
            description="Alto puntaje en evaluaciones (>80%)"
        ),
        DetectionRule(
            name="structured_responses",
            condition={
                "metric": "structured_response_pattern",
                "operator": "==",
                "value": True
            },
            weight=0.2,
            description="Respuestas organizadas"
        ),
        DetectionRule(
            name="seeks_clarification",
            condition={
                "metric": "clarification_requests",
                "operator": ">",
                "value": 2
            },
            weight=0.2,
            description="Pide aclaraciones (>2 veces)"
        ),
    ]

    # -------------------------------------------------------------------------
    # PERSISTENT: No se rinde
    # -------------------------------------------------------------------------
    PERSISTENT_RULES = [
        DetectionRule(
            name="multiple_returns",
            condition={
                "metric": "return_after_inactivity_count",
                "operator": ">",
                "value": 2
            },
            weight=0.3,
            description="Regresa múltiples veces tras inactividad"
        ),
        DetectionRule(
            name="retries_challenges",
            condition={
                "metric": "retries_failed_challenges",
                "operator": "==",
                "value": True
            },
            weight=0.3,
            description="Reintenta desafíos fallidos"
        ),
        DetectionRule(
            name="high_session_count",
            condition={
                "metric": "total_sessions",
                "operator": ">",
                "value": 0  # Se compara con avg_sessions * 1.5
            },
            weight=0.2,
            description="Más sesiones que promedio"
        ),
        DetectionRule(
            name="completes_difficult",
            condition={
                "metric": "completes_difficult_missions",
                "operator": "==",
                "value": True
            },
            weight=0.2,
            description="Completa misiones difíciles"
        ),
    ]

    # -------------------------------------------------------------------------
    # PATIENT: Procesa profundamente
    # -------------------------------------------------------------------------
    PATIENT_RULES = [
        DetectionRule(
            name="thoughtful_responses",
            condition={
                "metric": "avg_response_time_seconds",
                "operator": ">",
                "value": 30
            },
            weight=0.3,
            description="Respuestas pensadas (>30 segundos)"
        ),
        DetectionRule(
            name="never_skips",
            condition={
                "metric": "never_uses_skip",
                "operator": "==",
                "value": True
            },
            weight=0.25,
            description="Nunca usa funciones de saltar"
        ),
        DetectionRule(
            name="long_streaks",
            condition={
                "metric": "streak_length_days",
                "operator": ">",
                "value": 14
            },
            weight=0.25,
            description="Rachas largas (>14 días)"
        ),
        DetectionRule(
            name="consistent_activity",
            condition={
                "metric": "daily_activity_consistency",
                "operator": ">",
                "value": 0.7
            },
            weight=0.2,
            description="Actividad consistente (>70%)"
        ),
    ]

    # -------------------------------------------------------------------------
    # MAPEO DE REGLAS POR ARQUETIPO
    # -------------------------------------------------------------------------
    RULES_BY_ARCHETYPE: Dict[ExpandedArchetype, List[DetectionRule]] = {
        ExpandedArchetype.EXPLORER: EXPLORER_RULES,
        ExpandedArchetype.DIRECT: DIRECT_RULES,
        ExpandedArchetype.ROMANTIC: ROMANTIC_RULES,
        ExpandedArchetype.ANALYTICAL: ANALYTICAL_RULES,
        ExpandedArchetype.PERSISTENT: PERSISTENT_RULES,
        ExpandedArchetype.PATIENT: PATIENT_RULES,
    }


# =============================================================================
# 3. MAPEO DE COMPATIBILIDAD CON ARQUETIPOS ANTIGUOS
# =============================================================================

"""
Mapeo de compatibilidad entre arquetipos antiguos y nuevos.

Este mapeo ayuda a migrar usuarios clasificados con el sistema
antiguo (3 arquetipos) al nuevo sistema (6 arquetipos).

Uso:
    # Usuario era IMPULSIVE en sistema antiguo
    possible_new = LEGACY_ARCHETYPE_MAPPING.get("impulsive")
    # → [DIRECT, EXPLORER]

    # Se evalúan reglas de ambos para determinar cuál encaja mejor
"""

LEGACY_ARCHETYPE_MAPPING: Dict[str, List[ExpandedArchetype]] = {
    # Sistema antiguo: IMPULSIVE (< 5 segundos)
    "impulsive": [
        ExpandedArchetype.DIRECT,     # Respuestas rápidas y concisas
        ExpandedArchetype.EXPLORER,   # Explora rápidamente
    ],

    # Sistema antiguo: CONTEMPLATIVE (> 30 segundos)
    "contemplative": [
        ExpandedArchetype.ANALYTICAL,  # Analiza profundamente
        ExpandedArchetype.PATIENT,    # Toma su tiempo para procesar
    ],

    # Sistema antiguo: SILENT (timeout, sin respuesta)
    "silent": [
        # Requiere más datos - podría ser cualquiera
        # Se deja vacío para indicar "indeterminado"
    ],

    # Sistema antiguo: UNKNOWN
    "unknown": [],
}


# =============================================================================
# 4. ARCHETYPE SCORER
# =============================================================================

class ArchetypeScorer:
    """
    Calculadora de scores de arquetipo para usuarios.

    Evalúa los datos de comportamiento del usuario contra las reglas
    de cada arquetipo y retorna un score 0-100 para cada uno.

    El arquetipo dominante es el que tiene score > 60%.
    Si ninguno supera 60%, el usuario permanece como "sin arquetipo detectado".
    """

    @staticmethod
    def calculate_archetype_scores(user_data: Dict[str, Any]) -> Dict[ExpandedArchetype, float]:
        """
        Calcula el score de cada arquetipo basado en datos del usuario.

        Args:
            user_data: Diccionario con métricas de comportamiento del usuario.
                Debe contener:
                - content_view_percentage: float (0-1)
                - easter_eggs_found: int
                - avg_time_per_content_seconds: float
                - revisits_content: bool
                - avg_response_length_words: float
                - avg_decision_time_seconds: float
                - skips_optional_content: bool
                - linear_navigation_ratio: float
                - uses_emotional_language: bool
                - reacts_to_emotional_content: bool
                - adjective_frequency: float
                - asks_questions: bool
                - avg_evaluation_score_percent: float
                - structured_response_pattern: bool
                - clarification_requests: int
                - return_after_inactivity_count: int
                - retries_failed_challenges: bool
                - total_sessions: int
                - avg_sessions: float (para comparación)
                - completes_difficult_missions: bool
                - avg_response_time_seconds: float
                - never_uses_skip: bool
                - streak_length_days: int
                - daily_activity_consistency: float

        Returns:
            Diccionario con arquetipo como clave y score (0-100) como valor.

        Example:
            user_data = {
                "avg_response_length_words": 8,
                "avg_decision_time_seconds": 3,
                "skips_optional_content": True,
                # ... más datos
            }
            scores = ArchetypeScorer.calculate_archetype_scores(user_data)
            # {<Archetype.EXPLORER>: 45.0, <Archetype.DIRECT>: 85.0, ...}
        """
        scores: Dict[ExpandedArchetype, float] = {}

        for archetype, rules in ArchetypeDetectionRules.RULES_BY_ARCHETYPE.items():
            archetype_score = 0.0

            for rule in rules:
                rule_score = ArchetypeScorer._evaluate_rule(rule, user_data)
                archetype_score += rule_score * rule.weight

            # Normalizar a 0-100
            scores[archetype] = min(100.0, max(0.0, archetype_score * 100))

        return scores

    @staticmethod
    def get_dominant_archetype(scores: Dict[ExpandedArchetype, float]) -> Optional[ExpandedArchetype]:
        """
        Determina el arquetipo dominante basado en scores.

        Args:
            scores: Diccionario de scores por arquetipo (0-100)

        Returns:
            Arquetipo dominante si alguno tiene >60%, None en caso contrario
        """
        threshold = 60.0

        # Encontrar el score máximo
        if not scores:
            return None

        max_archetype = max(scores.items(), key=lambda x: x[1])

        if max_archetype[1] >= threshold:
            return max_archetype[0]

        return None

    @staticmethod
    def _evaluate_rule(rule: DetectionRule, user_data: Dict[str, Any]) -> float:
        """
        Evalúa una regla individual contra los datos del usuario.

        Returns:
            1.0 si la condición se cumple, 0.0 si no
        """
        metric = rule.condition.get("metric")
        operator = rule.condition.get("operator")
        expected_value = rule.condition.get("value")

        if metric not in user_data:
            return 0.0

        actual_value = user_data[metric]

        try:
            if operator == ">":
                return 1.0 if actual_value > expected_value else 0.0
            elif operator == "<":
                return 1.0 if actual_value < expected_value else 0.0
            elif operator == ">=":
                return 1.0 if actual_value >= expected_value else 0.0
            elif operator == "<=":
                return 1.0 if actual_value <= expected_value else 0.0
            elif operator == "==":
                return 1.0 if actual_value == expected_value else 0.0
            elif operator == "!=":
                return 1.0 if actual_value != expected_value else 0.0
            else:
                return 0.0
        except (TypeError, ValueError):
            return 0.0


# =============================================================================
# 5. ARCHETYPE TRAITS (CARACTERÍSTICAS NARRATIVAS)
# =============================================================================

"""
Características narrativas de cada arquetipo.

Define cómo Lucien debe adaptar su tono, qué tipo de misiones ofrecer,
y qué activa la conversión a VIP para cada arquetipo.
"""

ARCHETYPE_TRAITS: Dict[ExpandedArchetype, Dict[str, Any]] = {

    ExpandedArchetype.EXPLORER: {
        "lucien_tone": "desafiante, le oculta cosas deliberadamente",
        "mission_type": "búsqueda, descubrimiento, encontrar lo oculto",
        "content_preference": "contenido con capas, secrets, easter eggs",
        "conversion_trigger": "contenido oculto exclusivo VIP que solo los exploradores encuentran",
        "lucien_example": "Hay más de lo que ve. Pero no voy a decírselo. Busque.",
        "vip_pitch": "Diana tiene contenido que ni siquiera aparece en el mapa. Solo los verdaderos exploradores encuentran.",
    },

    ExpandedArchetype.DIRECT: {
        "lucien_tone": "conciso, sin rodeos, respeto por su tiempo",
        "mission_type": "acciones claras y medibles, objetivos directos",
        "content_preference": "contenido que va al grano, sin perder tiempo",
        "conversion_trigger": "oferta directa con beneficios listados claramente",
        "lucien_example": "No pierde tiempo. Se lo agradezco. Vayamos al punto.",
        "vip_pitch": "Acceso directo. Sin intermediarios. Contenido exclusivo. Ahorra tiempo.",
    },

    ExpandedArchetype.ROMANTIC: {
        "lucien_tone": "más suave, reconoce su sensibilidad, aún sarcástico",
        "mission_type": "conexión emocional, historias personales, descubrir sentimientos",
        "content_preference": "contenido emotivo, historias íntimas de Diana",
        "conversion_trigger": "contenido sentimental VIP, conexión emocional exclusiva",
        "lucien_example": "Siente. Interesante. No muchos sienten tan profundamente.",
        "vip_pitch": "Diana comparte cosas... sentimentales. Que no muestra a cualquiera. Solo a los que sienten.",
    },

    ExpandedArchetype.ANALYTICAL: {
        "lucien_tone": "respetuoso de su intellecto, desafíos mentales",
        "mission_type": "resolver enigmas, comprender la lógica, descubrir patrones",
        "content_preference": "contenido complejo, con profundidad, que requiere pensar",
        "conversion_trigger": "contenido intelectual VIP, análisis exclusivo, behind-the-scenes",
        "lucien_example": "Su mente es... notable. Entiende lo que otros no.",
        "vip_pitch": "Contenido que requiere más que observación. Requiere comprensión. Diana respeta eso.",
    },

    ExpandedArchetype.PERSISTENT: {
        "lucien_tone": "reconoce su tenacidad, le hace trabajar más",
        "mission_type": "misiones difíciles, multi-paso, que requieren volver",
        "content_preference": "contenido que se desbloquea con persistencia, progresión",
        "conversion_trigger": "contenido progresivo VIP, acceso a largo plazo",
        "lucien_example": "Sigue regresando. La mayoría se rinde. Usted no.",
        "vip_pitch": "Diana valora los que persisten. Hay contenido que toma tiempo... desbloquear.",
    },

    ExpandedArchetype.PATIENT: {
        "lucien_tone": "respetuoso del ritmo, no lo presiona, reconoce su profundidad",
        "mission_type": "observación, procesamiento, descubrimiento gradual",
        "content_preference": "contenido que se revela lentamente, sorpresas pacientes",
        "conversion_trigger": "contenido VIP por tiempo, recompensas de paciencia",
        "lucien_example": "Toma su tiempo. Bien. Las cosas buenas... esperan.",
        "vip_pitch": "Diana tiene contenido que premia la paciencia. Los que esperan... reciben más.",
    },
}


# =============================================================================
# 6. HELPER FUNCTIONS
# =============================================================================

def get_archetype_traits(archetype: ExpandedArchetype) -> Optional[Dict[str, Any]]:
    """
    Obtiene las características narrativas de un arquetipo.

    Args:
        archetype: Arquetipo a consultar

    Returns:
        Diccionario con características o None si no existe
    """
    return ARCHETYPE_TRAITS.get(archetype)


def get_archetype_by_name(name: str) -> Optional[ExpandedArchetype]:
    """
    Obtiene un arquetipo por su nombre (string).

    Args:
        name: Nombre del arquetipo (ej: "explorer", "direct")

    Returns:
        Instancia de ExpandedArchetype o None
    """
    try:
        return ExpandedArchetype(name)
    except ValueError:
        return None


def get_legacy_mapping_options(legacy_archetype: str) -> List[ExpandedArchetype]:
    """
    Obtiene las opciones de mapeo desde un arquetipo antiguo.

    Args:
        legacy_archetype: Nombre del arquetipo antiguo (ej: "IMPULSIVE")

    Returns:
        Lista de arquetipos nuevos posibles
    """
    return LEGACY_ARCHETYPE_MAPPING.get(legacy_archetype, [])


def detect_archetype_from_user_data(user_data: Dict[str, Any]) -> Optional[ExpandedArchetype]:
    """
    Detecta el arquetipo de un usuario desde sus datos de comportamiento.

    Args:
        user_data: Diccionario con métricas del usuario

    Returns:
        Arquetipo detectado si score > 60%, None en caso contrario
    """
    scores = ArchetypeScorer.calculate_archetype_scores(user_data)
    return ArchetypeScorer.get_dominant_archetype(scores)
