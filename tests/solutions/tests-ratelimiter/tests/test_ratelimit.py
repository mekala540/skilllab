import unittest

from ratelimit import TokenBucket


class Clock:
    def __init__(self, t=0.0):
        self.t = t

    def __call__(self):
        return self.t


class TestTokenBucket(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.b = TokenBucket(5, 2, clock=self.clock)

    def test_starts_full(self):
        for _ in range(5):
            self.assertTrue(self.b.allow())
        self.assertFalse(self.b.allow())

    def test_exact_tokens_allowed(self):
        self.assertTrue(self.b.allow(5))
        self.assertFalse(self.b.allow(1))

    def test_failed_allow_takes_nothing(self):
        self.b.allow(4)
        self.assertFalse(self.b.allow(2))
        self.assertTrue(self.b.allow(1))

    def test_refill_and_cap(self):
        self.b.allow(5)
        self.clock.t = 1.0
        self.assertTrue(self.b.allow(2))
        self.assertFalse(self.b.allow(1))
        self.clock.t = 100.0
        self.assertTrue(self.b.allow(5))
        self.assertFalse(self.b.allow(1))

    def test_validation(self):
        for cap, rate in [(0, 1), (1, 0), (-1, 1), (1, -1)]:
            with self.assertRaises(ValueError):
                TokenBucket(cap, rate, clock=self.clock)
        for cost in (0, -1, 6):
            with self.assertRaises(ValueError):
                self.b.allow(cost)
            with self.assertRaises(ValueError):
                self.b.wait_time(cost)
        self.assertTrue(self.b.allow(5))

    def test_clock_backwards(self):
        self.clock.t = 10.0
        self.b.allow(5)
        self.clock.t = 5.0
        self.assertFalse(self.b.allow(1))
        self.assertEqual(self.b.wait_time(1), 0.5)
        self.clock.t = 10.5
        self.assertTrue(self.b.allow(1))
        self.assertFalse(self.b.allow(1))

    def test_wait_time(self):
        self.assertEqual(self.b.wait_time(5), 0.0)
        self.b.allow(5)
        self.assertEqual(self.b.wait_time(3), 1.5)
        self.clock.t = 1.0
        self.assertEqual(self.b.wait_time(3), 0.5)


if __name__ == "__main__":
    unittest.main()
