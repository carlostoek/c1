"""
Validators - Funciones de validación reutilizables.

Validadores para:
- Emojis
- IDs de canales
- Tokens
- Etc.
"""
import re
from typing import List, Tuple


def validate_emoji_list(text: str) -> Tuple[bool, str, List[str]]:
    """
    Valida una lista de emojis separados por espacios.

    Reglas:
    - Mínimo 1 emoji
    - Máximo 10 emojis
    - Emojis válidos de Unicode
    - Separados por espacios
    - Duplicados se eliminan automáticamente

    Args:
        text: String con emojis separados por espacios

    Returns:
        Tuple[bool, str, List[str]]:
            - bool: True si válido, False si no
            - str: Mensaje de error (vacío si válido)
            - List[str]: Lista de emojis parseados (vacía si inválido)

    Ejemplos:
        >>> validate_emoji_list("👍 ❤️ 🔥")
        (True, "", ["👍", "❤️", "🔥"])

        >>> validate_emoji_list("")
        (False, "Debes enviar al menos 1 emoji", [])

        >>> validate_emoji_list("👍 " * 11)
        (False, "Máximo 10 emojis permitidos (enviaste 11)", [])

        >>> validate_emoji_list("👍 ❤️ 👍")
        (True, "", ["👍", "❤️"])
    """
    # Limpiar texto
    text = text.strip()

    if not text:
        return False, "Debes enviar al menos 1 emoji", []

    # Separar por espacios y filtrar vacíos
    parts = [part.strip() for part in text.split() if part.strip()]

    # Validar cantidad
    if len(parts) < 1:
        return False, "Debes enviar al menos 1 emoji", []

    if len(parts) > 10:
        return False, f"Máximo 10 emojis permitidos (enviaste {len(parts)})", []

    # Validar que sean emojis válidos (Unicode emoji range)
    # Regex para emojis comunes
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE
    )

    invalid_items = []
    for item in parts:
        if not emoji_pattern.fullmatch(item):
            invalid_items.append(item)

    if invalid_items:
        return (
            False,
            f"Caracteres inválidos detectados: {' '.join(invalid_items)}",
            []
        )

    # Eliminar duplicados manteniendo orden
    unique_emojis = []
    seen = set()
    for emoji in parts:
        if emoji not in seen:
            unique_emojis.append(emoji)
            seen.add(emoji)

    return True, "", unique_emojis


def is_valid_channel_id(channel_id: str) -> bool:
    """
    Valida que un ID de canal tenga el formato correcto.

    Formato válido: -100XXXXXXXXXX (empieza con -100)

    Args:
        channel_id: ID del canal a validar

    Returns:
        True si válido, False si no

    Ejemplos:
        >>> is_valid_channel_id("-1001234567890")
        True

        >>> is_valid_channel_id("1234567890")
        False
    """
    if not channel_id:
        return False

    # Debe empezar con -100
    if not channel_id.startswith("-100"):
        return False

    # Debe ser numérico
    try:
        int(channel_id)
        return True
    except ValueError:
        return False
