"""Enums y tipos personalizados para el módulo de gamificación.

Contiene:
- Enums para campos de modelos (MissionType, RewardType, etc.)
- TypedDicts para validación de JSON (criterios, metadata)
"""

from enum import Enum
from typing import TypedDict, Literal, Optional


# ============================================================
# ENUMS PRINCIPALES
# ============================================================


class MissionType(str, Enum):
    """Tipos de misión disponibles en el sistema."""

    ONE_TIME = "one_time"
    DAILY = "daily"
    WEEKLY = "weekly"
    STREAK = "streak"

    def __str__(self) -> str:
        return self.value


class MissionStatus(str, Enum):
    """Estado de progreso de una misión para un usuario."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CLAIMED = "claimed"
    EXPIRED = "expired"

    def __str__(self) -> str:
        return self.value


class RewardType(str, Enum):
    """Tipos de recompensa disponibles en el sistema."""

    BADGE = "badge"
    ITEM = "item"
    PERMISSION = "permission"
    TITLE = "title"
    BESITOS = "besitos"
    # Cross-module rewards (Fase 1 - Integración Tienda)
    SHOP_ITEM = "shop_item"  # Otorga item específico de la tienda
    # Cross-module rewards (Fase 2 - Integración Narrativa)
    NARRATIVE_UNLOCK = "narrative_unlock"  # Desbloquea contenido narrativo
    # Cross-module rewards (Fase 3 - Integración VIP)
    VIP_DAYS = "vip_days"  # Otorga días de suscripción VIP

    def __str__(self) -> str:
        return self.value


class BadgeRarity(str, Enum):
    """Nivel de rareza de un badge."""

    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"

    def __str__(self) -> str:
        return self.value


class ObtainedVia(str, Enum):
    """Forma en que se obtuvo una recompensa."""

    MISSION = "mission"
    PURCHASE = "purchase"
    ADMIN_GRANT = "admin_grant"
    EVENT = "event"
    LEVEL_UP = "level_up"
    AUTO_UNLOCK = "auto_unlock"  # Desbloqueada automáticamente al cumplir condición

    def __str__(self) -> str:
        return self.value


class TransactionType(str, Enum):
    """Tipo de transacción de besitos."""

    MISSION_REWARD = "mission_reward"
    REACTION = "reaction"
    REACTION_CUSTOM = "reaction_custom"  # Reacciones personalizadas en broadcasting
    PURCHASE = "purchase"
    ADMIN_GRANT = "admin_grant"
    ADMIN_DEDUCT = "admin_deduct"
    REFUND = "refund"
    STREAK_BONUS = "streak_bonus"
    LEVEL_UP_BONUS = "level_up_bonus"
    DAILY_GIFT = "daily_gift"  # Regalo diario

    def __str__(self) -> str:
        return self.value


class TemplateCategory(str, Enum):
    """Categoría de plantilla de configuración."""

    MISSION = "mission"
    REWARD = "reward"
    LEVEL_PROGRESSION = "level_progression"
    FULL_SYSTEM = "full_system"

    def __str__(self) -> str:
        return self.value


# ============================================================
# TYPEDDICTS PARA VALIDACIÓN JSON
# ============================================================


class StreakCriteria(TypedDict):
    """Criterios para misión tipo streak."""

    type: Literal["streak"]
    days: int
    require_consecutive: bool


class DailyCriteria(TypedDict):
    """Criterios para misión tipo daily."""

    type: Literal["daily"]
    count: int
    specific_reaction: Optional[str]  # Emoji o None


class WeeklyCriteria(TypedDict):
    """Criterios para misión tipo weekly."""

    type: Literal["weekly"]
    target: int
    specific_days: Optional[list[int]]  # [0-6] o None


class OneTimeCriteria(TypedDict):
    """Criterios para misión tipo one_time."""

    type: Literal["one_time"]


# Union de todos los criterios posibles
MissionCriteria = StreakCriteria | DailyCriteria | WeeklyCriteria | OneTimeCriteria


class BadgeMetadata(TypedDict):
    """Metadata para badges."""

    icon: str  # Emoji
    rarity: str  # BadgeRarity value


class PermissionMetadata(TypedDict):
    """Metadata para recompensas tipo permission."""

    permission_key: str  # ej: "custom_emoji", "change_username"
    expires_at: Optional[str]  # ISO datetime o None (permanente)


class ItemMetadata(TypedDict):
    """Metadata para recompensas tipo item."""

    item_key: str  # Identificador único del item
    item_name: str
    icon: str  # Emoji representativo


class TitleMetadata(TypedDict):
    """Metadata para recompensas tipo title."""

    title_text: str
    color: Optional[str]  # Código hex o None
    prefix: Optional[str]  # Emoji o text prefix


class UnlockCondition(TypedDict):
    """Condición para desbloquear una recompensa (legacy)."""

    type: Literal["mission", "level", "besitos"]
    value: int  # mission_id, level_id, o cantidad de besitos


class NarrativeChapterCondition(TypedDict):
    """Condición: completar capítulo narrativo."""

    type: Literal["narrative_chapter"]
    chapter_slug: str  # slug del capítulo (ej: "los-kinkys")


class NarrativeFragmentCondition(TypedDict):
    """Condición: llegar a fragmento narrativo."""

    type: Literal["narrative_fragment"]
    fragment_key: str  # key del fragmento (ej: "scene_3a")


class NarrativeDecisionCondition(TypedDict):
    """Condición: tomar decisión específica."""

    type: Literal["narrative_decision"]
    decision_key: str  # key de decisión


class ArchetypeCondition(TypedDict):
    """Condición: tener arquetipo específico."""

    type: Literal["archetype"]
    archetype: str  # "impulsive", "contemplative", "silent"


# Union de todas las condiciones posibles
AnyUnlockCondition = (
    UnlockCondition
    | NarrativeChapterCondition
    | NarrativeFragmentCondition
    | NarrativeDecisionCondition
    | ArchetypeCondition
)


class BesitosMetadata(TypedDict):
    """Metadata para recompensas tipo besitos."""

    amount: int
    multiplier: Optional[float]  # Multiplicador de besitos (ej: 1.5x)


class ShopItemMetadata(TypedDict):
    """Metadata para recompensas tipo shop_item (integración tienda).

    Permite otorgar items de la tienda como recompensa de misiones.
    El item debe existir previamente en la tienda.
    """

    item_id: int  # ID del ShopItem en la tienda
    item_slug: str  # Slug del item (para validación)
    quantity: int  # Cantidad a otorgar (default: 1)


class NarrativeUnlockMetadata(TypedDict):
    """Metadata para recompensas tipo narrative_unlock (integración narrativa).

    Permite desbloquear contenido narrativo como recompensa de misiones.
    """

    unlock_type: Literal["chapter", "fragment"]  # Qué desbloquear
    chapter_slug: Optional[str]  # Slug del capítulo (si unlock_type=chapter)
    fragment_key: Optional[str]  # Key del fragmento (si unlock_type=fragment)


class VipDaysMetadata(TypedDict):
    """Metadata para recompensas tipo vip_days (integración VIP).

    Permite otorgar días de suscripción VIP como recompensa de misiones.
    """

    days: int  # Cantidad de días VIP a otorgar
    extend_existing: bool  # Si extender suscripción existente (default: True)


# Union de todos los metadatos posibles
RewardMetadata = (
    BadgeMetadata
    | PermissionMetadata
    | ItemMetadata
    | TitleMetadata
    | BesitosMetadata
    | ShopItemMetadata
    | NarrativeUnlockMetadata
    | VipDaysMetadata
)
