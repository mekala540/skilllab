"""Regenerate the sample data in data/ (deterministic). Run from the project root:

    python3 scripts/make_data.py
"""

import json
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

PRODUCTS = [
    ("BK-1001", "Field Guide to Ferns", "18.50", "reduced", 420),
    ("BK-1002", "Pocket Atlas", "12.00", "reduced", 260),
    ("BK-1003", "Cooking with Fire", "29.90", "reduced", 980),
    ("CF-2001", "Single-origin Beans 250g", "9.75", "reduced", 250),
    ("CF-2002", "Espresso Blend 1kg", "31.40", "reduced", 1000),
    ("HW-3001", "Enamel Mug", "14.99", "standard", 380),
    ("HW-3002", "Pour-over Kettle", "54.00", "standard", 1150),
    ("HW-3003", "Ceramic Dripper", "23.33", "standard", 450),
    ("HW-3004", "Burr Grinder", "129.00", "standard", 2300),
    ("TX-4001", "Linen Apron", "38.00", "standard", 300),
    ("TX-4002", "Tea Towel Set", "16.67", "standard", 210),
    ("GC-5001", "Gift Card 25", "25.00", "zero", 10),
    ("GC-5002", "Gift Card 50", "50.00", "zero", 10),
    ("ST-6001", "Notebook A5", "7.45", "standard", 180),
    ("ST-6002", "Fountain Pen", "45.10", "standard", 60),
]
FIRST = ["Ada", "Bram", "Chiara", "Dev", "Elif", "Femi", "Greta", "Hiro", "Ines", "Jonas", "Kavya", "Lior",
         "Mara", "Niko", "Oona", "Pavel", "Quinn", "Rosa", "Sven", "Tara", "Uma", "Viggo", "Wen", "Yara"]
LAST = ["Okafor", "Visser", "Rossi", "Sharma", "Kaya", "Adeyemi", "Lund", "Tanaka", "Moreau", "Becker",
        "Iyer", "Levi", "Novak", "Laine", "Koski", "Petrov", "Byrne", "Silva", "Berg", "Nair", "Rao", "Holm",
        "Zhou", "Haddad"]
COUNTRIES = ["DE", "DE", "DE", "FR", "FR", "NL", "NL", "GB", "IN", "JP", "US", "DE"]
TIERS = ["standard"] * 6 + ["silver"] * 3 + ["gold"]


def main():
    rng = random.Random(20260301)
    catalog = [{"sku": s, "name": n, "price": p, "currency": "EUR", "tax_class": t, "weight_g": w}
               for s, n, p, t, w in PRODUCTS]
    customers = []
    for i, (first, last) in enumerate(zip(FIRST, LAST), start=1):
        customers.append({"id": f"C{i:04d}", "name": f"{first} {last}",
                          "email": f"{first.lower()}.{last.lower()}@example.com",
                          "country": COUNTRIES[i % len(COUNTRIES)], "tier": TIERS[i % len(TIERS)],
                          "currency": "EUR"})
    start = datetime(2026, 2, 1, tzinfo=timezone.utc)
    orders = []
    for i in range(1, 421):
        cust = rng.choice(customers)
        created = start + timedelta(minutes=rng.randrange(0, 59 * 24 * 60))
        lines = []
        for sku, _, price, _, _ in rng.sample(PRODUCTS, rng.choice([1, 1, 2, 2, 3, 4])):
            qty = rng.choice([1, 1, 1, 2, 2, 3, 5, 12, 25, 60, 120])
            lines.append({"sku": sku, "qty": qty, "unit_price": price, "currency": "EUR"})
        status = rng.choice(["paid"] * 7 + ["open"] * 2 + ["cancelled"])
        coupon = rng.choice([None] * 8 + ["WELCOME10", "SPRING15"])
        orders.append({"id": f"O{i:05d}", "customer_id": cust["id"],
                       "created_at": created.strftime("%Y-%m-%dT%H:%M:%SZ"), "status": status,
                       "coupon": coupon, "lines": lines})
    levels = {s: {"on_hand": rng.randrange(0, 400), "reserved": 0} for s, *_ in PRODUCTS}
    for sku in ("HW-3004", "ST-6002", "CF-2002"):
        levels[sku]["on_hand"] = rng.randrange(2, 9)

    DATA.mkdir(exist_ok=True)
    for name, payload in (("catalog", {"version": 1, "products": catalog}),
                          ("customers", {"version": 1, "customers": customers}),
                          ("orders", {"version": 1, "orders": orders}),
                          ("inventory", {"version": 1, "levels": levels})):
        (DATA / f"{name}.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {len(catalog)} products, {len(customers)} customers, {len(orders)} orders")


if __name__ == "__main__":
    main()
