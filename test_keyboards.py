"""
Tests para el keyboard factory (bot/utils/keyboards.py).
"""
from bot.utils.keyboards import (
    create_inline_keyboard,
    admin_main_menu_keyboard,
    back_to_main_menu_keyboard,
    yes_no_keyboard
)


def test_create_inline_keyboard():
    """Test la función base create_inline_keyboard"""
    print("\n" + "=" * 60)
    print("TEST: create_inline_keyboard")
    print("=" * 60)

    print("\n🧪 Test 1: Single button")
    keyboard = create_inline_keyboard([
        [{"text": "Botón 1", "callback_data": "btn1"}]
    ])
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) == 1
    assert len(keyboard.inline_keyboard[0]) == 1
    assert keyboard.inline_keyboard[0][0].text == "Botón 1"
    assert keyboard.inline_keyboard[0][0].callback_data == "btn1"
    print("✅ Single button OK")

    print("\n🧪 Test 2: Multiple rows and columns")
    keyboard = create_inline_keyboard([
        [{"text": "Botón 1", "callback_data": "btn1"}],
        [
            {"text": "Botón 2", "callback_data": "btn2"},
            {"text": "Botón 3", "callback_data": "btn3"}
        ],
        [
            {"text": "Botón 4", "callback_data": "btn4"},
            {"text": "Botón 5", "callback_data": "btn5"},
            {"text": "Botón 6", "callback_data": "btn6"}
        ]
    ])
    assert len(keyboard.inline_keyboard) == 3
    assert len(keyboard.inline_keyboard[0]) == 1
    assert len(keyboard.inline_keyboard[1]) == 2
    assert len(keyboard.inline_keyboard[2]) == 3
    print("✅ Multiple rows and columns OK")


def test_admin_main_menu_keyboard():
    """Test la función admin_main_menu_keyboard"""
    print("\n" + "=" * 60)
    print("TEST: admin_main_menu_keyboard")
    print("=" * 60)

    print("\n🧪 Test 1: Estructura del menú principal")
    menu = admin_main_menu_keyboard()

    assert menu is not None
    assert len(menu.inline_keyboard) == 3  # VIP, Free, Config
    assert len(menu.inline_keyboard[0]) == 1  # VIP row
    assert len(menu.inline_keyboard[1]) == 1  # Free row
    assert len(menu.inline_keyboard[2]) == 1  # Config row
    print("✅ Estructura OK (3 filas, 1 botón cada una)")

    print("\n🧪 Test 2: Textos y callbacks")
    assert menu.inline_keyboard[0][0].text == "📺 Gestión Canal VIP"
    assert menu.inline_keyboard[0][0].callback_data == "admin:vip"
    print(f"   VIP: {menu.inline_keyboard[0][0].text} → {menu.inline_keyboard[0][0].callback_data}")

    assert menu.inline_keyboard[1][0].text == "📺 Gestión Canal Free"
    assert menu.inline_keyboard[1][0].callback_data == "admin:free"
    print(f"   Free: {menu.inline_keyboard[1][0].text} → {menu.inline_keyboard[1][0].callback_data}")

    assert menu.inline_keyboard[2][0].text == "⚙️ Configuración"
    assert menu.inline_keyboard[2][0].callback_data == "admin:config"
    print(f"   Config: {menu.inline_keyboard[2][0].text} → {menu.inline_keyboard[2][0].callback_data}")

    print("✅ Textos y callbacks OK")


def test_back_to_main_menu_keyboard():
    """Test la función back_to_main_menu_keyboard"""
    print("\n" + "=" * 60)
    print("TEST: back_to_main_menu_keyboard")
    print("=" * 60)

    print("\n🧪 Test 1: Estructura del botón volver")
    back_menu = back_to_main_menu_keyboard()

    assert back_menu is not None
    assert len(back_menu.inline_keyboard) == 1
    assert len(back_menu.inline_keyboard[0]) == 1
    print("✅ Estructura OK (1 fila, 1 botón)")

    print("\n🧪 Test 2: Texto y callback")
    assert "Volver" in back_menu.inline_keyboard[0][0].text
    assert back_menu.inline_keyboard[0][0].callback_data == "admin:main"
    print(f"   Botón: {back_menu.inline_keyboard[0][0].text} → {back_menu.inline_keyboard[0][0].callback_data}")

    print("✅ Texto y callback OK")


def test_yes_no_keyboard():
    """Test la función yes_no_keyboard"""
    print("\n" + "=" * 60)
    print("TEST: yes_no_keyboard")
    print("=" * 60)

    print("\n🧪 Test 1: Estructura básica")
    yn = yes_no_keyboard("callback_yes", "callback_no")

    assert yn is not None
    assert len(yn.inline_keyboard) == 1  # 1 fila
    assert len(yn.inline_keyboard[0]) == 2  # 2 botones (Sí y No)
    print("✅ Estructura OK (1 fila, 2 botones)")

    print("\n🧪 Test 2: Textos y callbacks")
    assert yn.inline_keyboard[0][0].text == "✅ Sí"
    assert yn.inline_keyboard[0][0].callback_data == "callback_yes"
    print(f"   Sí: {yn.inline_keyboard[0][0].text} → {yn.inline_keyboard[0][0].callback_data}")

    assert yn.inline_keyboard[0][1].text == "❌ No"
    assert yn.inline_keyboard[0][1].callback_data == "callback_no"
    print(f"   No: {yn.inline_keyboard[0][1].text} → {yn.inline_keyboard[0][1].callback_data}")

    print("✅ Textos y callbacks OK")

    print("\n🧪 Test 3: Callbacks personalizados")
    yn2 = yes_no_keyboard("confirm:delete", "cancel:delete")
    assert yn2.inline_keyboard[0][0].callback_data == "confirm:delete"
    assert yn2.inline_keyboard[0][1].callback_data == "cancel:delete"
    print("✅ Callbacks personalizados OK")


def run_all_tests():
    """Ejecuta todos los tests"""
    print("\n" + "=" * 60)
    print("EJECUTANDO TESTS - KEYBOARD FACTORY")
    print("=" * 60)

    try:
        test_create_inline_keyboard()
        test_admin_main_menu_keyboard()
        test_back_to_main_menu_keyboard()
        test_yes_no_keyboard()

        print("\n" + "=" * 60)
        print("✅✅✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
        print("=" * 60)
        print("\nResumen:")
        print("- ✅ create_inline_keyboard (función base)")
        print("- ✅ admin_main_menu_keyboard (3 opciones)")
        print("- ✅ back_to_main_menu_keyboard (1 botón volver)")
        print("- ✅ yes_no_keyboard (confirmación Sí/No)")
        print("\n")

    except AssertionError as e:
        print(f"\n❌ TEST FALLIDO: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
