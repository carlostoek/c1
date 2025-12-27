"""
Tests E2E para el módulo de Tienda.

Prueba los flujos completos:
- Creación de categorías y productos
- Compra de productos
- Inventario y mochila
- Integración con gamificación (besitos)
- Integración con narrativa (desbloqueo de fragmentos)
"""

import pytest
from datetime import datetime, UTC

from bot.database import init_db, close_db, get_session
from bot.shop.services.container import ShopContainer, reset_shop_container
from bot.shop.database.enums import ItemType, ItemRarity, PurchaseStatus


@pytest.fixture(autouse=True)
async def setup_db():
    """Setup y teardown de BD para cada test."""
    await init_db()
    yield
    reset_shop_container()
    await close_db()


@pytest.fixture
async def session():
    """Proporciona sesión de BD."""
    async with get_session() as sess:
        yield sess


@pytest.fixture
async def shop_container(session):
    """Proporciona container de tienda."""
    return ShopContainer(session)


@pytest.fixture
async def sample_category(shop_container):
    """Crea categoría de prueba."""
    return await shop_container.shop.create_category(
        name="Artefactos de Test",
        description="Categoría para pruebas",
        emoji="🧪"
    )


@pytest.fixture
async def sample_item(shop_container, sample_category):
    """Crea producto de prueba."""
    success, msg, item = await shop_container.shop.create_item(
        category_id=sample_category.id,
        name="Llave Mágica",
        description="Desbloquea secretos ocultos",
        item_type=ItemType.NARRATIVE,
        price_besitos=50,
        icon="🔑",
        created_by=1
    )
    return item


@pytest.fixture
async def user_with_besitos(session):
    """Crea usuario con besitos para comprar."""
    from bot.gamification.database.models import UserGamification
    from bot.database.models import User

    user_id = 12345678

    # Crear usuario
    user = User(user_id=user_id, username="test_buyer")
    session.add(user)

    # Crear gamificación con besitos
    gamif = UserGamification(
        user_id=user_id,
        total_besitos=200,
        besitos_earned=200,
        besitos_spent=0
    )
    session.add(gamif)
    await session.commit()

    return user_id


# ========================================
# TESTS DE CATEGORÍAS
# ========================================

@pytest.mark.asyncio
async def test_create_category(shop_container):
    """Test: Crear categoría."""
    category = await shop_container.shop.create_category(
        name="Tesoros Ocultos",
        description="Artefactos antiguos",
        emoji="💎",
        order=1
    )

    assert category is not None
    assert category.name == "Tesoros Ocultos"
    assert category.slug == "tesoros-ocultos"
    assert category.emoji == "💎"
    assert category.is_active is True


@pytest.mark.asyncio
async def test_get_all_categories(shop_container):
    """Test: Obtener todas las categorías."""
    await shop_container.shop.create_category(name="Cat 1", emoji="1️⃣")
    await shop_container.shop.create_category(name="Cat 2", emoji="2️⃣")

    categories = await shop_container.shop.get_all_categories()

    assert len(categories) >= 2


@pytest.mark.asyncio
async def test_update_category(shop_container, sample_category):
    """Test: Actualizar categoría."""
    updated = await shop_container.shop.update_category(
        sample_category.id,
        name="Artefactos Actualizados",
        emoji="✨"
    )

    assert updated.name == "Artefactos Actualizados"
    assert updated.emoji == "✨"


# ========================================
# TESTS DE PRODUCTOS
# ========================================

@pytest.mark.asyncio
async def test_create_item(shop_container, sample_category):
    """Test: Crear producto."""
    success, msg, item = await shop_container.shop.create_item(
        category_id=sample_category.id,
        name="Espada del Destino",
        description="Arma legendaria",
        item_type=ItemType.NARRATIVE,
        rarity=ItemRarity.LEGENDARY,
        price_besitos=100,
        icon="⚔️",
        created_by=1
    )

    assert success is True
    assert item is not None
    assert item.name == "Espada del Destino"
    assert item.price_besitos == 100
    assert item.rarity == "legendary"


@pytest.mark.asyncio
async def test_create_item_invalid_category(shop_container):
    """Test: Error al crear con categoría inválida."""
    success, msg, item = await shop_container.shop.create_item(
        category_id=99999,
        name="Item Fantasma",
        description="No debería crearse",
        item_type=ItemType.DIGITAL,
        price_besitos=10,
        created_by=1
    )

    assert success is False
    assert "Categoría no encontrada" in msg


@pytest.mark.asyncio
async def test_get_items_by_category(shop_container, sample_category):
    """Test: Obtener items de una categoría."""
    await shop_container.shop.create_item(
        category_id=sample_category.id,
        name="Item 1",
        description="Desc 1",
        item_type=ItemType.DIGITAL,
        price_besitos=10,
        created_by=1
    )
    await shop_container.shop.create_item(
        category_id=sample_category.id,
        name="Item 2",
        description="Desc 2",
        item_type=ItemType.DIGITAL,
        price_besitos=20,
        created_by=1
    )

    items = await shop_container.shop.get_items_by_category(sample_category.id)

    assert len(items) == 2


@pytest.mark.asyncio
async def test_update_item(shop_container, sample_item):
    """Test: Actualizar producto."""
    updated = await shop_container.shop.update_item(
        sample_item.id,
        price_besitos=75,
        is_featured=True
    )

    assert updated.price_besitos == 75
    assert updated.is_featured is True


@pytest.mark.asyncio
async def test_delete_item(shop_container, sample_item):
    """Test: Eliminar producto (soft delete)."""
    result = await shop_container.shop.delete_item(sample_item.id)

    assert result is True

    item = await shop_container.shop.get_item(sample_item.id)
    assert item.is_active is False


# ========================================
# TESTS DE COMPRA
# ========================================

@pytest.mark.asyncio
async def test_can_purchase(shop_container, sample_item, user_with_besitos):
    """Test: Verificar si usuario puede comprar."""
    can_buy, reason = await shop_container.shop.can_purchase(
        user_with_besitos,
        sample_item.id
    )

    assert can_buy is True
    assert reason == "OK"


@pytest.mark.asyncio
async def test_cannot_purchase_insufficient_besitos(shop_container, sample_category, session):
    """Test: No puede comprar sin besitos suficientes."""
    from bot.gamification.database.models import UserGamification
    from bot.database.models import User

    user_id = 99999

    # Crear usuario pobre
    user = User(user_id=user_id, username="poor_user")
    session.add(user)
    gamif = UserGamification(user_id=user_id, total_besitos=5)
    session.add(gamif)
    await session.commit()

    # Crear item caro
    success, _, item = await shop_container.shop.create_item(
        category_id=sample_category.id,
        name="Item Caro",
        description="Muy caro",
        item_type=ItemType.DIGITAL,
        price_besitos=1000,
        created_by=1
    )

    can_buy, reason = await shop_container.shop.can_purchase(user_id, item.id)

    assert can_buy is False
    assert "Besitos insuficientes" in reason


@pytest.mark.asyncio
async def test_purchase_item(shop_container, sample_item, user_with_besitos, session):
    """Test: Comprar producto exitosamente."""
    success, msg, purchase = await shop_container.shop.purchase_item(
        user_with_besitos,
        sample_item.id
    )

    assert success is True
    assert purchase is not None
    assert purchase.price_paid == 50
    assert purchase.status == PurchaseStatus.COMPLETED.value

    # Verificar que los besitos fueron deducidos
    from bot.gamification.database.models import UserGamification
    user_gamif = await session.get(UserGamification, user_with_besitos)
    assert user_gamif.total_besitos == 150  # 200 - 50


@pytest.mark.asyncio
async def test_purchase_adds_to_inventory(shop_container, sample_item, user_with_besitos):
    """Test: Compra agrega item al inventario."""
    await shop_container.shop.purchase_item(user_with_besitos, sample_item.id)

    has_item = await shop_container.inventory.has_item(user_with_besitos, sample_item.id)
    assert has_item is True

    quantity = await shop_container.inventory.get_item_quantity(
        user_with_besitos,
        sample_item.id
    )
    assert quantity == 1


# ========================================
# TESTS DE INVENTARIO
# ========================================

@pytest.mark.asyncio
async def test_get_inventory_items(shop_container, sample_item, user_with_besitos):
    """Test: Obtener items del inventario."""
    await shop_container.shop.purchase_item(user_with_besitos, sample_item.id)

    items = await shop_container.inventory.get_inventory_items(user_with_besitos)

    assert len(items) == 1
    assert items[0].item.name == "Llave Mágica"


@pytest.mark.asyncio
async def test_inventory_summary(shop_container, sample_item, user_with_besitos):
    """Test: Obtener resumen del inventario."""
    await shop_container.shop.purchase_item(user_with_besitos, sample_item.id)

    summary = await shop_container.inventory.get_inventory_summary(user_with_besitos)

    assert summary['total_items'] == 1
    assert summary['total_spent'] == 50


@pytest.mark.asyncio
async def test_has_item_by_slug(shop_container, sample_item, user_with_besitos):
    """Test: Verificar posesión por slug."""
    await shop_container.shop.purchase_item(user_with_besitos, sample_item.id)

    has = await shop_container.inventory.has_item_by_slug(
        user_with_besitos,
        sample_item.slug
    )
    assert has is True

    no_has = await shop_container.inventory.has_item_by_slug(
        user_with_besitos,
        "item-inexistente"
    )
    assert no_has is False


@pytest.mark.asyncio
async def test_grant_item(shop_container, sample_item, session):
    """Test: Otorgar item sin cobrar."""
    from bot.database.models import User

    user_id = 77777
    user = User(user_id=user_id, username="gift_receiver")
    session.add(user)
    await session.commit()

    success, msg = await shop_container.inventory.grant_item(
        user_id=user_id,
        item_id=sample_item.id,
        obtained_via="admin_grant"
    )

    assert success is True

    has = await shop_container.inventory.has_item(user_id, sample_item.id)
    assert has is True


# ========================================
# TESTS DE ITEMS CONSUMIBLES
# ========================================

@pytest.mark.asyncio
async def test_use_consumable_item(shop_container, sample_category, user_with_besitos, session):
    """Test: Usar item consumible."""
    import json

    # Crear consumible que otorga besitos
    success, _, item = await shop_container.shop.create_item(
        category_id=sample_category.id,
        name="Poción de Besitos",
        description="Otorga 25 besitos extra",
        item_type=ItemType.CONSUMABLE,
        price_besitos=10,
        icon="🧪",
        metadata={"effect_type": "besitos_boost", "effect_value": 25},
        created_by=1
    )

    # Comprar item
    await shop_container.shop.purchase_item(user_with_besitos, item.id)

    # Usar item
    success, msg, effect = await shop_container.inventory.use_item(
        user_with_besitos,
        item.id
    )

    assert success is True
    assert effect.get("applied") is True
    assert effect.get("besitos_granted") == 25


@pytest.mark.asyncio
async def test_cannot_use_non_consumable(shop_container, sample_item, user_with_besitos):
    """Test: No se puede usar item que no es consumible."""
    await shop_container.shop.purchase_item(user_with_besitos, sample_item.id)

    success, msg, _ = await shop_container.inventory.use_item(
        user_with_besitos,
        sample_item.id
    )

    assert success is False
    assert "no es consumible" in msg


# ========================================
# TESTS DE COSMÉTICOS
# ========================================

@pytest.mark.asyncio
async def test_equip_cosmetic_item(shop_container, sample_category, user_with_besitos):
    """Test: Equipar item cosmético."""
    success, _, item = await shop_container.shop.create_item(
        category_id=sample_category.id,
        name="Título Especial",
        description="Un título único",
        item_type=ItemType.COSMETIC,
        price_besitos=30,
        icon="👑",
        created_by=1
    )

    await shop_container.shop.purchase_item(user_with_besitos, item.id)

    success, msg = await shop_container.inventory.equip_item(user_with_besitos, item.id)
    assert success is True

    # Verificar que está equipado
    inv_items = await shop_container.inventory.get_inventory_items(
        user_with_besitos,
        equipped_only=True
    )
    assert len(inv_items) == 1


@pytest.mark.asyncio
async def test_unequip_cosmetic_item(shop_container, sample_category, user_with_besitos):
    """Test: Desequipar item cosmético."""
    success, _, item = await shop_container.shop.create_item(
        category_id=sample_category.id,
        name="Título Para Quitar",
        description="Se equipará y desequipará",
        item_type=ItemType.COSMETIC,
        price_besitos=30,
        icon="🎭",
        created_by=1
    )

    await shop_container.shop.purchase_item(user_with_besitos, item.id)
    await shop_container.inventory.equip_item(user_with_besitos, item.id)

    success, msg = await shop_container.inventory.unequip_item(user_with_besitos, item.id)
    assert success is True


# ========================================
# TESTS DE ESTADÍSTICAS
# ========================================

@pytest.mark.asyncio
async def test_item_stats(shop_container, sample_item, user_with_besitos):
    """Test: Obtener estadísticas de un item."""
    await shop_container.shop.purchase_item(user_with_besitos, sample_item.id)

    stats = await shop_container.shop.get_item_stats(sample_item.id)

    assert stats['total_sold'] == 1
    assert stats['unique_owners'] == 1
    assert stats['total_revenue'] == 50


@pytest.mark.asyncio
async def test_shop_summary(shop_container, sample_item, user_with_besitos):
    """Test: Obtener resumen de la tienda."""
    await shop_container.shop.purchase_item(user_with_besitos, sample_item.id)

    summary = await shop_container.shop.get_shop_summary()

    assert summary['total_purchases'] >= 1
    assert summary['total_revenue'] >= 50


# ========================================
# TESTS DE REEMBOLSO
# ========================================

@pytest.mark.asyncio
async def test_refund_purchase(shop_container, sample_item, user_with_besitos, session):
    """Test: Reembolsar una compra."""
    # Comprar
    success, msg, purchase = await shop_container.shop.purchase_item(
        user_with_besitos,
        sample_item.id
    )

    # Verificar besitos antes del reembolso
    from bot.gamification.database.models import UserGamification
    user_gamif = await session.get(UserGamification, user_with_besitos)
    assert user_gamif.total_besitos == 150

    # Reembolsar
    success, msg = await shop_container.shop.refund_purchase(
        purchase.id,
        reason="Prueba de reembolso"
    )

    assert success is True

    # Verificar besitos después del reembolso
    await session.refresh(user_gamif)
    assert user_gamif.total_besitos == 200  # Recuperó los 50


# ========================================
# TESTS DE STOCK
# ========================================

@pytest.mark.asyncio
async def test_limited_stock(shop_container, sample_category, user_with_besitos, session):
    """Test: Producto con stock limitado."""
    from bot.database.models import User
    from bot.gamification.database.models import UserGamification

    # Crear item con stock de 1
    success, _, item = await shop_container.shop.create_item(
        category_id=sample_category.id,
        name="Item Único",
        description="Solo hay uno",
        item_type=ItemType.NARRATIVE,
        price_besitos=25,
        stock=1,
        created_by=1
    )

    # Primera compra exitosa
    success1, _, _ = await shop_container.shop.purchase_item(user_with_besitos, item.id)
    assert success1 is True

    # Crear segundo usuario
    user2_id = 88888
    user2 = User(user_id=user2_id, username="second_buyer")
    session.add(user2)
    gamif2 = UserGamification(user_id=user2_id, total_besitos=100)
    session.add(gamif2)
    await session.commit()

    # Segunda compra falla por stock
    can_buy, reason = await shop_container.shop.can_purchase(user2_id, item.id)
    assert can_buy is False
    assert "Stock insuficiente" in reason


@pytest.mark.asyncio
async def test_max_per_user(shop_container, sample_category, user_with_besitos):
    """Test: Límite máximo por usuario."""
    success, _, item = await shop_container.shop.create_item(
        category_id=sample_category.id,
        name="Item Limitado",
        description="Máximo 1 por usuario",
        item_type=ItemType.DIGITAL,
        price_besitos=10,
        max_per_user=1,
        created_by=1
    )

    # Primera compra
    await shop_container.shop.purchase_item(user_with_besitos, item.id)

    # Segunda compra falla
    can_buy, reason = await shop_container.shop.can_purchase(user_with_besitos, item.id)
    assert can_buy is False
    assert "Máximo" in reason
