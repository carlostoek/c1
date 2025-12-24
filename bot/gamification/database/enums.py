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

    def __str__(self) -> str:
        return self.value


class TransactionType(str, Enum):
    """Tipo de transacción de besitos."""

    MISSION_REWARD = "mission_reward"
    REACTION = "reaction"
    PURCHASE = "purchase"
    ADMIN_GRANT = "admin_grant"
    ADMIN_DEDUCT = "admin_deduct"
    REFUND = "refund"
    STREAK_BONUS = "streak_bonus"
    LEVEL_UP_BONUS = "level_up_bonus"

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


# Union de todos los metadatos posibles
RewardMetadata = BadgeMetadata | PermissionMetadata | ItemMetadata | TitleMetadata


class UnlockCondition(TypedDict):
    """Condición para desbloquear una recompensa."""

    type: Literal["mission", "level", "besitos"]
    value: int  # mission_id, level_id, o cantidad de besitos


class BesitosMetadata(TypedDict):
    """Metadata para recompensas tipo besitos."""

    amount: int
    multiplier: Optional[float]  # Multiplicador de besitos (ej: 1.5x)
