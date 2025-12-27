"""
Formatters - Funciones de formateo reutilizables.

Proporciona formateo consistente para:
- Fechas y tiempos
- Números y monedas
- Porcentajes
- Tiempos relativos (hace X, en X)
- User IDs
- Etc.

Todas las funciones son stateless y puras (sin efectos secundarios).
"""
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Union


# ===== FORMATEO DE FECHAS Y TIEMPOS =====

def format_datetime(dt: datetime, include_time: bool = True) -> str:
    """
    Formatea un datetime en formato ISO simplificado.

    Args:
        dt: Datetime a formatear
        include_time: Si incluir la hora (default: True)

    Returns:
        String formateado

    Examples:
        >>> format_datetime(datetime(2024, 12, 13, 14, 30))
        "2024-12-13 14:30"

        >>> format_datetime(datetime(2024, 12, 13, 14, 30), include_time=False)
        "2024-12-13"
    """
    if not isinstance(dt, datetime):
        raise TypeError("dt debe ser datetime")

    if include_time:
        return dt.strftime("%Y-%m-%d %H:%M")
    else:
        return dt.strftime("%Y-%m-%d")


def format_date_short(dt: datetime) -> str:
    """
    Formatea fecha en formato corto (DD/MM/YYYY).

    Args:
        dt: Datetime a formatear

    Returns:
        String formateado

    Examples:
        >>> format_date_short(datetime(2024, 12, 13))
        "13/12/2024"
    """
    if not isinstance(dt, datetime):
        raise TypeError("dt debe ser datetime")

    return dt.strftime("%d/%m/%Y")


def format_time_only(dt: datetime) -> str:
    """
    Formatea solo la hora (HH:MM).

    Args:
        dt: Datetime a formatear

    Returns:
        String formateado

    Examples:
        >>> format_time_only(datetime(2024, 12, 13, 14, 30))
        "14:30"
    """
    if not isinstance(dt, datetime):
        raise TypeError("dt debe ser datetime")

    return dt.strftime("%H:%M")


def format_relative_time(dt: datetime, reference: Optional[datetime] = None) -> str:
    """
    Formatea tiempo relativo ("hace X", "en X").

    Args:
        dt: Datetime a formatear
        reference: Punto de referencia (default: now UTC)

    Returns:
        String formateado en lenguaje natural

    Examples:
        >>> now = datetime.now(timezone.utc)
        >>> format_relative_time(now - timedelta(minutes=5), reference=now)
        "hace 5 minutos"

        >>> format_relative_time(now + timedelta(hours=2), reference=now)
        "en 2 horas"

        >>> format_relative_time(now - timedelta(days=3), reference=now)
        "hace 3 días"
    """
    if not isinstance(dt, datetime):
        raise TypeError("dt debe ser datetime")

    if reference is None:
        reference = datetime.now(timezone.utc)

    diff = dt - reference
    seconds = diff.total_seconds()

    # Pasado
    if seconds < 0:
        seconds = abs(seconds)
        prefix = "hace"

        # Segundos
        if seconds < 60:
            s = int(seconds)
            return f"{prefix} {s} segundo{'s' if s != 1 else ''}"

        # Minutos
        minutes = seconds / 60
        if minutes < 60:
            m = int(minutes)
            return f"{prefix} {m} minuto{'s' if m != 1 else ''}"

        # Horas
        hours = minutes / 60
        if hours < 24:
            h = int(hours)
            return f"{prefix} {h} hora{'s' if h != 1 else ''}"

        # Días
        days = hours / 24
        if days < 30:
            d = int(days)
            return f"{prefix} {d} día{'s' if d != 1 else ''}"

        # Meses
        months = days / 30
        if months < 12:
            mo = int(months)
            return f"{prefix} {mo} mes{'es' if mo != 1 else ''}"

        # Años
        years = int(months / 12)
        return f"{prefix} {years} año{'s' if years != 1 else ''}"

    # Futuro
    else:
        prefix = "en"

        # Segundos
        if seconds < 60:
            s = int(seconds)
            return f"{prefix} {s} segundo{'s' if s != 1 else ''}"

        # Minutos
        minutes = seconds / 60
        if minutes < 60:
            m = int(minutes)
            return f"{prefix} {m} minuto{'s' if m != 1 else ''}"

        # Horas
        hours = minutes / 60
        if hours < 24:
            h = int(hours)
            return f"{prefix} {h} hora{'s' if h != 1 else ''}"

        # Días
        days = hours / 24
        if days < 30:
            d = int(days)
            return f"{prefix} {d} día{'s' if d != 1 else ''}"

        # Meses
        months = days / 30
        if months < 12:
            mo = int(months)
            return f"{prefix} {mo} mes{'es' if mo != 1 else ''}"

        # Años
        years = int(months / 12)
        return f"{prefix} {years} año{'s' if years != 1 else ''}"


# ===== FORMATEO DE NÚMEROS =====

def format_number(number: Union[int, float], decimals: int = 0) -> str:
    """
    Formatea número con separadores de miles.

    Args:
        number: Número a formatear
        decimals: Número de decimales (default: 0)

    Returns:
        String formateado

    Examples:
        >>> format_number(1234567)
        "1,234,567"

        >>> format_number(1234.5678, decimals=2)
        "1,234.57"
    """
    if not isinstance(number, (int, float)):
        raise TypeError("number debe ser numérico")

    if decimals < 0:
        raise ValueError("decimals debe ser >= 0")

    if decimals == 0:
        return f"{int(number):,}"
    else:
        return f"{number:,.{decimals}f}"


def format_currency(amount: float, symbol: str = "$") -> str:
    """
    Formatea cantidad como moneda.

    Args:
        amount: Cantidad a formatear
        symbol: Símbolo de moneda (default: "$")

    Returns:
        String formateado

    Examples:
        >>> format_currency(1234.56)
        "$1,234.56"

        >>> format_currency(1000, symbol="€")
        "€1,000.00"
    """
    if not isinstance(amount, (int, float)):
        raise TypeError("amount debe ser numérico")

    return f"{symbol}{amount:,.2f}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Formatea porcentaje.

    Args:
        value: Valor a formatear (0-100)
        decimals: Número de decimales (default: 1)

    Returns:
        String formateado

    Examples:
        >>> format_percentage(85.5)
        "85.5%"

        >>> format_percentage(100, decimals=0)
        "100%"
    """
    if not isinstance(value, (int, float)):
        raise TypeError("value debe ser numérico")

    return f"{value:.{decimals}f}%"


# ===== FORMATEO DE DURACIONES =====

def format_duration_minutes(minutes: Union[int, float]) -> str:
    """
    Formatea duración en minutos a formato legible.

    Args:
        minutes: Minutos a formatear

    Returns:
        String formateado

    Examples:
        >>> format_duration_minutes(5)
        "5 minutos"

        >>> format_duration_minutes(65)
        "1 hora, 5 minutos"

        >>> format_duration_minutes(1440)
        "1 día"
    """
    if not isinstance(minutes, (int, float)):
        raise TypeError("minutes debe ser numérico")

    minutes = int(minutes)

    if minutes < 60:
        return f"{minutes} minuto{'s' if minutes != 1 else ''}"

    hours = minutes // 60
    remaining_minutes = minutes % 60

    if hours < 24:
        if remaining_minutes == 0:
            return f"{hours} hora{'s' if hours != 1 else ''}"
        else:
            return (
                f"{hours} hora{'s' if hours != 1 else ''}, "
                f"{remaining_minutes} minuto{'s' if remaining_minutes != 1 else ''}"
            )

    days = hours // 24
    remaining_hours = hours % 24

    if remaining_hours == 0:
        return f"{days} día{'s' if days != 1 else ''}"
    else:
        return (
            f"{days} día{'s' if days != 1 else ''}, "
            f"{remaining_hours} hora{'s' if remaining_hours != 1 else ''}"
        )


def format_seconds_to_time(seconds: Union[int, float]) -> str:
    """
    Formatea segundos a formato HH:MM:SS.

    Args:
        seconds: Segundos a formatear

    Returns:
        String formateado

    Examples:
        >>> format_seconds_to_time(3665)
        "01:01:05"

        >>> format_seconds_to_time(125)
        "00:02:05"
    """
    if not isinstance(seconds, (int, float)):
        raise TypeError("seconds debe ser numérico")

    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


# ===== FORMATEO DE IDs Y CÓDIGOS =====

def format_user_id(user_id: int, as_code: bool = True) -> str:
    """
    Formatea user ID para Telegram.

    Args:
        user_id: ID del usuario
        as_code: Si envolverlo en <code> tags (default: True)

    Returns:
        String formateado

    Examples:
        >>> format_user_id(123456789)
        "<code>123456789</code>"

        >>> format_user_id(123456789, as_code=False)
        "123456789"
    """
    if not isinstance(user_id, int):
        raise TypeError("user_id debe ser int")

    if as_code:
        return f"<code>{user_id}</code>"
    else:
        return str(user_id)


def format_token(token: str, as_code: bool = True) -> str:
    """
    Formatea token de invitación.

    Args:
        token: Token a formatear
        as_code: Si envolverlo en <code> tags (default: True)

    Returns:
        String formateado

    Examples:
        >>> format_token("ABC123DEF456")
        "<code>ABC123DEF456</code>"
    """
    if not isinstance(token, str):
        raise TypeError("token debe ser str")

    if as_code:
        return f"<code>{token}</code>"
    else:
        return token


# ===== FORMATEO DE LISTAS =====

def format_list_items(
    items: list,
    max_display: int = 5,
    truncate_message: str = "..."
) -> str:
    """
    Formatea lista de items para display, truncando si es muy larga.

    Args:
        items: Lista de items (cualquier tipo con __str__)
        max_display: Máximo de items a mostrar (default: 5)
        truncate_message: Mensaje cuando se trunca (default: "...")

    Returns:
        String formateado

    Examples:
        >>> format_list_items(["a", "b", "c"])
        "a, b, c"

        >>> format_list_items([1, 2, 3, 4, 5, 6], max_display=3)
        "1, 2, 3, ..."
    """
    if not isinstance(items, list):
        raise TypeError("items debe ser lista")

    if max_display < 1:
        raise ValueError("max_display debe ser >= 1")

    if len(items) <= max_display:
        return ", ".join(str(item) for item in items)
    else:
        displayed = items[:max_display]
        return ", ".join(str(item) for item in displayed) + f", {truncate_message}"


# ===== HELPERS DE EMOJIS =====

def status_emoji(status: str) -> str:
    """
    Retorna emoji apropiado para un status.

    Args:
        status: Status a representar

    Returns:
        Emoji string

    Examples:
        >>> status_emoji("active")
        "🟢"

        >>> status_emoji("expired")
        "⚪"

        >>> status_emoji("pending")
        "🟡"
    """
    if not isinstance(status, str):
        raise TypeError("status debe ser str")

    emoji_map = {
        "active": "🟢",
        "inactive": "⚪",
        "expired": "⚪",
        "pending": "🟡",
        "processing": "🔄",
        "completed": "✅",
        "failed": "❌",
        "warning": "⚠️",
        "healthy": "🟢",
        "degraded": "🟡",
        "down": "🔴",
    }

    return emoji_map.get(status.lower(), "⚪")


def days_remaining_emoji(days: int) -> str:
    """
    Retorna emoji según días restantes.

    Args:
        days: Días restantes

    Returns:
        Emoji string

    Examples:
        >>> days_remaining_emoji(45)
        "🟢"

        >>> days_remaining_emoji(10)
        "🟡"

        >>> days_remaining_emoji(2)
        "🔴"
    """
    if not isinstance(days, int):
        raise TypeError("days debe ser int")

    if days > 30:
        return "🟢"
    elif days > 7:
        return "🟡"
    else:
        return "🔴"


# ===== HELPERS DE TEXTO =====

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Trunca texto si excede longitud máxima.

    Args:
        text: Texto a truncar
        max_length: Longitud máxima (default: 100)
        suffix: Sufijo al truncar (default: "...")

    Returns:
        Texto truncado

    Examples:
        >>> truncate_text("Este es un texto muy largo", max_length=10)
        "Este es..."

        >>> truncate_text("Corto", max_length=10)
        "Corto"
    """
    if not isinstance(text, str):
        raise TypeError("text debe ser str")

    if not isinstance(max_length, int) or max_length < 1:
        raise ValueError("max_length debe ser int >= 1")

    if max_length <= len(suffix):
        raise ValueError("max_length debe ser mayor que len(suffix)")

    if len(text) <= max_length:
        return text
    else:
        return text[: max_length - len(suffix)] + suffix


def escape_html(text: str) -> str:
    """
    Escapa caracteres HTML para Telegram.

    Args:
        text: Texto a escapar

    Returns:
        Texto escapado

    Examples:
        >>> escape_html("<script>alert('xss')</script>")
        "&lt;script&gt;alert('xss')&lt;/script&gt;"
    """
    if not isinstance(text, str):
        raise TypeError("text debe ser str")

    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def pluralize(count: int, singular: str, plural: str) -> str:
    """
    Retorna forma singular o plural según conteo.

    Args:
        count: Cantidad
        singular: Forma singular
        plural: Forma plural

    Returns:
        Forma apropiada

    Examples:
        >>> pluralize(1, "día", "días")
        "día"

        >>> pluralize(5, "día", "días")
        "días"
    """
    if not isinstance(count, int):
        raise TypeError("count debe ser int")

    if not isinstance(singular, str) or not isinstance(plural, str):
        raise TypeError("singular y plural deben ser str")

    return singular if count == 1 else plural


# ===== BARRA DE PROGRESO =====

def format_progress_bar(
    current: int,
    total: int,
    filled: str = "█",
    empty: str = "░",
    length: int = 10
) -> str:
    """
    Genera barra de progreso visual.

    Args:
        current: Valor actual
        total: Valor total
        filled: Carácter para parte llena (default: █)
        empty: Carácter para parte vacía (default: ░)
        length: Longitud de la barra (default: 10)

    Returns:
        String con barra de progreso

    Examples:
        >>> format_progress_bar(4, 10)
        "████░░░░░░"

        >>> format_progress_bar(75, 100, length=20)
        "███████████░░░░░░░░░░"
    """
    if not isinstance(current, int) or not isinstance(total, int):
        raise TypeError("current y total deben ser int")

    if total <= 0:
        raise ValueError("total debe ser > 0")

    if current < 0:
        current = 0
    elif current > total:
        current = total

    percent = (current / total) * 100
    filled_length = int((current / total) * length)
    empty_length = length - filled_length

    bar = filled * filled_length + empty * empty_length

    return bar


def format_progress_with_percentage(
    current: int,
    total: int,
    show_numbers: bool = True,
    length: int = 10
) -> str:
    """
    Genera barra de progreso con porcentaje.

    Args:
        current: Valor actual
        total: Valor total
        show_numbers: Si mostrar números (default: True)
        length: Longitud de la barra (default: 10)

    Returns:
        String con barra + porcentaje

    Examples:
        >>> format_progress_with_percentage(4, 10)
        "████░░░░░░ 40%"

        >>> format_progress_with_percentage(4, 10, show_numbers=False)
        "████░░░░░░"
    """
    bar = format_progress_bar(current, total, length=length)

    if show_numbers:
        percent = int((current / total) * 100)
        return f"{bar} {percent}%"
    else:
        return bar


def format_progress_with_time(
    minutes_remaining: int,
    total_minutes: int,
    length: int = 10
) -> str:
    """
    Genera barra de progreso con tiempo restante.

    Args:
        minutes_remaining: Minutos restantes
        total_minutes: Minutos totales
        length: Longitud de la barra (default: 10)

    Returns:
        String con barra + tiempo

    Examples:
        >>> format_progress_with_time(5, 30)
        "░░░░███████░░░ 5 min restantes"
    """
    if minutes_remaining < 0:
        minutes_remaining = 0
    if minutes_remaining > total_minutes:
        minutes_remaining = total_minutes

    progress = total_minutes - minutes_remaining
    bar = format_progress_bar(progress, total_minutes, length=length)

    return f"{bar} {minutes_remaining} min restantes"


# ===== HELPERS DE VALIDACIÓN =====

def is_valid_emoji(text: str) -> bool:
    """
    Verifica si un string es un emoji válido.

    Args:
        text: String a verificar

    Returns:
        True si es emoji válido

    Examples:
        >>> is_valid_emoji("👍")
        True

        >>> is_valid_emoji("abc")
        False
    """
    if not isinstance(text, str):
        raise TypeError("text debe ser str")

    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F700-\U0001F77F"
        "\U0001F780-\U0001F7FF"
        "\U0001F800-\U0001F8FF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FA6F"
        "\U0001FA70-\U0001FAFF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE,
    )

    return bool(emoji_pattern.fullmatch(text.strip()))
