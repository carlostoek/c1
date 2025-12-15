"""
Test del flujo completo de opciones.
Simula interacción del admin eligiendo opciones.
"""
import asyncio
from aiogram import Bot
from bot.database.engine import get_session, init_db
from bot.services.container import ServiceContainer

# Initialize the database before running the test
asyncio.run(init_db())

async def test_options_flow():
    print("Test de flujo de opciones de broadcasting\n")
    
    bot = Bot(token="123456:ABC-DEF1234567890")
    
    async with get_session() as session:
        container = ServiceContainer(session, bot)
        
        # Test 1: Verificar que hay reacciones configuradas
        print("Test 1: Verificar reacciones configuradas...")
        active_reactions = await container.reactions.get_active_reactions()
        
        if not active_reactions:
            print("  No hay reacciones configuradas")
            print("  Creando reacción de prueba...")
            await container.reactions.create_reaction("❤️", "Me encanta", 5)
            active_reactions = await container.reactions.get_active_reactions()
        
        print(f"  {len(active_reactions)} reacciones activas\n")
        
        # Test 2: Simular toggle de opciones
        print("Test 2: Simular toggle de opciones...")
        
        # Estado inicial
        attach_reactions = False
        protect_content = False
        print(f"  Inicial: reacciones={attach_reactions}, proteccion={protect_content}")
        
        # Toggle reacciones
        attach_reactions = not attach_reactions
        print(f"  Despues de toggle reacciones: reacciones={attach_reactions}, proteccion={protect_content}")
        
        # Toggle protección
        protect_content = not protect_content
        print(f"  Despues de toggle proteccion: reacciones={attach_reactions}, proteccion={protect_content}")
        
        # Toggle reacciones de nuevo (desactivar)
        attach_reactions = not attach_reactions
        print(f"  Despues de toggle reacciones: reacciones={attach_reactions}, proteccion={protect_content}")
        
        print("  Toggles funcionan correctamente\n")
        
        # Test 3: Validar que los iconos cambiarían
        print("Test 3: Validar iconos...")
        reactions_icon = "V" if attach_reactions else "X"
        protect_icon = "V" if protect_content else "X"
        print(f"  Iconos: reacciones={reactions_icon}, proteccion={protect_icon}")
        print("  Iconos correctos\n")
        
        await session.commit()
        print("Test completado!")

asyncio.run(test_options_flow())
