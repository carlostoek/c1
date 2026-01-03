"""
Estructura de Contenido Narrativo - Los Kinkys y El Diván

Configuración de la historia completa del universo de Diana.
Define capítulos, fragmentos, speakers y desafíos para el sistema narrativo.

Este archivo solo define datos de estructura. NO modifica modelos de BD.

Historia:
- Los Kinkys (FREE): Niveles 1-3 - Bienvenida a Diana
- El Diván (VIP): Niveles 4-6 - Contenido exclusivo e íntimo

Author: Sistema Narrativo - Universo de Diana
Version: 1.0
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


# =============================================================================
# 1. SPEAKERS (Hablantes de la Historia)
# =============================================================================

"""
Diccionario de speakers con sus características.

Cada speaker tiene:
- name: Nombre real del personaje
- display_name: Cómo se muestra en UI (con emoji)
- style: Estilo de habla/personalidad
- emoji: Emoji representativo
"""

SPEAKERS: Dict[str, Dict[str, str]] = {
    "diana": {
        "name": "Diana",
        "display_name": "🌙 Diana",
        "style": "íntima, misteriosa, vulnerable calculada, primera persona",
        "emoji": "🌙",
        "description": "La creadora de contenido. Su voz es personal, "
                      "a veces vulnerable, siempre calculada. "
                      "Habla en primera persona, comparte fragmentos de su vida.",
    },

    "lucien": {
        "name": "Lucien",
        "display_name": "🎩 Lucien",
        "style": "formal, evaluador, protector, elegante sarcasmo",
        "emoji": "🎩",
        "description": "El mayordomo guardián del universo de Diana. "
                      "Formal, usa 'usted', irónico sutil. "
                      "Evalúa constantemente al usuario. Protege a Diana.",
    },

    "narrator": {
        "name": "Narrador",
        "display_name": "📖 Narrador",
        "style": "tercera persona, observador, descriptivo",
        "emoji": "📖",
        "description": "Voz narrativa en tercera persona. "
                      "Describe escenas, transiciones, y contexto. "
                      "Neutral pero evocador.",
    },
}


# =============================================================================
# 2. CHALLENGE TYPES (Tipos de Desafíos)
# =============================================================================

"""
Tipos de desafíos que pueden aparecer en fragmentos.

Cada tipo define qué debe hacer el usuario para avanzar.
"""

CHALLENGE_TYPES: Dict[str, str] = {
    "REACT_TO_LAST_MESSAGE": "Reaccionar a la última publicación del canal",
    "FIND_EASTER_EGGS": "Encontrar elementos ocultos en publicaciones",
    "ANSWER_QUESTIONS": "Responder preguntas de comprensión",
    "WAIT_TIME": "Esperar un período de tiempo",
    "WRITE_RESPONSE": "Escribir respuesta reflexiva",
    "COMPLETE_PROFILE": "Completar perfil de deseo",
    "MAKE_CHOICE": "Tomar una decisión entre opciones",
    "SOLVE_RIDDLE": "Resolver un acertijo",
}


# =============================================================================
# 3. CAPÍTULOS FREE (Los Kinkys - Niveles 1-3)
# =============================================================================

"""
Capítulos accesibles para todos los usuarios (FREE).

Cubren:
- Nivel 1: Bienvenida al universo
- Nivel 2: Observación y descubrimiento
- Nivel 3: Perfil de Deseo (punto de conversión)
"""

CHAPTERS_FREE: List[Dict[str, Any]] = [
    # =========================================================================
    # CAPÍTULO 1: Los Kinkys - Bienvenida (Nivel 1)
    # =========================================================================
    {
        "id": "ch_free_01",
        "title": "Los Kinkys - Bienvenida",
        "chapter_type": "FREE",
        "narrative_level": 1,
        "order": 1,
        "description": "Primera interacción con el universo de Diana. "
                       "Lucien evalúa, Diana aparece brevemente.",
        "estimated_duration_minutes": 5,
        "unlock_condition": {
            "type": "none",  # Accesible desde el inicio
        },
        "fragments": [
            # Fragmento 1.1: Diana saluda
            {
                "id": "frag_1_1",
                "fragment_type": "DIALOGUE",
                "speaker": "diana",
                "order": 1,
                "content": (
                    "Así que decidiste entrar. Interesante.\n\n"
                    "No todos dan ese paso. La mayoría observa desde afuera, "
                    "preguntándose qué hay aquí. Pero tú... tú cruzaste el umbral.\n\n"
                    "Soy Diana. Aunque aquí me conocen de otras formas."
                ),
                "triggers_next_on": "auto",  # Automático
                "delay_seconds": 3,
            },

            # Fragmento 1.2: Lucien se presenta
            {
                "id": "frag_1_2",
                "fragment_type": "DIALOGUE",
                "speaker": "lucien",
                "order": 2,
                "content": (
                    "Permítame presentarme. Soy Lucien.\n\n"
                    "Administro el acceso al universo de la Señorita. "
                    "No soy su amigo. No soy su enemigo. Soy... el filtro.\n\n"
                    "Diana no recibe a cualquiera. Mi trabajo es determinar "
                    "si usted merece su atención."
                ),
                "triggers_next_on": "auto",
                "delay_seconds": 4,
            },

            # Fragmento 1.3: Primer desafío
            {
                "id": "frag_1_3",
                "fragment_type": "CHALLENGE",
                "speaker": "lucien",
                "order": 3,
                "content": (
                    "Su primer desafío es simple. "
                    "Diana acaba de publicar algo en el canal. "
                    "Su reacción es... esperada.\n\n"
                    "No me decepcione."
                ),
                "challenge_type": "REACT_TO_LAST_MESSAGE",
                "challenge_data": {
                    "timeout_hours": 24,
                    "reaction_required": True,
                },
                "reward_besitos": 1.0,
                "triggers_next_on": "challenge_complete",
            },

            # Fragmento 1.4a: Respuesta rápida (DIRECT signal)
            {
                "id": "frag_1_4a",
                "fragment_type": "RESPONSE",
                "speaker": "lucien",
                "order": 4,
                "condition": {
                    "type": "challenge_completion_time",
                    "operator": "<",
                    "value": 30,  # Menos de 30 segundos
                },
                "content": (
                    "Rápido. Muy rápido.\n\n"
                    "La impulsividad puede ser virtud o defecto. "
                    "El tiempo dirá cuál es en su caso.\n\n"
                    "Ha ganado su primer Besito. Diana lo nota... apenas."
                ),
                "grants_archetype_signal": "DIRECT",
                "triggers_next_on": "auto",
            },

            # Fragmento 1.4b: Respuesta lenta (PATIENT signal)
            {
                "id": "frag_1_4b",
                "fragment_type": "RESPONSE",
                "speaker": "lucien",
                "order": 4,
                "condition": {
                    "type": "challenge_completion_time",
                    "operator": ">=",
                    "value": 30,  # 30 segundos o más
                },
                "content": (
                    "Se tomó su tiempo. Procesó. No reaccionó por impulso.\n\n"
                    "Eso es... inusual. La mayoría se apresura por agradar.\n\n"
                    "Ha ganado su primer Besito. Diana nota a quienes no se apresuran."
                ),
                "grants_archetype_signal": "PATIENT",
                "triggers_next_on": "auto",
            },

            # Fragmento 1.5: Entrega de pista
            {
                "id": "frag_1_5",
                "fragment_type": "CLUE",
                "speaker": "lucien",
                "order": 5,
                "content": (
                    "Su Mochila del Viajero ahora contiene algo.\n\n"
                    "Pista 1 del mapa hacia Diana. "
                    "Hay más. Aparecerán cuando Diana sienta que usted está listo.\n\n"
                    "Por ahora... observe. O regrese. La elección es suya."
                ),
                "grants_item": "clue_map_01",
                "unlocks_next_chapter": True,
            },
        ],
    },

    # =========================================================================
    # CAPÍTULO 2: Los Kinkys - Observación (Nivel 2)
    # =========================================================================
    {
        "id": "ch_free_02",
        "title": "Los Kinkys - Observación",
        "chapter_type": "FREE",
        "narrative_level": 2,
        "order": 2,
        "description": "Misión de observación de 3 días. Lucien monitorea actividad.",
        "estimated_duration_minutes": 10,
        "unlock_condition": {
            "type": "level_required",
            "value": 2,
        },
        "previous_chapter": "ch_free_01",
        "fragments": [
            {
                "id": "frag_2_1",
                "fragment_type": "DIALOGUE",
                "speaker": "lucien",
                "order": 1,
                "content": (
                    "Ha regresado. Y ha alcanzado un nuevo nivel... Observado.\n\n"
                    "Interesante. Muchos se quedan en Visitante. "
                    "Contentos con mirar desde afuera.\n\n"
                    "Usted decidió mirar más de cerca."
                ),
                "triggers_next_on": "auto",
            },
            # Más fragmentos se desarrollarán en fases posteriores
            # Esta es la estructura base para Nivel 2
        ],
    },

    # =========================================================================
    # CAPÍTULO 3: Los Kinkys - Perfil de Deseo (Nivel 3)
    # =========================================================================
    {
        "id": "ch_free_03",
        "title": "Los Kinkys - Perfil de Deseo",
        "chapter_type": "FREE",
        "narrative_level": 3,
        "order": 3,
        "description": "Cuestionario personal. Punto de conversión a VIP.",
        "estimated_duration_minutes": 15,
        "unlock_condition": {
            "type": "level_required",
            "value": 3,
        },
        "previous_chapter": "ch_free_02",
        "fragments": [
            {
                "id": "frag_3_1",
                "fragment_type": "DIALOGUE",
                "speaker": "diana",
                "order": 1,
                "content": (
                    "Hemos notado su persistencia. Lucien me ha mantenido informada.\n\n"
                    "Es... inusual. La mayoría se queda en la superficie.\n\n"
                    "Usted parece querer más. Estoy dispuesta a dar... "
                    "si está dispuesto a recibir."
                ),
                "triggers_next_on": "auto",
            },
            # Último fragmento es la invitación "Llave del Diván"
            # Más fragmentos se desarrollarán en fases posteriores
        ],
    },
]


# =============================================================================
# 4. CAPÍTULOS VIP (El Diván - Niveles 4-6)
# =============================================================================

"""
Capítulos exclusivos VIP (El Diván).

Solo accesibles con suscripción VIP.
Contenido más íntimo, personal y profundo.
"""

CHAPTERS_VIP: List[Dict[str, Any]] = [
    # =========================================================================
    # CAPÍTULO VIP 1: El Diván - Entrada (Nivel 4)
    # =========================================================================
    {
        "id": "ch_vip_01",
        "title": "El Diván - Entrada",
        "chapter_type": "VIP",
        "narrative_level": 4,
        "order": 1,
        "description": "Bienvenida al círculo íntimo. Contenido exclusivo comienza.",
        "estimated_duration_minutes": 20,
        "unlock_condition": {
            "type": "vip_status",  # Requiere ser VIP
        },
        "previous_chapter": "ch_free_03",
        "fragments": [
            {
                "id": "frag_vip_1_1",
                "fragment_type": "DIALOGUE",
                "speaker": "lucien",
                "order": 1,
                "content": (
                    "Bienvenido al Diván.\n\n"
                    "Muchos llaman. Pocos entran. Menos aún permanecen.\n\n"
                    "Usted ha demostrado... mérito. Diana lo ha notado. "
                    "Yo... he dejado de cuestionar su presencia.\n\n"
                    "Por favor, siéntase. Diana estará con usted shortly."
                ),
                "triggers_next_on": "auto",
            },
            # Más fragmentos VIP se desarrollarán en fases posteriores
        ],
    },

    # Capítulos adicionales VIP (Niveles 5-6) se desarrollarán posteriormente
]


# =============================================================================
# 5. FUNCIONES HELPER
# =============================================================================

def get_chapter_by_level(level: int, is_vip: bool) -> Optional[Dict[str, Any]]:
    """
    Obtiene el capítulo correspondiente a un nivel específico.

    Args:
        level: Nivel del usuario (1-7)
        is_vip: Si el usuario es VIP

    Returns:
        Diccionario del capítulo o None si no existe

    Example:
        chapter = get_chapter_by_level(1, False)
        # → Returns "Los Kinkys - Bienvenida"

        chapter = get_chapter_by_level(4, True)
        # → Returns "El Diván - Entrada"
    """
    chapters = CHAPTERS_VIP if is_vip else CHAPTERS_FREE

    for chapter in chapters:
        if chapter["narrative_level"] == level:
            return chapter

    return None


def get_chapter_by_id(chapter_id: str) -> Optional[Dict[str, Any]]:
    """
    Busca un capítulo por su ID.

    Args:
        chapter_id: ID del capítulo (ej: "ch_free_01")

    Returns:
        Diccionario del capítulo o None si no existe
    """
    all_chapters = CHAPTERS_FREE + CHAPTERS_VIP

    for chapter in all_chapters:
        if chapter["id"] == chapter_id:
            return chapter

    return None


def get_fragments_for_chapter(chapter_id: str) -> List[Dict[str, Any]]:
    """
    Obtiene todos los fragmentos de un capítulo.

    Args:
        chapter_id: ID del capítulo

    Returns:
        Lista de fragmentos ordenados por order

    Example:
        fragments = get_fragments_for_chapter("ch_free_01")
        # → Returns list of 5 fragments
    """
    chapter = get_chapter_by_id(chapter_id)

    if not chapter:
        return []

    fragments = chapter.get("fragments", [])
    # Ordenar por campo 'order'
    return sorted(fragments, key=lambda x: x.get("order", 0))


def get_next_chapter(current_chapter_id: str, user_is_vip: bool) -> Optional[Dict[str, Any]]:
    """
    Obtiene el siguiente capítulo en la secuencia narrativa.

    Args:
        current_chapter_id: ID del capítulo actual
        user_is_vip: Si el usuario es VIP

    Returns:
        Siguiente capítulo o None si no hay más
    """
    current_chapter = get_chapter_by_id(current_chapter_id)

    if not current_chapter:
        return None

    current_level = current_chapter.get("narrative_level", 0)
    next_level = current_level + 1

    return get_chapter_by_level(next_level, user_is_vip)


def get_speaker_by_name(speaker_name: str) -> Optional[Dict[str, str]]:
    """
    Obtiene información de un speaker por su nombre.

    Args:
        speaker_name: Nombre del speaker ("diana", "lucien", "narrator")

    Returns:
        Diccionario con información del speaker o None
    """
    return SPEAKERS.get(speaker_name.lower())


def get_all_chapters(is_vip: bool) -> List[Dict[str, Any]]:
    """
    Obtiene todos los capítulos disponibles según tipo de usuario.

    Args:
        is_vip: Si el usuario es VIP

    Returns:
        Lista de capítulos ordenados
    """
    if is_vip:
        return CHAPTERS_FREE + CHAPTERS_VIP
    else:
        return CHAPTERS_FREE


def get_fragment_by_id(fragment_id: str) -> Optional[Dict[str, Any]]:
    """
    Busca un fragmento específico por su ID.

    Args:
        fragment_id: ID del fragmento (ej: "frag_1_1")

    Returns:
        Diccionario del fragmento o None si no existe
    """
    all_chapters = CHAPTERS_FREE + CHAPTERS_VIP

    for chapter in all_chapters:
        fragments = chapter.get("fragments", [])
        for fragment in fragments:
            if fragment["id"] == fragment_id:
                return fragment

    return None


def count_total_fragments(is_vip: bool = False) -> int:
    """
    Cuenta el total de fragmentos disponibles.

    Args:
        is_vip: Si contar también fragmentos VIP

    Returns:
        Número total de fragmentos
    """
    chapters = get_all_chapters(is_vip)
    total = 0

    for chapter in chapters:
        fragments = chapter.get("fragments", [])
        total += len(fragments)

    return total


def get_story_statistics() -> Dict[str, Any]:
    """
    Retorna estadísticas de la historia.

    Returns:
        Diccionario con contadores y resúmenes
    """
    free_chapters = len(CHAPTERS_FREE)
    vip_chapters = len(CHAPTERS_VIP)
    total_chapters = free_chapters + vip_chapters

    free_fragments = count_total_fragments(is_vip=False)
    total_fragments = count_total_fragments(is_vip=True)

    # Estimación de duración total
    free_duration = sum(
        ch.get("estimated_duration_minutes", 0)
        for ch in CHAPTERS_FREE
    )
    total_duration = free_duration + sum(
        ch.get("estimated_duration_minutes", 0)
        for ch in CHAPTERS_VIP
    )

    return {
        "total_chapters": total_chapters,
        "free_chapters": free_chapters,
        "vip_chapters": vip_chapters,
        "total_fragments": total_fragments,
        "free_fragments": free_fragments,
        "vip_fragments": total_fragments - free_fragments,
        "estimated_duration_minutes_free": free_duration,
        "estimated_duration_minutes_total": total_duration,
        "speakers": list(SPEAKERS.keys()),
        "speakers_count": len(SPEAKERS),
        "challenge_types": list(CHALLENGE_TYPES.keys()),
    }


# =============================================================================
# 6. DATA CLASES PARA VALIDACIÓN
# =============================================================================

@dataclass
class ChapterValidationError:
    """Resultado de validación de capítulo."""
    is_valid: bool
    errors: List[str]


def validate_chapter(chapter: Dict[str, Any]) -> ChapterValidationError:
    """
    Valida que un capítulo tenga todos los campos requeridos.

    Args:
        chapter: Diccionario con datos del capítulo

    Returns:
        ChapterValidationError con resultado y errores
    """
    errors = []

    required_fields = [
        "id",
        "title",
        "chapter_type",
        "narrative_level",
        "order",
        "description",
        "fragments",
    ]

    for field in required_fields:
        if field not in chapter:
            errors.append(f"Campo requerido faltante: {field}")

    # Validar que chapter_type sea válido
    valid_types = ["FREE", "VIP"]
    if "chapter_type" in chapter and chapter["chapter_type"] not in valid_types:
        errors.append(f"chapter_type inválido: {chapter.get('chapter_type')}")

    # Validar nivel
    if "narrative_level" in chapter:
        level = chapter["narrative_level"]
        if not isinstance(level, int) or level < 1 or level > 7:
            errors.append("narrative_level debe estar entre 1 y 7")

    # Validar fragmentos
    if "fragments" in chapter:
        fragments = chapter["fragments"]
        if not isinstance(fragments, list):
            errors.append("fragments debe ser una lista")
        else:
            for i, fragment in enumerate(fragments):
                if not isinstance(fragment, dict):
                    errors.append(f"Fragmento {i} debe ser un diccionario")
                elif "id" not in fragment:
                    errors.append(f"Fragmento {i} no tiene 'id'")

    return ChapterValidationError(
        is_valid=len(errors) == 0,
        errors=errors
    )


def validate_fragment(fragment: Dict[str, Any]) -> ChapterValidationError:
    """
    Valida que un fragmento tenga todos los campos requeridos.

    Args:
        fragment: Diccionario con datos del fragmento

    Returns:
        ChapterValidationError con resultado y errores
    """
    errors = []

    required_fields = [
        "id",
        "fragment_type",
        "order",
        "content",
    ]

    for field in required_fields:
        if field not in fragment:
            errors.append(f"Campo requerido faltante: {field}")

    # Validar speaker para diálogos
    if fragment.get("fragment_type") == "DIALOGUE" and "speaker" not in fragment:
        errors.append("Fragmento DIALOGUE requiere 'speaker'")

    # Validar challenge_type para desafíos
    if fragment.get("fragment_type") == "CHALLENGE":
        if "challenge_type" not in fragment:
            errors.append("Fragmento CHALLENGE requiere 'challenge_type'")
        elif fragment["challenge_type"] not in CHALLENGE_TYPES:
            errors.append(f"challenge_type inválido: {fragment.get('challenge_type')}")

    return ChapterValidationError(
        is_valid=len(errors) == 0,
        errors=errors
    )
