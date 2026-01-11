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
from bot.narrative.database.models_immersive import (
    FragmentVariant,
    UserFragmentVisit,
    NarrativeCooldown,
    FragmentChallenge,
    UserChallengeAttempt,
    FragmentTimeWindow,
    ChapterCompletion,
    DailyNarrativeLimit,
)
from bot.narrative.database.onboarding_models import (
    UserOnboardingProgress,
    OnboardingFragment,
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
    # Models - Immersive
    "FragmentVariant",
    "UserFragmentVisit",
    "NarrativeCooldown",
    "FragmentChallenge",
    "UserChallengeAttempt",
    "FragmentTimeWindow",
    "ChapterCompletion",
    "DailyNarrativeLimit",
    # Models - Onboarding
    "UserOnboardingProgress",
    "OnboardingFragment",
]
