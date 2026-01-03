"""
Narrative configuration module.

Contains configuration files for the narrative system including
story content, chapter structures, and challenge definitions.
"""

from bot.narrative.config.story_content import (
    SPEAKERS,
    CHALLENGE_TYPES,
    CHAPTERS_FREE,
    CHAPTERS_VIP,
    get_chapter_by_level,
    get_chapter_by_id,
    get_fragments_for_chapter,
    get_next_chapter,
    get_speaker_by_name,
)

__all__ = [
    "SPEAKERS",
    "CHALLENGE_TYPES",
    "CHAPTERS_FREE",
    "CHAPTERS_VIP",
    "get_chapter_by_level",
    "get_chapter_by_id",
    "get_fragments_for_chapter",
    "get_next_chapter",
    "get_speaker_by_name",
]
