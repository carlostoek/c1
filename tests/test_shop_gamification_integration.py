"""
Tests de integración Tienda <-> Gamificación (Fase 1).

Valida:
- UnifiedRewardService.grant_shop_item()
- RewardService.grant_reward() con RewardType.SHOP_ITEM
- Validación de metadata SHOP_ITEM
- Flujo completo: Misión -> Recompensa SHOP_ITEM -> Item en inventario
"""
import pytest
import json
from datetime import datetime, UTC

from bot.database import get_session
from bot.gamification.services.unified import UnifiedRewardService
from bot.gamification.services.reward import RewardService
from bot.gamification.services.container import GamificationContainer
from bot.gamification.database.enums import RewardType, ObtainedVia
from bot.gamification.database.models import Reward
from bot.gamification.utils.validators import validate_reward_metadata
from bot.shop.services.shop import ShopService
from bot.shop.services.inventory import InventoryService
from bot.shop.database.models import ItemCategory, ShopItem


# ========================================
# HELPER FUNCTIONS
# ========================================

import uuid


def _unique_slug(prefix: str) -> str:
    """Genera un slug único para tests."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


async def create_test_category(session) -> ItemCategory:
    """Crea una categoría de prueba."""
    category = ItemCategory(
        name="Test Category",
        slug=_unique_slug("test-category"),
        description="Categoría de prueba",
        emoji="🧪",
        is_active=True,
        order=1
    )
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


async def create_test_item(session, category_id: int, is_active: bool = True) -> ShopItem:
    """Crea un item de prueba."""
    from bot.shop.database.enums import ItemType

    item = ShopItem(
        category_id=category_id,
        name="Test Item",
        slug=_unique_slug("test-item"),
        description="Item de prueba para tests",
        item_type=ItemType.CONSUMABLE.value,
        icon="🎁",
        price_besitos=100,
        rarity="common",
        is_active=is_active,
        stock=-1,  # Ilimitado
        created_by=1
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


# ========================================
# TEST: UNIFIED REWARD SERVICE
# ========================================

@pytest.mark.asyncio
async def test_grant_shop_item_success():
    """Test: Otorgar item de tienda correctamente."""
    async with get_session() as session:
        category = await create_test_category(session)
        shop_item = await create_test_item(session, category.id)

        unified = UnifiedRewardService(session)
        user_id = 123456789

        success, message, data = await unified.grant_shop_item(
            user_id=user_id,
            item_id=shop_item.id,
            quantity=1,
            source="mission_reward",
            reference_id=42
        )

        assert success is True
        assert "Recibiste" in message
        assert data is not None
        assert data["item_id"] == shop_item.id
        assert data["quantity"] == 1

        # Verificar que el item está en el inventario
        inventory = InventoryService(session)
        has_item = await inventory.has_item(user_id, shop_item.id)
        assert has_item is True


@pytest.mark.asyncio
async def test_grant_shop_item_by_slug():
    """Test: Otorgar item de tienda por slug."""
    async with get_session() as session:
        category = await create_test_category(session)
        shop_item = await create_test_item(session, category.id)

        unified = UnifiedRewardService(session)
        user_id = 123456790

        success, message, data = await unified.grant_shop_item_by_slug(
            user_id=user_id,
            item_slug=shop_item.slug,
            quantity=2,
            source="admin"
        )

        assert success is True
        assert data["item_slug"] == shop_item.slug
        assert data["quantity"] == 2


@pytest.mark.asyncio
async def test_grant_shop_item_not_found():
    """Test: Error al otorgar item inexistente."""
    async with get_session() as session:
        unified = UnifiedRewardService(session)

        success, message, data = await unified.grant_shop_item(
            user_id=123,
            item_id=99999,
            quantity=1,
            source="test"
        )

        assert success is False
        assert "no encontrado" in message.lower()
        assert data is None


@pytest.mark.asyncio
async def test_grant_unified_reward_shop_item():
    """Test: grant_unified_reward con tipo SHOP_ITEM."""
    async with get_session() as session:
        category = await create_test_category(session)
        shop_item = await create_test_item(session, category.id)

        unified = UnifiedRewardService(session)
        user_id = 123456791

        success, message, data = await unified.grant_unified_reward(
            user_id=user_id,
            reward_type=RewardType.SHOP_ITEM,
            reward_config={
                "item_id": shop_item.id,
                "quantity": 1
            },
            source="mission_reward"
        )

        assert success is True
        assert data is not None


# ========================================
# TEST: REWARD SERVICE + SHOP_ITEM
# ========================================

@pytest.mark.asyncio
async def test_reward_service_grant_shop_item():
    """Test: RewardService.grant_reward() con SHOP_ITEM."""
    async with get_session() as session:
        category = await create_test_category(session)
        shop_item = await create_test_item(session, category.id)

        # Crear reward tipo SHOP_ITEM
        reward = Reward(
            name="Test Shop Reward",
            description="Otorga un item de tienda",
            reward_type=RewardType.SHOP_ITEM.value,
            reward_metadata=json.dumps({
                "item_id": shop_item.id,
                "item_slug": shop_item.slug,
                "quantity": 1
            }),
            created_by=1
        )
        session.add(reward)
        await session.commit()
        await session.refresh(reward)

        # Otorgar reward
        reward_service = RewardService(session)
        user_id = 123456792

        success, message, user_reward = await reward_service.grant_reward(
            user_id=user_id,
            reward_id=reward.id,
            obtained_via=ObtainedVia.MISSION
        )

        assert success is True
        assert user_reward is not None

        # Verificar que el item está en el inventario
        inventory = InventoryService(session)
        has_item = await inventory.has_item(user_id, shop_item.id)
        assert has_item is True


# ========================================
# TEST: VALIDATORS
# ========================================

def test_validate_shop_item_metadata_valid():
    """Test: Validación de metadata SHOP_ITEM válida."""
    # Con item_id
    is_valid, error = validate_reward_metadata(
        RewardType.SHOP_ITEM,
        {"item_id": 1, "quantity": 1}
    )
    assert is_valid is True

    # Con item_slug
    is_valid, error = validate_reward_metadata(
        RewardType.SHOP_ITEM,
        {"item_slug": "test-item", "quantity": 2}
    )
    assert is_valid is True


def test_validate_shop_item_metadata_missing_id():
    """Test: Error si falta item_id e item_slug."""
    is_valid, error = validate_reward_metadata(
        RewardType.SHOP_ITEM,
        {"quantity": 1}
    )
    assert is_valid is False
    assert "item_id or item_slug" in error.lower()


def test_validate_shop_item_metadata_invalid_quantity():
    """Test: Error si quantity es inválida."""
    is_valid, error = validate_reward_metadata(
        RewardType.SHOP_ITEM,
        {"item_id": 1, "quantity": 0}
    )
    assert is_valid is False
    assert "quantity" in error.lower()


# ========================================
# TEST: INTEGRATION FLOW
# ========================================

@pytest.mark.asyncio
async def test_complete_mission_with_shop_item_reward():
    """Test: Flujo completo de misión con recompensa SHOP_ITEM."""
    from bot.gamification.services.mission import MissionService
    from bot.gamification.database.enums import MissionType

    async with get_session() as session:
        category = await create_test_category(session)
        shop_item = await create_test_item(session, category.id)

        user_id = 123456793
        admin_id = 1

        # 1. Crear reward tipo SHOP_ITEM
        reward = Reward(
            name="Shop Item Reward",
            description="Otorga item de tienda",
            reward_type=RewardType.SHOP_ITEM.value,
            reward_metadata=json.dumps({
                "item_id": shop_item.id,
                "quantity": 1
            }),
            created_by=admin_id
        )
        session.add(reward)
        await session.commit()
        await session.refresh(reward)

        # 2. Crear misión con unlock_rewards
        mission_service = MissionService(session)
        mission = await mission_service.create_mission(
            name="Test Mission",
            description="Misión de prueba",
            mission_type=MissionType.ONE_TIME,
            criteria={"type": "one_time", "count": 1},
            besitos_reward=100,
            unlock_rewards=[reward.id],
            created_by=admin_id
        )

        assert mission is not None
        assert mission.unlock_rewards is not None

        # 3. Verificar que unlock_rewards incluye el reward
        unlock_ids = json.loads(mission.unlock_rewards)
        assert reward.id in unlock_ids


@pytest.mark.asyncio
async def test_gamification_container_unified_reward():
    """Test: GamificationContainer incluye unified_reward."""
    async with get_session() as session:
        container = GamificationContainer(session)

        # Verificar que unified_reward está disponible
        unified = container.unified_reward
        assert unified is not None
        assert isinstance(unified, UnifiedRewardService)

        # Verificar lazy loading
        assert "unified_reward" in container.get_loaded_services()


# ========================================
# TEST: EDGE CASES
# ========================================

@pytest.mark.asyncio
async def test_grant_shop_item_inactive_item():
    """Test: Error al otorgar item inactivo."""
    async with get_session() as session:
        category = await create_test_category(session)
        inactive_item = await create_test_item(session, category.id, is_active=False)

        unified = UnifiedRewardService(session)

        success, message, data = await unified.grant_shop_item(
            user_id=123,
            item_id=inactive_item.id,
            quantity=1,
            source="test"
        )

        assert success is False
        assert "no está disponible" in message.lower()


@pytest.mark.asyncio
async def test_validate_shop_item_reward_config():
    """Test: Validación de configuración de recompensa."""
    async with get_session() as session:
        category = await create_test_category(session)
        shop_item = await create_test_item(session, category.id)

        unified = UnifiedRewardService(session)

        # Config válida
        is_valid, error = await unified.validate_shop_item_reward_config({
            "item_id": shop_item.id,
            "quantity": 1
        })
        assert is_valid is True

        # Config inválida (item no existe)
        is_valid, error = await unified.validate_shop_item_reward_config({
            "item_id": 99999,
            "quantity": 1
        })
        assert is_valid is False
