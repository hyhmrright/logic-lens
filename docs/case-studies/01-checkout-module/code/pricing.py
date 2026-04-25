# pricing.py — Coupon validation and final price computation
#
# L1 risk: shadow override — module-level `format` function shadows
# Python's builtin format(), causing a runtime AttributeError when
# _format_discount_line() is called with a plain float.

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import datetime


@dataclass
class Coupon:
    code: str
    discount_pct: float
    expires_at: datetime.date
    single_use: bool
    used: bool = False


# ------------------------------------------------------------------
# Module-level helper — name intentionally collides with builtin
# ------------------------------------------------------------------

def format(coupon: Coupon) -> str:               # BUG (L1): shadows builtin format()
    """Return a human-readable coupon summary for receipts."""
    status = "USED" if coupon.used else "VALID"
    return f"{coupon.code} ({coupon.discount_pct:.1f}% off) [{status}]"


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def validate_coupon(coupon: Coupon, today: Optional[datetime.date] = None) -> bool:
    """Return True if the coupon can still be applied."""
    today = today or datetime.date.today()
    if coupon.used and coupon.single_use:
        return False
    if coupon.expires_at < today:
        return False
    return True


def apply_coupon(subtotal: float, coupon: Coupon) -> float:
    """Deduct coupon discount from subtotal (in cents)."""
    if not validate_coupon(coupon):
        return subtotal
    return subtotal * (1.0 - coupon.discount_pct / 100.0)


def _format_discount_line(discount_amount: float) -> str:
    """Format the discount amount for the order confirmation email.

    Intended to call builtin format() for zero-padding, e.g.:
        format(1500, '06d')  →  '001500'
    But because this module defines its own format() above, this call
    dispatches to the module-level format(coupon) which expects a
    Coupon object — raising AttributeError on a plain float.
    """
    # BUG (L1): resolves to module-level format(coupon), not builtin
    return "Discount: -" + format(discount_amount, "06d")
