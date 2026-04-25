# tax.py — Tax rate lookup and calculation
#
# L6 risk: callee contract mismatch — calculate_tax() calls
# get_tax_rate() and multiplies its return value by the subtotal,
# assuming the function always returns a float.  But get_tax_rate()
# returns None for unrecognised region codes, which the caller never
# checks, causing a TypeError at the multiplication site.

from __future__ import annotations
from typing import Optional, Dict


# Tax rates by ISO 3166-1 alpha-2 region code (simplified demo data)
_TAX_RATES: Dict[str, float] = {
    "US-CA": 0.0725,
    "US-NY": 0.08,
    "US-TX": 0.0625,
    "GB":    0.20,
    "DE":    0.19,
    "FR":    0.20,
}


def get_tax_rate(region_code: str) -> Optional[float]:
    """Return the applicable tax rate for a region, or None if unknown.

    Callers MUST check for None before using the return value.
    This contract is documented here but not enforced by type-checking
    in the calling module.
    """
    return _TAX_RATES.get(region_code)   # returns None for unknown codes


def calculate_tax(subtotal_cents: float, region_code: str) -> float:
    """Return the tax amount in cents for the given subtotal and region.

    BUG (L6): calls get_tax_rate() without checking the return value.
    When region_code is not in _TAX_RATES (e.g. "AU", "JP", or a typo
    like "USA"), get_tax_rate() returns None, and
        subtotal_cents * None
    raises TypeError.  The order flow crashes silently for any customer
    outside the hardcoded region list.
    """
    rate = get_tax_rate(region_code)
    # Missing guard: `if rate is None: return 0.0` (or raise a domain error)
    return subtotal_cents * rate          # BUG (L6): rate may be None


def format_tax_summary(subtotal_cents: float, region_code: str) -> str:
    """Return a human-readable tax line for the order summary."""
    tax = calculate_tax(subtotal_cents, region_code)
    rate = get_tax_rate(region_code)
    pct = f"{rate * 100:.2f}%" if rate is not None else "N/A"
    return f"Tax ({pct}): {tax / 100:.2f}"
