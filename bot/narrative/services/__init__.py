"""
Servicios del módulo de narrativa.
"""
from bot.narrative.services.container import (
    NarrativeContainer,
    get_container,
    set_container,
    narrative_container,
)
from bot.narrative.services.fragment import FragmentService
from bot.narrative.services.progress import ProgressService
from bot.narrative.services.decision import DecisionService
from bot.narrative.services.reaction_narrative import NarrativeReactionService

__all__ = [
    # Container
    "NarrativeContainer",
    "get_container",
    "set_container",
    "narrative_container",
    # Services
    "FragmentService",
    "ProgressService",
    "DecisionService",
    "NarrativeReactionService",
]
