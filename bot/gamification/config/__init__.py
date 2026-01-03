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

__all__ = [
    "ExpandedArchetype",
    "ArchetypeDetectionRules",
    "ArchetypeScorer",
    "ARCHETYPE_TRAITS",
    "LEGACY_ARCHETYPE_MAPPING",
    "EconomyConfig",
]
