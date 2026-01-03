"""
Gamification configuration module.

Contains configuration files for the gamification system including
archetypes, economy, and other game rules.
"""

from bot.gamification.config.archetypes import (
    ExpandedArchetype,
    ArchetypeDetectionRules,
    ArchetypeScorer,
    ARCHETYPE_TRAITS,
    LEGACY_ARCHETYPE_MAPPING,
)
from bot.gamification.config.economy import EconomyConfig
from bot.gamification.config.archetype_detection import (
    ArchetypeDetectionConfig,
    NormalizationRanges,
    normalize,
    normalize_inverted,
    ScoreDefinitions,
    ArchetypeResult,
    ArchetypeInsights,
)

__all__ = [
    "ExpandedArchetype",
    "ArchetypeDetectionRules",
    "ArchetypeScorer",
    "ARCHETYPE_TRAITS",
    "LEGACY_ARCHETYPE_MAPPING",
    "EconomyConfig",
    "ArchetypeDetectionConfig",
    "NormalizationRanges",
    "normalize",
    "normalize_inverted",
    "ScoreDefinitions",
    "ArchetypeResult",
    "ArchetypeInsights",
]
