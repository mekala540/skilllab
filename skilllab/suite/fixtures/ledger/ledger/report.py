"""Monthly reports."""

from decimal import Decimal

from .dates import month_range
from .money import format_amount


def monthly_report(transactions, year, month):
    """Totals for one calendar month.

    Returns {"income": str, "expenses": str, "net": str, "count": int}. Expenses are
    reported as a positive number; net = income - expenses.
    """
    start, end = month_range(year, month)
    rows = [t for t in transactions if start <= t["date"] <= end]
    income = sum((t["amount"] for t in rows if t["amount"] > 0), Decimal(0))
    expenses = sum((-t["amount"] for t in rows if t["amount"] < 0), Decimal(0))
    return {
        "income": format_amount(income),
        "expenses": format_amount(expenses),
        "net": format_amount(income - expenses),
        "count": len(rows),
    }
