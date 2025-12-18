"""
Test de integración con ServiceContainer.
"""
import asyncio
from bot.database import get_session, init_db
from bot.database.models import User
from bot.services.container import ServiceContainer
from aiogram import Bot


async def test_container_integration():
    print("🧪 Test de integración ServiceContainer.\n")
    
    await init_db()
    
    # Mock bot instance for testing
    class MockBot:
        def __init__(self):
            pass

    mock_bot = MockBot()
    
    async with get_session() as session:
        # Test 1: Crear container
        print("Test 1: Crear ServiceContainer...")
        container = ServiceContainer(session, mock_bot)
        print("  ✅ Container creado\n")
        
        # Test 2: Acceder a points service (lazy loading)
        print("Test 2: Acceder a points service...")
        points_service = container.points
        
        assert points_service is not None
        assert hasattr(points_service, 'award_points')
        print("  ✅ PointsService accesible\n")
        
        # Test 3: Verificar que es singleton (mismo objeto)
        print("Test 3: Verificar lazy loading (singleton)...")
        points_service2 = container.points
        
        assert points_service is points_service2
        print("  ✅ Lazy loading funciona (mismo objeto)\n")
        
        # Test 4: Usar servicio desde container
        print("Test 4: Usar servicio desde container...")
        # Add a user first to the database
        from bot.database.models import User
        fresh_user_id = 999999
        user = User(user_id=fresh_user_id, username="testuser", first_name="Test")
        session.add(user)
        await session.commit()

        # Now award points which will create the user progress record automatically
        success, new_balance = await container.points.award_points(
            user_id=fresh_user_id,
            amount=100,
            reason="Test desde container",
            multiplier=1.0
        )

        assert success is True
        print(f"  ✅ award_points funciona desde container (nuevo saldo: {new_balance})\n")

        # Test 5: Consultar balance desde container
        print("Test 5: Consultar balance desde container...")
        balance = await container.points.get_user_balance(fresh_user_id)

        assert balance == new_balance
        print(f"  ✅ Balance: {balance} 💋\n")
        
        print("🎉 Todos los tests de integración pasaron!")


asyncio.run(test_container_integration())