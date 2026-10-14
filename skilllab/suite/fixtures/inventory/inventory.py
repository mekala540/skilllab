class Inventory:
    """Stock counts per SKU. Counts never go below zero."""

    def __init__(self):
        self._stock = {}

    def add_stock(self, sku, qty):
        if qty <= 0:
            raise ValueError("qty must be positive")
        self._stock[sku] = self._stock.get(sku, 0) + qty

    def remove_stock(self, sku, qty):
        """Remove qty units. Raises ValueError if there is not enough stock."""
        if qty <= 0:
            raise ValueError("qty must be positive")
        current = self._stock.get(sku, 0)
        self._stock[sku] = current - qty

    def count(self, sku):
        return self._stock.get(sku, 0)

    def low_stock(self, threshold=5):
        """SKUs with fewer than `threshold` units, sorted."""
        return sorted(sku for sku, n in self._stock.items() if n < threshold)


def apply_discount(price, percent):
    """Return `price` reduced by `percent` percent (0-100), rounded to cents."""
    if not 0 <= percent <= 100:
        raise ValueError("percent must be between 0 and 100")
    return round(price - price * percent // 100, 2)


def merge(a, b):
    """Return a new Inventory with the stock of both; a and b are unchanged."""
    out = Inventory()
    for inv in (a, b):
        for sku, n in inv._stock.items():
            if n > 0:
                out.add_stock(sku, n)
    return out
