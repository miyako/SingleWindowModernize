"""Static form/menu localisation checks; no 4D runtime or data file is needed."""

import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1] / "demo" / "4D Invoice"
SOURCES = ROOT / "Project" / "Sources"
RESOURCES = ROOT / "Resources"
LOCALES = {"en": "EN", "de": "DE", "fr": "FR", "ES": "ES", "ja": "JA"}
NAMESPACE = "urn:oasis:names:tc:xliff:document:1.2"
NS = {"x": NAMESPACE}
UI_PROPERTIES = {"text", "title", "windowTitle", "placeholder", "labels", "tooltip"}


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def units(path):
    return [
        unit for unit in ET.parse(path).getroot().iter()
        if unit.tag.split("}")[-1] == "trans-unit"
    ]


def content(unit, name):
    return next(
        (child.text or "" for child in unit if child.tag.split("}")[-1] == name),
        "",
    )


def keys(unit):
    return {unit.get("resname"), unit.get("id")} - {None}


def owned_resources(locale, suffix):
    folder = RESOURCES / f"{locale}.lproj"
    paths = [
        folder / f"StaticForms{suffix}.xlf",
        folder / f"StaticTooltips{suffix}.xlf",
        folder / f"Menu{suffix}.xlf",
    ]
    if locale == "ja":
        paths += [folder / f"{stem}JA.xlf" for stem in ("invoices", "Report", "Toolbar")]
    else:
        fallback = folder / f"LegacyFallback{suffix}.xlf"
        if fallback.exists():
            paths.append(fallback)
    return paths


class StaticLocalisationTests(unittest.TestCase):
    def test_all_form_labels_use_resources(self):
        forms = sorted(SOURCES.rglob("*.4DForm"))
        self.assertEqual(len(forms), 25)
        for path in forms:
            for obj in walk(json.loads(path.read_bytes())):
                for prop in UI_PROPERTIES & obj.keys():
                    values = obj[prop] if isinstance(obj[prop], list) else [obj[prop]]
                    for value in values:
                        if value:
                            with self.subTest(form=path, property=prop, value=value):
                                self.assertIsInstance(value, str)
                                self.assertTrue(value.startswith(":xliff:"))

    def test_menu_labels_and_separators(self):
        menu = json.loads((SOURCES / "menus.json").read_bytes())
        separators = []
        for obj in walk(menu):
            if "title" not in obj:
                continue
            if obj.get("isSeparator"):
                separators.append(obj["title"])
            else:
                self.assertTrue(obj["title"].startswith(":xliff:"))
        self.assertEqual(separators, ["Item 7", "Zeile 2", "Item 5", "(-", "(-"])

    def test_every_static_reference_resolves_in_every_locale(self):
        references = set()
        for path in [*SOURCES.rglob("*.4DForm"), SOURCES / "menus.json"]:
            for obj in walk(json.loads(path.read_bytes())):
                for value in obj.values():
                    values = value if isinstance(value, list) else [value]
                    for item in values:
                        if isinstance(item, str) and item.startswith(":xliff:"):
                            references.add(item.removeprefix(":xliff:"))
        references = {key for key in references if not key.startswith("Common")}
        for locale in LOCALES:
            available = set()
            for path in (RESOURCES / f"{locale}.lproj").glob("*.xlf"):
                for unit in units(path):
                    available.update(keys(unit))
            with self.subTest(locale=locale):
                self.assertFalse(references - available, references - available)

    def test_new_resources_are_direct_unique_xliff_12_units(self):
        for locale, suffix in LOCALES.items():
            identifiers = set()
            resource_names = set()
            for path in owned_resources(locale, suffix):
                root = ET.parse(path).getroot()
                self.assertEqual(root.tag, f"{{{NAMESPACE}}}xliff")
                self.assertEqual(root.get("version"), "1.2")
                file = root.find("x:file", NS)
                self.assertEqual(file.get("source-language"), "en")
                self.assertEqual(file.get("target-language"), locale.lower())
                direct = file.findall("x:body/x:trans-unit", NS)
                self.assertEqual(len(direct), len(units(path)))
                for unit in direct:
                    ident, name = unit.get("id"), unit.get("resname")
                    with self.subTest(path=path, name=name):
                        self.assertTrue(ident)
                        self.assertTrue(name)
                        self.assertNotIn(ident, identifiers)
                        self.assertNotIn(name, resource_names)
                        self.assertFalse(name.startswith("Common"))
                        self.assertIsNotNone(unit.find("x:source", NS))
                        self.assertIsNotNone(unit.find("x:target", NS))
                    identifiers.add(ident)
                    resource_names.add(name)

    def test_legacy_japanese_sources_match_english(self):
        for stem in ("invoices", "Report", "Toolbar"):
            english = {
                unit.get("resname"): content(unit, "source")
                for unit in units(RESOURCES / "en.lproj" / f"{stem}EN.xlf")
            }
            japanese = {
                unit.get("resname"): content(unit, "source")
                for unit in units(RESOURCES / "ja.lproj" / f"{stem}JA.xlf")
            }
            self.assertEqual(japanese, english)

    def test_fallbacks_do_not_shadow_existing_translations(self):
        for locale, suffix in LOCALES.items():
            if locale == "ja":
                continue
            paths = owned_resources(locale, suffix)
            existing_keys = set()
            for path in (RESOURCES / f"{locale}.lproj").glob("*.xlf"):
                if path not in paths:
                    for unit in units(path):
                        existing_keys.update(keys(unit))
            for path in paths:
                for unit in units(path):
                    self.assertFalse(keys(unit) & existing_keys, (path, unit.attrib))
                    self.assertEqual(content(unit, "source"), content(unit, "target"))

    def test_approved_japanese_ui_terms(self):
        entries = {}
        for path in owned_resources("ja", "JA"):
            for unit in units(path):
                entries[unit.get("resname")] = content(unit, "target")
        for key, expected in {
            "Clients": "顧客", "Invoices": "請求書", "Products": "商品",
            "Settings": "設定", "StaticToolbarSetup": "ツールバー設定",
            "MenuItemCustomFields": "カスタムフィールド",
            "Divider": "区切り",
        }.items():
            self.assertEqual(entries[key], expected)
        self.assertEqual(entries["currency"], "###,###,##0.00 ;###,###,##0.00-")
        self.assertEqual(entries["reorder_label_reverse"], "")
        self.assertEqual(entries["IE_TabControl"].count(";"), 2)
        self.assertTrue(entries["ColumnRightClick"].endswith(";-;"))


if __name__ == "__main__":
    unittest.main()
