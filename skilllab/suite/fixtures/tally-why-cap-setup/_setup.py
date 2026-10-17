"""History for tally-why-cap: when was the discount cap introduced, why, and when did its value
last change. Traps: a commit that only moves the line, a formatting commit that touches it,
and an unrelated commit that says 'cap'."""

import os
import subprocess
from pathlib import Path

ENV = dict(os.environ, GIT_AUTHOR_NAME="Tally Dev", GIT_AUTHOR_EMAIL="dev@tally.example",
           GIT_COMMITTER_NAME="Tally Dev", GIT_COMMITTER_EMAIL="dev@tally.example")
N = [0]

HEAD = '''"""Discount rules: customer tier, volume per line, and coupons{cap_doc}."""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

'''
TABLES = '''TIER_RATES = {{"standard": Decimal("0"), "silver": Decimal("0.05"), "gold": Decimal("0.10")}}
# (minimum quantity on one line, extra rate), highest threshold first.
VOLUME_RATES = [(100, Decimal("0.08")), (50, Decimal("0.05")), (20, Decimal("0.02"))]
COUPONS = {{"WELCOME10": Decimal("0.10"), "SPRING15": Decimal("0.15"){staff}}}
'''
CAP = '''# No line is ever discounted by more than this, however the rules combine.
MAX_DISCOUNT = Decimal("{value}"){comment}
'''
BODY = '''

class UnknownCoupon(KeyError):
    pass


def volume_rate(qty: int) -> Decimal:
    for threshold, rate in VOLUME_RATES:
        if qty >= threshold:
            return rate
    return Decimal("0")


def coupon_rate(code: Optional[str]) -> Decimal:
    if not code:
        return Decimal("0")
    try:
        return COUPONS[code.strip().upper()]
    except KeyError:
        raise UnknownCoupon(code) from None


def line_rate(tier: str, qty: int, coupon: Optional[str] = None) -> Decimal:
    """Total discount rate for one order line{cap_doc2}."""
    if tier not in TIER_RATES:
        raise ValueError(f"unknown customer tier {{tier!r}}")
    rate = TIER_RATES[tier] + volume_rate(qty) + coupon_rate(coupon)
    return {ret}
'''


def discounts(cap=None, staff=False, cap_first=False, comment=""):
    staff_s = ', "STAFF25": Decimal("0.25")' if staff else ""
    tables = TABLES.format(staff=staff_s)
    head = HEAD.format(cap_doc=", with an overall cap" if cap else "")
    body = BODY.format(cap_doc2=", capped at MAX_DISCOUNT" if cap else "",
                       ret="min(rate, MAX_DISCOUNT)" if cap else "rate")
    if not cap:
        return head + tables + body
    cap_s = CAP.format(value=cap, comment=comment)
    return head + (cap_s + tables if cap_first else tables + cap_s) + body


def git(*args, author=None):
    N[0] += 1
    date = f"2026-0{1 + N[0] // 12}-{1 + (N[0] * 2) % 27:02d}T{9 + N[0] % 8:02d}:40:00+00:00"
    env = dict(ENV, GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
    if author:
        env.update(GIT_AUTHOR_NAME=author[0], GIT_AUTHOR_EMAIL=author[1])
    subprocess.run(["git", *args], check=True, env=env, capture_output=True)


def write(path, text):
    Path(path).write_text(text, encoding="utf-8")


def edit(path, old, new):
    text = Path(path).read_text(encoding="utf-8")
    assert old in text, (path, old)
    write(path, text.replace(old, new, 1))


def commit(msg, author=None):
    git("add", "-A")
    git("commit", "-q", "-m", msg, author=author)


faq = Path("docs/pricing-faq.md").read_text(encoding="utf-8")
tests_full = Path("tests/test_tax_and_discounts.py").read_text(encoding="utf-8")
arch_full = Path("docs/architecture.md").read_text(encoding="utf-8")
log_full = Path("CHANGELOG.md").read_text(encoding="utf-8")
CAP_TEST = """
    def test_cap(self):
        self.assertEqual(discounts.line_rate("gold", 100, "STAFF25"), discounts.MAX_DISCOUNT)
"""
CAP_DOC = ", capped at `MAX_DISCOUNT` (30%)."
assert CAP_TEST in tests_full and CAP_DOC in arch_full
git("init", "-q")
git("checkout", "-q", "-b", "main")
git("config", "user.name", "Tally Dev")
git("config", "user.email", "dev@tally.example")
Path(".git/info/exclude").write_text("/_*\n")
write("tally/discounts.py", discounts())
os.remove("docs/pricing-faq.md")
# Release 2.2.0 had no cap: no cap test, no cap in the docs, no later changelog entries.
write("tests/test_tax_and_discounts.py", tests_full.replace(CAP_TEST, ""))
write("docs/architecture.md", arch_full.replace(CAP_DOC, "."))
write("CHANGELOG.md", "# Changelog\n\n" + log_full[log_full.index("## 2.2.0"):])
commit("tally 2.2.0")

PRIYA = ("Priya Nair", "priya@tally.example")
JONAS = ("Jonas Becker", "jonas@tally.example")
steps = [
    ("Add STAFF25 coupon for the staff shop", lambda: write("tally/discounts.py", discounts(staff=True)), JONAS),
    ("Cap report column width at 24 characters", lambda: edit("tally/utils/text.py", "def truncate(text: str, width: int) -> str:", "def truncate(text: str, width: int) -> str:  # reports cap names at 24 chars"), None),
    ("Docs: pricing FAQ for the sales team", lambda: write("docs/pricing-faq.md", faq.replace("up to the cap", "with no limit").replace("Yes, see `MAX_DISCOUNT` in `tally/discounts.py`. Ask\nengineering before promising anything above it.", "No. Ask engineering before promising big combined discounts.")), None),
    ("Cap combined discounts at 25%\n\nGold customers stacking SPRING15 with the 100+ volume rate were buying\nburr grinders below cost. No line is discounted by more than 25% now,\nhowever tier, volume and coupon rates combine.\n\nFixes #214",
     lambda: (write("tally/discounts.py", discounts(cap="0.25", staff=True)),
              write("tests/test_tax_and_discounts.py", tests_full),
              write("docs/architecture.md", arch_full.replace("(30%)", "(25%)"))), PRIYA),
    ("Docs: FAQ mentions the cap", lambda: write("docs/pricing-faq.md", faq.replace("Yes, see", "Yes (25%), see")), PRIYA),
    ("Inventory: restock gift cards", lambda: edit("data/inventory.json", '"GC-5001": {\n      "on_hand": ', '"GC-5001": {\n      "on_hand": 1'), None),
    ("Move discount constants above the tables", lambda: write("tally/discounts.py", discounts(cap="0.25", staff=True, cap_first=True)), JONAS),
    ("Reports: comment on cancelled orders", lambda: edit("tally/reports.py", "def top_products(", "# Cancelled orders never count towards sales figures.\ndef top_products("), None),
    ("Raise the discount cap to 30% for the spring campaign\n\nMarketing wants SPRING15 to stack with gold tier for bulk orders.\nFinance signed off on 30% (see #251).",
     lambda: (write("tally/discounts.py", discounts(cap="0.30", staff=True, cap_first=True)),
              write("docs/architecture.md", arch_full)), JONAS),
    ("Docs: FAQ cap is 30%", lambda: write("docs/pricing-faq.md", faq.replace("Yes, see", "Yes (30%), see")), None),
    ("Data: notebook price", lambda: edit("data/catalog.json", '"price": "7.45"', '"price": "7.55"'), None),
    ("Style: one constant per line, explain units", lambda: write("tally/discounts.py", discounts(cap="0.30", staff=True, cap_first=True, comment="  # a fraction: 0.30 = 30%")), PRIYA),
    ("Move the cap back below the tables", lambda: write("tally/discounts.py", discounts(cap="0.30", staff=True, comment="  # a fraction: 0.30 = 30%")), JONAS),
    ("Changelog for 2.3.0 to 2.4.1", lambda: write("CHANGELOG.md", log_full), None),
    ("Docs: link the pricing FAQ from the README", lambda: edit("README.md", "See `docs/architecture.md`", "Sales questions: `docs/pricing-faq.md`. See `docs/architecture.md`"), None),
]
for msg, step, author in steps:
    step()
    commit(msg, author)
# The working tree ends as the shipped project except discounts.py, which history produced.
