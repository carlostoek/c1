"""
Tests para bot/utils/formatters.py

Validación de todas las funciones de formateo.
"""
from datetime import datetime, timedelta, timezone

from bot.utils.formatters import (
    format_datetime,
    format_date_short,
    format_time_only,
    format_relative_time,
    format_number,
    format_currency,
    format_percentage,
    format_duration_minutes,
    format_seconds_to_time,
    format_user_id,
    format_token,
    format_list_items,
    status_emoji,
    days_remaining_emoji,
    truncate_text,
    escape_html,
    pluralize,
    is_valid_emoji,
)


def test_format_datetime():
    """Test formateo de datetime."""
    print("\n🧪 Test 1: format_datetime")

    dt = datetime(2024, 12, 13, 14, 30, 45)

    # Con hora
    result = format_datetime(dt)
    assert result == "2024-12-13 14:30"
    print(f"✅ Con hora: {result}")

    # Sin hora
    result = format_datetime(dt, include_time=False)
    assert result == "2024-12-13"
    print(f"✅ Sin hora: {result}")


def test_format_date_short():
    """Test formateo de fecha corta."""
    print("\n🧪 Test 2: format_date_short")

    dt = datetime(2024, 12, 13)

    result = format_date_short(dt)
    assert result == "13/12/2024"
    print(f"✅ Fecha corta: {result}")


def test_format_time_only():
    """Test formateo de hora."""
    print("\n🧪 Test 3: format_time_only")

    dt = datetime(2024, 12, 13, 14, 30)

    result = format_time_only(dt)
    assert result == "14:30"
    print(f"✅ Hora: {result}")


def test_format_relative_time():
    """Test formateo de tiempo relativo."""
    print("\n🧪 Test 4: format_relative_time")

    now = datetime.now(timezone.utc)

    # Pasado - minutos
    past = now - timedelta(minutes=5)
    result = format_relative_time(past, reference=now)
    assert result == "hace 5 minutos"
    print(f"✅ Pasado (5 min): {result}")

    # Futuro - horas
    future = now + timedelta(hours=2)
    result = format_relative_time(future, reference=now)
    assert result == "en 2 horas"
    print(f"✅ Futuro (2 hrs): {result}")

    # Días
    past_days = now - timedelta(days=3)
    result = format_relative_time(past_days, reference=now)
    assert result == "hace 3 días"
    print(f"✅ Pasado (3 días): {result}")

    # Un día
    past_one_day = now - timedelta(days=1)
    result = format_relative_time(past_one_day, reference=now)
    assert result == "hace 1 día"
    print(f"✅ Pasado (1 día): {result}")

    # Un minuto
    past_one_min = now - timedelta(minutes=1)
    result = format_relative_time(past_one_min, reference=now)
    assert result == "hace 1 minuto"
    print(f"✅ Pasado (1 min): {result}")


def test_format_number():
    """Test formateo de números."""
    print("\n🧪 Test 5: format_number")

    # Sin decimales
    result = format_number(1234567)
    assert result == "1,234,567"
    print(f"✅ Sin decimales: {result}")

    # Con decimales
    result = format_number(1234.5678, decimals=2)
    assert result == "1,234.57"
    print(f"✅ Con 2 decimales: {result}")

    # Pequeño número
    result = format_number(99)
    assert result == "99"
    print(f"✅ Pequeño número: {result}")


def test_format_currency():
    """Test formateo de moneda."""
    print("\n🧪 Test 6: format_currency")

    result = format_currency(1234.56)
    assert result == "$1,234.56"
    print(f"✅ USD: {result}")

    result = format_currency(1000, symbol="€")
    assert result == "€1,000.00"
    print(f"✅ EUR: {result}")

    result = format_currency(0.99)
    assert result == "$0.99"
    print(f"✅ Céntavos: {result}")


def test_format_percentage():
    """Test formateo de porcentaje."""
    print("\n🧪 Test 7: format_percentage")

    result = format_percentage(85.5)
    assert result == "85.5%"
    print(f"✅ 1 decimal: {result}")

    result = format_percentage(100, decimals=0)
    assert result == "100%"
    print(f"✅ Sin decimales: {result}")

    result = format_percentage(33.3333, decimals=2)
    assert result == "33.33%"
    print(f"✅ 2 decimales: {result}")


def test_format_duration_minutes():
    """Test formateo de duración."""
    print("\n🧪 Test 8: format_duration_minutes")

    result = format_duration_minutes(5)
    assert result == "5 minutos"
    print(f"✅ 5 min: {result}")

    result = format_duration_minutes(1)
    assert result == "1 minuto"
    print(f"✅ 1 min: {result}")

    result = format_duration_minutes(65)
    assert result == "1 hora, 5 minutos"
    print(f"✅ 65 min: {result}")

    result = format_duration_minutes(60)
    assert result == "1 hora"
    print(f"✅ 60 min: {result}")

    result = format_duration_minutes(1440)
    assert result == "1 día"
    print(f"✅ 1440 min: {result}")

    result = format_duration_minutes(1500)
    assert result == "1 día, 1 hora"
    print(f"✅ 1500 min: {result}")


def test_format_seconds_to_time():
    """Test formateo de segundos a HH:MM:SS."""
    print("\n🧪 Test 9: format_seconds_to_time")

    result = format_seconds_to_time(3665)
    assert result == "01:01:05"
    print(f"✅ 3665 seg: {result}")

    result = format_seconds_to_time(125)
    assert result == "00:02:05"
    print(f"✅ 125 seg: {result}")

    result = format_seconds_to_time(0)
    assert result == "00:00:00"
    print(f"✅ 0 seg: {result}")


def test_format_user_id():
    """Test formateo de user ID."""
    print("\n🧪 Test 10: format_user_id")

    result = format_user_id(123456789)
    assert result == "<code>123456789</code>"
    print(f"✅ Con <code>: {result}")

    result = format_user_id(123456789, as_code=False)
    assert result == "123456789"
    print(f"✅ Sin <code>: {result}")


def test_format_token():
    """Test formateo de token."""
    print("\n🧪 Test 11: format_token")

    result = format_token("ABC123DEF456")
    assert result == "<code>ABC123DEF456</code>"
    print(f"✅ Con <code>: {result}")

    result = format_token("TOKEN", as_code=False)
    assert result == "TOKEN"
    print(f"✅ Sin <code>: {result}")


def test_format_list_items():
    """Test formateo de lista."""
    print("\n🧪 Test 12: format_list_items")

    result = format_list_items(["a", "b", "c"])
    assert result == "a, b, c"
    print(f"✅ Lista corta: {result}")

    result = format_list_items([1, 2, 3, 4, 5, 6], max_display=3)
    assert result == "1, 2, 3, ..."
    print(f"✅ Lista truncada: {result}")


def test_status_emoji():
    """Test emojis de estado."""
    print("\n🧪 Test 13: status_emoji")

    assert status_emoji("active") == "🟢"
    assert status_emoji("expired") == "⚪"
    assert status_emoji("pending") == "🟡"
    assert status_emoji("healthy") == "🟢"
    assert status_emoji("degraded") == "🟡"
    assert status_emoji("down") == "🔴"
    assert status_emoji("completed") == "✅"
    assert status_emoji("failed") == "❌"
    print("✅ Emojis de estado correctos")


def test_days_remaining_emoji():
    """Test emojis por días."""
    print("\n🧪 Test 14: days_remaining_emoji")

    assert days_remaining_emoji(45) == "🟢"
    print("✅ >30 días: 🟢")

    assert days_remaining_emoji(10) == "🟡"
    print("✅ >7 días: 🟡")

    assert days_remaining_emoji(2) == "🔴"
    print("✅ <=7 días: 🔴")


def test_truncate_text():
    """Test truncado de texto."""
    print("\n🧪 Test 15: truncate_text")

    long_text = "Este es un texto muy largo que debe ser truncado"
    result = truncate_text(long_text, max_length=20)

    assert len(result) == 20
    assert result.endswith("...")
    print(f"✅ Truncado: {result}")

    short_text = "Corto"
    result = truncate_text(short_text, max_length=20)
    assert result == "Corto"
    print(f"✅ No truncado: {result}")


def test_escape_html():
    """Test escape de HTML."""
    print("\n🧪 Test 16: escape_html")

    result = escape_html("<script>alert('xss')</script>")
    assert result == "&lt;script&gt;alert('xss')&lt;/script&gt;"
    print(f"✅ Script escapado: {result}")

    result = escape_html("Texto & normal")
    assert result == "Texto &amp; normal"
    print(f"✅ Ampersand escapado: {result}")


def test_pluralize():
    """Test pluralización."""
    print("\n🧪 Test 17: pluralize")

    assert pluralize(1, "día", "días") == "día"
    print("✅ Singular: día")

    assert pluralize(5, "día", "días") == "días"
    print("✅ Plural: días")

    assert pluralize(0, "item", "items") == "items"
    print("✅ Cero plural: items")


def test_is_valid_emoji():
    """Test validación de emojis."""
    print("\n🧪 Test 18: is_valid_emoji")

    assert is_valid_emoji("👍") is True
    print("✅ Emoji válido: 👍")

    assert is_valid_emoji("❌") is True
    print("✅ Emoji válido: ❌")

    assert is_valid_emoji("abc") is False
    print("✅ Texto NO es emoji: abc")

    assert is_valid_emoji("a") is False
    print("✅ Carácter NO es emoji: a")


if __name__ == "__main__":
    test_format_datetime()
    test_format_date_short()
    test_format_time_only()
    test_format_relative_time()
    test_format_number()
    test_format_currency()
    test_format_percentage()
    test_format_duration_minutes()
    test_format_seconds_to_time()
    test_format_user_id()
    test_format_token()
    test_format_list_items()
    test_status_emoji()
    test_days_remaining_emoji()
    test_truncate_text()
    test_escape_html()
    test_pluralize()
    test_is_valid_emoji()

    print("\n" + "=" * 60)
    print("✅✅✅ TODOS LOS TESTS PASARON ✅✅✅")
    print("=" * 60)
