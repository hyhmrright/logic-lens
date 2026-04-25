# notifications.py — Post-purchase email and SMS dispatch
#
# No primary L-code bug here; this module is intentionally clean to
# show that Logic Health correctly assigns a high per-module score when
# no confirmed findings exist.  It also demonstrates realistic
# supporting code that a checkout module would have.

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class NotificationPayload:
    recipient_email: str
    subject: str
    body: str
    sms_number: Optional[str] = None


def send_order_confirmation(
    order_id: str,
    customer_email: str,
    total_cents: float,
    sms_number: Optional[str] = None,
) -> bool:
    """Dispatch order confirmation via email (and optionally SMS).

    Returns True if the email was queued successfully, False on failure.
    """
    subject = f"Your order {order_id} is confirmed"
    body = (
        f"Thank you for your purchase!\n\n"
        f"Order ID: {order_id}\n"
        f"Total charged: ${total_cents / 100:.2f}\n\n"
        f"You will receive a shipping notification once your order is packed."
    )

    payload = NotificationPayload(
        recipient_email=customer_email,
        subject=subject,
        body=body,
        sms_number=sms_number,
    )

    return _dispatch(payload)


def send_payment_failure(customer_email: str, error_message: str) -> bool:
    """Notify customer that their payment could not be processed."""
    subject = "Action required: payment not processed"
    body = (
        f"We were unable to process your payment.\n\n"
        f"Reason: {error_message}\n\n"
        f"Please update your payment method and try again."
    )
    payload = NotificationPayload(
        recipient_email=customer_email,
        subject=subject,
        body=body,
    )
    return _dispatch(payload)


def _dispatch(payload: NotificationPayload) -> bool:
    """Internal: deliver the notification payload.

    In production this would call an email/SMS service SDK.
    Logging is used here as a stand-in.
    """
    try:
        logger.info(
            "Dispatching notification to %s: %s",
            payload.recipient_email,
            payload.subject,
        )
        if payload.sms_number:
            logger.info("SMS to %s: %s", payload.sms_number, payload.subject)
        return True
    except Exception as exc:
        logger.error("Notification dispatch failed: %s", exc)
        return False
