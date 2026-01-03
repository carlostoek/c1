"""
Inventario Inicial del Gabinete de Lucien

Configuración de los items iniciales disponibles en la tienda (Gabinete).
Todos los items tienen precios en BESITOS (sistema existente) y están
diseñados con contenido narrativo apropiado para el universo de Diana.

Este archivo solo define datos. NO ejecuta inserts a BD.
Usar get_seed_data() para obtener los datos listos para insertar.

Author: Sistema de Tienda - Gabinete de Lucien
Version: 1.0
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


# =============================================================================
# 1. MAPEO DE CATEGORÍAS (Sistema Existente → Nombres Narrativos)
# =============================================================================

"""
Mapeo de categorías del sistema existente a nombres narrativos del Gabinete.

El sistema shop ya tiene estas categorías definidas en modelos:
- CONSUMIBLE → Efímeros (Placeres de un solo uso)
- COSMETIC → Distintivos (Marcas visibles de posición)
- NARRATIVE → Llaves (Abren puertas a contenido oculto)
- DIGITAL → Reliquias (Objetos más valiosos)
"""

CATEGORY_MAPPING: Dict[str, str] = {
    "CONSUMABLE": "Efímeros",
    "COSMETIC": "Distintivos",
    "NARRATIVE": "Llaves",
    "DIGITAL": "Reliquias",
}


# =============================================================================
# 2. DESCRIPCIONES DE CATEGORÍA (Para UI)
# =============================================================================

CATEGORY_DESCRIPTIONS: Dict[str, str] = {
    "Efímeros": "Placeres de un solo uso. Intensos pero fugaces.",
    "Distintivos": "Marcas visibles de su posición. Para quienes valoran el reconocimiento.",
    "Llaves": "Abren puertas a contenido que otros no pueden ver.",
    "Reliquias": "Los objetos más valiosos del Gabinete. Requieren Besitos... y dignidad.",
}


# =============================================================================
# 3. ITEMS INICIALES DEL GABINETE
# =============================================================================

"""
Lista de items iniciales disponibles en el Gabinete.

Cada item incluye:
- name: Nombre visible del item
- internal_code: Código único interno (slug)
- category: Categoría del sistema (CONSUMABLE, COSMETIC, NARRATIVE, DIGITAL)
- rarity: Rareza (COMMON, UNCOMMON, RARE, EPIC, LEGENDARY)
- price_besitos: Precio en besitos (sistema existente)
- description_short: Descripción corta para lista
- description_lucien: Descripción con la voz de Lucien
- effect_type: Tipo de efecto (BADGE, UNLOCK_AUDIO, PRIORITY_ACCESS, etc.)
- effect_data: Datos específicos del efecto
- stock: Cantidad disponible (None = ilimitado)
- level_required: Nivel mínimo de usuario requerido
- is_active: Si está disponible para compra
- icon: Emoji representativo
"""

INITIAL_ITEMS: List[Dict[str, Any]] = [
    # =========================================================================
    # DISTINTIVOS (Badges - COSMETIC)
    # =========================================================================

    {
        "name": "Sello del Visitante",
        "internal_code": "badge_visitor",
        "category": "COSMETIC",
        "rarity": "COMMON",
        "price_besitos": 2,
        "description_short": "Primera marca de reconocimiento",
        "description_lucien": (
            "Una marca visible en su perfil. "
            "Indica que ha dado el primer paso. "
            "No es mucho, pero es un comienzo."
        ),
        "effect_type": "BADGE",
        "effect_data": {"badge_id": "visitor_seal", "icon": "🏷️"},
        "stock": None,  # Ilimitado
        "level_required": 1,
        "is_active": True,
        "icon": "🏷️",
    },

    {
        "name": "Insignia del Observador",
        "internal_code": "badge_observer",
        "category": "COSMETIC",
        "rarity": "UNCOMMON",
        "price_besitos": 5,
        "description_short": "Lucien lo ha notado",
        "description_lucien": (
            "Esta insignia indica que he prestado atención a su comportamiento. "
            "No todos ameritan mi observación. "
            "Considérelo un... honor cuestionable."
        ),
        "effect_type": "BADGE",
        "effect_data": {"badge_id": "observer_mark", "icon": "👁️"},
        "stock": None,
        "level_required": 2,
        "is_active": True,
        "icon": "👁️",
    },

    {
        "name": "Marca del Confidente",
        "internal_code": "badge_confidant",
        "category": "COSMETIC",
        "rarity": "LEGENDARY",
        "price_besitos": 25,
        "description_short": "El nivel más alto de reconocimiento",
        "description_lucien": (
            "Esta marca indica que he decidido confiar en usted. "
            "No la otorgo a la ligera. "
            "De hecho, me cuestiono si debería existir siquiera. "
            "Pero aquí está."
        ),
        "effect_type": "BADGE",
        "effect_data": {"badge_id": "confidant_mark", "icon": "🎭"},
        "stock": 25,  # Limitado
        "level_required": 6,
        "is_active": True,
        "icon": "🎭",
    },

    # =========================================================================
    # EFÍMEROS (Consumibles - CONSUMABLE)
    # =========================================================================

    {
        "name": "Susurro Efímero",
        "internal_code": "audio_whisper_01",
        "category": "CONSUMABLE",
        "rarity": "UNCOMMON",
        "price_besitos": 3,
        "description_short": "Un mensaje de voz exclusivo de Diana",
        "description_lucien": (
            "Un susurro que Diana grabó en un momento de... inspiración. "
            "Úselo cuando necesite motivación. "
            "Solo puede escucharlo una vez."
        ),
        "effect_type": "UNLOCK_AUDIO",
        "effect_data": {"audio_id": "whisper_01", "duration_seconds": 15},
        "stock": None,
        "level_required": 2,
        "is_active": True,
        "icon": "🎙️",
    },

    {
        "name": "Pase de Prioridad",
        "internal_code": "priority_pass",
        "category": "CONSUMABLE",
        "rarity": "RARE",
        "price_besitos": 5,
        "description_short": "Acceso anticipado al próximo contenido",
        "description_lucien": (
            "Cuando Diana prepare algo nuevo, usted estará primero en la fila. "
            "La paciencia tiene recompensas... pero a veces, también la impaciencia."
        ),
        "effect_type": "PRIORITY_ACCESS",
        "effect_data": {"duration_hours": 24},
        "stock": 50,  # Limitado
        "level_required": 3,
        "is_active": True,
        "icon": "⏩",
    },

    # =========================================================================
    # LLAVES (Narrativos - NARRATIVE)
    # =========================================================================

    {
        "name": "Llave del Fragmento Oculto",
        "internal_code": "key_fragment_01",
        "category": "NARRATIVE",
        "rarity": "RARE",
        "price_besitos": 10,
        "description_short": "Desbloquea un fragmento narrativo secreto",
        "description_lucien": (
            "Hay historias que Diana no cuenta públicamente. "
            "Este fragmento es una de ellas. "
            "¿Está preparado para lo que podría encontrar?"
        ),
        "effect_type": "UNLOCK_NARRATIVE",
        "effect_data": {"fragment_id": "secret_01", "chapter_id": "ch_free_secret"},
        "stock": None,
        "level_required": 3,
        "is_active": True,
        "icon": "🗝️",
    },

    {
        "name": "El Primer Secreto",
        "internal_code": "key_chapter_secret",
        "category": "NARRATIVE",
        "rarity": "EPIC",
        "price_besitos": 20,
        "description_short": "Un capítulo que pocos conocen",
        "description_lucien": (
            "Diana tiene secretos. Este es uno de los primeros que decidió documentar. "
            "No es para los curiosos casuales. "
            "Es para quienes realmente quieren entender."
        ),
        "effect_type": "UNLOCK_CHAPTER",
        "effect_data": {"chapter_id": "secret_chapter_01", "unlock_condition": "key_purchased"},
        "stock": None,
        "level_required": 4,
        "is_active": True,
        "icon": "📜",
    },

    # =========================================================================
    # RELIQUIAS (Digitales - DIGITAL)
    # =========================================================================

    {
        "name": "Vistazo al Sensorium",
        "internal_code": "sensorium_preview",
        "category": "DIGITAL",
        "rarity": "EPIC",
        "price_besitos": 15,
        "description_short": "Muestra del contenido Sensorium",
        "description_lucien": (
            "El Sensorium es contenido diseñado para despertar sentidos que olvidó que tenía. "
            "Esta es solo una muestra. 30 segundos de lo que Diana puede hacer "
            "cuando realmente se concentra."
        ),
        "effect_type": "UNLOCK_CONTENT",
        "effect_data": {"content_id": "sensorium_sample_01", "duration_seconds": 30},
        "stock": 100,
        "level_required": 4,
        "is_active": True,
        "icon": "👁️‍🗨️",
    },

    {
        "name": "Reliquia de Diana",
        "internal_code": "relic_diana_01",
        "category": "DIGITAL",
        "rarity": "LEGENDARY",
        "price_besitos": 40,
        "description_short": "Un objeto único del universo de Diana",
        "description_lucien": (
            "Hay objetos que Diana guarda cerca. Este es uno de ellos. "
            "No puedo explicar qué es exactamente. "
            "Solo puedo decir que tiene significado. "
            "Para ella. Y ahora, para usted."
        ),
        "effect_type": "COLLECTIBLE",
        "effect_data": {"collectible_id": "relic_01", "unique": True},
        "stock": 10,
        "level_required": 5,
        "is_active": True,
        "icon": "💎",
    },
]


# =============================================================================
# 4. FUNCIONES HELPER
# =============================================================================

@dataclass
class ItemValidationError:
    """Resultado de validación de item."""
    is_valid: bool
    errors: List[str]


def validate_item(item: Dict[str, Any]) -> ItemValidationError:
    """
    Valida que un item tenga todos los campos requeridos.

    Args:
        item: Diccionario con datos del item

    Returns:
        ItemValidationError con resultado y lista de errores

    Example:
        item = {"name": "Test", "internal_code": "test", ...}
        result = validate_item(item)
        if result.is_valid:
            # Item válido
        else:
            print(result.errors)
    """
    errors = []

    # Campos requeridos
    required_fields = [
        "name",
        "internal_code",
        "category",
        "rarity",
        "price_besitos",
        "description_short",
        "description_lucien",
        "effect_type",
        "effect_data",
        "level_required",
        "is_active",
    ]

    for field in required_fields:
        if field not in item:
            errors.append(f"Campo requerido faltante: {field}")

    # Validaciones de tipo
    if "price_besitos" in item and not isinstance(item["price_besitos"], (int, float)):
        errors.append("price_besitos debe ser numérico")

    if "price_besitos" in item and item["price_besitos"] < 0:
        errors.append("price_besitos debe ser >= 0")

    if "level_required" in item and not isinstance(item["level_required"], int):
        errors.append("level_required debe ser entero")

    if "level_required" in item and (item["level_required"] < 1 or item["level_required"] > 7):
        errors.append("level_required debe estar entre 1 y 7")

    # Validaciones de categoría
    valid_categories = ["CONSUMABLE", "COSMETIC", "NARRATIVE", "DIGITAL"]
    if "category" in item and item["category"] not in valid_categories:
        errors.append(f"Categoría inválida: {item.get('category')}")

    # Validaciones de rareza
    valid_rarities = ["COMMON", "UNCOMMON", "RARE", "EPIC", "LEGENDARY"]
    if "rarity" in item and item["rarity"] not in valid_rarities:
        errors.append(f"Rareza inválida: {item.get('rarity')}")

    # Validar que internal_code sea único (slug-like)
    if "internal_code" in item:
        code = item["internal_code"]
        if not isinstance(code, str) or not code.replace("_", "").isalnum():
            errors.append("internal_code debe ser un slug válido (solo letras, números, guiones bajos)")

    return ItemValidationError(
        is_valid=len(errors) == 0,
        errors=errors
    )


def get_seed_data() -> List[Dict[str, Any]]:
    """
    Retorna los items listos para insertar en BD.

    Los items son validados antes de retornarse. Si algún item
    no es válido, se lanza ValueError con detalles.

    Returns:
        Lista de diccionarios con datos de items para insertar

    Raises:
        ValueError: Si algún item no pasa validación

    Example:
        items = get_seed_data()
        for item_data in items:
            shop_item = ShopItem(**item_data)
            session.add(shop_item)
    """
    validated_items = []

    for item in INITIAL_ITEMS:
        validation = validate_item(item)

        if not validation.is_valid:
            raise ValueError(
                f"Item inválido: {item.get('internal_code', 'UNKNOWN')}\n"
                f"Errores: {', '.join(validation.errors)}"
            )

        validated_items.append(item)

    return validated_items


def get_items_by_category(category: str) -> List[Dict[str, Any]]:
    """
    Filtra items por categoría.

    Args:
        category: Categoría (CONSUMABLE, COSMETIC, NARRATIVE, DIGITAL)

    Returns:
        Lista de items de esa categoría
    """
    return [item for item in INITIAL_ITEMS if item["category"] == category]


def get_items_by_rarity(rarity: str) -> List[Dict[str, Any]]:
    """
    Filtra items por rareza.

    Args:
        rarity: Rareza (COMMON, UNCOMMON, RARE, EPIC, LEGENDARY)

    Returns:
        Lista de items de esa rareza
    """
    return [item for item in INITIAL_ITEMS if item["rarity"] == rarity]


def get_items_by_level_range(min_level: int, max_level: int) -> List[Dict[str, Any]]:
    """
    Filtra items por rango de nivel requerido.

    Args:
        min_level: Nivel mínimo (inclusive)
        max_level: Nivel máximo (inclusive)

    Returns:
        Lista de items en ese rango de niveles
    """
    return [
        item for item in INITIAL_ITEMS
        if min_level <= item["level_required"] <= max_level
    ]


def get_item_by_internal_code(code: str) -> Optional[Dict[str, Any]]:
    """
    Busca un item por su código interno.

    Args:
        code: Código interno del item

    Returns:
        Item encontrado o None
    """
    for item in INITIAL_ITEMS:
        if item["internal_code"] == code:
            return item
    return None


def format_item_for_display(item: Dict[str, Any]) -> str:
    """
    Formatea un item para mostrar en UI.

    Args:
        item: Diccionario con datos del item

    Returns:
        String formateado con información del item

    Example:
        text = format_item_for_display(item)
        # "🗝️ Llave del Fragmento Oculto [RARE]
        #  10 Besitos | Nivel 3 requerido
        #  Desbloquea un fragmento narrativo secreto"
    """
    rarity_emoji = {
        "COMMON": "⚪",
        "UNCOMMON": "🟢",
        "RARE": "🔵",
        "EPIC": "🟣",
        "LEGENDARY": "🟡",
    }

    emoji = item.get("icon", "📦")
    name = item.get("name", "Unknown")
    rarity = item.get("rarity", "COMMON")
    price = item.get("price_besitos", 0)
    level = item.get("level_required", 1)
    desc = item.get("description_short", "")

    return (
        f"{emoji} <b>{name}</b> [{rarity}]\n"
        f"💰 {price} Besitos | 🎯 Nivel {level}\n"
        f"{desc}"
    )


# =============================================================================
# 5. ESTADÍSTICAS DEL INVENTARIO
# =============================================================================

def get_inventory_stats() -> Dict[str, Any]:
    """
    Retorna estadísticas del inventario inicial.

    Returns:
        Diccionario con contadores y resúmenes
    """
    total_items = len(INITIAL_ITEMS)

    items_by_category = {
        cat: len(get_items_by_category(cat))
        for cat in CATEGORY_MAPPING.keys()
    }

    items_by_rarity = {
        rarity: len(get_items_by_rarity(rarity))
        for rarity in ["COMMON", "UNCOMMON", "RARE", "EPIC", "LEGENDARY"]
    }

    total_value = sum(item["price_besitos"] for item in INITIAL_ITEMS)

    return {
        "total_items": total_items,
        "items_by_category": items_by_category,
        "items_by_rarity": items_by_rarity,
        "total_besitos_value": total_value,
        "avg_price": total_value / total_items if total_items > 0 else 0,
        "min_price": min((item["price_besitos"] for item in INITIAL_ITEMS), default=0),
        "max_price": max((item["price_besitos"] for item in INITIAL_ITEMS), default=0),
    }
