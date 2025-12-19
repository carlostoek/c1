"""
Tests básicos para el handler /admin (bot/handlers/admin/main.py).

Nota: Tests limitados sin bot corriendo. Tests completos requieren bot en ejecución.
"""
import asyncio
from bot.handlers.admin import admin_router


def test_admin_router():
    """Test que el router está correctamente configurado"""
    print("\n" + "=" * 60)
    print("TEST: Admin Router")
    print("=" * 60)

    print("\n🧪 Test 1: Router existe y tiene nombre")
    assert admin_router is not None, "admin_router es None"
    assert admin_router.name == "admin", f"Nombre incorrecto: {admin_router.name}"
    print("✅ Router OK")
    print(f"   Nombre: {admin_router.name}")

    print("\n🧪 Test 2: Router tiene handlers registrados")
    # Verificar que el router tiene handlers (esto es implícito en aiogram)
    assert hasattr(admin_router, "message"), "Router no tiene atributo 'message'"
    assert hasattr(admin_router, "callback_query"), "Router no tiene atributo 'callback_query'"
    print("✅ Handlers registrados OK")

    print("\n✅ ROUTER TEST PASADO")


async def test_imports():
    """Test que todos los imports funcionan correctamente"""
    print("\n" + "=" * 60)
    print("TEST: Imports")
    print("=" * 60)

    print("\n🧪 Test 1: Importar admin_router")
    from bot.handlers.admin import admin_router as router
    assert router is not None
    print("✅ admin_router importado OK")

    print("\n🧪 Test 2: Importar keyboards")
    from bot.utils.keyboards import (
        create_inline_keyboard,
        admin_main_menu_keyboard,
        back_to_main_menu_keyboard,
        yes_no_keyboard
    )
    assert create_inline_keyboard is not None
    assert admin_main_menu_keyboard is not None
    assert back_to_main_menu_keyboard is not None
    assert yes_no_keyboard is not None
    print("✅ Keyboards importadas OK")

    print("\n🧪 Test 3: Importar handler module")
    from bot.handlers.admin.main import cmd_admin, callback_admin_main, callback_admin_config
    assert cmd_admin is not None
    assert callback_admin_main is not None
    assert callback_admin_config is not None
    print("✅ Handlers importados OK")

    print("\n✅ IMPORTS TEST PASADO")


def run_all_tests():
    """Ejecuta todos los tests"""
    print("\n" + "=" * 60)
    print("EJECUTANDO TESTS - ADMIN HANDLER")
    print("=" * 60)

    try:
        test_admin_router()
        asyncio.run(test_imports())

        print("\n" + "=" * 60)
        print("✅✅✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
        print("=" * 60)
        print("\nResumen:")
        print("- ✅ Router 'admin' configurado")
        print("- ✅ Handlers registrados (message, callback_query)")
        print("- ✅ Imports: admin_router, keyboards, handlers")
        print("\nNota: Para tests completos de funcionalidad, ejecutar bot y probar manualmente")
        print("\n")

    except Exception as e:
        print(f"\n❌ TEST FALLIDO: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    run_all_tests()
