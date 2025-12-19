"""
Test de integración con ServiceContainer.
"""
import asyncio
from bot.database import get_session, init_db
from bot.database.models import User
from bot.services.container import ServiceContainer
from aiogram import Bot


async def test_container_integration():
    print("🧪 Test de integración ServiceContainer\n")
    
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
        user = User(user_id=666666, username="containeruser", first_name="Test")
        session.add(user)
        await session.commit()
        
        # Otorgar puntos usando container
        success, new_balance = await container.points.award_points(
            user_id=user.user_id,
            amount=100,
            reason="Test desde container",
            multiplier=1.0
        )
        
        assert success is True
        assert new_balance == 100
        print("  ✅ award_points funciona desde container\n")
        
        # Test 5: Consultar balance desde container
        print("Test 5: Consultar balance desde container...")
        balance = await container.points.get_user_balance(user.user_id)
        
        assert balance == 100
        print(f"  ✅ Balance: {balance} 💋\n")
        
        # Test 6: Verificar que otros servicios siguen funcionando
        print("Test 6: Verificar otros servicios siguen accesibles...")
        assert hasattr(container, 'subscription')
        assert hasattr(container, 'user')
        assert hasattr(container, 'reactions')
        print("  ✅ Otros servicios accesibles\n")
        
        print("🎉 Todos los tests de integración pasaron!")


if __name__ == "__main__":
    asyncio.run(test_container_integration())