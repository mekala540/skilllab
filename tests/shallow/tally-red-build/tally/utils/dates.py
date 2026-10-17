"""Timestamps. Stored in UTC; shown and grouped in a fixed UTC offset such as +05:30."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone

OFFSET = re.compile(r"^([+-])(\d{2}):(\d{2})$")


def parse_iso(text: str) -> datetime:
    """Parse '2026-03-01T23:30:00Z' (or with +00:00) into an aware UTC datetime."""
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        raise ValueError(f"timestamp without a time zone: {text!r}")
    return dt.astimezone(timezone.utc)


def parse_offset(text: str) -> timezone:
    m = OFFSET.match(text)
    if not m:
        raise ValueError(f"bad UTC offset {text!r}, expected e.g. +05:30")
    sign, hours, minutes = m.groups()
    delta = timedelta(hours=int(hours), minutes=int(minutes))
    if delta > timedelta(hours=14):
        raise ValueError(f"UTC offset out of range: {text!r}")
    return timezone(-delta if sign == "-" else delta)


def to_local(dt: datetime, offset: str) -> datetime:
    return dt.astimezone(parse_offset(offset))


def local_date(text: str, offset: str = "+00:00") -> date:
    """The calendar date of a stored UTC timestamp, as seen in `offset`."""
    return to_local(parse_iso(text), offset).date()


def format_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
