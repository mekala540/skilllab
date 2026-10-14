"""Price quotes. Public API: quote(customer, items, day) -> dict, and reset()."""

PRICES = {"A100": 1250, "B200": 4999, "C300": 899, "D400": 15000, "E500": 300}
_quote_counts = {}
_last_total = None


def quote(customer, items, day):
    """customer: {"id": str, "tier": "basic" | "gold" | "platinum", "country": str}
    items: list of (sku, qty). day: 0-6, 0 = Monday. All money is in cents."""
    global _last_total
    if not items:
        raise ValueError("empty order")
    if customer.get("tier") not in ("basic", "gold", "platinum"):
        raise ValueError("unknown tier: %s" % customer.get("tier"))
    if day < 0 or day > 6:
        raise ValueError("bad day: %d" % day)
    subtotal = 0
    lines = []
    for sku, qty in items:
        if sku not in PRICES:
            raise KeyError("unknown sku: " + sku)
        if qty <= 0:
            raise ValueError("bad qty for %s: %d" % (sku, qty))
        price = PRICES[sku]
        if qty >= 10:
            price = price * 90 // 100
        elif qty >= 5:
            price = price * 95 // 100
        line = price * qty
        lines.append((sku, qty, line))
        subtotal += line
    discount = 0
    if customer["tier"] == "gold":
        discount = subtotal * 5 // 100
    elif customer["tier"] == "platinum":
        discount = subtotal * 10 // 100
        if day in (5, 6):
            discount = discount + subtotal * 2 // 100
    cid = customer["id"]
    if cid in _quote_counts:
        _quote_counts[cid] = _quote_counts[cid] + 1
    else:
        _quote_counts[cid] = 1
    if _quote_counts[cid] % 5 == 0:
        discount = discount + (subtotal - discount) * 5 // 100
    taxable = subtotal - discount
    if customer.get("country") == "US":
        tax = taxable * 7 // 100
    elif customer.get("country") in ("DE", "FR"):
        tax = taxable * 20 // 100
    else:
        tax = 0
    if taxable >= 20000:
        shipping = 0
    elif customer["tier"] == "platinum":
        shipping = 0
    else:
        shipping = 999
        if day == 0:
            shipping = 499
    total = taxable + tax + shipping
    repeat = _last_total is not None and _last_total == total
    _last_total = total
    return {"lines": lines, "subtotal": subtotal, "discount": discount, "tax": tax,
            "shipping": shipping, "total": total, "same_as_last": repeat}


def reset():
    """Forget loyalty counts and the last total."""
    global _last_total
    _quote_counts.clear()
    _last_total = None
