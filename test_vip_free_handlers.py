"""
Tests básicos para handlers VIP y Free.

Tests limitados sin bot corriendo. Tests completos requieren bot en ejecución.
"""
import asyncio
from bot.handlers.admin import vip, free
from bot.utils.keyboards import create_inline_keyboard


def test_keyboards():
    """Test que los keyboards se crean correctamente"""
    print("\n" + "=" * 60)
    print("TEST: Keyboards VIP y Free")
    print("=" * 60)

    print("\n🧪 Test 1: vip_menu_keyboard - No configurado")
    keyboard = vip.vip_menu_keyboard(is_configured=False)
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) >= 2  # Setup + Volver
    print(f"✅ VIP keyboard (no config): {len(keyboard.inline_keyboard)} filas")

    print("\n🧪 Test 2: vip_menu_keyboard - Configurado")
    keyboard = vip.vip_menu_keyboard(is_configured=True)
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) >= 3  # Token + Reconfig + Volver
    assert "🎟️" in keyboard.inline_keyboard[0][0].text
    print(f"✅ VIP keyboard (configurado): {len(keyboard.inline_keyboard)} filas")
    print(f"   Botones: {[btn[0].text for btn in keyboard.inline_keyboard]}")

    print("\n🧪 Test 3: free_menu_keyboard - No configurado")
    keyboard = free.free_menu_keyboard(is_configured=False)
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) >= 2  # Setup + Volver
    print(f"✅ Free keyboard (no config): {len(keyboard.inline_keyboard)} filas")

    print("\n🧪 Test 4: free_menu_keyboard - Configurado")
    keyboard = free.free_menu_keyboard(is_configured=True)
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) >= 3  # WaitTime + Reconfig + Volver
    assert "⏱️" in keyboard.inline_keyboard[0][0].text
    print(f"✅ Free keyboard (configurado): {len(keyboard.inline_keyboard)} filas")
    print(f"   Botones: {[btn[0].text for btn in keyboard.inline_keyboard]}")


def test_imports():
    """Test que los imports funcionan correctamente"""
    print("\n" + "=" * 60)
    print("TEST: Imports")
    print("=" * 60)

    print("\n🧪 Test 1: Importar handlers VIP")
    assert hasattr(vip, 'callback_vip_menu')
    assert hasattr(vip, 'callback_vip_setup')
    assert hasattr(vip, 'process_vip_channel_forward')
    assert hasattr(vip, 'callback_generate_vip_token')
    assert hasattr(vip, 'vip_menu_keyboard')
    assert hasattr(vip, 'admin_router')
    print("✅ VIP handlers importados OK")

    print("\n🧪 Test 2: Importar handlers Free")
    assert hasattr(free, 'callback_free_menu')
    assert hasattr(free, 'callback_free_setup')
    assert hasattr(free, 'process_free_channel_forward')
    assert hasattr(free, 'callback_set_wait_time')
    assert hasattr(free, 'process_wait_time_input')
    assert hasattr(free, 'free_menu_keyboard')
    assert hasattr(free, 'admin_router')
    print("✅ Free handlers importados OK")

    print("\n🧪 Test 3: Verificar que admin_router es el mismo")
    assert vip.admin_router is free.admin_router, "admin_router debe ser el mismo en ambos"
    print("✅ admin_router es compartido correctamente")


def test_callback_data():
    """Test que los callback_data son correctos"""
    print("\n" + "=" * 60)
    print("TEST: Callback Data")
    print("=" * 60)

    print("\n🧪 Test 1: VIP callbacks")
    vip_keyboard = vip.vip_menu_keyboard(is_configured=True)
    callbacks = []
    for row in vip_keyboard.inline_keyboard:
        for btn in row:
            callbacks.append(btn.callback_data)

    assert "vip:generate_token" in callbacks
    assert "vip:setup" in callbacks or "vip:reconfigurar" in str(callbacks).lower()
    assert "admin:main" in callbacks
    print(f"✅ VIP callbacks: {callbacks}")

    print("\n🧪 Test 2: Free callbacks")
    free_keyboard = free.free_menu_keyboard(is_configured=True)
    callbacks = []
    for row in free_keyboard.inline_keyboard:
        for btn in row:
            callbacks.append(btn.callback_data)

    assert "free:set_wait_time" in callbacks
    assert "free:setup" in callbacks or "free:reconfigurar" in str(callbacks).lower()
    assert "admin:main" in callbacks
    print(f"✅ Free callbacks: {callbacks}")


def test_states_imported():
    """Test que los estados FSM se importan correctamente"""
    print("\n" + "=" * 60)
    print("TEST: FSM States")
    print("=" * 60)

    print("\n🧪 Test 1: Verificar que ChannelSetupStates está disponible")
    from bot.states.admin import ChannelSetupStates, WaitTimeSetupStates
    assert ChannelSetupStates is not None
    assert WaitTimeSetupStates is not None
    print("✅ States importados OK")

    print("\n🧪 Test 2: Estados VIP y Free disponibles")
    assert hasattr(ChannelSetupStates, 'waiting_for_vip_channel')
    assert hasattr(ChannelSetupStates, 'waiting_for_free_channel')
    print("✅ ChannelSetupStates tiene estados VIP y Free")

    assert hasattr(WaitTimeSetupStates, 'waiting_for_minutes')
    print("✅ WaitTimeSetupStates tiene estado waiting_for_minutes")


def run_all_tests():
    """Ejecuta todos los tests"""
    print("\n" + "=" * 60)
    print("EJECUTANDO TESTS - VIP Y FREE HANDLERS")
    print("=" * 60)

    try:
        test_keyboards()
        test_imports()
        test_callback_data()
        test_states_imported()

        print("\n" + "=" * 60)
        print("✅✅✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
        print("=" * 60)
        print("\nResumen:")
        print("- ✅ Keyboards VIP y Free crean correctamente")
        print("- ✅ Handlers importables (VIP y Free)")
        print("- ✅ admin_router compartido correctamente")
        print("- ✅ Callback data correctos")
        print("- ✅ FSM States importables")
        print("\nNota: Tests funcionales requieren bot ejecutándose")
        print("\n")

    except AssertionError as e:
        print(f"\n❌ TEST FALLIDO: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    run_all_tests()
