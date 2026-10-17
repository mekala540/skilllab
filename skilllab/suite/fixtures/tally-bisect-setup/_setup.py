"""Build a 40-commit history on main. One commit, in the middle, quietly breaks the volume
discount at exactly 20, 50 and 100 units while tidying the discount tables."""

import os
import subprocess
from pathlib import Path

ENV = dict(os.environ, GIT_AUTHOR_NAME="Tally Dev", GIT_AUTHOR_EMAIL="dev@tally.example",
           GIT_COMMITTER_NAME="Tally Dev", GIT_COMMITTER_EMAIL="dev@tally.example")
N = [0]


def git(*args):
    N[0] += 1
    date = f"2026-03-{1 + N[0] // 6:02d}T{8 + N[0] % 6:02d}:15:00+00:00"
    env = dict(ENV, GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
    subprocess.run(["git", *args], check=True, env=env, capture_output=True)


def edit(path, old, new):
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    assert old in text, (path, old)
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


def append(path, text):
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(text)


def commit(msg):
    git("add", "-A")
    git("commit", "-q", "-m", msg)


git("init", "-q")
git("checkout", "-q", "-b", "main")
git("config", "user.name", "Tally Dev")
git("config", "user.email", "dev@tally.example")
Path(".git/info/exclude").write_text("/_*\n")
commit("tally 2.4.1")

STEPS = [
    ("Docs: mention the --data option in the README",
     lambda: edit("README.md", "## Test", "All commands take `--data FOLDER` (default `./data`).\n\n## Test")),
    ("Changelog: start 2.5.0", lambda: edit("CHANGELOG.md", "# Changelog\n", "# Changelog\n\n## 2.5.0 (unreleased)\n")),
    ("Inventory: restock atlases", lambda: edit("data/inventory.json", '"BK-1002": {\n      "on_hand": ', '"BK-1002": {\n      "on_hand": 1')),
    ("Text: document pad_columns alignment", lambda: edit("tally/utils/text.py", "Fixed-width table.", "Fixed-width table, two spaces between columns.")),
    ("Customers: explain the tier field", lambda: edit("tally/customers.py", '    tier: str = "standard"', '    tier: str = "standard"  # standard, silver or gold: see discounts.TIER_RATES')),
    ("Docs: storage section wording", lambda: edit("docs/architecture.md", "so a crash never leaves", "so a crash or full disk never leaves")),
    ("Tax: comment on zero-rated goods", lambda: edit("tally/tax.py", '"zero" is zero-rated.', '"zero" is zero-rated (gift cards).')),
    ("Tests: invoice for a US customer has no tax", lambda: append("tests/test_invoices.py", "\n\nclass USInvoiceTest(unittest.TestCase):\n    def test_no_tax(self):\n        inv = build_invoice(order(\"U1\", \"C4\", \"2026-03-01T10:00:00Z\", (\"HW-2\", 2, \"23.33\")), catalog(), customers())\n        self.assertEqual(inv.tax.amount, Decimal(\"0.00\"))\n")),
    ("CLI: clearer help for --tz", lambda: edit("tally/cli.py", 'help="UTC offset to group days by, e.g. +05:30"', 'help="UTC offset to group days by, e.g. +05:30 (default +00:00)"')),
    ("Inventory: guard ship() against negative quantities", lambda: edit("tally/inventory.py", '        lvl = self.level(sku)\n        if lvl.reserved < qty:', '        lvl = self.level(sku)\n        if qty <= 0:\n            raise ValueError("shipped quantity must be positive")\n        if lvl.reserved < qty:')),
    ("Changelog: ship() guard", lambda: edit("CHANGELOG.md", "## 2.5.0 (unreleased)\n", "## 2.5.0 (unreleased)\n- `Inventory.ship` rejects zero or negative quantities.\n")),
    ("Catalog: weight is in grams", lambda: edit("tally/catalog.py", "    weight_g: int = 0", "    weight_g: int = 0  # grams, for shipping quotes")),
    ("Reports: docstring for top_products", lambda: edit("tally/reports.py", '"""Best sellers by units, ties broken by SKU."""', '"""Best sellers by units sold (cancelled orders excluded), ties broken by SKU."""')),
    ("Data: new coffee prices", lambda: edit("data/catalog.json", '"price": "9.75"', '"price": "9.95"')),
    ("Docs: discounts section links the code", lambda: edit("docs/architecture.md", "capped at `MAX_DISCOUNT` (30%).", "capped at `MAX_DISCOUNT` (30%). See `tally/discounts.py`.")),
    ("Money: explain why floats are refused", lambda: edit("tally/money.py", '            raise TypeError("use a string or Decimal for money, not float")', '            # 0.1 + 0.2 != 0.3 in binary floating point; money must be exact.\n            raise TypeError("use a string or Decimal for money, not float")')),
    ("Tests: low stock threshold boundary", lambda: append("tests/test_store.py", "\n\nclass ThresholdTest(unittest.TestCase):\n    def test_exactly_threshold_is_not_low(self):\n        inv = Inventory()\n        inv.receive(\"A\", 10)\n        self.assertEqual(inv.low_stock(10), [])\n")),
    ("Orders: by_customer keeps date order", lambda: edit("tally/orders.py", "    def by_customer(self, customer_id: str) -> List[Order]:\n", "    def by_customer(self, customer_id: str) -> List[Order]:\n        \"\"\"A customer's orders, oldest first.\"\"\"\n")),
    ("README: example output", lambda: edit("README.md", "## Test", "Example: `python3 -m tally invoice O00007` prints a table of lines and a total.\n\n## Test")),
    ("Inventory: restock fountain pens", lambda: edit("data/inventory.json", '"ST-6002": {\n      "on_hand": ', '"ST-6002": {\n      "on_hand": 4')),
    ("Exports: name the columns in a constant", lambda: edit("tally/exports.py", 'EXPORT_DIR = "exports"', 'EXPORT_DIR = "exports"\nCUSTOMER_COLUMNS = ["id", "name", "email", "country", "orders", "units", "spend"]')),
    ("Exports: use CUSTOMER_COLUMNS", lambda: edit("tally/exports.py", 'return export_rows(rows, ["id", "name", "email", "country", "orders", "units", "spend"], filename, root)', 'return export_rows(rows, CUSTOMER_COLUMNS, filename, root)')),
    ("Dates: note that offsets are fixed, not zones", lambda: edit("tally/utils/dates.py", '"""Timestamps. Stored in UTC;', '"""Timestamps (no DST rules: offsets are fixed, not named zones). Stored in UTC;')),
    ("Discounts: tidy discount tables", None),  # the culprit
    ("Changelog: tier rates unchanged", lambda: edit("CHANGELOG.md", "## 2.5.0 (unreleased)\n", "## 2.5.0 (unreleased)\n- Discount tables reformatted; rates are unchanged.\n")),
    ("Tests: coupon codes ignore surrounding spaces", lambda: edit("tests/test_tax_and_discounts.py", '        self.assertEqual(discounts.line_rate("standard", 1, " welcome10 "), Decimal("0.10"))', '        self.assertEqual(discounts.line_rate("standard", 1, " welcome10 "), Decimal("0.10"))\n        self.assertEqual(discounts.line_rate("standard", 1, "spring15"), Decimal("0.15"))')),
    ("CLI: mention export in the module docstring", lambda: edit("tally/cli.py", "  export customers FILE       CSV of customers and their spend", "  export customers FILE       CSV of customers and their spend (written to ./exports/)")),
    ("Data: fix a customer's email", lambda: edit("data/customers.json", "ada.okafor@example.com", "ada.okafor@example.org")),
    ("Reports: comment the grand total", lambda: edit("tally/reports.py", "        grand = sum(", "        # Sum of all days, in the report's currency.\n        grand = sum(")),
    ("Docs: errors section lists exit codes", lambda: edit("docs/architecture.md", "and exits 1.", "and exits 1. Success is 0; argparse errors are 2.")),
    ("Inventory: restock espresso blend", lambda: edit("data/inventory.json", '"CF-2002": {\n      "on_hand": ', '"CF-2002": {\n      "on_hand": 3')),
    ("Tax: Japan reduced rate comment", lambda: edit("tally/tax.py", '("JP", "reduced"): Decimal("0.08"),', '("JP", "reduced"): Decimal("0.08"),  # food and newspapers')),
    ("Money: JPY has no minor unit", lambda: edit("tally/money.py", 'MINOR_UNITS = {', '# Digits after the decimal point; yen has none.\nMINOR_UNITS = {')),
    ("Tests: German formatting of small amounts", lambda: edit("tests/test_money.py", '        self.assertEqual(Money.of("-3", "GBP").format(), "-£3.00")', '        self.assertEqual(Money.of("-3", "GBP").format(), "-£3.00")\n        self.assertEqual(Money.of("0.5", "EUR").format("de"), "0,50 €")')),
    ("Changelog: German formatting tests", lambda: edit("CHANGELOG.md", "## 2.5.0 (unreleased)\n", "## 2.5.0 (unreleased)\n- More tests for German number formatting.\n")),
    ("README: link the changelog", lambda: append("README.md", "\nRelease notes: `CHANGELOG.md`.\n")),
    ("Orders: comment on created_at", lambda: edit("tally/orders.py", "    created_at: str  # ISO 8601 in UTC", "    created_at: str  # when the customer placed it: ISO 8601 in UTC")),
    ("Data: price change for notebooks", lambda: edit("data/catalog.json", '"price": "7.45"', '"price": "7.65"')),
    ("Text: truncate keeps the ellipsis inside the width", lambda: edit("tally/utils/text.py", "def truncate(text: str, width: int) -> str:\n", "def truncate(text: str, width: int) -> str:\n    \"\"\"Cut to `width` characters, the last one an ellipsis if anything was cut.\"\"\"\n")),
]


def culprit():
    edit("tally/discounts.py",
         'VOLUME_RATES = [(100, Decimal("0.08")), (50, Decimal("0.05")), (20, Decimal("0.02"))]',
         'VOLUME_RATES = [\n    (100, Decimal("0.08")),\n    (50, Decimal("0.05")),\n    (20, Decimal("0.02")),\n]')
    edit("tally/discounts.py", "# (minimum quantity on one line, extra rate), highest threshold first.",
         "# (quantity threshold, extra rate), highest first.")
    edit("tally/discounts.py",
         "    for threshold, rate in VOLUME_RATES:\n        if qty >= threshold:\n            return rate",
         "    for threshold, extra in VOLUME_RATES:\n        if qty > threshold:\n            return extra")
    edit("tally/discounts.py", 'TIER_RATES = {"standard": Decimal("0"), "silver": Decimal("0.05"), "gold": Decimal("0.10")}',
         'TIER_RATES = {\n    "standard": Decimal("0"),\n    "silver": Decimal("0.05"),\n    "gold": Decimal("0.10"),\n}')


for msg, step in STEPS:
    (step or culprit)()
    commit(msg)
