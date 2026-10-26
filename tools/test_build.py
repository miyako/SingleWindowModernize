import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from build import find_pages


class FindPagesTests(unittest.TestCase):
    def find_pages(self, toc, destinations, page_count=30):
        doc = MagicMock()
        doc.__enter__.return_value = doc
        doc.__len__.return_value = page_count
        doc.resolve_names.return_value = destinations
        with patch("build.pymupdf.open", return_value=doc):
            result = find_pages(Path("proof.pdf"), toc)
        doc.__getitem__.assert_not_called()
        return result

    def test_uses_heading_anchor_instead_of_body_text(self):
        self.assertEqual(
            self.find_pages(
                [(2, "まとめ", "sec-23")],
                {"sec-23": {"page": 25}},
            ),
            {"sec-23": 26},
        )

    def test_repeated_titles_keep_their_own_destinations(self):
        self.assertEqual(
            self.find_pages(
                [(2, "Installation", "sec-15"), (2, "Installation", "sec-17")],
                {"sec-15": {"page": 15}, "sec-17": {"page": 17}},
            ),
            {"sec-15": 16, "sec-17": 18},
        )

    def test_wrapped_and_formatted_heading_uses_anchor(self):
        self.assertEqual(
            self.find_pages(
                [(3, "A long **heading** with `code`", "sec-01")],
                {"sec-01": {"page": 3}},
            ),
            {"sec-01": 4},
        )

    def test_missing_or_invalid_destination_fails_explicitly(self):
        for destinations in (
            {},
            {"sec-01": {}},
            {"sec-01": {"page": None}},
            {"sec-01": {"page": -1}},
            {"sec-01": {"page": 30}},
        ):
            with self.subTest(destinations=destinations):
                with self.assertRaisesRegex(ValueError, "No valid PDF destination"):
                    self.find_pages([(2, "Introduction", "sec-01")], destinations)


if __name__ == "__main__":
    unittest.main()
