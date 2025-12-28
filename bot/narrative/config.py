"""
Configuración del módulo de narrativa inmersiva.

Define valores por defecto para cooldowns, límites y mecánicas
de slowdown que controlan el ritmo de la experiencia narrativa.
"""
import random
from datetime import datetime
from typing import Dict, Any


class NarrativeConfig:
    """
    Configuración de narrativa inmersiva.

    Todos los valores son configurables y pueden ser sobrescritos
    en tiempo de ejecución o desde la base de datos.
    """

    # ========================================
    # COOLDOWNS (en segundos)
    # ========================================

    # Cooldown entre decisiones consecutivas
    DECISION_COOLDOWN_SECONDS: int = 30

    # Cooldown para fragmentos marcados como "intensos"
    INTENSE_FRAGMENT_COOLDOWN_SECONDS: int = 300  # 5 minutos

    # Cooldown después de completar un capítulo
    CHAPTER_COMPLETION_COOLDOWN_SECONDS: int = 600  # 10 minutos

    # Cooldown para reintentar un desafío fallado
    CHALLENGE_RETRY_COOLDOWN_SECONDS: int = 60  # 1 minuto

    # Cooldown mínimo entre visitas al mismo fragmento
    FRAGMENT_REVISIT_COOLDOWN_SECONDS: int = 0  # Desactivado por defecto

    # ========================================
    # LÍMITES DIARIOS
    # ========================================

    # Máximo de fragmentos que se pueden ver por día
    DAILY_FRAGMENT_LIMIT: int = 50  # 0 = sin límite

    # Máximo de decisiones por día
    DAILY_DECISION_LIMIT: int = 30  # 0 = sin límite

    # Máximo de intentos de desafíos por día
    DAILY_CHALLENGE_ATTEMPTS: int = 10  # 0 = sin límite

    # ========================================
    # DESAFÍOS
    # ========================================

    # Intentos permitidos por desafío (por defecto)
    DEFAULT_CHALLENGE_ATTEMPTS: int = 3

    # Timeout para respuestas cronometradas (segundos)
    DEFAULT_CHALLENGE_TIMEOUT: int = 60

    # Número máximo de pistas por desafío
    MAX_HINTS_PER_CHALLENGE: int = 3

    # ========================================
    # TIEMPO DE LECTURA
    # ========================================

    # Tiempo mínimo de lectura estimado por fragmento (segundos)
    MIN_READING_TIME_SECONDS: int = 10

    # Tiempo máximo de lectura antes de considerar "inactivo"
    MAX_READING_TIME_SECONDS: int = 300  # 5 minutos

    # ========================================
    # VENTANAS DE TIEMPO
    # ========================================

    # Definiciones de períodos del día (hora UTC)
    TIME_WINDOWS: Dict[str, tuple] = {
        "morning": (6, 12),      # 6:00 - 11:59
        "afternoon": (12, 18),   # 12:00 - 17:59
        "evening": (18, 22),     # 18:00 - 21:59
        "night": (22, 6),        # 22:00 - 5:59
    }

    # ========================================
    # ARQUETIPOS Y VARIANTES
    # ========================================

    # Confianza mínima para aplicar variante por arquetipo
    MIN_ARCHETYPE_CONFIDENCE: float = 0.6

    # Número de decisiones para detectar arquetipo
    ARCHETYPE_DETECTION_THRESHOLD: int = 5

    # ========================================
    # MENSAJES NARRATIVOS
    # ========================================

    # Mensajes de cooldown (aleatorios)
    COOLDOWN_MESSAGES: Dict[str, list] = {
        "decision": [
            "Diana necesita un momento para procesar lo que acabas de decir...",
            "Tómate un respiro antes de continuar...",
            "Las mejores decisiones se toman con calma...",
        ],
        "fragment": [
            "Este momento necesita tiempo para asimilarse...",
            "Deja que la historia repose un poco...",
            "A veces pausar es parte del viaje...",
        ],
        "chapter": [
            "Has completado un capítulo importante. Descansa antes de continuar...",
            "Lo que viene requiere que estés preparado/a...",
            "El siguiente capítulo te espera, pero no hay prisa...",
        ],
        "challenge": [
            "Piensa un poco más antes de intentar de nuevo...",
            "La respuesta vendrá si le das tiempo...",
            "Cada intento te acerca más a la solución...",
        ],
    }

    # ========================================
    # LÍMITES DE VISUALIZACIÓN
    # ========================================

    # Fragmentos por página en navegación
    FRAGMENTS_PER_PAGE: int = 5

    # Pistas por página en mochila
    CLUES_PER_PAGE: int = 5

    # Capítulos máximos a mostrar en selector
    MAX_CHAPTERS_IN_SELECTOR: int = 6

    # ========================================
    # MÉTODOS DE CONFIGURACIÓN
    # ========================================

    @classmethod
    def get_cooldown_message(cls, cooldown_type: str) -> str:
        """
        Obtiene un mensaje aleatorio para un tipo de cooldown.

        Args:
            cooldown_type: Tipo de cooldown (decision, fragment, chapter, challenge)

        Returns:
            Mensaje aleatorio
        """
        messages = cls.COOLDOWN_MESSAGES.get(cooldown_type, [])
        if messages:
            return random.choice(messages)
        return "Espera un momento antes de continuar..."

    @classmethod
    def get_time_window(cls) -> str:
        """
        Obtiene la ventana de tiempo actual.

        Returns:
            Nombre del período (morning, afternoon, evening, night)
        """
        hour = datetime.utcnow().hour

        for period, (start, end) in cls.TIME_WINDOWS.items():
            if start < end:
                if start <= hour < end:
                    return period
            else:  # Cruza medianoche
                if hour >= start or hour < end:
                    return period

        return "unknown"

    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """
        Convierte la configuración a diccionario.

        Returns:
            Diccionario con todos los valores
        """
        return {
            "cooldowns": {
                "decision": cls.DECISION_COOLDOWN_SECONDS,
                "intense_fragment": cls.INTENSE_FRAGMENT_COOLDOWN_SECONDS,
                "chapter_completion": cls.CHAPTER_COMPLETION_COOLDOWN_SECONDS,
                "challenge_retry": cls.CHALLENGE_RETRY_COOLDOWN_SECONDS,
                "fragment_revisit": cls.FRAGMENT_REVISIT_COOLDOWN_SECONDS,
            },
            "limits": {
                "daily_fragments": cls.DAILY_FRAGMENT_LIMIT,
                "daily_decisions": cls.DAILY_DECISION_LIMIT,
                "daily_challenges": cls.DAILY_CHALLENGE_ATTEMPTS,
            },
            "challenges": {
                "default_attempts": cls.DEFAULT_CHALLENGE_ATTEMPTS,
                "default_timeout": cls.DEFAULT_CHALLENGE_TIMEOUT,
                "max_hints": cls.MAX_HINTS_PER_CHALLENGE,
            },
            "display": {
                "fragments_per_page": cls.FRAGMENTS_PER_PAGE,
                "clues_per_page": cls.CLUES_PER_PAGE,
            },
        }


# Instancia por defecto para importar directamente
narrative_config = NarrativeConfig()
