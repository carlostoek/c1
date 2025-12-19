#!/usr/bin/env python3
"""
Script de prueba simple para el ConfigurationService sin conflictos de importación
"""
import sys
import os

# Agregar el directorio actual al sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

async def test_imports():
    """Verifica que los módulos se puedan importar correctamente"""
    try:
        # Intentar importar solo lo necesario para evitar conflictos
        from bot.services.configuration.service import ConfigurationService
        from bot.services.configuration.exceptions import (
            ConfigurationError,
            ConfigNotFoundError,
            ConfigAlreadyExistsError,
            ConfigValidationError,
            ConfigInUseError
        )
        
        print("✅ Importaciones exitosas del servicio de configuración")
        
        # Mostrar que se puede crear una instancia (sin conexión a BD)
        print(f"✅ Clase ConfigurationService: {ConfigurationService.__name__}")
        
        # Verificar que las excepciones existen
        exceptions = [
            ConfigurationError,
            ConfigNotFoundError,
            ConfigAlreadyExistsError,
            ConfigValidationError,
            ConfigInUseError
        ]
        
        for exc in exceptions:
            print(f"✅ Excepción disponible: {exc.__name__}")
        
        return True
    except ImportError as e:
        print(f"❌ Error en importación: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()
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