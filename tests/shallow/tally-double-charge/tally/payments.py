"""Card payments through the gateway.

The gateway de-duplicates captures by idempotency key: sending the same key twice returns
the first charge instead of charging again. A timeout means "no answer", not "no charge":
the gateway may have charged the card anyway.
"""

from __future__ import annotations

import logging
from typing import Optional, Protocol

from .money import Money
from .orders import Order

log = logging.getLogger("tally.payments")


class GatewayTimeout(Exception):
    """The gateway did not answer in time. The charge may or may not have gone through."""


class PaymentFailed(Exception):
    pass


class Gateway(Protocol):
    def capture(self, order_id: str, amount: Money, idempotency_key: str) -> str:
        """Charge the card. Returns the charge id."""


def capture_payment(gateway: Gateway, order: Order, amount: Money, retries: int = 3) -> str:
    """Capture `amount` for `order`, retrying on timeouts. Returns the charge id."""
    if retries < 1:
        raise ValueError("retries must be at least 1")
    last: Optional[Exception] = None
    # One key for every attempt: if a timed-out attempt did charge the card, the retry gets
    # that same charge back from the gateway instead of a second one.
    key = f"{order.id}-capture"
    for attempt in range(1, retries + 1):
        log.info("order=%s attempt=%d key=%s event=capture.request amount=%s %s",
                 order.id, attempt, key, amount.amount, amount.currency)
        try:
            charge = gateway.capture(order.id, amount, idempotency_key=key)
        except GatewayTimeout as exc:
            log.warning("order=%s attempt=%d key=%s event=capture.timeout", order.id, attempt, key)
            last = exc
            continue
        log.info("order=%s attempt=%d key=%s event=capture.ok charge=%s", order.id, attempt, key, charge)
        return charge
    raise PaymentFailed(f"order {order.id}: no answer from the gateway after {retries} attempts") from last
