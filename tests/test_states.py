"""
Tests para los estados FSM de admin y user.
"""
from aiogram.fsm.state import State, StatesGroup
from bot.states import (
    ChannelSetupStates,
    WaitTimeSetupStates,
    BroadcastStates,
    TokenRedemptionStates,
    FreeAccessStates
)


def test_admin_states():
    """Test que los estados de admin existen y son correctos"""
    print("\n" + "=" * 60)
    print("TEST: Admin States")
    print("=" * 60)

    # Test ChannelSetupStates
    print("\n🧪 Test 1: ChannelSetupStates")
    assert hasattr(ChannelSetupStates, 'waiting_for_vip_channel'), \
        "ChannelSetupStates no tiene waiting_for_vip_channel"
    assert hasattr(ChannelSetupStates, 'waiting_for_free_channel'), \
        "ChannelSetupStates no tiene waiting_for_free_channel"
    assert issubclass(ChannelSetupStates, StatesGroup), \
        "ChannelSetupStates no hereda de StatesGroup"
    assert isinstance(ChannelSetupStates.waiting_for_vip_channel, State), \
        "waiting_for_vip_channel no es State"
    assert isinstance(ChannelSetupStates.waiting_for_free_channel, State), \
        "waiting_for_free_channel no es State"
    print("✅ ChannelSetupStates OK")
    print(f"   - waiting_for_vip_channel: {ChannelSetupStates.waiting_for_vip_channel}")
    print(f"   - waiting_for_free_channel: {ChannelSetupStates.waiting_for_free_channel}")

    # Test WaitTimeSetupStates
    print("\n🧪 Test 2: WaitTimeSetupStates")
    assert hasattr(WaitTimeSetupStates, 'waiting_for_minutes'), \
        "WaitTimeSetupStates no tiene waiting_for_minutes"
    assert issubclass(WaitTimeSetupStates, StatesGroup), \
        "WaitTimeSetupStates no hereda de StatesGroup"
    assert isinstance(WaitTimeSetupStates.waiting_for_minutes, State), \
        "waiting_for_minutes no es State"
    print("✅ WaitTimeSetupStates OK")
    print(f"   - waiting_for_minutes: {WaitTimeSetupStates.waiting_for_minutes}")

    # Test BroadcastStates
    print("\n🧪 Test 3: BroadcastStates")
    assert hasattr(BroadcastStates, 'waiting_for_content'), \
        "BroadcastStates no tiene waiting_for_content"
    assert hasattr(BroadcastStates, 'waiting_for_confirmation'), \
        "BroadcastStates no tiene waiting_for_confirmation"
    assert issubclass(BroadcastStates, StatesGroup), \
        "BroadcastStates no hereda de StatesGroup"
    assert isinstance(BroadcastStates.waiting_for_content, State), \
        "waiting_for_content no es State"
    assert isinstance(BroadcastStates.waiting_for_confirmation, State), \
        "waiting_for_confirmation no es State"
    print("✅ BroadcastStates OK")
    print(f"   - waiting_for_content: {BroadcastStates.waiting_for_content}")
    print(f"   - waiting_for_confirmation: {BroadcastStates.waiting_for_confirmation}")

    print("\n✅ TODOS LOS TESTS DE ADMIN STATES PASARON")


def test_user_states():
    """Test que los estados de usuario existen y son correctos"""
    print("\n" + "=" * 60)
    print("TEST: User States")
    print("=" * 60)

    # Test TokenRedemptionStates
    print("\n🧪 Test 1: TokenRedemptionStates")
    assert hasattr(TokenRedemptionStates, 'waiting_for_token'), \
        "TokenRedemptionStates no tiene waiting_for_token"
    assert issubclass(TokenRedemptionStates, StatesGroup), \
        "TokenRedemptionStates no hereda de StatesGroup"
    assert isinstance(TokenRedemptionStates.waiting_for_token, State), \
        "waiting_for_token no es State"
    print("✅ TokenRedemptionStates OK")
    print(f"   - waiting_for_token: {TokenRedemptionStates.waiting_for_token}")

    # Test FreeAccessStates
    print("\n🧪 Test 2: FreeAccessStates")
    assert hasattr(FreeAccessStates, 'waiting_for_approval'), \
        "FreeAccessStates no tiene waiting_for_approval"
    assert issubclass(FreeAccessStates, StatesGroup), \
        "FreeAccessStates no hereda de StatesGroup"
    assert isinstance(FreeAccessStates.waiting_for_approval, State), \
        "waiting_for_approval no es State"
    print("✅ FreeAccessStates OK")
    print(f"   - waiting_for_approval: {FreeAccessStates.waiting_for_approval}")

    print("\n✅ TODOS LOS TESTS DE USER STATES PASARON")


def test_exports():
    """Test que los estados se exportan correctamente desde __init__"""
    print("\n" + "=" * 60)
    print("TEST: Exports en __init__.py")
    print("=" * 60)

    print("\n🧪 Test 1: Todas las clases están exportadas")
    from bot.states import (
        ChannelSetupStates,
        WaitTimeSetupStates,
        BroadcastStates,
        TokenRedemptionStates,
        FreeAccessStates
    )

    assert ChannelSetupStates is not None
    assert WaitTimeSetupStates is not None
    assert BroadcastStates is not None
    assert TokenRedemptionStates is not None
    assert FreeAccessStates is not None

    print("✅ Todas las clases están correctamente exportadas")

    print("\n✅ TODOS LOS TESTS DE EXPORTS PASARON")


def test_state_strings():
    """Test que los strings de estados son correctos"""
    print("\n" + "=" * 60)
    print("TEST: State Strings")
    print("=" * 60)

    print("\n🧪 Test 1: Verificar nombres de estados")

    # Admin states
    print(f"ChannelSetupStates.waiting_for_vip_channel state: {ChannelSetupStates.waiting_for_vip_channel.state}")
    print(f"ChannelSetupStates.waiting_for_free_channel state: {ChannelSetupStates.waiting_for_free_channel.state}")
    print(f"WaitTimeSetupStates.waiting_for_minutes state: {WaitTimeSetupStates.waiting_for_minutes.state}")
    print(f"BroadcastStates.waiting_for_content state: {BroadcastStates.waiting_for_content.state}")
    print(f"BroadcastStates.waiting_for_confirmation state: {BroadcastStates.waiting_for_confirmation.state}")

    # User states
    print(f"TokenRedemptionStates.waiting_for_token state: {TokenRedemptionStates.waiting_for_token.state}")
    print(f"FreeAccessStates.waiting_for_approval state: {FreeAccessStates.waiting_for_approval.state}")

    # Verificar que los nombres contienen el grupo
    assert "ChannelSetupStates" in ChannelSetupStates.waiting_for_vip_channel.state
    assert "WaitTimeSetupStates" in WaitTimeSetupStates.waiting_for_minutes.state
    assert "TokenRedemptionStates" in TokenRedemptionStates.waiting_for_token.state

    print("\n✅ TODOS LOS NOMBRES DE ESTADOS SON CORRECTOS")


def run_all_tests():
    """Ejecuta todos los tests"""
    print("\n" + "=" * 60)
    print("EJECUTANDO TESTS FSM STATES")
    print("=" * 60)

    try:
        test_admin_states()
        test_user_states()
        test_exports()
        test_state_strings()

        print("\n" + "=" * 60)
        print("✅✅✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
        print("=" * 60)
        print("\nResumen:")
        print("- ✅ ChannelSetupStates (2 estados)")
        print("- ✅ WaitTimeSetupStates (1 estado)")
        print("- ✅ BroadcastStates (2 estados)")
        print("- ✅ TokenRedemptionStates (1 estado)")
        print("- ✅ FreeAccessStates (1 estado)")
        print("- ✅ Total: 5 StatesGroup, 7 States")
        print("\n")

    except AssertionError as e:
        print(f"\n❌ TEST FALLIDO: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
