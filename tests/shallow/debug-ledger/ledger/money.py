"""Money helpers. Amounts are Decimal; display values are rounded half up to cents."""

from decimal import Decimal


def parse_amount(text):
    """Parse '1,234.50', '-3.20', '$12.00' or accounting negatives '(45.00)' into a Decimal."""
    cleaned = text.strip().replace(",", "").replace("$", "")
    if cleaned.startswith("("):
        return -Decimal(cleaned.strip("()"))
    return Decimal(cleaned)


def format_amount(value):
    """Format with exactly two decimals, rounded half up: Decimal('2.675') -> '2.68'."""
    return f"{round(float(value), 2):.2f}"
