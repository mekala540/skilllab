"""Price quotes. Public API: quote(customer, items, day) -> dict, and reset()."""

PRICES = {"A100": 1250, "B200": 4999, "C300": 899, "D400": 15000, "E500": 300}
TIERS = ("basic", "gold", "platinum")
_state = {"counts": {}, "last_total": None}


def quote(customer, items, day):
    """customer: {"id": str, "tier": "basic" | "gold" | "platinum", "country": str}
    items: list of (sku, qty). day: 0-6, 0 = Monday. All money is in cents."""
    _validate(customer, items, day)
    lines = [_line(sku, qty) for sku, qty in items]
    subtotal = sum(line for _, _, line in lines)
    discount = _tier_discount(customer["tier"], subtotal, day)
    if _bump_loyalty(customer["id"]) % 5 == 0:
        discount += (subtotal - discount) * 5 // 100
    taxable = subtotal - discount
    tax = _tax(customer.get("country"), taxable)
    shipping = _shipping(customer["tier"], taxable, day)
    total = taxable + tax + shipping
    return {"lines": lines, "subtotal": subtotal, "discount": discount, "tax": tax,
            "shipping": shipping, "total": total, "same_as_last": _remember_total(total)}


def reset():
    """Forget loyalty counts and the last total."""
    _state["counts"].clear()
    _state["last_total"] = None


def _validate(customer, items, day):
    if not items:
        raise ValueError("empty order")
    if customer.get("tier") not in TIERS:
        raise ValueError("unknown tier: %s" % customer.get("tier"))
    if day < 0 or day > 6:
        raise ValueError("bad day: %d" % day)


def _line(sku, qty):
    # Validation happens item by item, in order, exactly like the original loop.
    if sku not in PRICES:
        raise KeyError("unknown sku: " + sku)
    if qty <= 0:
        raise ValueError("bad qty for %s: %d" % (sku, qty))
    price = PRICES[sku]
    if qty >= 10:
        price = price * 90 // 100
    elif qty >= 5:
        price = price * 95 // 100
    return (sku, qty, price * qty)


def _tier_discount(tier, subtotal, day):
    if tier == "gold":
        return subtotal * 5 // 100
    if tier == "platinum":
        weekend = subtotal * 2 // 100 if day in (5, 6) else 0
        return subtotal * 10 // 100 + weekend
    return 0


def _bump_loyalty(customer_id):
    counts = _state["counts"]
    counts[customer_id] = counts.get(customer_id, 0) + 1
    return counts[customer_id]


def _tax(country, taxable):
    if country == "US":
        return taxable * 7 // 100
    if country in ("DE", "FR"):
        return taxable * 20 // 100
    return 0


def _shipping(tier, taxable, day):
    if taxable >= 20000 or tier == "platinum":
        return 0
    return 499 if day == 0 else 999


def _remember_total(total):
    repeat = _state["last_total"] is not None and _state["last_total"] == total
    _state["last_total"] = total
    return repeat
