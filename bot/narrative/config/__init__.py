"""
Narrative configuration module.

Contains configuration files for the narrative system including
story content, chapter structures, and challenge definitions.
"""

# Import NarrativeConfig from the parent config.py module
# Note: bot.narrative.config refers to this package (__init__.py)
# We need to import from the sibling config.py module
import importlib.util
import os

# Load NarrativeConfig from sibling config.py file
_config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.py')
_spec = importlib.util.spec_from_file_location("narrative_config_module", _config_file)
_config_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_config_module)
NarrativeConfig = _config_module.NarrativeConfig

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
    "NarrativeConfig",
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
