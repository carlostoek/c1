"""
Enumeraciones para el módulo de narrativa.

Define tipos de capítulos, requisitos y arquetipos de usuario.
"""
from enum import Enum


class ChapterType(str, Enum):
    """Tipo de capítulo narrativo."""

    FREE = "free"  # Los Kinkys (accesible para todos)
    VIP = "vip"    # El Diván (requiere suscripción VIP)


class RequirementType(str, Enum):
    """Tipo de requisito para acceder a fragmento."""

    NONE = "none"           # Sin requisitos
    VIP_STATUS = "vip"      # Debe ser VIP
    MIN_BESITOS = "besitos" # Besitos mínimos
    ARCHETYPE = "archetype" # Arquetipo específico
    DECISION = "decision"   # Decisión previa tomada
    ITEM = "item"           # Posee item de la tienda (slug del item)

    # --- Nuevos requisitos para sistema inmersivo ---
    HAS_CLUE = "clue"           # Tiene pista específica (item slug con is_clue=True)
    VISITED = "visited"          # Visitó fragmento X al menos una vez
    VISIT_COUNT = "visit_count"  # Visitó fragmento X cantidad de veces
    TIME_SPENT = "time_spent"    # Pasó N segundos acumulados en fragmento
    COOLDOWN_PASSED = "cooldown" # Ha pasado el cooldown desde última interacción
    TIME_WINDOW = "time_window"  # Dentro de ventana horaria
    CHAPTER_COMPLETE = "chapter" # Completó capítulo específico


class VariantConditionType(str, Enum):
    """Tipo de condición para activar variante de fragmento."""

    VISIT_COUNT = "visit_count"    # Número de visitas al fragmento
    HAS_CLUE = "has_clue"          # Tiene pista específica
    ARCHETYPE = "archetype"        # Arquetipo del usuario
    TIME_OF_DAY = "time_of_day"    # Hora del día (morning, afternoon, night)
    DAYS_SINCE_START = "days"      # Días desde que inició historia
    DECISION_TAKEN = "decision"    # Tomó decisión específica en otro fragmento
    CHAPTER_COMPLETE = "chapter"   # Completó capítulo específico
    FIRST_VISIT = "first_visit"    # Es primera visita (condición especial)
    RETURN_VISIT = "return_visit"  # Es visita de retorno (>= 2)


class ChallengeType(str, Enum):
    """Tipo de desafío/acertijo en fragmento."""

    TEXT_INPUT = "text_input"       # Usuario escribe respuesta
    CHOICE_SEQUENCE = "sequence"    # Secuencia correcta de decisiones
    TIMED_RESPONSE = "timed"        # Responder antes de timeout
    MEMORY_RECALL = "memory"        # Recordar dato de fragmento anterior
    OBSERVATION = "observation"     # Encontrar detalle oculto


class CooldownType(str, Enum):
    """Tipo de cooldown narrativo."""

    FRAGMENT = "fragment"     # Cooldown para acceder a fragmento
    CHAPTER = "chapter"       # Cooldown para acceder a capítulo
    DECISION = "decision"     # Cooldown entre decisiones
    CHALLENGE = "challenge"   # Cooldown para reintentar desafío


class ArchetypeType(str, Enum):
    """Arquetipos de usuario detectados por comportamiento."""

    UNKNOWN = "unknown"              # No determinado aún
    IMPULSIVE = "impulsive"          # Reacciona rápido (< 5 segundos)
    CONTEMPLATIVE = "contemplative"  # Toma su tiempo (> 30 segundos)
    SILENT = "silent"                # No reacciona (timeout)
