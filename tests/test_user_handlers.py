"""
Tests básicos para handlers de usuario.

Tests limitados sin bot corriendo. Tests completos requieren bot en ejecución.
"""
from bot.handlers.user import user_router
from bot.handlers.user import start, vip_flow, free_flow


def test_user_router():
    """Test que el router de usuario está configurado"""
    print("\n" + "=" * 60)
    print("TEST: User Router")
    print("=" * 60)

    print("\n🧪 Test 1: Router existe y tiene nombre")
    assert user_router is not None, "user_router es None"
    assert user_router.name == "user", f"Nombre incorrecto: {user_router.name}"
    print("✅ Router OK")
    print(f"   Nombre: {user_router.name}")

    print("\n🧪 Test 2: Router tiene handlers registrados")
    assert hasattr(user_router, "message"), "Router no tiene atributo 'message'"
    assert hasattr(user_router, "callback_query"), "Router no tiene atributo 'callback_query'"
    print("✅ Handlers registrados OK")


def test_start_handler():
    """Test que el handler /start existe y es accesible"""
    print("\n" + "=" * 60)
    print("TEST: Start Handler")
    print("=" * 60)

    print("\n🧪 Test 1: cmd_start existe")
    assert hasattr(start, 'cmd_start'), "Handler cmd_start no existe"
    assert callable(start.cmd_start), "cmd_start no es callable"
    print("✅ cmd_start OK")

    print("\n🧪 Test 2: user_router en start")
    assert start.user_router is not None
    assert start.user_router.name == "user"
    print("✅ user_router compartido OK")


def test_vip_flow_handlers():
    """Test que los handlers VIP existen"""
    print("\n" + "=" * 60)
    print("TEST: VIP Flow Handlers")
    print("=" * 60)

    print("\n🧪 Test 1: VIP flow callbacks")
    assert hasattr(vip_flow, 'callback_redeem_token'), "callback_redeem_token no existe"
    assert hasattr(vip_flow, 'process_token_input'), "process_token_input no existe"
    assert hasattr(vip_flow, 'callback_cancel'), "callback_cancel no existe"
    print("✅ VIP callbacks OK")

    print("\n🧪 Test 2: VIP flow callables")
    assert callable(vip_flow.callback_redeem_token)
    assert callable(vip_flow.process_token_input)
    assert callable(vip_flow.callback_cancel)
    print("✅ VIP callables OK")


def test_free_flow_handlers():
    """Test que los handlers Free existen"""
    print("\n" + "=" * 60)
    print("TEST: Free Flow Handlers")
    print("=" * 60)

    print("\n🧪 Test 1: Free flow callback")
    assert hasattr(free_flow, 'callback_request_free'), "callback_request_free no existe"
    assert callable(free_flow.callback_request_free)
    print("✅ Free callback OK")


def test_callback_data():
    """Test que los callback_data son correctos"""
    print("\n" + "=" * 60)
    print("TEST: Callback Data")
    print("=" * 60)

    print("\n🧪 Test 1: Verificar prefijos de callbacks")
    # Los callbacks están registrados con F.data == "user:..."
    # Verificamos que el código los menciona correctamente

    import inspect

    # Check vip_flow
    vip_source = inspect.getsource(vip_flow.callback_redeem_token)
    assert '"user:redeem_token"' in vip_source or "'user:redeem_token'" in vip_source
    print("✅ VIP callback data: user:redeem_token")

    # Check free_flow
    free_source = inspect.getsource(free_flow.callback_request_free)
    assert '"user:request_free"' in free_source or "'user:request_free'" in free_source
    print("✅ Free callback data: user:request_free")

    # Check cancel
    cancel_source = inspect.getsource(vip_flow.callback_cancel)
    assert '"user:cancel"' in cancel_source or "'user:cancel'" in cancel_source
    print("✅ Cancel callback data: user:cancel")


def test_states_imported():
    """Test que los estados FSM se importan correctamente"""
    print("\n" + "=" * 60)
    print("TEST: FSM States")
    print("=" * 60)

    print("\n🧪 Test 1: Verificar que TokenRedemptionStates está disponible")
    from bot.states.user import TokenRedemptionStates, FreeAccessStates
    assert TokenRedemptionStates is not None
    assert FreeAccessStates is not None
    print("✅ User states importados OK")

    print("\n🧪 Test 2: Estados disponibles")
    assert hasattr(TokenRedemptionStates, 'waiting_for_token')
    assert hasattr(FreeAccessStates, 'waiting_for_approval')
    print("✅ Token y Free states disponibles")


def test_imports():
    """Test que todos los imports funcionan"""
    print("\n" + "=" * 60)
    print("TEST: Imports")
    print("=" * 60)

    print("\n🧪 Test 1: Importar user_router")
    from bot.handlers.user import user_router as router
    assert router is not None
    print("✅ user_router importado OK")

    print("\n🧪 Test 2: Verificar que user_router es el mismo en todos los módulos")
    assert start.user_router is vip_flow.user_router
    assert vip_flow.user_router is free_flow.user_router
    print("✅ user_router compartido en todos los módulos")


def run_all_tests():
    """Ejecuta todos los tests"""
    print("\n" + "=" * 60)
    print("EJECUTANDO TESTS - USER HANDLERS")
    print("=" * 60)

    try:
        test_user_router()
        test_start_handler()
        test_vip_flow_handlers()
        test_free_flow_handlers()
        test_callback_data()
        test_states_imported()
        test_imports()

        print("\n" + "=" * 60)
        print("✅✅✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
        print("=" * 60)
        print("\nResumen:")
        print("- ✅ Router 'user' configurado")
        print("- ✅ Handler /start implementado")
        print("- ✅ VIP flow: redeem_token, process_input, cancel")
        print("- ✅ Free flow: request_free")
        print("- ✅ Callback data correctos: user:*")
        print("- ✅ FSM States importables")
        print("- ✅ user_router compartido")
        print("\nNota: Tests funcionales requieren bot ejecutándose")
        print("\n")

    except AssertionError as e:
        print(f"\n❌ TEST FALLIDO: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    run_all_tests()
