"""
Servicios del módulo de Tienda.
"""

from bot.shop.services.shop import ShopService
from bot.shop.services.inventory import InventoryService
from bot.shop.services.discounts import DiscountService
from bot.shop.services.recommendations import RecommendationService
from bot.shop.services.container import ShopContainer, get_shop_container

__all__ = [
    "ShopService",
    "InventoryService",
    "DiscountService",
    "RecommendationService",
    "ShopContainer",
    "get_shop_container",
]
