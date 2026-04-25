# inventory.py — Stock reservation and release
#
# L4 risk: state mutation hazard — reserve_items() iterates over
# self._stock while potentially modifying a shared alias.  More
# concretely, release_reservation() mutates the same dict that an
# in-flight reserve_items() call is reading, causing silent
# double-release when called concurrently (e.g., two async request
# handlers sharing one Inventory instance).

from __future__ import annotations
from typing import Dict, List
from cart import CartItem


class InsufficientStockError(Exception):
    pass


class Inventory:
    """In-process inventory store. Not thread-safe by design (demo only)."""

    def __init__(self, stock: Dict[str, int]) -> None:
        # BUG (L4): _stock is the live dict; callers who hold a reference
        # to the original dict passed in share the same mutable object.
        self._stock = stock
        self._reserved: Dict[str, int] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def available(self, sku: str) -> int:
        """Return units currently available (stock minus reserved)."""
        return self._stock.get(sku, 0) - self._reserved.get(sku, 0)

    def reserve_items(self, items: List[CartItem]) -> None:
        """Reserve all items atomically; raise if any SKU is short.

        Iterates over items twice: first to check availability, then to
        commit reservations.  If release_reservation() is called between
        the check pass and the commit pass (concurrent requests), the
        check result is stale and a negative reservation can be committed.
        """
        # Pass 1: validate
        for item in items:
            if self.available(item.sku) < item.quantity:
                raise InsufficientStockError(
                    f"SKU {item.sku}: need {item.quantity}, "
                    f"have {self.available(item.sku)}"
                )
        # Pass 2: commit  ← BUG (L4): state can change between passes
        for item in items:
            self._reserved[item.sku] = (
                self._reserved.get(item.sku, 0) + item.quantity
            )

    def release_reservation(self, items: List[CartItem]) -> None:
        """Release a previously committed reservation."""
        for item in items:
            current = self._reserved.get(item.sku, 0)
            # BUG (L4): no floor guard — can go negative on double-release
            self._reserved[item.sku] = current - item.quantity

    def commit_sale(self, items: List[CartItem]) -> None:
        """Deduct reserved units from stock and clear reservation."""
        for item in items:
            self._stock[item.sku] = self._stock.get(item.sku, 0) - item.quantity
            self._reserved[item.sku] = (
                max(0, self._reserved.get(item.sku, 0) - item.quantity)
            )
