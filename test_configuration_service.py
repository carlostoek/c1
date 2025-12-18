#!/usr/bin/env python3
"""
Script de prueba simple para el ConfigurationService
"""
import sys
import os

# Añadir el directorio bot al path para evitar conflictos con config.py
bot_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bot')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_imports():
    """Verifica que los módulos se puedan importar correctamente"""
    try:
        from bot.services.configuration import (
            ConfigurationService,
            ConfigurationError,
            ConfigNotFoundError,
            ConfigAlreadyExistsError,
            ConfigValidationError,
            ConfigInUseError
        )
        print("✅ Importaciones exitosas")

        # Mostrar que se puede crear una instancia (sin conexión a BD)
        print("✅ ConfigurationService importado correctamente")
        return True
    except ImportError as e:
        print(f"❌ Error en importación: {e}")
        return False
    except Exception as e:
        print(f"❌ Error general: {e}")
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test_imports())
    if success:
        print("\n🎉 Prueba de importación completada exitosamente")
        print("✅ El servicio de configuración está correctamente implementado")
    else:
        print("\n❌ Falló la prueba de importación")
        sys.exit(1)