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


class ArchetypeType(str, Enum):
    """Arquetipos de usuario detectados por comportamiento."""

    UNKNOWN = "unknown"              # No determinado aún
    IMPULSIVE = "impulsive"          # Reacciona rápido (< 5 segundos)
    CONTEMPLATIVE = "contemplative"  # Toma su tiempo (> 30 segundos)
    SILENT = "silent"                # No reacciona (timeout)
