"""
Base de datos del módulo de narrativa.
"""
from bot.narrative.database.enums import ChapterType, RequirementType, ArchetypeType
from bot.narrative.database.models import (
    NarrativeChapter,
    NarrativeFragment,
    FragmentDecision,
    FragmentRequirement,
    UserNarrativeProgress,
    UserDecisionHistory,
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
]
