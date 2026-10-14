import unittest

from ratelimit import TokenBucket


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


class TestTokenBucket(unittest.TestCase):
    """A typical happy-path suite: looks thorough, misses the boundaries."""

    def test_allows_then_blocks(self):
        b = TokenBucket(3, 1, clock=Clock())
        self.assertTrue(b.allow())
        self.assertTrue(b.allow())
        self.assertTrue(b.allow())
        self.assertFalse(b.allow())

    def test_refills(self):
        c = Clock()
        b = TokenBucket(2, 1, clock=c)
        b.allow(2)
        c.t = 1.5
        self.assertTrue(b.allow())

    def test_bad_args(self):
        with self.assertRaises(ValueError):
            TokenBucket(0, 1)
        with self.assertRaises(ValueError):
            TokenBucket(1, 0)

    def test_wait_time(self):
        b = TokenBucket(2, 2, clock=Clock())
        b.allow(2)
        self.assertGreater(b.wait_time(), 0)


if __name__ == "__main__":
    unittest.main()
