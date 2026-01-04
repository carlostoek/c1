"""Estructura de contenido narrativo para el sistema de historia.

Este archivo define la estructura de capítulos y fragmentos que forman
la historia interactiva de Diana y Lucien.

El contenido completo de todos los fragmentos se completará en Fase 5.
Por ahora, esta estructura define el esqueleto de la historia con los
primeros fragmentos del Nivel 1 como ejemplo.

Uso:
    from bot.narrative.config.story_content import (
        get_chapter_by_level,
        get_fragments_for_chapter
    )

    chapter = get_chapter_by_level(level=1, is_vip=False)
    fragments = get_fragments_for_chapter(chapter["id"])
"""

from typing import List, Dict, Any, Optional


# ============================================================
# 1. SPEAKERS (personajes que narran)
# ============================================================

SPEAKERS = {
    "diana": {
        "name": "Diana",
        "display_name": "🌙 Diana",
        "style": "íntima, misteriosa, vulnerable calculada, primera persona"
    },
    "lucien": {
        "name": "Lucien",
        "display_name": "🎩 Lucien",
        "style": "formal, evaluador, protector, elegante sarcasmo"
    },
    "narrator": {
        "name": "Narrador",
        "display_name": "📖 Narrador",
        "style": "tercera persona, descriptivo, atmosférico"
    }
}


# ============================================================
# 2. CHALLENGE TYPES (tipos de desafíos)
# ============================================================

CHALLENGE_TYPES = {
    "REACT_TO_LAST_MESSAGE": "Reaccionar a la última publicación del canal",
    "FIND_EASTER_EGGS": "Encontrar elementos ocultos en publicaciones",
    "ANSWER_QUESTIONS": "Responder preguntas de comprensión",
    "WAIT_TIME": "Esperar un período de tiempo",
    "WRITE_RESPONSE": "Escribir respuesta reflexiva",
    "COMPLETE_PROFILE": "Completar perfil de deseo"
}


# ============================================================
# 3. CAPÍTULOS FREE (Niveles 1-3)
# ============================================================

CHAPTERS_FREE = [
    {
        "id": "ch_free_01",
        "name": "Los Kinkys - Bienvenida",
        "slug": "los-kinkys-bienvenida",
        "chapter_type": "FREE",
        "narrative_level": 1,
        "order": 1,
        "description": "Primera interacción con el universo de Diana",
        "is_active": True,
        "fragments": [
            {
                "id": "frag_1_1",
                "fragment_key": "scene_1_1_diana_intro",
                "title": "Primera Aparición",
                "speaker": "diana",
                "order": 1,
                "is_entry_point": True,
                "is_ending": False,
                "is_active": True,
                "content": (
                    "<i>Así que decidiste entrar. Interesante.</i>\n\n"
                    "No todos dan ese paso. La mayoría observa desde afuera, "
                    "preguntándose qué hay aquí. Pero tú... tú cruzaste el umbral.\n\n"
                    "Soy Diana. Aunque aquí me conocen de otras formas."
                ),
                "visual_hint": "Diana en penumbra, solo su silueta visible",
                "decisions": [
                    {
                        "button_text": "Continuar",
                        "target_fragment_key": "scene_1_2_lucien_intro",
                        "order": 1
                    }
                ]
            },
            {
                "id": "frag_1_2",
                "fragment_key": "scene_1_2_lucien_intro",
                "title": "El Filtro",
                "speaker": "lucien",
                "order": 2,
                "is_entry_point": False,
                "is_ending": False,
                "is_active": True,
                "content": (
                    "Permítame presentarme. Soy Lucien.\n\n"
                    "Administro el acceso al universo de la Señorita. "
                    "No soy su amigo. No soy su enemigo. Soy... el filtro.\n\n"
                    "Diana no recibe a cualquiera. Mi trabajo es determinar "
                    "si usted merece su atención."
                ),
                "visual_hint": "Lucien de pie, elegante y distante",
                "decisions": [
                    {
                        "button_text": "Entiendo",
                        "target_fragment_key": "scene_1_3_challenge",
                        "order": 1
                    }
                ]
            },
            {
                "id": "frag_1_3",
                "fragment_key": "scene_1_3_challenge",
                "title": "El Primer Desafío",
                "speaker": "lucien",
                "order": 3,
                "is_entry_point": False,
                "is_ending": False,
                "is_active": True,
                "content": (
                    "Su primer desafío es simple. "
                    "Diana acaba de publicar algo en el canal. "
                    "Su reacción es... esperada.\n\n"
                    "No me decepcione."
                ),
                "visual_hint": "Lucien observa con expectación",
                "extra_metadata": {
                    "challenge_type": "REACT_TO_LAST_MESSAGE",
                    "challenge_data": {"timeout_hours": 24},
                    "reward_besitos": 1
                },
                "decisions": []
            },
            {
                "id": "frag_1_4a",
                "fragment_key": "scene_1_4a_fast_response",
                "title": "Impulsivo",
                "speaker": "lucien",
                "order": 4,
                "is_entry_point": False,
                "is_ending": False,
                "is_active": True,
                "content": (
                    "Rápido. Muy rápido.\n\n"
                    "La impulsividad puede ser virtud o defecto. "
                    "El tiempo dirá cuál es en su caso.\n\n"
                    "Ha ganado su primer Favor. Diana lo nota... apenas."
                ),
                "extra_metadata": {
                    "condition": "challenge_completed_fast",  # <30 segundos
                    "grants_archetype_signal": "DIRECT"
                },
                "decisions": [
                    {
                        "button_text": "Continuar",
                        "target_fragment_key": "scene_1_5_clue",
                        "order": 1
                    }
                ]
            },
            {
                "id": "frag_1_4b",
                "fragment_key": "scene_1_4b_slow_response",
                "title": "Paciente",
                "speaker": "lucien",
                "order": 4,
                "is_entry_point": False,
                "is_ending": False,
                "is_active": True,
                "content": (
                    "Se tomó su tiempo. Procesó. No reaccionó por impulso.\n\n"
                    "Eso es... inusual. La mayoría se apresura por agradar.\n\n"
                    "Ha ganado su primer Favor. Diana nota a quienes no se apresuran."
                ),
                "extra_metadata": {
                    "condition": "challenge_completed_slow",  # >5 minutos
                    "grants_archetype_signal": "PATIENT"
                },
                "decisions": [
                    {
                        "button_text": "Continuar",
                        "target_fragment_key": "scene_1_5_clue",
                        "order": 1
                    }
                ]
            },
            {
                "id": "frag_1_5",
                "fragment_key": "scene_1_5_clue",
                "title": "La Mochila",
                "speaker": "lucien",
                "order": 5,
                "is_entry_point": False,
                "is_ending": True,
                "is_active": True,
                "content": (
                    "Su Mochila del Viajero ahora contiene algo.\n\n"
                    "<b>Pista 1 del mapa hacia Diana.</b>\n\n"
                    "Hay más. Aparecerán cuando Diana sienta que usted está listo."
                ),
                "extra_metadata": {
                    "grants_item": "clue_map_01",
                    "item_type": "NARRATIVE",
                    "item_rarity": "COMMON"
                },
                "decisions": [
                    {
                        "button_text": "Ver Mochila",
                        "target_fragment_key": "backpack",
                        "order": 1
                    }
                ]
            }
        ]
    },
    {
        "id": "ch_free_02",
        "name": "Los Kinkys - Observación",
        "slug": "los-kinkys-observacion",
        "chapter_type": "FREE",
        "narrative_level": 2,
        "order": 2,
        "description": "Misión de observación de 3 días",
        "is_active": True,
        "unlock_condition": {
            "level_required": 2,
            "previous_chapter": "ch_free_01"
        },
        "fragments": [
            {
                "id": "frag_2_1",
                "fragment_key": "scene_2_1_mission_start",
                "title": "El Periodo de Observación",
                "speaker": "lucien",
                "order": 1,
                "is_entry_point": True,
                "is_ending": False,
                "is_active": True,
                "content": (
                    "Ahora que ha demostrado interés básico, "
                    "comienza la verdadera evaluación.\n\n"
                    "Durante los próximos 3 días, observaré su comportamiento:\n"
                    "• ¿Con qué frecuencia interactúa?\n"
                    "• ¿Cómo responde al contenido?\n"
                    "• ¿Muestra interés genuino o curiosidad superficial?\n\n"
                    "Diana valora la consistencia."
                ),
                "decisions": [
                    {
                        "button_text": "Comenzar Observación",
                        "target_fragment_key": "scene_2_2_daily_check",
                        "order": 1
                    }
                ]
            },
            {
                "id": "frag_2_2",
                "fragment_key": "scene_2_2_daily_check",
                "title": "Día 1",
                "speaker": "lucien",
                "order": 2,
                "is_entry_point": False,
                "is_ending": False,
                "is_active": True,
                "content": (
                    "Primer día de observación. "
                    "Haga lo que suele hacer. Solo observe... y sea observado."
                ),
                "extra_metadata": {
                    "mission_type": "DAILY",
                    "mission_data": {"target_interactions": 3}
                },
                "decisions": []
            }
            # Más fragmentos se agregarán en Fase 5
        ]
    },
    {
        "id": "ch_free_03",
        "name": "Los Kinkys - Perfil de Deseo",
        "slug": "los-kinkys-perfil-deseo",
        "chapter_type": "FREE",
        "narrative_level": 3,
        "order": 3,
        "description": "Cuestionario personal y punto de conversión",
        "is_active": True,
        "unlock_condition": {
            "level_required": 3,
            "previous_chapter": "ch_free_02"
        },
        "fragments": [
            {
                "id": "frag_3_1",
                "fragment_key": "scene_3_1_questionnaire",
                "title": "El Cuestionario",
                "speaker": "lucien",
                "order": 1,
                "is_entry_point": True,
                "is_ending": False,
                "is_active": True,
                "content": (
                    "Ha llegado lejos. Más lejos que la mayoría.\n\n"
                    "Diana quiere conocerlo mejor. "
                    "No sus datos básicos... eso ya lo sabemos.\n\n"
                    "Ella quiere entender lo que motiva sus acciones.\n\n"
                    "Responda con honestidad. Las mentiras se detectan."
                ),
                "decisions": [
                    {
                        "button_text": "Comenzar Cuestionario",
                        "target_fragment_key": "scene_3_2_questions",
                        "order": 1
                    }
                ]
            },
            {
                "id": "frag_3_2",
                "fragment_key": "scene_3_2_questions",
                "title": "Preguntas",
                "speaker": "diana",
                "order": 2,
                "is_entry_point": False,
                "is_ending": False,
                "is_active": True,
                "content": (
                    "<b>Pregunta 1:</b>\n\n"
                    "¿Qué busca aquí?\n\n"
                    "a) Entretenimiento pasajero\n"
                    "b) Conexión genuina\n"
                    "c) Algo que aún no puedo definir\n\n"
                    "Piense su respuesta."
                ),
                "decisions": [
                    {
                        "button_text": "a) Entretenimiento",
                        "target_fragment_key": "scene_3_3_response_a",
                        "order": 1
                    },
                    {
                        "button_text": "b) Conexión",
                        "target_fragment_key": "scene_3_3_response_b",
                        "order": 2
                    },
                    {
                        "button_text": "c) No lo sé",
                        "target_fragment_key": "scene_3_3_response_c",
                        "order": 3
                    }
                ]
            }
            # Más fragmentos se agregarán en Fase 5
        ]
    }
]


# ============================================================
# 4. CAPÍTULOS VIP (Niveles 4-6)
# ============================================================

CHAPTERS_VIP = [
    {
        "id": "ch_vip_01",
        "name": "El Diván - Entrada",
        "slug": "el-divan-entrada",
        "chapter_type": "VIP",
        "narrative_level": 4,
        "order": 1,
        "description": "Bienvenida al espacio exclusivo de Diana",
        "is_active": True,
        "unlock_condition": {
            "level_required": 4,
            "requires_vip": True
        },
        "fragments": [
            {
                "id": "frag_vip_1_1",
                "fragment_key": "scene_vip_1_1_welcome",
                "title": "Bienvenida al Diván",
                "speaker": "diana",
                "order": 1,
                "is_entry_point": True,
                "is_ending": False,
                "is_active": True,
                "content": (
                    "<i>Entró.</i>\n\n"
                    "No todos llegan hasta aquí. De hecho, muy pocos.\n\n"
                    "Este es mi espacio privado. El Diván. "
                    "Donde comparto lo que no comparto en público.\n\n"
                    "Bienvenido... realmente."
                ),
                "visual_hint": "Diana más relajada, ambiente íntimo",
                "decisions": [
                    {
                        "button_text": "Estoy honrado",
                        "target_fragment_key": "scene_vip_1_2_explanation",
                        "order": 1
                    }
                ]
            },
            {
                "id": "frag_vip_1_2",
                "fragment_key": "scene_vip_1_2_explanation",
                "title": "Las Reglas del Diván",
                "speaker": "lucien",
                "order": 2,
                "is_entry_point": False,
                "is_ending": False,
                "is_active": True,
                "content": (
                    "Ahora que está aquí, debe conocer las reglas:\n\n"
                    "1. <b>Discreción</b> - Lo que ve aquí, permanece aquí.\n"
                    "2. <b>Respeto</b> - A Diana y a otros miembros.\n"
                    "3. <b>Autenticidad</b> - No finja ser quien no es.\n\n"
                    "¿Acepta estos términos?"
                ),
                "decisions": [
                    {
                        "button_text": "Acepto",
                        "target_fragment_key": "scene_vip_1_3_access",
                        "order": 1
                    },
                    {
                        "button_text": "Necesito pensar",
                        "target_fragment_key": "pause",
                        "order": 2
                    }
                ]
            }
            # Más fragmentos VIP se agregarán en Fase 5
        ]
    },
    {
        "id": "ch_vip_02",
        "name": "El Diván - Profundización",
        "slug": "el-divan-profundizacion",
        "chapter_type": "VIP",
        "narrative_level": 5,
        "order": 2,
        "description": "Contenido más íntimo y personal",
        "is_active": True,
        "unlock_condition": {
            "level_required": 5,
            "requires_vip": True,
            "previous_chapter": "ch_vip_01"
        },
        "fragments": []
        # Contenido se agregará en Fase 5
    },
    {
        "id": "ch_vip_03",
        "name": "El Diván - Confidencias",
        "slug": "el-divan-confidencias",
        "chapter_type": "VIP",
        "narrative_level": 6,
        "order": 3,
        "description": "El nivel más profundo de conexión con Diana",
        "is_active": True,
        "unlock_condition": {
            "level_required": 6,
            "requires_vip": True,
            "previous_chapter": "ch_vip_02"
        },
        "fragments": []
        # Contenido se agregará en Fase 5
    }
]


# ============================================================
# 5. FUNCIONES HELPER
# ============================================================

def get_chapter_by_level(level: int, is_vip: bool = False) -> Optional[Dict[str, Any]]:
    """Obtiene el capítulo correspondiente a un nivel.

    Args:
        level: Nivel narrativo (1-6)
        is_vip: Si el usuario es VIP (para capítulos VIP)

    Returns:
        Dict con datos del capítulo o None si no existe
    """
    chapters = CHAPTERS_VIP if is_vip else CHAPTERS_FREE

    for chapter in chapters:
        if chapter["narrative_level"] == level:
            return chapter

    return None


def get_fragments_for_chapter(chapter_id: str) -> List[Dict[str, Any]]:
    """Obtiene todos los fragmentos de un capítulo.

    Args:
        chapter_id: ID del capítulo (ej: "ch_free_01")

    Returns:
        Lista de fragmentos ordenados por order
    """
    # Buscar en FREE
    for chapter in CHAPTERS_FREE:
        if chapter["id"] == chapter_id:
            return chapter.get("fragments", [])

    # Buscar en VIP
    for chapter in CHAPTERS_VIP:
        if chapter["id"] == chapter_id:
            return chapter.get("fragments", [])

    return []


def get_next_chapter(
    current_chapter_id: str,
    user_is_vip: bool
) -> Optional[Dict[str, Any]]:
    """Obtiene el siguiente capítulo después del actual.

    Args:
        current_chapter_id: ID del capítulo actual
        user_is_vip: Si el usuario es VIP

    Returns:
        Dict con datos del siguiente capítulo o None si no hay más
    """
    chapters = CHAPTERS_VIP if user_is_vip else CHAPTERS_FREE

    # Buscar capítulo actual
    current_index = None
    for i, chapter in enumerate(chapters):
        if chapter["id"] == current_chapter_id:
            current_index = i
            break

    # Retornar siguiente
    if current_index is not None and current_index + 1 < len(chapters):
        return chapters[current_index + 1]

    return None


def get_entry_fragment(chapter_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene el fragmento de entrada de un capítulo.

    Args:
        chapter_id: ID del capítulo

    Returns:
        Dict con datos del fragmento de entrada o None
    """
    fragments = get_fragments_for_chapter(chapter_id)

    for fragment in fragments:
        if fragment.get("is_entry_point", False):
            return fragment

    return None


def get_all_chapters(is_vip: bool = False) -> List[Dict[str, Any]]:
    """Retorna todos los capítulos (FREE o VIP).

    Args:
        is_vip: Si retornar capítulos VIP (False = FREE)

    Returns:
        Lista de todos los capítulos del tipo especificado
    """
    return CHAPTERS_VIP if is_vip else CHAPTERS_FREE


def get_chapter_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    """Busca un capítulo por su slug.

    Args:
        slug: Slug del capítulo (ej: "los-kinkys-bienvenida")

    Returns:
        Dict con datos del capítulo o None
    """
    all_chapters = CHAPTERS_FREE + CHAPTERS_VIP

    for chapter in all_chapters:
        if chapter["slug"] == slug:
            return chapter

    return None


def get_fragment_by_key(fragment_key: str) -> Optional[Dict[str, Any]]:
    """Busca un fragmento por su key único.

    Args:
        fragment_key: Key del fragmento (ej: "scene_1_1_diana_intro")

    Returns:
        Dict con datos del fragmento o None
    """
    all_chapters = CHAPTERS_FREE + CHAPTERS_VIP

    for chapter in all_chapters:
        for fragment in chapter.get("fragments", []):
            if fragment["fragment_key"] == fragment_key:
                return fragment

    return None


def validate_chapter(chapter: Dict[str, Any]) -> tuple[bool, str]:
    """Valida que un capítulo tenga todos los campos requeridos.

    Args:
        chapter: Diccionario con datos del capítulo

    Returns:
        Tuple (is_valid, error_message)
    """
    required_fields = ["id", "name", "slug", "chapter_type", "narrative_level", "order"]

    for field in required_fields:
        if field not in chapter:
            return False, f"Missing required field: {field}"

    # Validar chapter_type
    valid_types = ["FREE", "VIP"]
    if chapter["chapter_type"] not in valid_types:
        return False, f"Invalid chapter_type: {chapter['chapter_type']}"

    # Validar nivel
    if chapter["narrative_level"] < 1 or chapter["narrative_level"] > 6:
        return False, f"Invalid narrative_level: {chapter['narrative_level']}"

    # Validar slug formato
    slug = chapter["slug"]
    if not slug.replace("-", "").isalnum():
        return False, f"Invalid slug format: {slug}"

    return True, "OK"


def validate_fragment(fragment: Dict[str, Any]) -> tuple[bool, str]:
    """Valida que un fragmento tenga todos los campos requeridos.

    Args:
        fragment: Diccionario con datos del fragmento

    Returns:
        Tuple (is_valid, error_message)
    """
    required_fields = [
        "id", "fragment_key", "title", "speaker",
        "order", "is_entry_point", "is_ending", "content"
    ]

    for field in required_fields:
        if field not in fragment:
            return False, f"Missing required field: {field}"

    # Validar speaker
    valid_speakers = ["diana", "lucien", "narrator"]
    if fragment["speaker"] not in valid_speakers:
        return False, f"Invalid speaker: {fragment['speaker']}"

    # Validar key formato
    key = fragment["fragment_key"]
    if not key.replace("_", "").isalnum():
        return False, f"Invalid fragment_key format: {key}"

    return True, "OK"


def get_content_summary() -> Dict[str, Any]:
    """Retorna un resumen del contenido narrativo.

    Returns:
        Dict con estadísticas del contenido
    """
    free_fragments = sum(len(ch.get("fragments", [])) for ch in CHAPTERS_FREE)
    vip_fragments = sum(len(ch.get("fragments", [])) for ch in CHAPTERS_VIP)

    return {
        "total_chapters": len(CHAPTERS_FREE) + len(CHAPTERS_VIP),
        "free_chapters": len(CHAPTERS_FREE),
        "vip_chapters": len(CHAPTERS_VIP),
        "total_fragments": free_fragments + vip_fragments,
        "free_fragments": free_fragments,
        "vip_fragments": vip_fragments,
        "narrative_levels": {
            "free": [ch["narrative_level"] for ch in CHAPTERS_FREE],
            "vip": [ch["narrative_level"] for ch in CHAPTERS_VIP]
        }
    }
