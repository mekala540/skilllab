import unittest

from tally.money import Money
from tally.payments import GatewayTimeout, PaymentFailed, capture_payment

from helpers import order


class FakeGateway:
    def __init__(self, timeouts=0):
        self.timeouts = timeouts
        self.charges = {}

    def capture(self, order_id, amount, idempotency_key):
        if self.timeouts:
            self.timeouts -= 1
            raise GatewayTimeout()
        charge = self.charges.setdefault(idempotency_key, f"ch_{len(self.charges) + 1}")
        return charge


class PaymentsTest(unittest.TestCase):
    def setUp(self):
        self.order = order("O1", "C1", "2026-03-01T10:00:00Z", ("HW-1", 1, "14.99"))

    def test_capture(self):
        gw = FakeGateway()
        self.assertEqual(capture_payment(gw, self.order, Money.of("14.99", "EUR")), "ch_1")

    def test_retries_after_timeout(self):
        gw = FakeGateway(timeouts=2)
        self.assertEqual(capture_payment(gw, self.order, Money.of("14.99", "EUR")), "ch_1")

    def test_gives_up(self):
        with self.assertRaises(PaymentFailed):
            capture_payment(FakeGateway(timeouts=5), self.order, Money.of("14.99", "EUR"))


if __name__ == "__main__":
    unittest.main()
