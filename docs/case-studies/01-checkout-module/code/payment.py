# payment.py — Payment gateway integration
#
# L5 risk: control-flow escape — the payment connection object acquired
# at the top of process_payment() is never closed on the exception path,
# leaking a TCP connection to the payment gateway on every failed charge.

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import uuid


@dataclass
class PaymentResult:
    transaction_id: str
    amount_charged: float   # cents
    success: bool
    error_message: Optional[str] = None


class GatewayConnection:
    """Simulates a stateful connection to an external payment gateway."""

    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint
        self._open = False

    def connect(self) -> None:
        self._open = True

    def charge(self, amount: float, card_token: str) -> dict:
        if not self._open:
            raise RuntimeError("Connection is not open")
        # Simulate a declined card for amounts over 1_000_000 cents ($10k)
        if amount > 1_000_000:
            raise ValueError(f"Amount {amount} exceeds single-transaction limit")
        return {"transaction_id": str(uuid.uuid4()), "status": "ok"}

    def close(self) -> None:
        self._open = False


GATEWAY_ENDPOINT = "https://payments.example.com/v2/charge"


def process_payment(amount: float, card_token: str) -> PaymentResult:
    """Charge the card and return a PaymentResult.

    Opens a GatewayConnection, charges the card, then closes the connection.
    """
    conn = GatewayConnection(GATEWAY_ENDPOINT)
    conn.connect()

    # BUG (L5): if conn.charge() raises, conn.close() is never called —
    # the connection object is abandoned with _open=True, leaking the
    # underlying TCP socket to the gateway.
    response = conn.charge(amount, card_token)
    conn.close()                          # only reached on happy path

    return PaymentResult(
        transaction_id=response["transaction_id"],
        amount_charged=amount,
        success=True,
    )
