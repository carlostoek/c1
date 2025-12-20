#!/usr/bin/env python3
"""
Tests para bot/utils/formatters.py

Prueba todas las funciones de formateo:
- Fechas y tiempos
- Números y monedas  
- Porcentajes
- Tiempos relativos
- Etc.
"""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from bot.utils.formatters import (
    # Fechas y tiempos
    format_datetime,
    format_date_short,
    format_time_only,
    format_relative_time,
    
    # Números y monedas
    format_number,
    format_currency,
    format_percentage,
    
    # Duraciones
    format_duration_minutes,
    format_seconds_to_time,
    
    # IDs y códigos
    format_user_id,
    format_token,
    
    # Listas
    format_list_items,
    
    # Emojis
    status_emoji,
    days_remaining_emoji,
    
    # Texto
    truncate_text,
    escape_html,
    pluralize,
    
    # Validación
    is_valid_emoji,
)


# ===== TESTS DE FECHAS Y TIEMPOS =====

def test_format_datetime():
    """Test de formateo de datetime"""
    dt = datetime(2024, 12, 13, 14, 30)
    
    # Con hora
    result = format_datetime(dt, include_time=True)
    assert result == "2024-12-13 14:30"
    
    # Sin hora
    result = format_datetime(dt, include_time=False)
    assert result == "2024-12-13"
    
    # Validación de tipo
    with pytest.raises(TypeError):
        format_datetime("2024-12-13")


def test_format_date_short():
    """Test de formateo de fecha corta"""
    dt = datetime(2024, 12, 13)
    result = format_date_short(dt)
    assert result == "13/12/2024"
    
    with pytest.raises(TypeError):
        format_date_short("2024-12-13")


def test_format_time_only():
    """Test de formateo de hora"""
    dt = datetime(2024, 12, 13, 14, 30)
    result = format_time_only(dt)
    assert result == "14:30"
    
    with pytest.raises(TypeError):
        format_time_only("14:30")


def test_format_relative_time():
    """Test de tiempo relativo"""
    now = datetime.now(timezone.utc)
    
    # Hace 5 minutos
    past = now - timedelta(minutes=5)
    result = format_relative_time(past, reference=now)
    assert "hace 5 minuto" in result
    
    # En 2 horas
    future = now + timedelta(hours=2)
    result = format_relative_time(future, reference=now)
    assert "en 2 hora" in result
    
    # Validación de tipo
    with pytest.raises(TypeError):
        format_relative_time("datetime")


# ===== TESTS DE NÚMEROS Y MONEDAS =====

def test_format_number():
    """Test de formateo de número"""
    assert format_number(1234567) == "1,234,567"
    assert format_number(1234.5678, decimals=2) == "1,234.57"
    assert format_number(1234, decimals=0) == "1,234"
    
    # Validaciones
    with pytest.raises(TypeError):
        format_number("1234")
    with pytest.raises(ValueError):
        format_number(1234, decimals=-1)


def test_format_currency():
    """Test de formateo de moneda"""
    assert format_currency(1234.56) == "$1,234.56"
    assert format_currency(1000, symbol="€") == "€1,000.00"
    
    with pytest.raises(TypeError):
        format_currency("1234.56")


def test_format_percentage():
    """Test de formateo de porcentaje"""
    assert format_percentage(85.5) == "85.5%"
    assert format_percentage(100, decimals=0) == "100%"
    
    with pytest.raises(TypeError):
        format_percentage("85.5")


# ===== TESTS DE DURACIONES =====

def test_format_duration_minutes():
    """Test de formateo de duración"""
    assert format_duration_minutes(5) == "5 minutos"
    assert format_duration_minutes(65) == "1 hora, 5 minutos"
    assert format_duration_minutes(1440) == "1 día"
    
    with pytest.raises(TypeError):
        format_duration_minutes("65")


def test_format_seconds_to_time():
    """Test de formateo de segundos a HH:MM:SS"""
    assert format_seconds_to_time(3665) == "01:01:05"
    assert format_seconds_to_time(125) == "00:02:05"
    
    with pytest.raises(TypeError):
        format_seconds_to_time("3665")


# ===== TESTS DE IDs Y CÓDIGOS =====

def test_format_user_id():
    """Test de formateo de user ID"""
    assert format_user_id(123456789) == "<code>123456789</code>"
    assert format_user_id(123456789, as_code=False) == "123456789"
    
    with pytest.raises(TypeError):
        format_user_id("123456789")


def test_format_token():
    """Test de formateo de token"""
    assert format_token("ABC123DEF456") == "<code>ABC123DEF456</code>"
    assert format_token("ABC123DEF456", as_code=False) == "ABC123DEF456"
    
    with pytest.raises(TypeError):
        format_token(123456)


# ===== TESTS DE LISTAS =====

def test_format_list_items():
    """Test de formateo de listas"""
    assert format_list_items(["a", "b", "c"]) == "a, b, c"
    assert format_list_items([1, 2, 3, 4, 5, 6], max_display=3) == "1, 2, 3, ..."
    
    with pytest.raises(TypeError):
        format_list_items("not a list")


# ===== TESTS DE EMOJIS =====

def test_status_emoji():
    """Test de emojis de status"""
    assert status_emoji("active") == "🟢"
    assert status_emoji("inactive") == "⚪"
    assert status_emoji("unknown") == "⚪"  # Default


def test_days_remaining_emoji():
    """Test de emoji según días restantes"""
    assert days_remaining_emoji(45) == "🟢"
    assert days_remaining_emoji(10) == "🟡"
    assert days_remaining_emoji(2) == "🔴"


# ===== TESTS DE TEXTO =====

def test_truncate_text():
    """Test de truncamiento de texto"""
    text = "Este es un texto muy largo"
    result = truncate_text(text, max_length=10)
    assert result == "Este es..."
    
    # Texto corto no se trunca
    short = "Corto"
    result = truncate_text(short, max_length=10)
    assert result == "Corto"
    
    with pytest.raises(ValueError):
        truncate_text(text, max_length=0)


def test_escape_html():
    """Test de escape de HTML"""
    html = "<script>alert('xss')</script>"
    result = escape_html(html)
    assert result == "&lt;script&gt;alert('xss')&lt;/script&gt;"


def test_pluralize():
    """Test de pluralización"""
    assert pluralize(1, "día", "días") == "día"
    assert pluralize(5, "día", "días") == "días"


# ===== TESTS DE VALIDACIÓN =====

def test_is_valid_emoji():
    """Test de validación de emoji"""
    assert is_valid_emoji("👍") == True
    assert is_valid_emoji("🏆") == True
    assert is_valid_emoji("text") == False
    assert is_valid_emoji("") == False


if __name__ == "__main__":
    # Ejecutar todos los tests
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
    
    print("✅✅✅ TODOS LOS TESTS PASARON ✅✅✅")