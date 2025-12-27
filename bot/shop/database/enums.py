"""
Enums y tipos para el módulo de Tienda.
"""

from enum import Enum
from typing import TypedDict, Optional


class ItemType(str, Enum):
    """Tipo de producto en la tienda."""

    NARRATIVE = "narrative"      # Artefactos que desbloquean fragmentos
    DIGITAL = "digital"          # Paquetes de contenido digital
    CONSUMABLE = "consumable"    # Items de uso único (boost, etc.)
    COSMETIC = "cosmetic"        # Items cosméticos (títulos, badges extra)

    def __str__(self) -> str:
        return self.value

    @property
    def emoji(self) -> str:
        """Emoji representativo del tipo."""
        emojis = {
            "narrative": "📜",
            "digital": "💾",
            "consumable": "🧪",
            "cosmetic": "✨",
        }
        return emojis.get(self.value, "📦")

    @property
    def display_name(self) -> str:
        """Nombre para mostrar en UI."""
        names = {
            "narrative": "Artefacto Narrativo",
            "digital": "Contenido Digital",
            "consumable": "Consumible",
            "cosmetic": "Cosmético",
        }
        return names.get(self.value, "Producto")


class ItemRarity(str, Enum):
    """Rareza del producto (afecta visualización)."""

    COMMON = "common"        # Blanco/Gris
    UNCOMMON = "uncommon"    # Verde
    RARE = "rare"            # Azul
    EPIC = "epic"            # Púrpura
    LEGENDARY = "legendary"  # Dorado

    def __str__(self) -> str:
        return self.value

    @property
    def emoji(self) -> str:
        """Emoji representativo de la rareza."""
        emojis = {
            "common": "⚪",
            "uncommon": "🟢",
            "rare": "🔵",
            "epic": "🟣",
            "legendary": "🟡",
        }
        return emojis.get(self.value, "⚪")

    @property
    def display_name(self) -> str:
        """Nombre para mostrar en UI."""
        names = {
            "common": "Común",
            "uncommon": "Poco Común",
            "rare": "Raro",
            "epic": "Épico",
            "legendary": "Legendario",
        }
        return names.get(self.value, "Común")


class PurchaseStatus(str, Enum):
    """Estado de una compra."""

    COMPLETED = "completed"    # Compra exitosa
    REFUNDED = "refunded"      # Compra reembolsada
    CANCELLED = "cancelled"    # Compra cancelada

    def __str__(self) -> str:
        return self.value


# ============================================================
# TYPEDDICTS PARA METADATA
# ============================================================


class NarrativeItemMetadata(TypedDict):
    """Metadata para items narrativos."""

    unlocks_fragment_key: Optional[str]   # Fragment key que desbloquea
    unlocks_chapter_slug: Optional[str]   # Chapter slug que desbloquea
    lore_text: Optional[str]              # Texto de lore del artefacto


class DigitalItemMetadata(TypedDict):
    """Metadata para items digitales."""

    content_description: str              # Descripción del contenido
    download_url: Optional[str]           # URL de descarga (si aplica)
    access_key: Optional[str]             # Key de acceso a contenido


class ConsumableItemMetadata(TypedDict):
    """Metadata para items consumibles."""

    effect_type: str                      # Tipo de efecto ("besitos_boost", "xp_boost", etc.)
    effect_value: int                     # Valor del efecto
    duration_hours: Optional[int]         # Duración en horas (None = permanente)


class CosmeticItemMetadata(TypedDict):
    """Metadata para items cosméticos."""

    cosmetic_type: str                    # "title", "badge", "emoji"
    cosmetic_value: str                   # Valor del cosmético
    is_animated: bool                     # Si es animado (para badges)
