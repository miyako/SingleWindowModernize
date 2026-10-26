"""Prepare the approved Tokyo customer subset without changing the 4D demo."""
import argparse
from collections import Counter
import csv
from datetime import date, datetime, timezone
import hashlib
import heapq
from html.parser import HTMLParser
from http.cookiejar import CookieJar
import io
import json
from pathlib import Path
import re
from urllib.parse import urlencode
from urllib.request import build_opener, HTTPCookieProcessor, Request
import zipfile


LISTING = "https://www.houjin-bangou.nta.go.jp/download/zenken/"
FORM = LISTING + "index.html"
SCHEMA = "https://www.houjin-bangou.nta.go.jp/pc/download/images/k-resource-dl.pdf"
TERMS = "https://www.houjin-bangou.nta.go.jp/riyokiyaku/"
COUNT = 200
KINDS = ("301", "302", "303", "304", "305")
NTA_COLUMNS = (
    "sequenceNumber", "corporateNumber", "process", "correct", "updateDate",
    "changeDate", "name", "nameImageId", "kind", "prefectureName", "cityName",
    "streetNumber", "addressImageId", "prefectureCode", "cityCode", "postCode",
    "addressOutside", "addressOutsideImageId", "closeDate", "closeCause",
    "successorCorporateNumber", "changeCause", "assignmentDate", "latest",
    "enName", "enPrefectureName", "enCityName", "enAddressOutside", "furigana",
    "hihyoji",
)
CLIENT_COLUMNS = (
    "name", "address1", "city", "state", "postcode", "country",
    "phone", "mobile", "fax", "email", "contact",
)
REQUIRED = ("name", "prefectureName", "cityName", "streetNumber", "postCode")


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


class FormInputs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inputs = {}
        self.active = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form":
            self.active = attrs.get("id") == "appForm"
        if tag == "input" and self.active and attrs.get("name"):
            self.inputs[attrs["name"]] = attrs.get("value", "")

    def handle_endtag(self, tag):
        if tag == "form":
            self.active = False


def load_manifest(path):
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    date.fromisoformat(manifest["snapshot_date"])
    if manifest["listing_url"] != LISTING or manifest["form_url"] != FORM:
        raise ValueError("Manifest is not for the official NTA full download")
    archives = manifest["archives"]
    if len(archives) != 2:
        raise ValueError("The approved Tokyo snapshot requires both source archives")
    if len({source["download_id"] for source in archives}) != 2:
        raise ValueError("Duplicate source download IDs")
    stamp = manifest["snapshot_date"].replace("-", "")
    for part, source in enumerate(archives, 1):
        path = Path(source["path"])
        if sha256(path) != source["sha256"] or path.stat().st_size != source["bytes"]:
            raise ValueError(f"Source archive checksum/size mismatch: {path}")
        with zipfile.ZipFile(path) as archive:
            members = archive.namelist()
        expected = f"13_tokyo_all_{stamp}_{part:02}.csv"
        if [n for n in members if n.endswith(".csv")] != [expected]:
            raise ValueError(f"Unexpected Tokyo CSV member in {path}: {members}")
    return manifest


def fetch(snapshot, cache):
    date.fromisoformat(snapshot)
    cache = Path(cache)
    manifest_path = cache / "download.json"
    if manifest_path.exists():
        manifest = load_manifest(manifest_path)
        if manifest["snapshot_date"] != snapshot:
            raise ValueError("Cache contains another snapshot; use another cache folder")
        return manifest_path
    opener = build_opener(HTTPCookieProcessor(CookieJar()))
    with opener.open(LISTING, timeout=60) as response:
        html = response.read().decode("utf-8")
    sections = html.split('id="csv-unicode"', 1)
    if len(sections) != 2:
        raise ValueError("Official Unicode download section is missing")
    section = sections[1].split('id="xml-unicode"', 1)[0]
    updated = re.search(r"令和(\d+)年(\d+)月(\d+)日更新", section)
    if not updated:
        raise ValueError("Could not identify the official snapshot date")
    observed = date(2018 + int(updated[1]), int(updated[2]), int(updated[3])).isoformat()
    if observed != snapshot:
        raise ValueError(f"Requested snapshot {snapshot}; NTA currently offers {observed}")
    entries = [dl for dl in re.findall(r"<dl\b.*?</dl>", section, re.S) if "東京都" in dl]
    if len(entries) != 1:
        raise ValueError("Could not uniquely identify the Unicode Tokyo download")
    ids = re.findall(r"doDownload\((\d+)\)", entries[0])
    if len(ids) != 2 or len(set(ids)) != 2:
        raise ValueError("Expected the two distinct approved Tokyo download parts")
    form = FormInputs()
    form.feed(html)
    if not any("request.token" in key for key in form.inputs):
        raise ValueError("Official download form token is missing")
    cache.mkdir(parents=True, exist_ok=True)
    manifest = {
        "listing_url": LISTING, "form_url": FORM, "snapshot_date": snapshot,
        "retrieved_at": datetime.now(timezone.utc).isoformat(), "archives": [],
    }
    for part, ident in enumerate(ids, 1):
        target = cache / f"{snapshot.replace('-', '')}-tokyo-{part}.zip"
        partial = target.with_suffix(".part")
        if target.exists() or partial.exists():
            raise FileExistsError(f"Unmanifested download exists: {target} or {partial}")
        fields = dict(form.inputs, event="download", selDlFileNo=ident)
        request = Request(FORM, urlencode(fields).encode(), headers={"Referer": LISTING})
        with opener.open(request, timeout=120) as response, partial.open("xb") as output:
            disposition = response.headers.get("Content-Disposition")
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        with zipfile.ZipFile(partial) as archive:
            members = archive.namelist()
        partial.rename(target)
        manifest["archives"].append({
            "path": str(target), "download_id": ident, "sha256": sha256(target),
            "bytes": target.stat().st_size, "members": members,
            "content_disposition": disposition,
        })
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
    load_manifest(manifest_path)
    return manifest_path


def source_records(manifest):
    for source in manifest["archives"]:
        with zipfile.ZipFile(source["path"]) as archive:
            member = next(n for n in archive.namelist() if n.endswith(".csv"))
            with archive.open(member) as raw:
                reader = csv.reader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""))
                for number, row in enumerate(reader, 1):
                    if len(row) != len(NTA_COLUMNS):
                        raise ValueError(f"{member}:{number}: expected 30 NTA columns")
                    record = dict(zip(NTA_COLUMNS, row))
                    if not re.fullmatch(r"[0-9]{13}", record["corporateNumber"]):
                        raise ValueError(f"{member}:{number}: invalid corporate number")
                    yield record


def exclusion(record):
    if record["kind"] not in KINDS:
        return "not_company"
    if record["closeDate"] or record["process"] == "99":
        return "closed_or_cancelled"
    if record["prefectureName"] != "東京都" or record["prefectureCode"] != "13":
        return "not_Tokyo"
    if record["latest"] != "1":
        return "not_latest"
    if not all(record[key].strip() for key in REQUIRED):
        return "missing_fields"
    if not re.fullmatch(r"[0-9]{7}", record["postCode"]):
        raise ValueError(f"Invalid postcode: {record['corporateNumber']}")
    return None


def select(records, count=COUNT):
    stats = Counter()

    def eligible():
        for record in records:
            stats["total"] += 1
            reason = exclusion(record)
            stats[reason or "eligible"] += 1
            if reason is None:
                yield record

    selected = heapq.nsmallest(count, eligible(), key=lambda r: int(r["corporateNumber"]))
    if len(selected) != count:
        raise ValueError(f"Expected {count} eligible companies, found {len(selected)}")
    numbers = [r["corporateNumber"] for r in selected]
    if len(set(numbers)) != count:
        raise ValueError("Duplicate corporate numbers in selected records")
    return selected, dict(stats)


def client_bytes(records):
    lines = []
    for record in records:
        values = [
            record["name"], record["streetNumber"], record["cityName"],
            record["prefectureName"], record["postCode"], "日本", "", "", "", "", "",
        ]
        if any(any(char in value for char in "\t\r\n\0") for value in values):
            raise ValueError(f"TSV-unsafe source value: {record['corporateNumber']}")
        lines.append("\t".join(values))
    return ("\n".join(lines) + "\n").encode("utf-8")


def selected_bytes(records):
    text = io.StringIO(newline="")
    writer = csv.DictWriter(text, fieldnames=NTA_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)
    return text.getvalue().encode("utf-8")


def prepare(manifest_path, output):
    manifest = load_manifest(manifest_path)
    records, stats = select(source_records(manifest))
    output = Path(output)
    names = ("Clients.txt", "nta-selected.csv", "provenance.json")
    for name in names:
        if (output / name).exists():
            raise FileExistsError(f"Refusing to overwrite {output / name}")
    clients, selected = client_bytes(records), selected_bytes(records)
    metadata = {
        "status": "prepared_only_not_imported_into_4D",
        "source": "国税庁法人番号公表サイト（国税庁）",
        "listing_url": LISTING, "resource_definition_url": SCHEMA, "terms_url": TERMS,
        "license_url": "https://www.digital.go.jp/resources/open_data/public_data_license_v1.0",
        "attribution": f"国税庁法人番号公表サイト（国税庁）（{LISTING}）を加工して作成",
        "snapshot_date": manifest["snapshot_date"], "retrieved_at": manifest["retrieved_at"],
        "source_archives": manifest["archives"], "pgp_signature_verified": False,
        "selection": {
            "prefecture": "東京都", "prefecture_code": "13", "kinds": list(KINDS),
            "closeDate": "", "exclude_cancelled_process": "99", "latest": "1",
            "required_fields": list(REQUIRED),
            "sort": "corporateNumber ascending (numeric)", "count": COUNT,
            "statistically_representative": False,
        },
        "source_counts": stats,
        "client_format": {"encoding": "UTF-8 without BOM", "newline": "LF",
                          "header": False, "columns": list(CLIENT_COLUMNS)},
        "mapping": {"name": "name", "address1": "streetNumber", "city": "cityName",
                    "state": "prefectureName", "postcode": "postCode",
                    "country": "日本 (domestic Tokyo address)",
                    "phone": "", "mobile": "", "fax": "", "email": "", "contact": ""},
        "row_linkage": "Clients.txt row N = nta-selected.csv data row N (after header)",
        "max_source_characters": {key: max(len(r[key]) for r in records) for key in REQUIRED},
        "image_references": [
            {"corporateNumber": r["corporateNumber"], "nameImageId": r["nameImageId"],
             "addressImageId": r["addressImageId"]}
            for r in records if r["nameImageId"] or r["addressImageId"]
        ],
        "caveats": [
            "Published CSV text is preserved without guessing missing data or changing glyphs.",
            "Image-referenced registered-name glyphs have not been verified against the images.",
            "No phone, mobile, fax, email, contact person, website or credit assessment is supplied.",
            "No transactions have been generated. Future transactions must be marked synthetic demo data.",
            "Current FillData must NOT import this file unchanged: it invents websites and customer assessments.",
            "Raw ZIP hashes record the downloaded snapshot; PGP signatures were not verified.",
        ],
        "artifact_sha256": {
            "Clients.txt": hashlib.sha256(clients).hexdigest(),
            "nta-selected.csv": hashlib.sha256(selected).hexdigest(),
        },
    }
    encoded = (json.dumps(metadata, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    output.mkdir(parents=True, exist_ok=True)
    for name, content in zip(names, (clients, selected, encoded)):
        with (output / name).open("xb") as stream:
            stream.write(content)
    verify(output)
    return metadata


def verify(output):
    output = Path(output)
    metadata = json.loads((output / "provenance.json").read_text(encoding="utf-8"))
    for name in ("Clients.txt", "nta-selected.csv"):
        if sha256(output / name) != metadata["artifact_sha256"][name]:
            raise ValueError(f"Prepared artifact checksum mismatch: {name}")
    with (output / "nta-selected.csv").open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != list(NTA_COLUMNS):
            raise ValueError("Selected-source CSV header mismatch")
        records = list(reader)
    selected, _ = select(records)
    if records != selected:
        raise ValueError("Selected-source rows are not in corporate-number order")
    if (output / "Clients.txt").read_bytes() != client_bytes(records):
        raise ValueError("Clients.txt does not match the retained source rows")
    return len(records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    download = commands.add_parser("fetch")
    download.add_argument("--snapshot", required=True, help="Approved YYYY-MM-DD snapshot")
    download.add_argument("--cache", default="build/nta")
    prep = commands.add_parser("prepare")
    prep.add_argument("--manifest", default="build/nta/download.json")
    prep.add_argument("--output", default="data/ja")
    check = commands.add_parser("verify")
    check.add_argument("output", nargs="?", default="data/ja")
    args = parser.parse_args()
    if args.command == "fetch":
        print(fetch(args.snapshot, args.cache))
    elif args.command == "prepare":
        metadata = prepare(args.manifest, args.output)
        print(json.dumps({"selected": COUNT, "source_counts": metadata["source_counts"],
                          "image_references": metadata["image_references"]},
                         ensure_ascii=False, indent=2))
    else:
        print(f"Verified {verify(args.output)} prepared customers; 4D import remains pending.")


if __name__ == "__main__":
    main()
