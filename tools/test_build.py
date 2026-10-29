import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from build import CFG, find_pages, to_html


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


class CoverTests(unittest.TestCase):
    SOURCE = "# Title\n\nAuthor\n\nTechnical Note 24-14\n\n## Abstract\n\nBody.\n"

    def cover(self, lang, setting):
        with patch.dict(CFG, {"cover": setting}):
            page, _ = to_html(self.SOURCE, {}, lang)
        return page.split('<section class="cover">', 1)[1].split("</section>", 1)[0]

    def test_default_preserves_all_cover_metadata(self):
        cover = self.cover("en", {})
        self.assertIn("<p>Author</p>", cover)
        self.assertIn("<p>Technical Note 24-14</p>", cover)

    def test_limit_applies_only_to_selected_language(self):
        setting = {"metadata_paragraphs": {"ja": 1}}
        japanese = self.cover("ja", setting)
        self.assertIn("<h1>Title</h1>", japanese)
        self.assertIn("<p>Author</p>", japanese)
        self.assertNotIn("Technical Note 24-14", japanese)
        self.assertIn("Technical Note 24-14", self.cover("en", setting))

    def test_zero_shows_title_without_metadata(self):
        self.assertEqual(
            self.cover("ja", {"metadata_paragraphs": {"ja": 0}}),
            "<h1>Title</h1>",
        )

    def test_invalid_limit_fails_explicitly(self):
        for limit in (-1, 3, "1", True, None):
            with self.subTest(limit=limit):
                with self.assertRaisesRegex(ValueError, "cover.metadata_paragraphs"):
                    self.cover("ja", {"metadata_paragraphs": {"ja": limit}})


if __name__ == "__main__":
    unittest.main()
