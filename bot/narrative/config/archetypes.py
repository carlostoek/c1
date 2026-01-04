"""Configuración expandida de arquetipos de usuario.

Este archivo define el sistema extendido de 6 arquetipos que reemplaza
los 3 arquetipos básicos (IMPULSIVE, CONTEMPLATIVE, SILENT).

Los 6 arquetipos expandidos permiten una segmentación más rica del
comportamiento del usuario, lo que permite:
- Contenido narrativo personalizado
- Misiones adaptadas al estilo del usuario
- Mensajes de Lucien específicos por arquetipo
- Triggers de conversión personalizados

Mapeo de compatibilidad:
- IMPULSIVE → DIRECT o EXPLORER (según velocidad de exploración)
- CONTEMPLATIVE → ANALYTICAL o PATIENT (según profundidad de procesamiento)
- SILENT → Requiere más datos para clasificar

Uso:
    from bot.narrative.config.archetypes import (
        ExpandedArchetype,
        ArchetypeDetectionRules,
        calculate_archetype_scores
    )

    scores = calculate_archetype_scores(user_data)
    dominant = max(scores, key=scores.get)
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


# ============================================================
# 1. ENUM DE ARQUETIPOS EXPANDIDOS
# ============================================================

class ExpandedArchetype(str, Enum):
    """Arquetipos de usuario expandidos (6 valores).

    Cada arquetipo representa un patrón de comportamiento distinto
    que afecta cómo el usuario experimenta la narrativa.
    """

    EXPLORER = "explorer"      # El que busca cada detalle
    DIRECT = "direct"          # Respuestas concisas, al punto
    ROMANTIC = "romantic"      # Poético, busca conexión emocional
    ANALYTICAL = "analytical"  # Reflexivo, comprensión intelectual
    PERSISTENT = "persistent"  # No se rinde, múltiples intentos
    PATIENT = "patient"        # Procesa profundamente, toma tiempo

    def __str__(self) -> str:
        return self.value

    @property
    def display_name(self) -> str:
        """Nombre para mostrar en UI."""
        names = {
            "explorer": "Explorador",
            "direct": "Directo",
            "romantic": "Romántico",
            "analytical": "Analítico",
            "persistent": "Persistente",
            "patient": "Paciente"
        }
        return names.get(self.value, "Desconocido")

    @property
    def emoji(self) -> str:
        """Emoji representativo del arquetipo."""
        emojis = {
            "explorer": "🔍",
            "direct": "🎯",
            "romantic": "🌹",
            "analytical": "🧠",
            "persistent": "💪",
            "patient": "⏳"
        }
        return emojis.get(self.value, "❓")


# ============================================================
# 2. REGLAS DE DETECCIÓN POR ARQUETIPO
# ============================================================

class ArchetypeDetectionRules:
    """Reglas de detección para cada arquetipo.

    Cada arquetipo tiene señales específicas que, cuando se detectan,
    aumentan la probabilidad de que el usuario pertenezca a esa categoría.
    """

    # EXPLORER: Ve más del 80% del contenido, encuentra easter eggs
    EXPLORER = {
        "content_view_percentage": 0.8,     # Ve más del 80% del contenido disponible
        "easter_eggs_found": 1,              # Ha encontrado contenido oculto
        "avg_time_per_content": 30,          # Tiempo alto en cada contenido (segundos)
        "revisits_content": True,            # Vuelve a ver contenido previo
        "uses_search": True,                 # Usa funciones de búsqueda
        "explores_all_options": True         # Prueba todas las opciones en decisiones
    }

    # DIRECT: Respuestas cortas, decide rápido, navegación lineal
    DIRECT = {
        "avg_response_length": 10,           # Respuestas cortas (<10 palabras)
        "decision_time": 5,                  # Decide rápido (<5 segundos)
        "skips_optional_content": True,      # Salta contenido opcional
        "linear_navigation": True,           # Navegación lineal, sin explorar
        "uses_fast_forward": True,           # Usa funciones de avanzar rápido
        "minimal_engagement": False          # No se detiene en detalles
    }

    # ROMANTIC: Lenguaje emocional, respuestas elaboradas
    ROMANTIC = {
        "uses_emotional_language": True,     # Detectar palabras emocionales
        "avg_response_length": 30,           # Respuestas elaboradas (>30 palabras)
        "reacts_to_emotional_content": True, # Reacciona a contenido sentimental
        "uses_adjectives_frequently": True,  # Lenguaje descriptivo
        "seeks_connection": True,            # Busca conexión con Diana
        "values_atmosphere": True            # Valora la atmósfera sobre la acción
    }

    # ANALYTICAL: Hace preguntas, alto puntaje en evaluaciones
    ANALYTICAL = {
        "asks_questions": True,              # Hace preguntas en sus respuestas
        "evaluation_scores": 80,             # Alto puntaje en evaluaciones (>80%)
        "structured_responses": True,        # Respuestas organizadas
        "seeks_clarification": True,         # Pide aclaraciones
        "analyzes_before_deciding": True,    # Analiza antes de decidir
        "notes_patterns": True               # Detecta y comenta patrones
    }

    # PERSISTENT: Regresa múltiples veces, reintenta desafíos
    PERSISTENT = {
        "return_after_inactivity_count": 2,  # Regresa múltiples veces tras inactividad
        "retry_failed_challenges": True,     # Reintenta desafíos fallidos
        "total_sessions_multiplier": 1.5,    # Más sesiones que promedio (>1.5x)
        "completes_difficult_missions": True,# Completa misiones difíciles
        "streak_length": 7,                  # Rachas largas (>7 días)
        "never_gives_up": True               # Completa todo lo que empieza
    }

    # PATIENT: Respuestas pensadas, nunca usa skip, rachas largas
    PATIENT = {
        "avg_response_time": 30,             # Respuestas pensadas (>30 segundos)
        "never_uses_skip": True,             # Nunca usa funciones de saltar
        "streak_length": 14,                 # Rachas muy largas (>14 días)
        "consistent_daily_activity": True,   # Actividad consistente diaria
        "consumes_all_content": True,        # Consume todo el contenido disponible
        "reads_thoroughly": True             # Lee todo completamente
    }

    @classmethod
    def get_rules(cls, archetype: ExpandedArchetype) -> Dict[str, Any]:
        """Obtiene las reglas de un arquetipo específico.

        Args:
            archetype: Arquetipo a consultar

        Returns:
            Dict con reglas de detección
        """
        return getattr(cls, archetype.name.upper(), {})

    @classmethod
    def all_rules(cls) -> Dict[str, Dict[str, Any]]:
        """Retorna todas las reglas de todos los arquetipos.

        Returns:
            Dict mapeando nombre de arquetipo a sus reglas
        """
        return {
            "EXPLORER": cls.EXPLORER,
            "DIRECT": cls.DIRECT,
            "ROMANTIC": cls.ROMANTIC,
            "ANALYTICAL": cls.ANALYTICAL,
            "PERSISTENT": cls.PERSISTENT,
            "PATIENT": cls.PATIENT
        }


# ============================================================
# 3. MAPEO DE COMPATIBILIDAD (ARQUETIPOS ANTIGUOS → NUEVOS)
# ============================================================

ARCHETYPE_COMPATIBILITY_MAPPING = {
    # IMPULSIVE puede mapearse a:
    "IMPULSIVE": {
        "primary": ExpandedArchetype.DIRECT,      # Si es rápido y conciso
        "secondary": ExpandedArchetype.EXPLORER   # Si explora rápidamente
    },

    # CONTEMPLATIVE puede mapearse a:
    "CONTEMPLATIVE": {
        "primary": ExpandedArchetype.ANALYTICAL,  # Si analiza profundamente
        "secondary": ExpandedArchetype.PATIENT    # Si toma su tiempo
    },

    # SILENT requiere más datos
    "SILENT": {
        "primary": None,    # No se puede determinar sin más datos
        "secondary": None,
        "requires_more_data": True
    }
}


def map_legacy_archetype(
    legacy_archetype: str,
    user_data: Optional[Dict[str, Any]] = None
) -> Optional[ExpandedArchetype]:
    """Mapea un arquetipo legacy al sistema expandido.

    Args:
        legacy_archetype: Arquetipo antiguo (IMPULSIVE, CONTEMPLATIVE, SILENT)
        user_data: Datos opcionales del usuario para decidir entre primary/secondary

    Returns:
        ExpandedArchetype o None si requiere más datos
    """
    mapping = ARCHETYPE_COMPATIBILITY_MAPPING.get(legacy_archetype)

    if not mapping:
        return None

    # Si requiere más datos (SILENT)
    if mapping.get("requires_more_data"):
        return None

    # Si hay datos de usuario, decidir entre primary/secondary
    if user_data:
        # Lógica de decisión basada en datos adicionales
        if legacy_archetype == "IMPULSIVE":
            # Si explora mucho → EXPLORER, si no → DIRECT
            if user_data.get("content_view_percentage", 0) > 0.7:
                return ExpandedArchetype.EXPLORER
            return ExpandedArchetype.DIRECT

        elif legacy_archetype == "CONTEMPLATIVE":
            # Si hace preguntas → ANALYTICAL, si no → PATIENT
            if user_data.get("asks_questions", False):
                return ExpandedArchetype.ANALYTICAL
            return ExpandedArchetype.PATIENT

    # Default: retornar primary
    return mapping.get("primary")


# ============================================================
# 4. CARACTERÍSTICAS NARRATIVAS POR ARQUETIPO
# ============================================================

ARCHETYPE_TRAITS = {
    "EXPLORER": {
        "lucien_tone": "desafiante, le oculta cosas deliberadamente",
        "narrative_style": "misterio, descubrimiento, contenido oculto",
        "mission_type": "búsqueda, descubrimiento, encontrar easter eggs",
        "conversion_trigger": "contenido oculto exclusivo VIP",
        "lucien_phrases": [
            "Su curiosidad es... notable.",
            "Ve todo. ¿O eso cree?",
            "Hay más aquí de lo que parece.",
            "No todos encuentran lo que usted encuentra."
        ],
        "preferred_rewards": ["NARRATIVE", "EASTER_EGGS"],
        "shop_preferences": ["NARRATIVE", "Llaves"]
    },

    "DIRECT": {
        "lucien_tone": "conciso, sin rodeos, respeto por su tiempo",
        "narrative_style": "directo, eficiente, sin relleno",
        "mission_type": "acciones claras y medibles",
        "conversion_trigger": "oferta directa con beneficios listados",
        "lucien_phrases": [
            "Va al grano. Me gusta.",
            "No pierde tiempo. Apreciable.",
            "Eficiente. Refrescante.",
            "Su tiempo es valioso. Lo es el mío también."
        ],
        "preferred_rewards": ["BESITOS", "CONSUMABLE"],
        "shop_preferences": ["CONSUMABLE", "Efímeros"]
    },

    "ROMANTIC": {
        "lucien_tone": "suavemente irónico, reconoce su sensibilidad",
        "narrative_style": "emocional, atmosférico, poético",
        "mission_type": "conexión emocional, experiencias íntimas",
        "conversion_trigger": "contenido emocional exclusivo VIP",
        "lucien_phrases": [
            "Sus palabras revelan más de lo que cree.",
            "Siente. Eso es... raro últimamente.",
            "Busca significado. Lo encontrará... o no.",
            "La emoción tiene su lugar. Aquí, especialmente."
        ],
        "preferred_rewards": ["NARRATIVE", "COSMETIC"],
        "shop_preferences": ["COSMETIC", "Distintivos"]
    },

    "ANALYTICAL": {
        "lucien_tone": "respetuoso de su intelecto, desafiante",
        "narrative_style": "complejo, con capas, requiere análisis",
        "mission_type": "resolución de puzzles, comprender la historia",
        "conversion_trigger": "contenido profundo y analítico VIP",
        "lucien_phrases": [
            "Una mente notable.",
            "Analiza. Cuestiona. Comprende.",
            "Entiende más de lo que muestra.",
            "La superficie es solo el comienzo."
        ],
        "preferred_rewards": ["NARRATIVE", "DIGITAL"],
        "shop_preferences": ["DIGITAL", "Reliquias"]
    },

    "PERSISTENT": {
        "lucien_tone": "respetuoso, reconocimiento de su tenacidad",
        "narrative_style": "progresivo, acumulativo, recompensa esfuerzo",
        "mission_type": "logros a largo plazo, streaks, desafíos difíciles",
        "conversion_trigger": "reconocimiento exclusivo VIP por dedicación",
        "lucien_phrases": [
            "Su tenacidad es... admirable.",
            "No se rinde. Cualidad rara.",
            "La persistencia tiene recompensas.",
            "Continúa. Eso es todo lo que pido."
        ],
        "preferred_rewards": ["BESITOS", "COSMETIC"],
        "shop_preferences": ["COSMETIC", "Distintivos"]
    },

    "PATIENT": {
        "lucien_tone": "apreciativo, valora su paciencia",
        "narrative_style": "lento pero profundo, revelación gradual",
        "mission_type": "esperar, observar, contenido que se revela con tiempo",
        "conversion_trigger": "acceso anticipado VIP por fidelidad",
        "lucien_phrases": [
            "La paciencia es una virtud. La posee.",
            "Espera. Procesa. Actúa cuando debe.",
            "El tiempo revela lo que la prisa oculta.",
            "Todo llega a su tiempo. El suyo también."
        ],
        "preferred_rewards": ["NARRATIVE", "VIP_DAYS"],
        "shop_preferences": ["NARRATIVE", "Llaves"]
    }
}


def get_archetype_traits(archetype: ExpandedArchetype) -> Dict[str, Any]:
    """Obtiene las características narrativas de un arquetipo.

    Args:
        archetype: Arquetipo a consultar

    Returns:
        Dict con características narrativas
    """
    return ARCHETYPE_TRAITS.get(archetype.name.upper(), {})


# ============================================================
# 5. CALCULADOR DE PUNTAJES DE ARQUETIPO
# ============================================================

class ArchetypeScorer:
    """Calcula puntajes de arquetipo basado en datos del usuario.

    El puntaje va de 0 a 100 para cada arquetipo.
    El arquetipo dominante es el que tiene puntaje > 60.
    Si ninguno supera 60, el usuario permanece como "Observado".
    """

    @staticmethod
    def calculate_response_time_score(avg_time: float) -> Dict[str, float]:
        """Calcula puntajes basados en tiempo de respuesta.

        Args:
            avg_time: Tiempo promedio de respuesta en segundos

        Returns:
            Dict con puntajes por arquetipo
        """
        scores = {
            "DIRECT": 0.0,
            "EXPLORER": 0.0,
            "PATIENT": 0.0,
            "ANALYTICAL": 0.0
        }

        if avg_time < 5:
            # Muy rápido → DIRECT
            scores["DIRECT"] = 80.0
            scores["EXPLORER"] = 40.0

        elif avg_time < 15:
            # Rápido pero no impulsivo → EXPLORER o DIRECT mix
            scores["DIRECT"] = 60.0
            scores["EXPLORER"] = 50.0

        elif avg_time < 30:
            # Tiempo medio → ANALYTICAL
            scores["ANALYTICAL"] = 60.0
            scores["EXPLORER"] = 30.0

        else:
            # Lento → PATIENT
            scores["PATIENT"] = 80.0
            scores["ANALYTICAL"] = 50.0

        return scores

    @staticmethod
    def calculate_engagement_score(user_data: Dict[str, Any]) -> Dict[str, float]:
        """Calcula puntajes basados en patrones de engagement.

        Args:
            user_data: Dict con datos del usuario

        Returns:
            Dict con puntajes por arquetipo
        """
        scores = {
            "EXPLORER": 0.0,
            "ROMANTIC": 0.0,
            "ANALYTICAL": 0.0,
            "PERSISTENT": 0.0,
            "PATIENT": 0.0
        }

        # Content view percentage
        view_pct = user_data.get("content_view_percentage", 0.0)
        if view_pct > 0.8:
            scores["EXPLORER"] += 30.0
            scores["PATIENT"] += 20.0

        # Revisits content
        if user_data.get("revisits_content", False):
            scores["EXPLORER"] += 25.0
            scores["ROMANTIC"] += 10.0

        # Asks questions
        if user_data.get("asks_questions", False):
            scores["ANALYTICAL"] += 30.0

        # Emotional language
        if user_data.get("uses_emotional_language", False):
            scores["ROMANTIC"] += 35.0

        # Retry failed challenges
        if user_data.get("retry_failed_challenges", False):
            scores["PERSISTENT"] += 30.0

        # Long streak
        streak = user_data.get("streak_length", 0)
        if streak >= 14:
            scores["PATIENT"] += 30.0
            scores["PERSISTENT"] += 20.0
        elif streak >= 7:
            scores["PERSISTENT"] += 25.0

        # Daily consistent activity
        if user_data.get("consistent_daily_activity", False):
            scores["PATIENT"] += 25.0

        return scores

    @staticmethod
    def calculate_archetype_scores(
        user_data: Dict[str, Any],
        confidence_threshold: float = 60.0
    ) -> Dict[str, float]:
        """Calcula puntajes completos de arquetipo.

        Args:
            user_data: Dict con datos completos del usuario:
                - avg_response_time: Tiempo promedio de respuesta (segundos)
                - content_view_percentage: Porcentaje de contenido visto
                - avg_response_length: Longitud promedio de respuesta (palabras)
                - revisits_content: Si vuelve a ver contenido
                - asks_questions: Si hace preguntas
                - uses_emotional_language: Si usa lenguaje emocional
                - retry_failed_challenges: Si reintenta desafíos
                - streak_length: Días de racha actual
                - consistent_daily_activity: Actividad diaria consistente
                - total_sessions: Total de sesiones
                - avg_sessions_per_week: Sesiones promedio por semana

            confidence_threshold: Umbral para considerar arquetipo dominante (default: 60)

        Returns:
            Dict mapeando nombre de arquetipo a puntaje 0-100
        """
        # Inicializar scores
        scores = {
            "EXPLORER": 0.0,
            "DIRECT": 0.0,
            "ROMANTIC": 0.0,
            "ANALYTICAL": 0.0,
            "PERSISTENT": 0.0,
            "PATIENT": 0.0
        }

        # 1. Score basado en tiempo de respuesta
        avg_time = user_data.get("avg_response_time", 15.0)
        time_scores = ArchetypeScorer.calculate_response_time_score(avg_time)
        for arch, score in time_scores.items():
            scores[arch] += score

        # 2. Score basado en engagement
        engagement_scores = ArchetypeScorer.calculate_engagement_score(user_data)
        for arch, score in engagement_scores.items():
            scores[arch] += score

        # 3. Score basado en longitud de respuesta
        avg_length = user_data.get("avg_response_length", 15)

        if avg_length < 10:
            # Cortas → DIRECT
            scores["DIRECT"] += 20.0
        elif avg_length > 30:
            # Largas → ROMANTIC o ANALYTICAL
            if user_data.get("uses_emotional_language", False):
                scores["ROMANTIC"] += 30.0
            else:
                scores["ANALYTICAL"] += 30.0

        # 4. Score basado en sesiones (PERSISTENT)
        total_sessions = user_data.get("total_sessions", 0)
        avg_sessions = user_data.get("avg_sessions_per_week", 0)

        if total_sessions > avg_sessions * 1.5:
            scores["PERSISTENT"] += 30.0

        # Normalizar todos los scores a 0-100
        max_score = max(scores.values()) if scores else 1.0
        if max_score > 100:
            for arch in scores:
                scores[arch] = (scores[arch] / max_score) * 100

        return scores

    @staticmethod
    def get_dominant_archetype(
        scores: Dict[str, float],
        confidence_threshold: float = 60.0
    ) -> Optional[ExpandedArchetype]:
        """Obtiene el arquetipo dominante basado en puntajes.

        Args:
            scores: Dict con puntajes por arquetipo
            confidence_threshold: Umbral mínimo para ser dominante

        Returns:
            ExpandedArchetype dominante o None si ninguno supera el umbral
        """
        # Encontrar máximo
        max_archetype = max(scores, key=scores.get)
        max_score = scores[max_archetype]

        # Verificar si supera umbral
        if max_score >= confidence_threshold:
            try:
                return ExpandedArchetype(max_archetype.lower())
            except ValueError:
                return None

        return None

    @staticmethod
    def get_archetype_confidence(
        archetype: ExpandedArchetype,
        scores: Dict[str, float]
    ) -> float:
        """Calcula qué tan confiable es la clasificación de un arquetipo.

        Args:
            archetype: Arquetipo a evaluar
            scores: Dict con puntajes por arquetipo

        Returns:
            Confianza 0.0-1.0 basada en diferencia con segundo más alto
        """
        arch_score = scores.get(archetype.name.upper(), 0.0)

        # Encontrar segundo más alto
        sorted_scores = sorted(scores.values(), reverse=True)

        if len(sorted_scores) < 2:
            return 1.0 if arch_score > 0 else 0.0

        second_highest = sorted_scores[1]

        # Si el primero es mucho más alto que el segundo, mayor confianza
        if second_highest == 0:
            return 1.0

        confidence = arch_score / (arch_score + second_highest)

        return min(max(confidence, 0.0), 1.0)


# ============================================================
# 6. FUNCIÓN PRINCIPAL (INTERFACE SIMPLE)
# ============================================================

def calculate_archetype_scores(
    user_data: Dict[str, Any],
    confidence_threshold: float = 60.0
) -> tuple[Optional[ExpandedArchetype], Dict[str, float], float]:
    """Calcula arquetipo dominante y retorna resultados completos.

    Esta es la función principal que se debe usar para detectar arquetipos.

    Args:
        user_data: Dict con datos del usuario (ver ArchetypeScorer.calculate_archetype_scores)
        confidence_threshold: Umbral para considerar arquetipo dominante (default: 60)

    Returns:
        Tuple de:
        - dominant_archetype: ExpandedArchetype o None
        - all_scores: Dict con todos los puntajes 0-100
        - confidence: Confianza 0.0-1.0 en la clasificación

    Example:
        >>> user_data = {
        ...     "avg_response_time": 8.5,
        ...     "content_view_percentage": 0.75,
        ...     "revisits_content": True,
        ...     "streak_length": 5
        ... }
        >>> arch, scores, conf = calculate_archetype_scores(user_data)
        >>> print(f"Dominante: {arch}, Confianza: {conf:.2f}")
    """
    # Calcular scores
    scores = ArchetypeScorer.calculate_archetype_scores(user_data)

    # Obtener dominante
    dominant = ArchetypeScorer.get_dominant_archetype(scores, confidence_threshold)

    # Calcular confianza
    if dominant:
        confidence = ArchetypeScorer.get_archetype_confidence(dominant, scores)
    else:
        confidence = 0.0

    return dominant, scores, confidence


# ============================================================
# 7. HELPERS DE DISPLAY
# ============================================================

def format_archetype_name(archetype: ExpandedArchetype) -> str:
    """Formatea el nombre del arquetipo con emoji.

    Args:
        archetype: Arquetipo a formatear

    Returns:
        String con emoji y nombre (ej: "🔍 Explorador")
    """
    return f"{archetype.emoji} {archetype.display_name}"


def get_archetype_description(archetype: ExpandedArchetype) -> str:
    """Retorna una descripción del arquetipo para mostrar al usuario.

    Args:
        archetype: Arquetipo a describir

    Returns:
        Descripción en voz de Lucien
    """
    descriptions = {
        ExpandedArchetype.EXPLORER: (
            "Usted busca. Siempre busca. "
            "Hay más aquí de lo que la mayoría ve, y usted lo sabe."
        ),
        ExpandedArchetype.DIRECT: (
            "Va al grano. No pierde tiempo. "
            "Su eficiencia es... refrescante en este mundo de indecisos."
        ),
        ExpandedArchetype.ROMANTIC: (
            "Siente. Conecta. "
            "Sus emociones lo guían más de lo que admite."
        ),
        ExpandedArchetype.ANALYTICAL: (
            "Analiza. Comprende. "
            "Su mente procesa capas que otros ni siquiera saben que existen."
        ),
        ExpandedArchetype.PERSISTENT: (
            "No se rinde. Continúa. "
            "La mayoría abandonaría mucho antes. Usted no."
        ),
        ExpandedArchetype.PATIENT: (
            "Espera. Procesa. Actúa cuando debe. "
            "La paciencia es una virtud que posee en abundancia."
        )
    }

    return descriptions.get(archetype, "Arquetipo desconocido.")
