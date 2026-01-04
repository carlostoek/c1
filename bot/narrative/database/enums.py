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
    """Arquetipos de usuario detectados por comportamiento.

    SISTEMA EXPANDIDO (6 arquetipos):
    - EXPLORER: Busca cada detalle, encuentra contenido oculto
    - DIRECT: Respuestas concisas, decide rápido
    - ROMANTIC: Poético, busca conexión emocional
    - ANALYTICAL: Reflexivo, comprensión intelectual
    - PERSISTENT: No se rinde, múltiples intentos
    - PATIENT: Procesa profundamente, toma tiempo

    SISTEMA LEGACY (mantenido para compatibilidad):
    - IMPULSIVE: Reacciona rápido (< 5 segundos) → mapea a DIRECT o EXPLORER
    - CONTEMPLATIVE: Toma su tiempo (> 30 segundos) → mapea a ANALYTICAL o PATIENT
    - SILENT: No reacciona (timeout) → requiere más datos
    """

    # ========================================
    # SISTEMA EXPANDIDO (6 arquetipos nuevos)
    # ========================================
    EXPLORER = "explorer"        # El que busca cada detalle
    DIRECT = "direct"            # Respuestas concisas, al punto
    ROMANTIC = "romantic"        # Poético, busca conexión emocional
    ANALYTICAL = "analytical"    # Reflexivo, comprensión intelectual
    PERSISTENT = "persistent"    # No se rinde, múltiples intentos
    PATIENT = "patient"          # Procesa profundamente, toma tiempo

    # ========================================
    # SISTEMA LEGACY (mantenido para compatibilidad)
    # ========================================
    UNKNOWN = "unknown"          # No determinado aún
    IMPULSIVE = "impulsive"      # Reacciona rápido (< 5 segundos) [LEGACY]
    CONTEMPLATIVE = "contemplative"  # Toma su tiempo (> 30 segundos) [LEGACY]
    SILENT = "silent"            # No reacciona (timeout) [LEGACY]

    @property
    def is_expanded(self) -> bool:
        """True si es parte del sistema expandido de 6 arquetipos."""
        return self.value in [
            "explorer", "direct", "romantic",
            "analytical", "persistent", "patient"
        ]

    @property
    def is_legacy(self) -> bool:
        """True si es parte del sistema legacy de 3 arquetipos."""
        return self.value in ["impulsive", "contemplative", "silent"]

    @classmethod
    def get_expanded_archetypes(cls) -> list:
        """Retorna los 6 arquetipos del sistema expandido."""
        return [
            cls.EXPLORER, cls.DIRECT, cls.ROMANTIC,
            cls.ANALYTICAL, cls.PERSISTENT, cls.PATIENT
        ]

    @classmethod
    def get_legacy_archetypes(cls) -> list:
        """Retorna los 3 arquetipos del sistema legacy."""
        return [cls.IMPULSIVE, cls.CONTEMPLATIVE, cls.SILENT]
