"""
Servicios del módulo de narrativa.
"""
from bot.narrative.services.container import (
    NarrativeContainer,
    get_container,
    set_container,
    narrative_container,
)

__all__ = [
    "NarrativeContainer",
    "get_container",
    "set_container",
    "narrative_container",
]
