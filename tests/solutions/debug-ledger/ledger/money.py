"""Money helpers. Amounts are Decimal; display values are rounded half up to cents."""

from decimal import ROUND_HALF_UP, Decimal


def parse_amount(text):
    """Parse '1,234.50', '-3.20', '$12.00' or accounting negatives '(45.00)' into a Decimal."""
    cleaned = text.strip().replace(",", "").replace("$", "")
    if cleaned.startswith("(") and cleaned.endswith(")"):
        return -Decimal(cleaned[1:-1])
    return Decimal(cleaned)


def format_amount(value):
    """Format with exactly two decimals, rounded half up: Decimal('2.675') -> '2.68'."""
    return str(Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
