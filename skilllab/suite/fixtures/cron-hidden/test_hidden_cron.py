import unittest
from datetime import datetime as dt

from cron import next_run

# 2024-01-01 is a Monday. 2024-03-15 is a Friday. 2024 is a leap year.
CASES = [
    ("* * * * *", dt(2024, 3, 15, 10, 0, 30), dt(2024, 3, 15, 10, 1)),
    ("* * * * *", dt(2024, 3, 15, 10, 0), dt(2024, 3, 15, 10, 1)),
    ("@hourly", dt(2024, 3, 15, 10, 0, 30), dt(2024, 3, 15, 11, 0)),
    ("@DAILY", dt(2024, 12, 31, 23, 59), dt(2025, 1, 1, 0, 0)),
    ("@weekly", dt(2024, 3, 15), dt(2024, 3, 17)),
    ("@monthly", dt(2024, 1, 31, 12), dt(2024, 2, 1)),
    ("@annually", dt(2024, 1, 1), dt(2025, 1, 1)),
    ("*/15 9-17 * * MON-FRI", dt(2024, 3, 15, 17, 50), dt(2024, 3, 18, 9, 0)),
    ("*/15 9-17 * * MON-FRI", dt(2024, 3, 15, 9, 7), dt(2024, 3, 15, 9, 15)),
    ("5/20 * * * *", dt(2024, 3, 15, 10, 50), dt(2024, 3, 15, 11, 5)),
    ("10-30/10 * * * *", dt(2024, 3, 15, 10, 20), dt(2024, 3, 15, 10, 30)),
    ("0 0 29 2 *", dt(2025, 1, 1), dt(2028, 2, 29)),
    ("0 0 31 * *", dt(2024, 4, 1), dt(2024, 5, 31)),
    ("0 0 13 * FRI", dt(2024, 1, 1), dt(2024, 1, 5)),
    ("0 0 13 * FRI", dt(2024, 1, 12, 1), dt(2024, 1, 13)),
    ("0 0 */2 * 1", dt(2024, 1, 1), dt(2024, 1, 15)),
    ("0 0 1-7 * 1", dt(2024, 1, 1), dt(2024, 1, 2)),
    ("0 0 1-7 * 1", dt(2024, 1, 7), dt(2024, 1, 8)),
    ("0 0 * * 1", dt(2024, 1, 1), dt(2024, 1, 8)),
    ("30 4 * * 7", dt(2024, 3, 15), dt(2024, 3, 17, 4, 30)),
    ("30 4 * * SUN", dt(2024, 3, 15), dt(2024, 3, 17, 4, 30)),
    ("0 9 * * mon", dt(2024, 3, 15), dt(2024, 3, 18, 9, 0)),
    ("0 12 * JAN,jul *", dt(2024, 2, 1), dt(2024, 7, 1, 12, 0)),
    ("0 0 1 */3 *", dt(2024, 2, 1), dt(2024, 4, 1)),
    ("59 23 31 12 *", dt(2024, 12, 31, 23, 59), dt(2025, 12, 31, 23, 59)),
    ("0 0 15 * 5-7", dt(2024, 3, 9), dt(2024, 3, 10)),
    ("0,30 8 * * *", dt(2024, 3, 15, 8, 0), dt(2024, 3, 15, 8, 30)),
    ("0 0 * FEB *", dt(2023, 2, 28, 0, 0), dt(2024, 2, 1)),
]

INVALID = [
    "* * * *", "* * * * * *", "", "60 * * * *", "* 24 * * *", "* * 0 * *", "* * 32 * *",
    "* * * 13 *", "* * * * 8", "*/0 * * * *", "5-3 * * * *", "* * * FOO *", "1,,2 * * * *",
    "@reboot", "0 0 30 2 *", "a * * * *", "-1 * * * *", "1-2-3 * * * *", "*/x * * * *",
    "* * * * MON-SUN",
]


class HiddenCron(unittest.TestCase):
    def test_cases(self):
        for expr, after, want in CASES:
            with self.subTest(expr=expr, after=after):
                got = next_run(expr, after)
                self.assertEqual(got, want)
                self.assertEqual((got.second, got.microsecond), (0, 0))

    def test_invalid(self):
        for expr in INVALID:
            with self.subTest(expr=expr):
                with self.assertRaises(ValueError):
                    next_run(expr, dt(2024, 1, 1))


if __name__ == "__main__":
    unittest.main()
