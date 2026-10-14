import re
from fractions import Fraction

_PART = re.compile(r"\s*(\d+(?:\.\d+)?)\s*([hms])", re.I)
_SECONDS = {"h": 3600, "m": 60, "s": 1}


def parse_duration(text):
    """Parse a duration like "1h30m" into whole seconds. See SPEC.md."""
    s = text.strip()
    if not s:
        raise ValueError("empty duration")
    pos, last, total = 0, -1, Fraction(0)
    while pos < len(s):
        m = _PART.match(s, pos)
        if not m:
            raise ValueError(f"bad duration: {text!r}")
        unit = m.group(2).lower()
        rank = "hms".index(unit)
        if rank <= last:
            raise ValueError(f"repeated or out-of-order unit in {text!r}")
        last = rank
        total += Fraction(m.group(1)) * _SECONDS[unit]
        pos = m.end()
    if total.denominator != 1:
        raise ValueError(f"not a whole number of seconds: {text!r}")
    return int(total)
