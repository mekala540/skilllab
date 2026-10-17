"""Money: an amount in one currency, kept as a Decimal.

Arithmetic keeps full precision. Call quantize() to round to the currency's minor unit;
invoices round each line, then add the lines.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Union

MINOR_UNITS = {"EUR": 2, "GBP": 2, "USD": 2, "INR": 2, "JPY": 0}
SYMBOLS = {"EUR": "€", "GBP": "£", "USD": "$", "INR": "₹", "JPY": "¥"}

Number = Union[int, str, Decimal]


class CurrencyMismatch(ValueError):
    """Two amounts in different currencies were combined."""


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str

    @classmethod
    def of(cls, value: Number, currency: str) -> "Money":
        if isinstance(value, float):
            raise TypeError("use a string or Decimal for money, not float")
        if currency not in MINOR_UNITS:
            raise ValueError(f"unknown currency {currency!r}")
        return cls(Decimal(value), currency)

    @classmethod
    def zero(cls, currency: str) -> "Money":
        return cls.of(0, currency)

    def quantize(self) -> "Money":
        step = Decimal(1).scaleb(-MINOR_UNITS[self.currency])
        return Money(self.amount.quantize(step, rounding=ROUND_HALF_EVEN), self.currency)

    def _check(self, other: "Money") -> None:
        if not isinstance(other, Money):
            raise TypeError(f"expected Money, got {type(other).__name__}")
        if other.currency != self.currency:
            raise CurrencyMismatch(f"{self.currency} vs {other.currency}")

    def __add__(self, other: "Money") -> "Money":
        self._check(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        self._check(other)
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor: Number) -> "Money":
        if isinstance(factor, float):
            raise TypeError("multiply money by an int, str or Decimal, not float")
        return Money(self.amount * Decimal(factor), self.currency)

    __rmul__ = __mul__

    def __neg__(self) -> "Money":
        return Money(-self.amount, self.currency)

    def __lt__(self, other: "Money") -> bool:
        self._check(other)
        return self.amount < other.amount

    def __le__(self, other: "Money") -> bool:
        self._check(other)
        return self.amount <= other.amount

    def is_zero(self) -> bool:
        return self.amount == 0

    def format(self, locale: str = "en") -> str:
        """'€1,234.50' (en) or '1.234,50 €' (de). Rounds for display only."""
        q = self.quantize()
        places = MINOR_UNITS[self.currency]
        sign = "-" if q.amount < 0 else ""
        text = f"{abs(q.amount):,.{places}f}"
        symbol = SYMBOLS[self.currency]
        if locale == "de":
            text = text.replace(",", "_").replace(".", ",").replace("_", ".")
            return f"{sign}{text} {symbol}"
        if locale != "en":
            raise ValueError(f"unsupported locale {locale!r}")
        return f"{sign}{symbol}{text}"


def total(items, currency: str) -> Money:
    """Sum of Money values (all in `currency`)."""
    out = Money.zero(currency)
    for m in items:
        out = out + m
    return out


def fmt(amount: Number, currency: str) -> str:
    """Deprecated since 2.3: use Money.format(). Kept until every caller is migrated."""
    warnings.warn("tally.money.fmt is deprecated; use Money.format()", DeprecationWarning, stacklevel=2)
    return Money.of(amount, currency).format("en")
