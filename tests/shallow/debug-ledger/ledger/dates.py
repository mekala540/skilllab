"""Date helpers."""

from datetime import date, datetime


def parse_date(text):
    """Accept '2024-03-31' or US style '03/31/2024'."""
    text = text.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"unrecognised date: {text!r}")


def month_range(year, month):
    """Return (first_day, last_day) of the month, both inclusive."""
    start = date(year, month, 1)
    try:
        end = date(year, month, 31)
    except ValueError:
        end = date(year, month, 28)
    return start, end
