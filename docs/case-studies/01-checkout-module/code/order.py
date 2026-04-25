# order.py — Order creation and address validation
#
# L2 risk: type contract breach — build_shipping_label() calls
# address.upper() assuming `address` is always a str, but
# get_shipping_address() returns None when the customer profile
# has no address on file, flowing None into str.upper().

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import uuid


@dataclass
class Order:
    order_id: str
    customer_id: str
    total_cents: float
    shipping_address: Optional[str]  # None when address not yet confirmed
    status: str = "pending"


@dataclass
class CustomerProfile:
    customer_id: str
    name: str
    email: str
    saved_address: Optional[str] = None   # None if not set in profile


def get_shipping_address(profile: CustomerProfile) -> Optional[str]:
    """Return the saved shipping address, or None if not on file."""
    return profile.saved_address          # can legitimately return None


def build_shipping_label(profile: CustomerProfile) -> str:
    """Format the shipping label string for the warehouse system.

    Assumes get_shipping_address() always returns a non-None str.
    """
    address = get_shipping_address(profile)
    # BUG (L2): address is Optional[str] — .upper() raises AttributeError
    # when saved_address is None (guest checkout, new account, etc.)
    return f"SHIP TO: {address.upper()}"


def create_order(
    customer_id: str,
    total_cents: float,
    profile: CustomerProfile,
) -> Order:
    """Create a new order record."""
    return Order(
        order_id=str(uuid.uuid4()),
        customer_id=customer_id,
        total_cents=total_cents,
        shipping_address=profile.saved_address,
    )


def confirm_order(order: Order) -> Order:
    """Transition order from pending to confirmed."""
    order.status = "confirmed"
    return order
