import unittest
from decimal import Decimal

from tally import discounts, tax
from tally.money import Money


class TaxTest(unittest.TestCase):
    def test_rates(self):
        self.assertEqual(tax.rate_for("DE", "standard"), Decimal("0.19"))
        self.assertEqual(tax.rate_for("FR", "reduced"), Decimal("0.055"))
        self.assertEqual(tax.rate_for("GB", "zero"), Decimal("0"))

    def test_unknown(self):
        with self.assertRaises(tax.UnknownTaxRate):
            tax.rate_for("XX", "standard")
        with self.assertRaises(tax.UnknownTaxRate):
            tax.rate_for("DE", "luxury")

    def test_tax_on_rounds(self):
        self.assertEqual(tax.tax_on(Money.of("10.05", "EUR"), "DE", "standard").amount, Decimal("1.91"))


class DiscountTest(unittest.TestCase):
    def test_tiers_and_volume(self):
        self.assertEqual(discounts.line_rate("standard", 1), Decimal("0"))
        self.assertEqual(discounts.line_rate("silver", 1), Decimal("0.05"))
        self.assertEqual(discounts.line_rate("standard", 30), Decimal("0.02"))
        self.assertEqual(discounts.line_rate("gold", 60), Decimal("0.15"))

    def test_coupon_case_insensitive(self):
        self.assertEqual(discounts.line_rate("standard", 1, " welcome10 "), Decimal("0.10"))

    def test_unknown_coupon(self):
        with self.assertRaises(discounts.UnknownCoupon):
            discounts.line_rate("standard", 1, "FREE")

    def test_cap(self):
        self.assertEqual(discounts.line_rate("gold", 100, "STAFF25"), discounts.MAX_DISCOUNT)


if __name__ == "__main__":
    unittest.main()
