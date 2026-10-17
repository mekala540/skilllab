"""VAT / GST rates by country and tax class."""

from __future__ import annotations

from decimal import Decimal

from .money import Money

# (country, tax class) -> rate. "reduced" covers food and books, "zero" is zero-rated.
RATES = {
    ("DE", "standard"): Decimal("0.19"), ("DE", "reduced"): Decimal("0.07"),
    ("FR", "standard"): Decimal("0.20"), ("FR", "reduced"): Decimal("0.055"),
    ("NL", "standard"): Decimal("0.21"), ("NL", "reduced"): Decimal("0.09"),
    ("GB", "standard"): Decimal("0.20"), ("GB", "reduced"): Decimal("0.05"),
    ("IN", "standard"): Decimal("0.18"), ("IN", "reduced"): Decimal("0.05"),
    ("JP", "standard"): Decimal("0.10"), ("JP", "reduced"): Decimal("0.08"),
    ("US", "standard"): Decimal("0"), ("US", "reduced"): Decimal("0"),
}
TAX_CLASSES = ("standard", "reduced", "zero")


class UnknownTaxRate(KeyError):
    pass


def rate_for(country: str, tax_class: str) -> Decimal:
    if tax_class not in TAX_CLASSES:
        raise UnknownTaxRate(f"unknown tax class {tax_class!r}")
    if tax_class == "zero":
        if not any(c == country for c, _ in RATES):
            raise UnknownTaxRate(f"no tax rates for country {country!r}")
        return Decimal("0")
    try:
        return RATES[(country, tax_class)]
    except KeyError:
        raise UnknownTaxRate(f"no {tax_class} rate for country {country!r}") from None


def tax_on(net: Money, country: str, tax_class: str) -> Money:
    """Tax on a net amount, rounded to the currency's minor unit."""
    return (net * rate_for(country, tax_class)).quantize()
