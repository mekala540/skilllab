from datetime import datetime, timedelta

MONTHS = {n: i for i, n in enumerate(
    ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], 1)}
DAYS = {n: i for i, n in enumerate(["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"])}
FIELDS = [(0, 59, None), (0, 23, None), (1, 31, None), (1, 12, MONTHS), (0, 7, DAYS)]
MACROS = {"@yearly": "0 0 1 1 *", "@annually": "0 0 1 1 *", "@monthly": "0 0 1 * *",
          "@weekly": "0 0 * * 0", "@daily": "0 0 * * *", "@midnight": "0 0 * * *",
          "@hourly": "0 * * * *"}


def _value(token, lo, hi, names):
    t = token.upper()
    if names and t in names:
        return names[t]
    if not t.isdigit():
        raise ValueError(f"bad value: {token!r}")
    v = int(t)
    if not lo <= v <= hi:
        raise ValueError(f"out of range: {v}")
    return v


def _field(text, lo, hi, names):
    values = set()
    for item in text.split(","):
        base, slash, step_text = item.partition("/")
        if slash and (not step_text.isdigit() or int(step_text) == 0):
            raise ValueError(f"bad step: {item!r}")
        step = int(step_text) if slash else 1
        if base == "*":
            a, b = lo, hi
        elif "-" in base:
            a_text, b_text = base.split("-", 1)
            a, b = _value(a_text, lo, hi, names), _value(b_text, lo, hi, names)
            if a > b:
                raise ValueError(f"reversed range: {item!r}")
        else:
            a = _value(base, lo, hi, names)
            b = hi if slash else a
        values.update(range(a, b + 1, step))
    return values


def next_run(expr, after):
    """First datetime strictly after `after` matching cron expression `expr`. See SPEC.md."""
    expr = expr.strip()
    if expr.startswith("@"):
        if expr.lower() not in MACROS:
            raise ValueError(f"unknown macro: {expr}")
        expr = MACROS[expr.lower()]
    parts = expr.split()
    if len(parts) != 5:
        raise ValueError("expected 5 fields")
    minutes, hours, doms, months, dows = [_field(p, *f) for p, f in zip(parts, FIELDS)]
    dows = {0 if d == 7 else d for d in dows}
    either = not parts[2].startswith("*") and not parts[4].startswith("*")

    def day_ok(day):
        dom, dow = day.day in doms, (day.isoweekday() % 7) in dows
        return (dom or dow) if either else (dom and dow)

    start = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
    day, last_day = start.date(), (after + timedelta(days=5 * 366)).date()
    while day <= last_day:
        if day.month in months and day_ok(day):
            first = day == start.date()
            for h in sorted(hours):
                if first and h < start.hour:
                    continue
                for m in sorted(minutes):
                    if first and h == start.hour and m < start.minute:
                        continue
                    return datetime(day.year, day.month, day.day, h, m)
        day += timedelta(days=1)
    raise ValueError("no matching time within 5 years")
