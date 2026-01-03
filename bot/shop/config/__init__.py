"""
Shop configuration module.

Contains configuration files for the shop system including
initial inventory, category mappings, and pricing rules.
"""

from bot.shop.config.initial_inventory import (
    CATEGORY_MAPPING,
    CATEGORY_DESCRIPTIONS,
    INITIAL_ITEMS,
    get_seed_data,
    validate_item,
)

__all__ = [
    "CATEGORY_MAPPING",
    "CATEGORY_DESCRIPTIONS",
    "INITIAL_ITEMS",
    "get_seed_data",
    "validate_item",
]
