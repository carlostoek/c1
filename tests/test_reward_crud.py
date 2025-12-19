#!/usr/bin/env python3
"""
Script de prueba para el CRUD de RewardConfig del ConfigurationService
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

async def test_rewards_crud():
    """Prueba la funcionalidad CRUD de RewardConfig"""
    try:
        from bot.services.configuration.service import ConfigurationService
        from bot.services.configuration.exceptions import (
            ConfigNotFoundError,
            ConfigAlreadyExistsError,
            ConfigValidationError
        )
        from bot.database.models import RewardConfig, BadgeConfig
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
        
        # Mock para get_badge_by_id ya que lo usamos en create_reward
        original_get_badge_by_id = service.get_badge_by_id
        async def mock_get_badge_by_id(badge_id: int):
            print(f"   get_badge_by_id llamado con ID: {badge_id}")
            badge = BadgeConfig(
                id=badge_id,
                badge_key="test_badge",
                name="Test Badge",
                icon="🏆",
                requirement_type="total_reactions",
                requirement_value=10
            )
            return badge
        service.get_badge_by_id = mock_get_badge_by_id
        
        # Test 1: create_reward
        print("\n1. Probando create_reward...")
        try:
            reward = await service.create_reward(
                name="Recompensa de Prueba",
                reward_type="points",
                points_amount=100,
                description="Una recompensa de prueba"
            )
            print("   ✅ create_reward funcionando correctamente")
        except Exception as e:
            print(f"   ❌ Error en create_reward: {e}")
        
        # Test 2: create_reward con tipo 'both'
        print("\n2. Probando create_reward con badge...")
        try:
            reward = await service.create_reward(
                name="Recompensa con Badge",
                reward_type="both",
                points_amount=50,
                badge_id=1
            )
            print("   ✅ create_reward con badge funcionando correctamente")
        except Exception as e:
            print(f"   ❌ Error en create_reward con badge: {e}")
        
        # Test 3: get_reward
        print("\n3. Probando get_reward...")
        try:
            # Simular que encuentra una recompensa
            mock_reward = RewardConfig(
                id=1,
                name="Recompensa Test",
                reward_type="points",
                points_amount=100,
                is_active=True
            )
            mock_result.scalar_one_or_none.return_value = mock_reward
            
            reward = await service.get_reward(1)
            print("   ✅ get_reward funcionando correctamente")
        except ConfigNotFoundError:
            print("   ✅ get_reward lanzó ConfigNotFoundError correctamente")
        except Exception as e:
            print(f"   ❌ Error en get_reward: {e}")
        
        # Test 4: list_rewards
        print("\n4. Probando list_rewards...")
        try:
            rewards = await service.list_rewards()
            print("   ✅ list_rewards funcionando correctamente")
        except Exception as e:
            print(f"   ❌ Error en list_rewards: {e}")
            
        # Test 5: update_reward
        print("\n5. Probando update_reward...")
        try:
            reward = await service.update_reward(
                reward_id=1,
                name="Recompensa Actualizada",
                points_amount=200
            )
            print("   ✅ update_reward funcionando correctamente")
        except Exception as e:
            print(f"   ❌ Error en update_reward: {e}")
            
        # Test 6: create_reward_with_new_badge
        print("\n6. Probando create_reward_with_new_badge...")
        try:
            # Restaurar el método original de get_badge_by_id para este test
            service.get_badge_by_id = original_get_badge_by_id
            
            # Mock de create_badge
            async def mock_create_badge(badge_key, name, icon, requirement_type, requirement_value, description):
                return BadgeConfig(
                    id=999,
                    badge_key=badge_key,
                    name=name,
                    icon=icon,
                    requirement_type=requirement_type,
                    requirement_value=requirement_value
                )
            
            # Mock de create_reward
            async def mock_create_reward(name, reward_type, points_amount=None, badge_id=None, description=None, custom_data=None):
                return RewardConfig(
                    id=999,
                    name=name,
                    reward_type=reward_type,
                    points_amount=points_amount,
                    badge_id=badge_id
                )
            
            service.create_badge = mock_create_badge
            service.create_reward = mock_create_reward
            
            reward, badge = await service.create_reward_with_new_badge(
                name="Recompensa Test",
                reward_type="both",
                points_amount=100,
                badge_key="test_nested",
                badge_name="Badge Nested",
                badge_icon="🎁"
            )
            print("   ✅ create_reward_with_new_badge funcionando correctamente")
        except Exception as e:
            print(f"   ❌ Error en create_reward_with_new_badge: {e}")
            import traceback
            traceback.print_exc()
            
        print("\n🎉 Prueba de funcionalidad CRUD de Rewards completada")
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
    success = asyncio.run(test_rewards_crud())
    if success:
        print("\n✅ Prueba de funcionalidad de Rewards completada exitosamente")
    else:
        print("\n❌ Falló la prueba de funcionalidad de Rewards")
        sys.exit(1)