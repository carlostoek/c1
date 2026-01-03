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
    # EFÍMEROS (Consumibles - CONSUMABLE)
    # =========================================================================

    {
        "name": "Sello del Día",
        "internal_code": "eph_001_daily_seal",
        "category": "CONSUMABLE",
        "rarity": "COMMON",
        "price_besitos": 1,
        "description_short": "Marca temporal de actividad por 24 horas",
        "description_lucien": (
            "Una marca temporal que indica actividad reciente. Válida hasta medianoche. "
            "Algunos lo consideran un ritual diario. Otros, una vanidad menor."
        ),
        "effect_type": "BADGE_TEMPORAL",
        "effect_data": {"badge_id": "daily_seal", "duration_hours": 24},
        "stock": None,
        "level_required": 1,
        "is_active": True,
        "icon": "⚡",
    },

    {
        "name": "Susurro Efímero",
        "internal_code": "eph_002_whisper",
        "category": "CONSUMABLE",
        "rarity": "UNCOMMON",
        "price_besitos": 3,
        "description_short": "Mensaje de voz exclusivo de 15 segundos",
        "description_lucien": (
            "Un mensaje de voz que Diana grabó en un momento de... inspiración. "
            "15 segundos. Una vez. Luego se desvanece como si nunca hubiera existido."
        ),
        "effect_type": "UNLOCK_AUDIO",
        "effect_data": {"audio_id": "whisper_01", "duration_seconds": 15},
        "stock": None,
        "level_required": 1,
        "is_active": True,
        "icon": "🎙️",
    },

    {
        "name": "Pase de Prioridad",
        "internal_code": "eph_003_priority_pass",
        "category": "CONSUMABLE",
        "rarity": "RARE",
        "price_besitos": 5,
        "description_short": "Acceso anticipado al próximo contenido",
        "description_lucien": (
            "Cuando Diana libere contenido de acceso limitado, usted estará primero en la fila. "
            "No garantiza acceso - garantiza oportunidad."
        ),
        "effect_type": "PRIORITY_ACCESS",
        "effect_data": {"duration_hours": 24},
        "stock": 50,
        "level_required": 2,
        "is_active": True,
        "icon": "⏩",
    },

    {
        "name": "Vistazo al Sensorium",
        "internal_code": "eph_004_sensorium_preview",
        "category": "CONSUMABLE",
        "rarity": "EPIC",
        "price_besitos": 15,
        "description_short": "Muestra de 30 segundos del contenido Sensorium",
        "description_lucien": (
            "Una muestra del contenido Sensorium. Treinta segundos diseñados para "
            "alterar su percepción sensorial. "
            "Diana pasó meses estudiando cómo el cerebro procesa el placer."
        ),
        "effect_type": "UNLOCK_CONTENT",
        "effect_data": {"content_id": "sensorium_sample_01", "duration_seconds": 30},
        "stock": 100,
        "level_required": 3,
        "is_active": True,
        "icon": "👁️‍🗨️",
    },

    {
        "name": "Confesión Nocturna",
        "internal_code": "eph_005_night_confession",
        "category": "CONSUMABLE",
        "rarity": "RARE",
        "price_besitos": 8,
        "description_short": "Texto exclusivo que Diana escribió tarde en la noche",
        "description_lucien": (
            "Un texto que Diana escribió tarde en la noche. Pensamientos que "
            "normalmente no comparte. Una confesión entre ella y la oscuridad."
        ),
        "effect_type": "UNLOCK_TEXT",
        "effect_data": {"text_id": "confession_night_01", "word_count": 400},
        "stock": None,
        "level_required": 2,
        "is_active": True,
        "icon": "🌙",
    },

    # =========================================================================
    # DISTINTIVOS (Badges - COSMETIC)
    # =========================================================================

    {
        "name": "Sello del Visitante",
        "internal_code": "dist_001_visitor_seal",
        "category": "COSMETIC",
        "rarity": "COMMON",
        "price_besitos": 2,
        "description_short": "Primera marca de reconocimiento",
        "description_lucien": (
            "La marca más básica. Indica que existe en este universo y decidió "
            "hacerlo oficial. No es mucho. Pero es un comienzo."
        ),
        "effect_type": "BADGE",
        "effect_data": {"badge_id": "visitor_seal", "icon": "👁️"},
        "stock": None,
        "level_required": 1,
        "is_active": True,
        "icon": "👁️",
    },

    {
        "name": "Insignia del Observador",
        "internal_code": "dist_002_observer_mark",
        "category": "COSMETIC",
        "rarity": "UNCOMMON",
        "price_besitos": 5,
        "description_short": "Lucien lo ha notado",
        "description_lucien": (
            "Lucien lo ha notado. Esta insignia lo certifica. "
            "¿Significa algo? Para algunos, todo. Para otros, nada. "
            "Depende de cuánto valore ser visto."
        ),
        "effect_type": "BADGE",
        "effect_data": {"badge_id": "observer_mark", "icon": "🔍"},
        "stock": None,
        "level_required": 2,
        "is_active": True,
        "icon": "🔍",
    },

    {
        "name": "Marca del Evaluado",
        "internal_code": "dist_003_evaluated_mark",
        "category": "COSMETIC",
        "rarity": "RARE",
        "price_besitos": 8,
        "description_short": "Ha pasado las primeras pruebas",
        "description_lucien": (
            "Ha pasado las primeras pruebas. Esta marca lo atestigua. "
            "No todas las pruebas. Pero las suficientes para merecer reconocimiento."
        ),
        "effect_type": "BADGE",
        "effect_data": {"badge_id": "evaluated_mark", "icon": "✓"},
        "stock": None,
        "level_required": 3,
        "is_active": True,
        "icon": "✓",
    },

    {
        "name": "Emblema del Reconocido",
        "internal_code": "dist_004_recognized_emblem",
        "category": "COSMETIC",
        "rarity": "EPIC",
        "price_besitos": 12,
        "description_short": "Diana sabe su nombre",
        "description_lucien": (
            "Diana sabe su nombre. Este emblema lo confirma públicamente. "
            "No es algo que se otorgue fácilmente. Usted lo ganó."
        ),
        "effect_type": "BADGE",
        "effect_data": {"badge_id": "recognized_emblem", "icon": "⭐", "discount_bonus": 5},
        "stock": None,
        "level_required": 4,
        "is_active": True,
        "icon": "⭐",
    },

    {
        "name": "Marca del Confidente",
        "internal_code": "dist_005_confidant_mark",
        "category": "COSMETIC",
        "rarity": "LEGENDARY",
        "price_besitos": 25,
        "description_short": "El círculo interno de Lucien",
        "description_lucien": (
            "Pocos llevan esta marca. Indica que Lucien confía en usted. "
            "Relativamente, por supuesto. La confianza absoluta no existe. "
            "Pero esto es lo más cercano que ofrezco."
        ),
        "effect_type": "BADGE",
        "effect_data": {"badge_id": "confidant_mark", "icon": "🤫", "discount_bonus": 10},
        "stock": 25,
        "level_required": 6,
        "is_active": True,
        "icon": "🤫",
    },

    {
        "name": "Corona del Guardián",
        "internal_code": "dist_006_guardian_crown",
        "category": "COSMETIC",
        "rarity": "LEGENDARY",
        "price_besitos": 50,
        "description_short": "El distintivo más alto del Gabinete",
        "description_lucien": (
            "El distintivo más alto del Gabinete. Solo los Guardianes de Secretos "
            "pueden portarlo. Usted no solo conoce los secretos de Diana. Los protege."
        ),
        "effect_type": "BADGE",
        "effect_data": {"badge_id": "guardian_crown", "icon": "👑", "discount_bonus": 15},
        "stock": 10,
        "level_required": 7,
        "is_active": True,
        "icon": "👑",
    },

    # =========================================================================
    # LLAVES (Narrativos - NARRATIVE)
    # =========================================================================

    {
        "name": "Llave del Fragmento I",
        "internal_code": "key_001_fragment_i",
        "category": "NARRATIVE",
        "rarity": "RARE",
        "price_besitos": 10,
        "description_short": "Abre el primer secreto oculto",
        "description_lucien": (
            "Abre el primer secreto oculto. Un fragmento de historia que Diana "
            "no cuenta públicamente. El comienzo de algo... más profundo."
        ),
        "effect_type": "UNLOCK_NARRATIVE",
        "effect_data": {"fragment_id": "secret_01", "word_count": 500},
        "stock": None,
        "level_required": 3,
        "is_active": True,
        "icon": "🗝️",
    },

    {
        "name": "Llave del Fragmento II",
        "internal_code": "key_002_fragment_ii",
        "category": "NARRATIVE",
        "rarity": "RARE",
        "price_besitos": 12,
        "description_short": "El segundo secreto, más profundo",
        "description_lucien": (
            "El segundo secreto. Más profundo que el primero. "
            "Aquí Diana muestra algo que preferiría esconder."
        ),
        "effect_type": "UNLOCK_NARRATIVE",
        "effect_data": {"fragment_id": "secret_02", "word_count": 600, "requires": "key_001"},
        "stock": None,
        "level_required": 3,
        "is_active": True,
        "icon": "🗝️",
    },

    {
        "name": "Llave del Fragmento III",
        "internal_code": "key_003_fragment_iii",
        "category": "NARRATIVE",
        "rarity": "EPIC",
        "price_besitos": 15,
        "description_short": "El tercer secreto",
        "description_lucien": (
            "El tercer secreto. Aquí las cosas se ponen... interesantes. "
            "Diana no aprobó que esto estuviera disponible. Lo hice yo. "
            "Ella no sabe. O finge no saber."
        ),
        "effect_type": "UNLOCK_NARRATIVE",
        "effect_data": {"fragment_id": "secret_03", "word_count": 700, "includes_image": True},
        "stock": None,
        "level_required": 4,
        "is_active": True,
        "icon": "🗝️",
    },

    {
        "name": "Llave del Archivo Oculto",
        "internal_code": "key_004_hidden_archive",
        "category": "NARRATIVE",
        "rarity": "EPIC",
        "price_besitos": 20,
        "description_short": "Un archivo completo de memorias",
        "description_lucien": (
            "No un fragmento. Un archivo completo. Memorias que Diana "
            "preferiría olvidar. O quizás no. Con ella nunca se sabe."
        ),
        "effect_type": "UNLOCK_NARRATIVE",
        "effect_data": {"fragment_id": "archive_01", "type": "diary_entries"},
        "stock": None,
        "level_required": 4,
        "is_active": True,
        "icon": "🗝️",
    },

    {
        "name": "Llave de la Primera Vez",
        "internal_code": "key_005_first_time",
        "category": "NARRATIVE",
        "rarity": "LEGENDARY",
        "price_besitos": 18,
        "description_short": "La historia de cómo Diana se convirtió en Señorita Kinky",
        "description_lucien": (
            "La historia de cómo Diana se convirtió en Señorita Kinky. "
            "El momento exacto. La decisión. Lo que sintió. "
            "Esto no lo cuenta a nadie. Excepto ahora, a usted."
        ),
        "effect_type": "UNLOCK_NARRATIVE",
        "effect_data": {"fragment_id": "origin_story", "type": "vulnerable"},
        "stock": None,
        "level_required": 5,
        "is_active": True,
        "icon": "🗝️",
    },

    # =========================================================================
    # RELIQUIAS (Digitales - DIGITAL)
    # =========================================================================

    {
        "name": "El Primer Secreto",
        "internal_code": "rel_001_first_secret",
        "category": "DIGITAL",
        "rarity": "EPIC",
        "price_besitos": 30,
        "description_short": "Objeto que representa el primer secreto de Diana",
        "description_lucien": (
            "Un objeto que representa el primer secreto que Diana me confió. "
            "No el objeto literal, claro. Pero su esencia. "
            "Ahora puede ser suyo. Con todo lo que eso implica."
        ),
        "effect_type": "COLLECTIBLE",
        "effect_data": {"collectible_id": "relic_01", "badge": "Portador del Primer Secreto", "icon": "🔮", "discount_bonus": 3},
        "stock": None,
        "level_required": 5,
        "is_active": True,
        "icon": "🔮",
    },

    {
        "name": "Fragmento del Espejo",
        "internal_code": "rel_002_mirror_fragment",
        "category": "DIGITAL",
        "rarity": "LEGENDARY",
        "price_besitos": 40,
        "description_short": "Vea lo que Diana ve",
        "description_lucien": (
            "Un pedazo del espejo donde Diana se mira antes de cada sesión. "
            "A través de él, verá lo que ella ve. "
            "Diana sin el maquillaje de la perfección."
        ),
        "effect_type": "UNLOCK_CONTENT",
        "effect_data": {"content_id": "mirror_vision", "type": "behind_scenes"},
        "stock": None,
        "level_required": 5,
        "is_active": True,
        "icon": "🪞",
    },

    {
        "name": "La Carta No Enviada",
        "internal_code": "rel_003_unsent_letter",
        "category": "DIGITAL",
        "rarity": "LEGENDARY",
        "price_besitos": 50,
        "description_short": "Una carta que Diana escribió pero nunca envió",
        "description_lucien": (
            "Diana escribió esto hace tiempo. A alguien. No sé a quién. "
            "Nunca lo envió. Las palabras quedaron guardadas. "
            "Ahora usted puede leerlas. El destinatario original nunca lo hará."
        ),
        "effect_type": "UNLOCK_TEXT",
        "effect_data": {"text_id": "unsent_letter", "badge": "Lector de lo No Enviado", "icon": "💌"},
        "stock": None,
        "level_required": 6,
        "is_active": True,
        "icon": "💌",
    },

    {
        "name": "Cristal de Medianoche",
        "internal_code": "rel_004_midnight_crystal",
        "category": "DIGITAL",
        "rarity": "LEGENDARY",
        "price_besitos": 45,
        "description_short": "Contenido especial cada medianoche",
        "description_lucien": (
            "Un artefacto que activa contenido especial a medianoche. "
            "Cada noche, cuando el reloj marca las 00:00, algo se desbloquea. "
            "Solo para quienes poseen el Cristal."
        ),
        "effect_type": "DAILY_UNLOCK",
        "effect_data": {"unlock_time": "00:00", "content_type": "rotating"},
        "stock": None,
        "level_required": 5,
        "is_active": True,
        "icon": "🔮",
    },

    {
        "name": "Llave Maestra del Gabinete",
        "internal_code": "rel_005_master_key",
        "category": "DIGITAL",
        "rarity": "LEGENDARY",
        "price_besitos": 75,
        "description_short": "Abre todas las puertas del Gabinete",
        "description_lucien": (
            "La única Llave Maestra. Abre todo lo que está cerrado en el Gabinete. "
            "Todos los fragmentos. Todos los archivos. Todo. "
            "Es el objeto más valioso que poseo. Y el más peligroso."
        ),
        "effect_type": "MASTER_UNLOCK",
        "effect_data": {"badge": "Portador de la Llave Maestra", "icon": "🗝️", "discount_bonus": 20},
        "stock": 5,
        "level_required": 7,
        "is_active": True,
        "icon": "🗝️",
    },

    # =========================================================================
    # ITEMS OCULTOS (Solo visibles para nivel 6+)
    # =========================================================================

    {
        "name": "Susurro de Lucien",
        "internal_code": "secret_001_lucien_whisper",
        "category": "DIGITAL",
        "rarity": "LEGENDARY",
        "price_besitos": 20,
        "description_short": "La perspectiva de Lucien sobre los usuarios",
        "description_lucien": (
            "No todo es sobre Diana. A veces, incluso yo tengo algo que decir. "
            "Este es mi susurro. Mi perspectiva. Lo que observo y no comento. "
            "Hasta ahora."
        ),
        "effect_type": "UNLOCK_AUDIO",
        "effect_data": {"audio_id": "lucien_whisper", "meta": True},
        "stock": None,
        "level_required": 6,
        "is_active": True,
        "icon": "🤫",
        "is_hidden": True,  # Solo visible para nivel 6+
    },

    {
        "name": "Las Coordenadas",
        "internal_code": "secret_002_coordinates",
        "category": "DIGITAL",
        "rarity": "LEGENDARY",
        "price_besitos": 35,
        "description_short": "Números crípticos con significado oculto",
        "description_lucien": (
            "Números. Solo números. No diré qué significan. "
            "Quizás nada. Quizás todo. "
            "Los exploradores verdaderos encontrarán su significado."
        ),
        "effect_type": "EASTER_EGG",
        "effect_data": {"type": "coordinates", "value": "encrypted"},
        "stock": None,
        "level_required": 6,
        "is_active": True,
        "icon": "📍",
        "is_hidden": True,  # Solo visible para nivel 6+
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
