import unittest

from pager import page_count, paginate


class HiddenPager(unittest.TestCase):
    def test_pages(self):
        items = list(range(10))
        self.assertEqual(paginate(items, 1, 3), [0, 1, 2])
        self.assertEqual(paginate(items, 2, 3), [3, 4, 5])
        self.assertEqual(paginate(items, 4, 3), [9])
        self.assertEqual(paginate(items, 5, 3), [])

    def test_invalid(self):
        with self.assertRaises(ValueError):
            paginate([1], 0, 3)
        with self.assertRaises(ValueError):
            paginate([1], 1, 0)

    def test_page_count(self):
        self.assertEqual(page_count(list(range(10)), 3), 4)
        self.assertEqual(page_count(list(range(9)), 3), 3)
        self.assertEqual(page_count([], 3), 0)
        self.assertEqual(page_count([1], 5), 1)


if __name__ == "__main__":
    unittest.main()
