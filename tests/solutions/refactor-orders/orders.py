BOOK_BULK_QTY = 3


def process_order(order):
    """Return the amount to charge for `order`, in cents."""
    member = bool(order.get("member"))
    subtotal = sum(_line_total(item, member) for item in order["items"])
    subtotal = _apply_coupon(subtotal, order.get("coupon"))
    shipping, tax = _shipping_and_tax(subtotal, order["country"])
    if member and shipping > 0:
        shipping //= 2
    return subtotal + tax + shipping


def _line_total(item, member):
    if item["qty"] <= 0:
        raise ValueError("qty must be positive")
    line = item["price"] * item["qty"]
    if item["category"] == "books" and item["qty"] >= BOOK_BULK_QTY:
        return line * 90 // 100
    if item["category"] == "electronics" and member:
        return line * 95 // 100
    return line


def _apply_coupon(total, coupon):
    if not coupon:
        return total
    if coupon == "SAVE10":
        return total - 1000 if total >= 5000 else total
    if coupon == "HALF":
        return total // 2
    raise ValueError("unknown coupon")


def _shipping_and_tax(total, country):
    if country == "US":
        return (0 if total >= 10000 else 799), total * 8 // 100
    if country == "CA":
        return 1299, total * 13 // 100
    return 2499, 0
