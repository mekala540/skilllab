def process_order(order):
    """Return the amount to charge for `order`, in cents.

    order = {"items": [{"price": cents, "qty": n, "category": str}],
             "coupon": str or None, "country": str, "member": bool}
    """
    total = 0
    for item in order["items"]:
        if item["qty"] <= 0:
            raise ValueError("qty must be positive")
        line = item["price"] * item["qty"]
        if item["category"] == "books":
            if item["qty"] >= 3:
                line = line * 90 // 100
        elif item["category"] == "electronics":
            if order.get("member"):
                line = line * 95 // 100
        total += line
    coupon = order.get("coupon")
    if coupon:
        if coupon == "SAVE10":
            if total >= 5000:
                total = total - 1000
        elif coupon == "HALF":
            total = total // 2
        else:
            raise ValueError("unknown coupon")
    if order["country"] == "US":
        if total >= 10000:
            shipping = 0
        else:
            shipping = 799
        tax = total * 8 // 100
    elif order["country"] == "CA":
        shipping = 1299
        tax = total * 13 // 100
    else:
        shipping = 2499
        tax = 0
    if order.get("member"):
        if shipping > 0:
            shipping = shipping // 2
    return total + tax + shipping
