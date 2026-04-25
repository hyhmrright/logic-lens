# checkout.py — Orchestration layer: runs the full checkout pipeline
#
# This module is clean of primary bugs; it orchestrates cart, pricing,
# inventory, order, tax, and payment.  Its logic is correct given the
# contracts it assumes from callees — which makes it the ideal place to
# observe L6 propagation: calculate_tax() is called here, and its None
# return (from tax.py's L6 bug) crashes exactly at the line that looks
# most innocuous.

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from cart import Cart
from inventory import Inventory, InsufficientStockError
from order import CustomerProfile, create_order, build_shipping_label
from payment import process_payment, PaymentResult
from pricing import apply_coupon, Coupon
from tax import calculate_tax


@dataclass
class CheckoutResult:
    success: bool
    order_id: Optional[str] = None
    transaction_id: Optional[str] = None
    total_charged_cents: float = 0.0
    error: Optional[str] = None


def run_checkout(
    cart: Cart,
    profile: CustomerProfile,
    card_token: str,
    region_code: str,
    coupon: Optional[Coupon] = None,
    inventory: Optional[Inventory] = None,
) -> CheckoutResult:
    """Execute the full checkout pipeline.

    Steps:
    1. Reserve inventory.
    2. Compute subtotal, apply coupon, compute tax, derive total.
    3. Charge the card.
    4. Create the order record.
    5. Return the result.

    On any failure, reserved inventory is released before returning.
    """
    if inventory is not None:
        try:
            inventory.reserve_items(cart.items)
        except InsufficientStockError as exc:
            return CheckoutResult(success=False, error=str(exc))

    try:
        subtotal = cart.subtotal()

        if coupon is not None:
            subtotal = apply_coupon(subtotal, coupon)

        # This line crashes for unknown region codes due to tax.py L6 bug:
        #   calculate_tax("AU", ...) → None * subtotal → TypeError
        tax = calculate_tax(subtotal, region_code)
        total = subtotal + tax

        payment_result: PaymentResult = process_payment(total, card_token)
        if not payment_result.success:
            raise RuntimeError(payment_result.error_message or "Payment failed")

        order = create_order(
            customer_id=cart.customer_id,
            total_cents=total,
            profile=profile,
        )

        return CheckoutResult(
            success=True,
            order_id=order.order_id,
            transaction_id=payment_result.transaction_id,
            total_charged_cents=total,
        )

    except Exception as exc:
        if inventory is not None:
            inventory.release_reservation(cart.items)
        return CheckoutResult(success=False, error=str(exc))
