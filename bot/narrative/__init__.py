"""
Módulo de narrativa - Sistema de fragmentos narrativos con decisiones.

Características:
- Capítulos y fragmentos narrativos
- Decisiones del usuario con ramificaciones
- Requisitos para acceso (VIP, besitos, arquetipo)
- Tracking de progreso y detección de arquetipos
- Integración con gamificación y canales
"""
from bot.narrative.database import (
    ChapterType,
    RequirementType,
    ArchetypeType,
    NarrativeChapter,
    NarrativeFragment,
    FragmentDecision,
    FragmentRequirement,
    UserNarrativeProgress,
    UserDecisionHistory,
)
from bot.narrative.services import (
    NarrativeContainer,
    get_container,
    set_container,
    narrative_container,
)

__all__ = [
    # Enums
    "ChapterType",
    "RequirementType",
    "ArchetypeType",
    # Models
    "NarrativeChapter",
    "NarrativeFragment",
    "FragmentDecision",
    "FragmentRequirement",
    "UserNarrativeProgress",
    "UserDecisionHistory",
    # Services
    "NarrativeContainer",
    "get_container",
    "set_container",
    "narrative_container",
]

__version__ = "0.1.0"
