"""Configuración del módulo narrativo."""

from bot.narrative.config.story_content import (
    SPEAKERS,
    CHALLENGE_TYPES,
    CHAPTERS_FREE,
    CHAPTERS_VIP,
    get_chapter_by_level,
    get_fragments_for_chapter,
    get_next_chapter,
    get_entry_fragment,
    get_all_chapters,
    get_chapter_by_slug,
    get_fragment_by_key,
    validate_chapter,
    validate_fragment,
    get_content_summary
)

from bot.narrative.config.archetypes import (
    ExpandedArchetype,
    ArchetypeDetectionRules,
    ARCHETYPE_COMPATIBILITY_MAPPING,
    map_legacy_archetype,
    ARCHETYPE_TRAITS,
    get_archetype_traits,
    ArchetypeScorer,
    calculate_archetype_scores,
    format_archetype_name,
    get_archetype_description
)

__all__ = [
    # Story content
    "SPEAKERS",
    "CHALLENGE_TYPES",
    "CHAPTERS_FREE",
    "CHAPTERS_VIP",
    "get_chapter_by_level",
    "get_fragments_for_chapter",
    "get_next_chapter",
    "get_entry_fragment",
    "get_all_chapters",
    "get_chapter_by_slug",
    "get_fragment_by_key",
    "validate_chapter",
    "validate_fragment",
    "get_content_summary",
    # Arquetipos
    "ExpandedArchetype",
    "ArchetypeDetectionRules",
    "ARCHETYPE_COMPATIBILITY_MAPPING",
    "map_legacy_archetype",
    "ARCHETYPE_TRAITS",
    "get_archetype_traits",
    "ArchetypeScorer",
    "calculate_archetype_scores",
    "format_archetype_name",
    "get_archetype_description"
]
