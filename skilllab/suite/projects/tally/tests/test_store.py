import tempfile
import unittest
from pathlib import Path

from tally.catalog import Catalog, UnknownProduct
from tally.customers import Customer, CustomerBook
from tally.inventory import Inventory, OutOfStock
from tally.orders import OrderBook

from helpers import book, catalog, customers, order


class RoundTripTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_catalog(self):
        catalog().save(self.tmp / "c.json")
        again = Catalog.load(self.tmp / "c.json")
        self.assertEqual(again.get("HW-2").price.amount, catalog().get("HW-2").price.amount)
        with self.assertRaises(UnknownProduct):
            again.get("nope")

    def test_customers(self):
        customers().save(self.tmp / "u.json")
        self.assertEqual(CustomerBook.load(self.tmp / "u.json").get("C3").tier, "gold")

    def test_orders(self):
        b = book(order("O1", "C1", "2026-03-01T10:00:00Z", ("HW-1", 2, "14.99"), coupon="WELCOME10"))
        b.save(self.tmp / "o.json")
        again = OrderBook.load(self.tmp / "o.json")
        self.assertEqual(again.get("O1").coupon, "WELCOME10")
        self.assertEqual(again.get("O1").lines[0].qty, 2)

    def test_missing_file_is_empty(self):
        self.assertEqual(len(OrderBook.load(self.tmp / "none.json")), 0)

    def test_bad_version(self):
        (self.tmp / "o.json").write_text('{"version": 9, "orders": []}')
        with self.assertRaises(ValueError):
            OrderBook.load(self.tmp / "o.json")

    def test_inventory(self):
        inv = Inventory()
        inv.receive("HW-1", 5)
        inv.reserve("HW-1", 3)
        inv.save(self.tmp / "i.json")
        again = Inventory.load(self.tmp / "i.json")
        self.assertEqual(again.level("HW-1").available, 2)


class CustomerValidationTest(unittest.TestCase):
    def test_bad_email(self):
        with self.assertRaises(ValueError):
            CustomerBook().add(Customer("C9", "X", "not-an-email", "DE"))

    def test_bad_country(self):
        with self.assertRaises(ValueError):
            CustomerBook().add(Customer("C9", "X", "x@example.com", "Germany"))


class InventoryTest(unittest.TestCase):
    def test_reserve_release_ship(self):
        inv = Inventory()
        inv.receive("A", 10)
        inv.reserve("A", 4)
        inv.release("A", 1)
        inv.ship("A", 3)
        self.assertEqual((inv.level("A").on_hand, inv.level("A").reserved), (7, 0))

    def test_out_of_stock(self):
        inv = Inventory()
        inv.receive("A", 1)
        with self.assertRaises(OutOfStock):
            inv.reserve("A", 2)

    def test_low_stock(self):
        inv = Inventory()
        inv.receive("A", 3)
        inv.receive("B", 30)
        self.assertEqual(inv.low_stock(10), ["A"])


class OrderBookTest(unittest.TestCase):
    def test_cancel_paid_refused(self):
        b = book(order("O1", "C1", "2026-03-01T10:00:00Z", ("HW-1", 1, "14.99"), status="paid"))
        with self.assertRaises(ValueError):
            b.cancel("O1")

    def test_duplicate(self):
        b = book(order("O1", "C1", "2026-03-01T10:00:00Z", ("HW-1", 1, "14.99")))
        with self.assertRaises(ValueError):
            b.add(order("O1", "C1", "2026-03-01T10:00:00Z", ("HW-1", 1, "14.99")))

    def test_bad_timestamp(self):
        with self.assertRaises(ValueError):
            order("O1", "C1", "2026-03-01 10:00", ("HW-1", 1, "14.99"))


if __name__ == "__main__":
    unittest.main()
