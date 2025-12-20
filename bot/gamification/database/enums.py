# bot/gamification/database/enums.py

"""
Enums y tipos personalizados para el módulo de gamificación.

Contiene:
- Enums para campos de modelos (MissionType, RewardType, etc.)
- TypedDicts para validación de JSON (Criterias, Metadata)
"""

from enum import Enum
from typing import TypedDict, Literal


# ============================================================
# ENUMS PRINCIPALES
# ============================================================

class MissionType(str, Enum):
    """Tipos de misión disponibles en el sistema."""
    
    ONE_TIME = "one_time"        # Misión única (ej: bienvenida)
    DAILY = "daily"              # Se repite diariamente
    WEEKLY = "weekly"            # Se repite semanalmente
    STREAK = "streak"            # Basada en rachas consecutivas
    
    def __str__(self) -> str:
        return self.value


class MissionStatus(str, Enum):
    """Estados posibles de una misión para un usuario."""
    
    NOT_STARTED = "not_started"  # Usuario no ha iniciado la misión
    IN_PROGRESS = "in_progress"  # Misión activa pero no completada
    COMPLETED = "completed"      # Completada pero recompensa no reclamada
    CLAIMED = "claimed"          # Recompensa reclamada
    EXPIRED = "expired"          # Misión expiró sin completarse (para temporales)
    
    def __str__(self) -> str:
        return self.value


class RewardType(str, Enum):
    """Tipos de recompensas disponibles."""
    
    BADGE = "badge"              # Badge/logro
    ITEM = "item"                # Item virtual (futuro: stickers, etc.)
    PERMISSION = "permission"    # Permiso especial (ej: cambiar nombre, emoji custom)
    TITLE = "title"              # Título especial para perfil
    BESITOS = "besitos"          # Besitos extra (bonus)
    
    def __str__(self) -> str:
        return self.value


class BadgeRarity(str, Enum):
    """Raridad de los badges en el sistema."""
    
    COMMON = "common"            # Común (fácil de obtener)
    RARE = "rare"                # Raro (requiere esfuerzo)
    EPIC = "epic"                # Épico (difícil)
    LEGENDARY = "legendary"      # Legendario (muy difícil)
    
    def __str__(self) -> str:
        return self.value


class ObtainedVia(str, Enum):
    """Formas en que se puede obtener una recompensa."""
    
    MISSION = "mission"          # Obtenido completando misión
    PURCHASE = "purchase"        # Comprado con besitos
    ADMIN_GRANT = "admin_grant"  # Otorgado por admin
    EVENT = "event"              # Evento especial (futuro)
    LEVEL_UP = "level_up"        # Al subir de nivel
    
    def __str__(self) -> str:
        return self.value


class TransactionType(str, Enum):
    """Tipos de transacciones de besitos."""
    
    MISSION_REWARD = "mission_reward"    # Recompensa de misión
    REACTION = "reaction"                # Por reaccionar en canal
    PURCHASE = "purchase"                # Compra de recompensa
    ADMIN_GRANT = "admin_grant"          # Admin otorgó besitos
    ADMIN_DEDUCT = "admin_deduct"        # Admin quitó besitos
    REFUND = "refund"                    # Devolución por error
    STREAK_BONUS = "streak_bonus"        # Bonus por racha
    LEVEL_UP_BONUS = "level_up_bonus"    # Bonus por subir nivel
    
    def __str__(self) -> str:
        return self.value


class TemplateCategory(str, Enum):
    """Categorías de plantillas de configuración."""
    
    MISSION = "mission"                  # Plantilla de misión
    REWARD = "reward"                    # Plantilla de recompensa
    LEVEL_PROGRESSION = "level_progression"  # Plantilla de niveles completos
    FULL_SYSTEM = "full_system"          # Sistema completo (misiones + recompensas + niveles)
    
    def __str__(self) -> str:
        return self.value


# ============================================================
# TYPEDDICTS PARA JSON
# ============================================================

class StreakCriteria(TypedDict):
    """Estructura de criterios para misiones tipo streak."""
    type: Literal["streak"]
    days: int
    require_consecutive: bool


class DailyCriteria(TypedDict):
    """Estructura de criterios para misiones tipo daily."""
    type: Literal["daily"]
    count: int
    specific_reaction: str | None  # Emoji o None


class WeeklyCriteria(TypedDict):
    """Estructura de criterios para misiones tipo weekly."""
    type: Literal["weekly"]
    target: int
    specific_days: list[int] | None  # [0-6] o None


class OneTimeCriteria(TypedDict):
    """Estructura de criterios para misiones tipo one_time."""
    type: Literal["one_time"]
    # No necesita criterios adicionales


class MissionCriteria(TypedDict):
    """Tipo base para criterios de misión (unión de todos los tipos)."""
    type: Literal["streak", "daily", "weekly", "one_time"]
    days: int  # Para streak
    require_consecutive: bool  # Para streak
    count: int  # Para daily
    specific_reaction: str | None  # Para daily
    target: int  # Para weekly
    specific_days: list[int] | None  # Para weekly


class BadgeMetadata(TypedDict):
    """Estructura de metadatos para recompensas de tipo Badge."""
    icon: str  # Emoji
    rarity: str  # BadgeRarity value


class PermissionMetadata(TypedDict):
    """Estructura de metadatos para recompensas de tipo Permission."""
    permission_key: str  # ej: "custom_emoji", "change_username"
    expires_at: str | None  # ISO datetime o None (permanente)


class TitleMetadata(TypedDict):
    """Estructura de metadatos para recompensas de tipo Title."""
    title: str
    icon: str | None  # Emoji opcional para mostrar con el título
    color: str | None  # Código de color hexadecimal (opcional)


class ItemMetadata(TypedDict):
    """Estructura de metadatos para recompensas de tipo Item."""
    item_type: str  # Tipo de item (ej: "sticker", "emoji", "theme")
    item_id: str | int  # ID del item específico
    quantity: int | None  # Cantidad (para consumibles)
    expires_at: str | None  # ISO datetime o None (permanente)


class BesitosMetadata(TypedDict):
    """Estructura de metadatos para recompensas de tipo Besitos."""
    amount: int  # Cantidad de besitos extra otorgados


class RewardMetadata(TypedDict):
    """Tipo base para metadatos de recompensa (unión de todos los tipos)."""
    icon: str  # Para Badge
    rarity: str  # Para Badge
    permission_key: str  # Para Permission
    expires_at: str | None  # Para Permission o Item
    title: str  # Para Title
    item_type: str  # Para Item
    item_id: str | int  # Para Item
    quantity: int | None  # Para Item
    amount: int  # Para Besitos