"""Discount rules: customer tier, volume per line, and coupons, with an overall cap."""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

TIER_RATES = {"standard": Decimal("0"), "silver": Decimal("0.05"), "gold": Decimal("0.10")}
# (minimum quantity on one line, extra rate), highest threshold first.
VOLUME_RATES = [(100, Decimal("0.08")), (50, Decimal("0.05")), (20, Decimal("0.02"))]
COUPONS = {"WELCOME10": Decimal("0.10"), "SPRING15": Decimal("0.15"), "STAFF25": Decimal("0.25")}
# No line is ever discounted by more than this, however the rules combine.
MAX_DISCOUNT = Decimal("0.30")


class UnknownCoupon(KeyError):
    pass


def volume_rate(qty: int) -> Decimal:
    for threshold, rate in VOLUME_RATES:
        if qty >= threshold:
            return rate
    return Decimal("0")


def coupon_rate(code: Optional[str]) -> Decimal:
    if not code:
        return Decimal("0")
    try:
        return COUPONS[code.strip().upper()]
    except KeyError:
        raise UnknownCoupon(code) from None


def line_rate(tier: str, qty: int, coupon: Optional[str] = None) -> Decimal:
    """Total discount rate for one order line, capped at MAX_DISCOUNT."""
    if tier not in TIER_RATES:
        raise ValueError(f"unknown customer tier {tier!r}")
    rate = TIER_RATES[tier] + volume_rate(qty) + coupon_rate(coupon)
    return min(rate, MAX_DISCOUNT)
