"""
Test de generación de keyboard de reacciones.
"""
import asyncio
from bot.utils.keyboards import create_reaction_keyboard

def test_reaction_keyboard():
    print("Test de generación de keyboard de reacciones\n")
    
    # Test 1: Keyboard sin contadores
    print("Test 1: Keyboard sin contadores...")
    reactions = [
        (1, "❤", "Me encanta"),
        (2, "👍", "Me gusta"),
        (3, "🔥", "Genial")
    ]
    
    keyboard = create_reaction_keyboard(
        reactions=reactions,
        channel_id=-1001234567890,
        message_id=12345,
        counts=None
    )
    
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) == 1  # 3 botones = 1 fila
    assert len(keyboard.inline_keyboard[0]) == 3  # 3 botones en fila
    
    # Verificar texto de botones (sin contador)
    for i, button in enumerate(keyboard.inline_keyboard[0]):
        assert button.text == reactions[i][1]  # Solo emoji
        print(f"  Boton {i+1}: {button.text}")
    
    print("  Keyboard generado correctamente\n")
    
    # Test 2: Keyboard con contadores
    print("Test 2: Keyboard con contadores...")
    counts = {"❤": 10, "👍": 5, "🔥": 3}
    
    keyboard_with_counts = create_reaction_keyboard(
        reactions=reactions,
        channel_id=-1001234567890,
        message_id=12345,
        counts=counts
    )
    
    # Verificar texto de botones (con contador)
    for i, button in enumerate(keyboard_with_counts.inline_keyboard[0]):
        emoji = reactions[i][1]
        expected_text = f"{emoji} {counts[emoji]}"
        assert button.text == expected_text
        print(f"  Boton {i+1}: {button.text}")
    
    print("  Contadores funcionan\n")
    
    # Test 3: Keyboard con 5 reacciones (2 filas)
    print("Test 3: Keyboard con 5 reacciones (2 filas)...")
    reactions_5 = reactions + [
        (4, "😍", "Amor"),
        (5, "�슃", "Perfecto")
    ]
    
    keyboard_5 = create_reaction_keyboard(
        reactions=reactions_5,
        channel_id=-1001234567890,
        message_id=12345,
        counts=None
    )
    
    assert len(keyboard_5.inline_keyboard) == 2  # 2 filas
    assert len(keyboard_5.inline_keyboard[0]) == 3  # Primera fila: 3 botones
    assert len(keyboard_5.inline_keyboard[1]) == 2  # Segunda fila: 2 botones
    print("  Agrupacion correcta (3 + 2)\n")
    
    # Test 4: Verificar formato de callback_data
    print("Test 4: Verificar formato de callback_data...")
    button = keyboard.inline_keyboard[0][0]
    expected_callback = "react:❤:-1001234567890:12345"
    assert button.callback_data == expected_callback
    print(f"  Callback data: {button.callback_data}\n")
    
    print("Todos los tests pasaron!")

test_reaction_keyboard()
