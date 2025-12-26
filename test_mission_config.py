"""
Test script para validar mission_config.py
"""
import asyncio
import sys


async def test_imports():
    """Test que todos los imports funcionan correctamente."""
    print("1. Testing imports...")

    try:
        from bot.gamification.services.mission import MissionService
        print("   ✅ MissionService imported")
    except Exception as e:
        print(f"   ❌ Error importing MissionService: {e}")
        return False

    try:
        from bot.gamification.handlers.admin import mission_config
        print("   ✅ mission_config imported")
    except Exception as e:
        print(f"   ❌ Error importing mission_config: {e}")
        return False

    try:
        from bot.gamification.states.admin import MissionConfigStates
        print("   ✅ MissionConfigStates imported")
    except Exception as e:
        print(f"   ❌ Error importing MissionConfigStates: {e}")
        return False

    return True


async def test_service_method():
    """Test que el método get_mission_stats existe."""
    print("\n2. Testing MissionService.get_mission_stats()...")

    try:
        from bot.gamification.services.mission import MissionService
        import inspect

        # Verificar que el método existe
        if hasattr(MissionService, 'get_mission_stats'):
            print("   ✅ Method get_mission_stats exists")

            # Verificar firma
            sig = inspect.signature(MissionService.get_mission_stats)
            params = list(sig.parameters.keys())
            if 'self' in params and 'mission_id' in params:
                print(f"   ✅ Method signature correct: {params}")
            else:
                print(f"   ❌ Unexpected parameters: {params}")
                return False
        else:
            print("   ❌ Method get_mission_stats not found")
            return False

        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


async def test_router():
    """Test que el router está configurado correctamente."""
    print("\n3. Testing router configuration...")

    try:
        from bot.gamification.handlers.admin import mission_config

        if hasattr(mission_config, 'router'):
            print("   ✅ Router exists")

            # Verificar que tiene handlers registrados
            handlers = mission_config.router.observers
            if handlers:
                print(f"   ✅ Router has {len(handlers)} handler groups registered")
            else:
                print("   ⚠️  Router has no handlers (may be normal)")

            return True
        else:
            print("   ❌ Router not found")
            return False

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


async def test_states():
    """Test que los estados FSM están configurados."""
    print("\n4. Testing FSM states...")

    try:
        from bot.gamification.states.admin import MissionConfigStates

        required_states = [
            'waiting_for_name',
            'waiting_for_description',
            'waiting_for_besitos',
            'editing_criteria',
            'waiting_for_streak_days',
            'waiting_for_daily_count',
            'waiting_for_weekly_target'
        ]

        for state_name in required_states:
            if hasattr(MissionConfigStates, state_name):
                print(f"   ✅ State {state_name} exists")
            else:
                print(f"   ❌ State {state_name} not found")
                return False

        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


async def test_registration():
    """Test que el router está registrado en handlers/__init__.py."""
    print("\n5. Testing router registration...")

    try:
        from bot.gamification.handlers import gamification_mission_config_router
        print("   ✅ gamification_mission_config_router exported")

        from bot.handlers import register_all_handlers
        print("   ✅ register_all_handlers imported")

        # Verificar que el router es válido
        if hasattr(gamification_mission_config_router, 'observers'):
            print("   ✅ Router is valid Aiogram Router")
        else:
            print("   ❌ Router is not valid")
            return False

        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


async def main():
    """Run all tests."""
    print("="*60)
    print("MISSION_CONFIG.PY - VALIDATION TESTS")
    print("="*60)

    results = []

    results.append(await test_imports())
    results.append(await test_service_method())
    results.append(await test_router())
    results.append(await test_states())
    results.append(await test_registration())

    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)

    passed = sum(results)
    total = len(results)

    print(f"\nTests passed: {passed}/{total}")

    if passed == total:
        print("\n✅ ALL TESTS PASSED")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
