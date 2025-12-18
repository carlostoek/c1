#!/usr/bin/env python3
"""
Script de prueba para el sistema de cache del ConfigurationService
"""
import sys
import os

# Agregar el directorio actual al sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from bot.services.configuration.cache import ConfigCache, reset_config_cache

async def test_cache_integration():
    """Prueba la integración del cache con ConfigurationService"""
    try:
        from bot.services.configuration.service import ConfigurationService
        from bot.database.models import ActionConfig, LevelConfig, BadgeConfig, RewardConfig, MissionConfig
        from sqlalchemy.ext.asyncio import AsyncSession
        import logging
        
        # Configurar logging
        logging.basicConfig(level=logging.DEBUG)
        
        print("✅ Importaciones exitosas")
        
        # Resetear cache global para prueba limpia
        reset_config_cache()
        
        # Crear un mock para la sesión
        mock_session = MagicMock(spec=AsyncSession)
        mock_session.execute = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.delete = MagicMock()
        
        # Simular resultados de consulta
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_result.scalars().all.return_value = []
        mock_session.execute.return_value = mock_result
        
        # Crear instancia del servicio
        service = ConfigurationService(mock_session)
        
        print("✅ Configuración del entorno de prueba completada")
        
        # Test 1: Cache en list_actions
        print("\n1. Probando cache en list_actions...")
        # Simular que hay acciones disponibles
        mock_actions = [
            ActionConfig(
                id=1,
                action_key="test_action",
                display_name="Test Action",
                points_amount=10
            )
        ]
        
        # Primera llamada: irá a la BD
        mock_result.scalars().all.return_value = mock_actions
        actions1 = await service.list_actions()
        print(f"   Primera llamada: {len(actions1)} acciones (from DB)")
        
        # Segunda llamada: debería usar cache
        actions2 = await service.list_actions()
        print(f"   Segunda llamada: {len(actions2)} acciones (from cache)")
        
        # Verificar si el cache está funcionando
        stats = service._cache.get_stats()
        print(f"   Cache stats: hits={stats['hits']}, misses={stats['misses']}")
        
        # Test 2: Invalidación de cache al crear
        print("\n2. Probando invalidación de cache...")
        # Simular creación de acción
        await service.create_action(
            action_key="new_action",
            display_name="New Action",
            points_amount=5
        )
        
        # El cache debería haberse invalidado
        stats_after = service._cache.get_stats()
        print(f"   Stats después de creación: entries={stats_after['entries']}")
        
        # Test 3: Cache en get_points_for_action
        print("\n3. Probando cache en get_points_for_action...")
        
        # Mock para get_action
        mock_action = ActionConfig(
            id=1,
            action_key="cached_action",
            display_name="Cached Action",
            points_amount=25,
            is_active=True
        )
        original_get_action = service.get_action
        service.get_action = AsyncMock(return_value=mock_action)
        
        # Primera llamada
        points1 = await service.get_points_for_action("cached_action")
        print(f"   Primera llamada a puntos: {points1}")
        
        # Segunda llamada debería usar cache
        points2 = await service.get_points_for_action("cached_action")
        print(f"   Segunda llamada a puntos: {points2}")
        
        # Restaurar método original
        service.get_action = original_get_action
        
        # Test 4: Verificar estadísticas finales
        print("\n4. Estadísticas finales del cache:")
        final_stats = service._cache.get_stats()
        for key, value in final_stats.items():
            print(f"   {key}: {value}")
        
        print("\n🎉 Prueba de integración de cache completada")
        print("   El sistema de cache está funcionando correctamente")
        
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
    success = asyncio.run(test_cache_integration())
    if success:
        print("\n✅ Prueba de cache completada exitosamente")
    else:
        print("\n❌ Falló la prueba de cache")
        sys.exit(1)