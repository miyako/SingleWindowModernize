import csv
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import zipfile

from nta_customers import (
    CLIENT_COLUMNS, COUNT, NTA_COLUMNS, client_bytes, exclusion, fetch,
    load_manifest, prepare, select, selected_bytes, verify,
)


def record(number=1010001000006, **updates):
    row = dict.fromkeys(NTA_COLUMNS, "")
    row.update(corporateNumber=str(number), kind="301", process="01", latest="1",
               name="株式会社テスト", prefectureName="東京都", prefectureCode="13",
               cityName="文京区", streetNumber="後楽２丁目２番８号", postCode="1120004")
    row.update(updates)
    return row


class SelectionTests(unittest.TestCase):
    def test_sorts_numerically_and_retains_exact_values(self):
        low = record(name="株式会社「テスト」")
        high = record(2010001000006)
        chosen, stats = select([high, low], count=2)
        self.assertEqual(chosen, [low, high])
        self.assertEqual(stats, {"total": 2, "eligible": 2})

    def test_exclusions_and_required_fields(self):
        for updates, expected in [
            ({"kind": "101"}, "not_company"),
            ({"kind": "399"}, "not_company"),
            ({"closeDate": "2025-01-01"}, "closed_or_cancelled"),
            ({"process": "99"}, "closed_or_cancelled"),
            ({"prefectureName": "大阪府"}, "not_Tokyo"),
            ({"prefectureCode": "27"}, "not_Tokyo"),
            ({"latest": "0"}, "not_latest"),
            ({"streetNumber": ""}, "missing_fields"),
            ({"name": " "}, "missing_fields"),
            ({"postCode": ""}, "missing_fields"),
        ]:
            with self.subTest(updates=updates):
                self.assertEqual(exclusion(record(**updates)), expected)
        for kind in ("301", "302", "303", "304", "305"):
            self.assertIsNone(exclusion(record(kind=kind)))

    def test_invalid_postcode_duplicate_and_shortfall_fail(self):
        with self.assertRaisesRegex(ValueError, "postcode"):
            select([record(postCode="112-0004")], count=1)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            select([record(), record()], count=2)
        with self.assertRaisesRegex(ValueError, "Expected 200"):
            select([record()])

    def test_tsv_has_exact_format_and_empty_contacts(self):
        row = record(name='株式会社"テスト"')
        raw = client_bytes([row])
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))
        self.assertTrue(raw.endswith(b"\n"))
        self.assertNotIn(b"\r", raw)
        values = raw.decode().rstrip("\n").split("\t")
        self.assertEqual(len(values), len(CLIENT_COLUMNS))
        self.assertEqual(values[:6], [row["name"], row["streetNumber"], row["cityName"],
                                     "東京都", "1120004", "日本"])
        self.assertEqual(values[6:], [""] * 5)

    def test_unsafe_tsv_values_fail_without_silent_repair(self):
        for value in ("a\tb", "a\nb", "a\rb", "a\0b"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "TSV-unsafe"):
                    client_bytes([record(name=value)])

    def test_raw_selected_csv_roundtrips_all_fields(self):
        row = record(name='株式会社"テスト"', nameImageId="00049087")
        reader = csv.DictReader(io.StringIO(selected_bytes([row]).decode()))
        self.assertEqual(reader.fieldnames, list(NTA_COLUMNS))
        self.assertEqual(list(reader), [row])

    def test_prepared_verification_and_negative_mutation(self):
        records = [record(1010001000006 + n) for n in range(COUNT)]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifacts = {"Clients.txt": client_bytes(records),
                         "nta-selected.csv": selected_bytes(records)}
            for name, content in artifacts.items():
                (root / name).write_bytes(content)
            metadata = {"artifact_sha256": {
                name: hashlib.sha256(content).hexdigest()
                for name, content in artifacts.items()
            }}
            (root / "provenance.json").write_text(json.dumps(metadata), encoding="utf-8")
            self.assertEqual(verify(root), COUNT)
            (root / "Clients.txt").write_bytes(artifacts["Clients.txt"] + b"\n")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                verify(root)


class DownloadTests(unittest.TestCase):
    HTML = b"""
        <form id="appForm">
        <input name="framework.request.token" value="test-token">
        <input name="event" value="download">
        </form>
        <h2 id="csv-unicode">CSV</h2><p>REPLACE_DATE</p>
        <dl><dt>REPLACE_PREFECTURE</dt><dd>
        <a onclick="return doDownload(28154);">part 1</a>
        <a onclick="return doDownload(28155);">part 2</a>
        </dd></dl><h2 id="xml-unicode">XML</h2>
    """.replace(b"REPLACE_DATE", "令和8年9月30日更新".encode()).replace(
        b"REPLACE_PREFECTURE", "東京都".encode())

    def response(self, content):
        response = io.BytesIO(content)
        response.headers = {}
        return response

    def archive(self, part, records):
        content = io.BytesIO()
        with zipfile.ZipFile(content, "w") as archive:
            archive.writestr(f"13_tokyo_all_20260930_{part:02}.csv",
                             selected_bytes(records).split(b"\n", 1)[1])
        return content.getvalue()

    def test_download_prepare_reproduction_and_source_mutation(self):
        # Lowest IDs deliberately occur in the second part.
        rows = [record(1010001000006 + n) for n in range(COUNT)]
        opener = MagicMock()
        opener.open.side_effect = [
            self.response(self.HTML),
            self.response(self.archive(1, rows[100:])),
            self.response(self.archive(2, rows[:100])),
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch("nta_customers.build_opener", return_value=opener):
                manifest = fetch("2026-09-30", root / "cache")
            first = prepare(manifest, root / "first")
            self.assertEqual(first["source_counts"], {"total": COUNT, "eligible": COUNT})
            self.assertEqual((root / "first/Clients.txt").read_bytes(), client_bytes(rows))
            prepare(manifest, root / "second")
            for name in ("Clients.txt", "nta-selected.csv", "provenance.json"):
                self.assertEqual((root / "first" / name).read_bytes(),
                                 (root / "second" / name).read_bytes())
            with self.assertRaisesRegex(FileExistsError, "overwrite"):
                prepare(manifest, root / "first")
            source = load_manifest(manifest)["archives"][0]["path"]
            with Path(source).open("ab") as stream:
                stream.write(b"mutation")
            with self.assertRaisesRegex(ValueError, "checksum/size mismatch"):
                load_manifest(manifest)

    def test_missing_part_and_wrong_snapshot_fail(self):
        opener = MagicMock()
        opener.open.side_effect = [self.response(self.HTML)]
        with tempfile.TemporaryDirectory() as directory:
            with patch("nta_customers.build_opener", return_value=opener):
                with self.assertRaisesRegex(ValueError, "currently offers 2026-09-30"):
                    fetch("2026-08-31", directory)
            manifest = Path(directory) / "download.json"
            manifest.write_text(json.dumps({
                "listing_url": "https://www.houjin-bangou.nta.go.jp/download/zenken/",
                "form_url": "https://www.houjin-bangou.nta.go.jp/download/zenken/index.html",
                "snapshot_date": "2026-09-30", "archives": [],
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "both source archives"):
                load_manifest(manifest)


if __name__ == "__main__":
    unittest.main()
