import unittest

from durations import parse_duration


class HiddenDurations(unittest.TestCase):
    def test_examples(self):
        cases = {"90s": 90, "1h30m": 5400, "2h": 7200, "1h 5m 10s": 3910, "1.5h": 5400,
                 "0s": 0, "10M": 600, " 1h 30 m ": 5400, "1.5m": 90, "0.25m": 15,
                 "1H2M3S": 3723, "100m": 6000}
        for text, want in cases.items():
            with self.subTest(text=text):
                self.assertEqual(parse_duration(text), want)
                self.assertIsInstance(parse_duration(text), int)

    def test_invalid(self):
        for text in ["", "   ", "90", "h", "5x", "1d", "-1h", "1.h", ".5h", "1..5h",
                     "1h1h", "5s1m", "30m1h", "0.5s", "1h-30m", "1 h x"]:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_duration(text)


if __name__ == "__main__":
    unittest.main()
