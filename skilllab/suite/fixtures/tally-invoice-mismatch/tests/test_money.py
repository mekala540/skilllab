import unittest
import warnings
from decimal import Decimal

from tally.money import CurrencyMismatch, Money, fmt, total


class MoneyTest(unittest.TestCase):
    def test_of_rejects_float(self):
        with self.assertRaises(TypeError):
            Money.of(1.5, "EUR")

    def test_unknown_currency(self):
        with self.assertRaises(ValueError):
            Money.of("1", "XYZ")

    def test_add_and_sub(self):
        self.assertEqual(Money.of("1.10", "EUR") + Money.of("2.20", "EUR"), Money.of("3.30", "EUR"))
        self.assertEqual(Money.of("5", "EUR") - Money.of("0.01", "EUR"), Money.of("4.99", "EUR"))

    def test_mismatch(self):
        with self.assertRaises(CurrencyMismatch):
            Money.of("1", "EUR") + Money.of("1", "GBP")

    def test_multiply_keeps_precision(self):
        self.assertEqual((Money.of("0.333", "EUR") * 3).amount, Decimal("0.999"))

    def test_quantize(self):
        self.assertEqual(Money.of("2.344", "EUR").quantize().amount, Decimal("2.34"))
        self.assertEqual(Money.of("2.346", "EUR").quantize().amount, Decimal("2.35"))

    def test_format(self):
        self.assertEqual(Money.of("1234.5", "EUR").format(), "€1,234.50")
        self.assertEqual(Money.of("1234.5", "EUR").format("de"), "1.234,50 €")
        self.assertEqual(Money.of("-3", "GBP").format(), "-£3.00")
        self.assertEqual(Money.of("1500", "JPY").format(), "¥1,500")

    def test_total(self):
        self.assertEqual(total([Money.of("1", "EUR"), Money.of("2", "EUR")], "EUR"), Money.of("3", "EUR"))
        self.assertEqual(total([], "EUR"), Money.zero("EUR"))

    def test_fmt_matches_format(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            self.assertEqual(fmt(Decimal("9.5"), "EUR"), "€9.50")


if __name__ == "__main__":
    unittest.main()
