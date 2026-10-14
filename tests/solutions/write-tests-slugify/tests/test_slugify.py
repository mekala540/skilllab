import unittest

from slugify import slugify


class TestSlugify(unittest.TestCase):
    def test_accents(self):
        self.assertEqual(slugify("café"), "cafe")

    def test_lowercase(self):
        self.assertEqual(slugify("Hello World"), "hello-world")

    def test_runs_collapse(self):
        self.assertEqual(slugify("a  --  b"), "a-b")

    def test_trim(self):
        self.assertEqual(slugify("  !hi!  "), "hi")

    def test_custom_separator(self):
        self.assertEqual(slugify("a b", separator="_"), "a_b")

    def test_max_length(self):
        self.assertEqual(slugify("abcdef", max_length=3), "abc")
        self.assertEqual(slugify("abc", max_length=3), "abc")

    def test_cut_does_not_end_in_separator(self):
        self.assertEqual(slugify("ab cd", max_length=3), "ab")

    def test_invalid_max_length(self):
        with self.assertRaises(ValueError):
            slugify("a", max_length=0)


if __name__ == "__main__":
    unittest.main()
