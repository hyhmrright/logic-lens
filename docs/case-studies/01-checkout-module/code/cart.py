# cart.py — Shopping cart: add, remove, and compute totals
#
# L3 risk: boundary blindspot — average_item_price() divides by len(items)
# without a guard for the empty-cart case.

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class CartItem:
    sku: str
    name: str
    unit_price: float   # in cents
    quantity: int


@dataclass
class Cart:
    customer_id: str
    items: List[CartItem] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_item(self, item: CartItem) -> None:
        """Add an item, merging quantity if the SKU already exists."""
        for existing in self.items:
            if existing.sku == item.sku:
                existing.quantity += item.quantity
                return
        self.items.append(item)

    def remove_item(self, sku: str) -> None:
        """Remove all units of a SKU from the cart."""
        self.items = [i for i in self.items if i.sku != sku]

    def subtotal(self) -> float:
        """Return sum of unit_price * quantity for all items (in cents)."""
        return sum(i.unit_price * i.quantity for i in self.items)

    def item_count(self) -> int:
        """Return total number of individual units in the cart."""
        return sum(i.quantity for i in self.items)

    def average_item_price(self) -> float:
        """Return the mean unit price across all distinct SKUs.

        Used by the recommendation engine to bucket customers into
        'budget', 'mid-range', and 'premium' segments.
        """
        # BUG (L3): no guard for empty cart — ZeroDivisionError at runtime
        return sum(i.unit_price for i in self.items) / len(self.items)

    def apply_bulk_discount(self, threshold: int, discount_pct: float) -> float:
        """If item_count >= threshold, return subtotal after discount."""
        if self.item_count() >= threshold:
            return self.subtotal() * (1.0 - discount_pct / 100.0)
        return self.subtotal()
