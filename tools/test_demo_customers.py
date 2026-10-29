import csv
import io
import unittest

from demo_customers import TARGET, customer_bytes


class DemoCustomerTests(unittest.TestCase):
    def test_static_fixture_matches_generator(self):
        self.assertEqual(TARGET.read_bytes(), customer_bytes())
        self.assertEqual(customer_bytes(), customer_bytes())

    def test_original_import_format_and_field_limits(self):
        raw = customer_bytes()
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b"\r", raw)
        self.assertTrue(raw.endswith(b"\n"))
        rows = list(csv.reader(io.StringIO(raw.decode("utf-8")), delimiter="\t"))
        self.assertEqual(len(rows), 200)
        self.assertEqual(len({row[0] for row in rows}), 200)
        limits = (40, 40, 40, 40, 10, 40, 20, 20, 20, 80, 80)
        for row in rows:
            self.assertEqual(len(row), 11)
            self.assertEqual(row[6:], [""] * 5)
            for value, limit in zip(row, limits):
                self.assertLessEqual(len(value), limit)
                self.assertNotIn("\0", value)

    def test_explicitly_fictional_values_and_stable_order(self):
        rows = [line.split("\t") for line in customer_bytes().decode().splitlines()]
        self.assertEqual(rows[0][0], "デモ文具001（架空）")
        self.assertEqual(rows[-1][0], "デモ企画200（架空）")
        for row in rows:
            self.assertIn("（架空）", row[0])
            self.assertEqual(row[2:6], ["サンプル市", "架空県", "0000000", "日本"])


if __name__ == "__main__":
    unittest.main()
