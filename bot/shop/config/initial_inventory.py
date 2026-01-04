"""Inventario inicial del Gabinete de Lucien.

Este archivo define los items iniciales que estarán disponibles en la tienda.
Cada item tiene un propósito narrativo y una descripción en la voz de Lucien.

Uso:
    from bot.shop.config.initial_inventory import get_seed_data

    items = get_seed_data()
    for item_data in items:
        shop_item = ShopItem(**item_data)
        session.add(shop_item)
"""

from typing import List, Dict, Any


# ============================================================
# 1. MAPEO DE CATEGORÍAS
# ============================================================

CATEGORY_MAPPING = {
    "CONSUMABLE": "Efímeros",     # Placeres de un solo uso
    "COSMETIC": "Distintivos",    # Marcas visibles de posición
    "NARRATIVE": "Llaves",        # Abren puertas a contenido oculto
    "DIGITAL": "Reliquias"        # Objetos más valiosos
}


CATEGORY_DESCRIPTIONS = {
    "Efímeros": (
        "Placeres de un solo uso. "
        "Intensos pero fugaces. Como los buenos momentos."
    ),
    "Distintivos": (
        "Marcas visibles de su posición. "
        "Para quienes valoran el reconocimiento... o necesitan validación."
    ),
    "Llaves": (
        "Abren puertas a contenido que otros no pueden ver. "
        "El conocimiento es poder, pero acceso requiere... mérito."
    ),
    "Reliquias": (
        "Los objetos más valiosos del Gabinete. "
        "Requieren Besitos... y dignidad."
    )
}


# ============================================================
# 2. ITEMS INICIALES
# ============================================================

INITIAL_ITEMS = [
    {
        "name": "Sello del Visitante",
        "slug": "badge_visitor",
        "description": "Primera marca de reconocimiento",
        "long_description": (
            "Una marca visible en su perfil. Indica que ha dado el primer paso. "
            "No es mucho, pero es un comienzo."
        ),
        "item_type": "COSMETIC",
        "rarity": "COMMON",
        "price_besitos": 2,
        "icon": "🔖",
        "item_metadata": {
            "cosmetic_type": "badge",
            "badge_id": "visitor_seal",
            "is_animated": False
        },
        "stock": None,
        "max_per_user": 1,
        "requires_vip": False,
        "is_featured": False,
        "is_active": True,
        "order": 1
    },
    {
        "name": "Susurro Efímero",
        "slug": "audio_whisper_01",
        "description": "Un mensaje de voz exclusivo de Diana",
        "long_description": (
            "Un susurro que Diana grabó en un momento de... inspiración. "
            "Úselo cuando necesite motivación. Solo puede escucharlo una vez."
        ),
        "item_type": "CONSUMABLE",
        "rarity": "UNCOMMON",
        "price_besitos": 3,
        "icon": "🎤",
        "item_metadata": {
            "effect_type": "UNLOCK_AUDIO",
            "audio_id": "whisper_01",
            "duration_seconds": 15
        },
        "stock": None,
        "max_per_user": 3,
        "requires_vip": False,
        "is_featured": True,
        "is_active": True,
        "order": 2
    },
    {
        "name": "Pase de Prioridad",
        "slug": "priority_pass",
        "description": "Acceso anticipado al próximo contenido",
        "long_description": (
            "Cuando Diana prepare algo nuevo, usted estará primero en la fila. "
            "La paciencia tiene recompensas... pero a veces, también la impaciencia."
        ),
        "item_type": "CONSUMABLE",
        "rarity": "RARE",
        "price_besitos": 5,
        "icon": "🎫",
        "item_metadata": {
            "effect_type": "PRIORITY_ACCESS",
            "duration_hours": 24
        },
        "stock": 50,
        "max_per_user": 1,
        "requires_vip": False,
        "is_featured": True,
        "is_active": True,
        "order": 3
    },
    {
        "name": "Insignia del Observador",
        "slug": "badge_observer",
        "description": "Lucien lo ha notado",
        "long_description": (
            "Esta insignia indica que he prestado atención a su comportamiento. "
            "No todos ameritan mi observación. Considérelo un... honor cuestionable."
        ),
        "item_type": "COSMETIC",
        "rarity": "UNCOMMON",
        "price_besitos": 5,
        "icon": "👁️",
        "item_metadata": {
            "cosmetic_type": "badge",
            "badge_id": "observer_mark",
            "is_animated": False
        },
        "stock": None,
        "max_per_user": 1,
        "requires_vip": False,
        "is_featured": False,
        "is_active": True,
        "order": 4
    },
    {
        "name": "Llave del Fragmento Oculto",
        "slug": "key_fragment_01",
        "description": "Desbloquea un fragmento narrativo secreto",
        "long_description": (
            "Hay historias que Diana no cuenta públicamente. "
            "Este fragmento es una de ellas. "
            "¿Está preparado para lo que podría encontrar?"
        ),
        "item_type": "NARRATIVE",
        "rarity": "RARE",
        "price_besitos": 10,
        "icon": "🗝️",
        "item_metadata": {
            "effect_type": "UNLOCK_NARRATIVE",
            "fragment_id": "secret_01",
            "unlocks_fragment_key": "secret_fragment_01"
        },
        "stock": None,
        "max_per_user": 1,
        "requires_vip": False,
        "is_featured": True,
        "is_active": True,
        "order": 5
    },
    {
        "name": "Vistazo al Sensorium",
        "slug": "sensorium_preview",
        "description": "Muestra del contenido Sensorium",
        "long_description": (
            "El Sensorium es contenido diseñado para despertar sentidos que olvidó que tenía. "
            "Esta es solo una muestra. 30 segundos de lo que Diana puede hacer "
            "cuando realmente se concentra."
        ),
        "item_type": "CONSUMABLE",
        "rarity": "EPIC",
        "price_besitos": 15,
        "icon": "👁️‍🗨️",
        "item_metadata": {
            "effect_type": "UNLOCK_CONTENT",
            "content_id": "sensorium_sample_01",
            "duration_seconds": 30
        },
        "stock": 100,
        "max_per_user": 3,
        "requires_vip": False,
        "is_featured": True,
        "is_active": True,
        "order": 6
    },
    {
        "name": "El Primer Secreto",
        "slug": "key_chapter_secret",
        "description": "Un capítulo que pocos conocen",
        "long_description": (
            "Diana tiene secretos. Este es uno de los primeros que decidió documentar. "
            "No es para los curiosos casuales. "
            "Es para quienes realmente quieren entender."
        ),
        "item_type": "NARRATIVE",
        "rarity": "EPIC",
        "price_besitos": 20,
        "icon": "📜",
        "item_metadata": {
            "effect_type": "UNLOCK_CHAPTER",
            "chapter_id": "secret_chapter_01",
            "unlocks_chapter_slug": "primer-secreto"
        },
        "stock": None,
        "max_per_user": 1,
        "requires_vip": False,
        "is_featured": True,
        "is_active": True,
        "order": 7
    },
    {
        "name": "Marca del Confidente",
        "slug": "badge_confidant",
        "description": "El nivel más alto de reconocimiento",
        "long_description": (
            "Esta marca indica que he decidido confiar en usted. "
            "No la otorgo a la ligera. De hecho, me cuestiono si debería existir siquiera. "
            "Pero aquí está."
        ),
        "item_type": "COSMETIC",
        "rarity": "LEGENDARY",
        "price_besitos": 25,
        "icon": "🏅",
        "item_metadata": {
            "cosmetic_type": "badge",
            "badge_id": "confidant_mark",
            "is_animated": True
        },
        "stock": 25,
        "max_per_user": 1,
        "requires_vip": False,
        "is_featured": True,
        "is_active": True,
        "order": 8
    },
    {
        "name": "Reliquia de Diana",
        "slug": "relic_diana_01",
        "description": "Un objeto único del universo de Diana",
        "long_description": (
            "Hay objetos que Diana guarda cerca. Este es uno de ellos. "
            "No puedo explicar qué es exactamente. Solo puedo decir que tiene significado. "
            "Para ella. Y ahora, para usted."
        ),
        "item_type": "DIGITAL",
        "rarity": "LEGENDARY",
        "price_besitos": 40,
        "icon": "💎",
        "item_metadata": {
            "effect_type": "COLLECTIBLE",
            "collectible_id": "relic_01",
            "unique": True
        },
        "stock": 10,
        "max_per_user": 1,
        "requires_vip": False,
        "is_featured": True,
        "is_active": True,
        "order": 9
    }
]


# ============================================================
# 3. FUNCIONES HELPER
# ============================================================

def get_seed_data(admin_user_id: int = 1) -> List[Dict[str, Any]]:
    """Retorna los items listos para insertar en BD.

    Args:
        admin_user_id: ID del usuario admin que crea los items (default: 1)

    Returns:
        Lista de diccionarios con datos de ShopItem
    """
    items = []

    for item in INITIAL_ITEMS:
        item_data = item.copy()
        item_data["created_by"] = admin_user_id
        items.append(item_data)

    return items


def validate_item(item: Dict[str, Any]) -> tuple[bool, str]:
    """Valida que un item tenga todos los campos requeridos.

    Args:
        item: Diccionario con datos del item

    Returns:
        Tuple (is_valid, error_message)
    """
    required_fields = [
        "name", "slug", "description", "item_type",
        "rarity", "price_besitos", "icon"
    ]

    # Verificar campos requeridos
    for field in required_fields:
        if field not in item:
            return False, f"Missing required field: {field}"

    # Validar tipo de item
    valid_types = ["CONSUMABLE", "COSMETIC", "NARRATIVE", "DIGITAL"]
    if item["item_type"] not in valid_types:
        return False, f"Invalid item_type: {item['item_type']}"

    # Validar rareza
    valid_rarities = ["COMMON", "UNCOMMON", "RARE", "EPIC", "LEGENDARY"]
    if item["rarity"] not in valid_rarities:
        return False, f"Invalid rarity: {item['rarity']}"

    # Validar precio positivo
    if item["price_besitos"] < 0:
        return False, "price_besitos must be >= 0"

    # Validar slug formato
    slug = item["slug"]
    if not slug.replace("-", "").replace("_", "").isalnum():
        return False, f"Invalid slug format: {slug}"

    # Validar stock si existe
    if "stock" in item and item["stock"] is not None:
        if item["stock"] < 0:
            return False, "stock must be >= 0 or None"

    # Validar max_per_user si existe
    if "max_per_user" in item and item["max_per_user"] is not None:
        if item["max_per_user"] < 1:
            return False, "max_per_user must be >= 1 or None"

    return True, "OK"


def get_items_by_type(item_type: str) -> List[Dict[str, Any]]:
    """Filtra items por tipo.

    Args:
        item_type: Tipo de item (CONSUMABLE, COSMETIC, NARRATIVE, DIGITAL)

    Returns:
        Lista de items del tipo especificado
    """
    return [item for item in INITIAL_ITEMS if item["item_type"] == item_type]


def get_items_by_rarity(rarity: str) -> List[Dict[str, Any]]:
    """Filtra items por rareza.

    Args:
        rarity: Rareza (COMMON, UNCOMMON, RARE, EPIC, LEGENDARY)

    Returns:
        Lista de items de la rareza especificada
    """
    return [item for item in INITIAL_ITEMS if item["rarity"] == rarity]


def get_featured_items() -> List[Dict[str, Any]]:
    """Retorna items destacados.

    Returns:
        Lista de items con is_featured=True
    """
    return [item for item in INITIAL_ITEMS if item.get("is_featured", False)]


def get_category_summary() -> Dict[str, Dict[str, Any]]:
    """Retorna un resumen de items por categoría.

    Returns:
        Dict con:
        {
            "Efímeros": {"count": 3, "price_range": [3, 15]},
            "Distintivos": {"count": 3, "price_range": [2, 25]},
            ...
        }
    """
    summary = {}

    for type_key, category_name in CATEGORY_MAPPING.items():
        items = get_items_by_type(type_key)

        if items:
            prices = [item["price_besitos"] for item in items]
            summary[category_name] = {
                "count": len(items),
                "price_range": [min(prices), max(prices)],
                "description": CATEGORY_DESCRIPTIONS[category_name]
            }

    return summary
