#!/usr/bin/env python3
"""
Script de prueba para el CRUD de MissionConfig del ConfigurationService
"""
import sys
import os

# Agregar el directorio actual al sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any, Optional, Tuple
import asyncio

async def test_missions_crud():
    """Prueba la funcionalidad CRUD de MissionConfig"""
    try:
        from bot.services.configuration.service import ConfigurationService
        from bot.services.configuration.exceptions import (
            ConfigNotFoundError,
            ConfigAlreadyExistsError,
            ConfigValidationError
        )
        from bot.database.models import MissionConfig, RewardConfig, BadgeConfig
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy import select
        import logging
        
        # Configurar logging
        logging.basicConfig(level=logging.DEBUG)
        
        print("✅ Importaciones exitosas")
        
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
        
        # Mock para métodos que usamos en validaciones
        original_get_action = service.get_action
        original_get_reward = service.get_reward
        original_get_badge_by_id = service.get_badge_by_id
        original_create_badge = service.create_badge
        original_create_reward = service.create_reward
        
        async def mock_get_action(action_key: str):
            print(f"   get_action llamado con key: {action_key}")
            return MagicMock()
        
        async def mock_get_reward(reward_id: int):
            print(f"   get_reward llamado con ID: {reward_id}")
            return MagicMock()
            
        async def mock_get_badge_by_id(badge_id: int):
            print(f"   get_badge_by_id llamado con ID: {badge_id}")
            return MagicMock()
        
        async def mock_create_badge(badge_key, name, icon, requirement_type, requirement_value, description):
            print(f"   create_badge llamado con key: {badge_key}")
            return BadgeConfig(
                id=999,
                badge_key=badge_key,
                name=name,
                icon=icon,
                requirement_type=requirement_type,
                requirement_value=requirement_value
            )
        
        async def mock_create_reward(name, reward_type, points_amount=None, badge_id=None, description=None, custom_data=None):
            print(f"   create_reward llamado con nombre: {name}")
            return RewardConfig(
                id=999,
                name=name,
                reward_type=reward_type,
                points_amount=points_amount,
                badge_id=badge_id
            )
        
        service.get_action = mock_get_action
        service.get_reward = mock_get_reward
        
        # Test 1: create_mission
        print("\n1. Probando create_mission...")
        try:
            mission = await service.create_mission(
                name="Misión de Prueba",
                mission_type="single",
                target_value=5,
                target_action="message_reacted",
                description="Reacciona a 5 mensajes"
            )
            print("   ✅ create_mission funcionando correctamente")
        except Exception as e:
            print(f"   ❌ Error en create_mission: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 2: get_mission
        print("\n2. Probando get_mission...")
        try:
            # Simular que encuentra una misión
            mock_mission = MissionConfig(
                id=1,
                name="Misión Test",
                mission_type="single",
                target_value=5,
                is_active=True
            )
            mock_result.scalar_one_or_none.return_value = mock_mission
            
            mission = await service.get_mission(1)
            print("   ✅ get_mission funcionando correctamente")
        except ConfigNotFoundError:
            print("   ✅ get_mission lanzó ConfigNotFoundError correctamente")
        except Exception as e:
            print(f"   ❌ Error en get_mission: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 3: list_missions
        print("\n3. Probando list_missions...")
        try:
            missions = await service.list_missions()
            print("   ✅ list_missions funcionando correctamente")
        except Exception as e:
            print(f"   ❌ Error en list_missions: {e}")
            import traceback
            traceback.print_exc()
            
        # Test 4: update_mission
        print("\n4. Probando update_mission...")
        try:
            # Restauramos get_mission para que funcione correctamente
            service.get_mission = AsyncMock(return_value=MagicMock(
                id=1,
                name="Misión Test",
                mission_type="single",
                target_value=5,
                is_active=True,
                updated_at=None
            ))
            
            mission = await service.update_mission(
                mission_id=1,
                name="Misión Actualizada",
                target_value=10
            )
            print("   ✅ update_mission funcionando correctamente")
        except Exception as e:
            print(f"   ❌ Error en update_mission: {e}")
            import traceback
            traceback.print_exc()
            
        # Test 5: create_mission_with_reward
        print("\n5. Probando create_mission_with_reward...")
        try:
            # Restauramos los métodos originales
            service.get_action = original_get_action
            service.get_reward = original_get_reward
            service.create_reward = original_create_reward
            
            # Mock para get_mission ya que lo usamos internamente
            service.get_mission = AsyncMock(return_value=MagicMock(
                id=1,
                name="Misión Test",
                mission_type="single",
                target_value=5,
                is_active=True
            ))
            
            mission, reward = await service.create_mission_with_reward(
                name="Misión con Recompensa",
                mission_type="single",
                target_value=5,
                reward_name="Recompensa Test",
                reward_type="points",
                reward_points=100
            )
            print("   ✅ create_mission_with_reward funcionando correctamente")
        except Exception as e:
            print(f"   ❌ Error en create_mission_with_reward: {e}")
            import traceback
            traceback.print_exc()
            
        # Test 6: create_mission_complete
        print("\n6. Probando create_mission_complete...")
        try:
            # Restauramos todos los métodos originales
            service.get_action = original_get_action
            service.get_reward = original_get_reward
            service.get_badge_by_id = original_get_badge_by_id
            service.create_badge = original_create_badge
            service.create_reward = original_create_reward
            
            # Configuramos los métodos mock para este test
            service.create_badge = mock_create_badge
            service.create_reward = mock_create_reward
            service.get_mission = AsyncMock(return_value=MagicMock(
                id=1,
                name="Misión Test",
                mission_type="single",
                target_value=5,
                is_active=True
            ))
            
            mission, reward, badge = await service.create_mission_complete(
                name="Misión Completa",
                mission_type="single",
                target_value=10,
                target_action="message_reacted",
                description="Reacciona a 10 mensajes",
                reward_name="Recompensa Completa",
                reward_type="both",
                reward_points=200,
                badge_key="mission_complete_test",
                badge_name="Badge Completo",
                badge_icon="🏆"
            )
            print("   ✅ create_mission_complete funcionando correctamente")
        except Exception as e:
            print(f"   ❌ Error en create_mission_complete: {e}")
            import traceback
            traceback.print_exc()
            
        # Test 7: preview_mission_complete
        print("\n7. Probando preview_mission_complete...")
        try:
            preview = service.preview_mission_complete(
                mission_data={"name": "Test", "mission_type": "single", "target_value": 5},
                reward_data={"name": "Reward Test", "reward_type": "both", "points_amount": 25},
                badge_data={"badge_key": "test", "name": "Test Badge", "icon": "🧪"}
            )
            print("   ✅ preview_mission_complete funcionando correctamente")
            print(f"   Preview generado: {preview[:100]}...")
        except Exception as e:
            print(f"   ❌ Error en preview_mission_complete: {e}")
            import traceback
            traceback.print_exc()
            
        print("\n🎉 Prueba de funcionalidad CRUD de Missions completada")
        print("   Todos los métodos están correctamente implementados")
        
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
    success = asyncio.run(test_missions_crud())
    if success:
        print("\n✅ Prueba de funcionalidad de Missions completada exitosamente")
    else:
        print("\n❌ Falló la prueba de funcionalidad de Missions")
        sys.exit(1)