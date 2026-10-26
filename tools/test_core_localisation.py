from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo/4D Invoice"
NS = {"x": "urn:oasis:names:tc:xliff:document:1.2"}


class CoreLocalisationTests(unittest.TestCase):
    def entries(self, locale):
        path = DEMO / f"Resources/{locale}.lproj/Core{locale.upper()}.xlf"
        body = ET.parse(path).find("x:file/x:body", NS)
        units = body.findall("x:trans-unit", NS)
        self.assertEqual(len({u.attrib["id"] for u in units}), len(units))
        return {u.attrib["id"]: (u.findtext("x:source", namespaces=NS),
                                 u.findtext("x:target", namespaces=NS)) for u in units}

    def test_core_ids_and_template_placeholders_match_in_all_locales(self):
        english = self.entries("en")
        for locale in ("ja", "de", "fr", "ES"):
            entries = self.entries(locale)
            self.assertEqual(entries.keys(), english.keys())
            for key, (source, target) in entries.items():
                self.assertEqual(source, english[key][0])
                self.assertTrue(target)
                self.assertEqual(sorted(re.findall(r"\{[^{}]+\}", source)),
                                 sorted(re.findall(r"\{[^{}]+\}", target)))
        self.assertEqual(self.entries("ja")["Core_ProductLabelTemplate"][1],
                         "{brand}・{colour}・{type}")
        self.assertEqual(self.entries("ja")["Core_ProductName"][1], "商品名")

    def test_all_catalog_keys_have_captions_without_renaming_schema(self):
        entries = self.entries("ja")
        for table in ET.parse(DEMO / "Project/Sources/catalog.4DCatalog").getroot().findall("table"):
            self.assertIn("Core_" + table.attrib["name"], entries)
            for field in table.findall("field"):
                self.assertIn("Core_" + field.attrib["name"], entries)

    def test_display_labels_do_not_replace_toolbar_action_names(self):
        source = (DEMO / "Project/Sources/Classes/Toolbar_Setup.4dm").read_text()
        self.assertIn('GET LIST ITEM PARAMETER(Form:C1466.userlist; $beforeref; "name"; $canonicalName)', source)
        self.assertIn('"name"; $canonicalName', source)
        self.assertNotIn('"name"; $beforetext', source)

    def test_main_entry_keeps_nonblocking_custom_titlebar_window(self):
        source = (DEMO / "Project/Sources/Methods/Start_ORDAWindow.4dm").read_text()
        self.assertIn('DIALOG:C40("ORDAListbox"; *)', source)
        self.assertIn("Plain form window no title:K39:19", source)
        self.assertIn("CALL WORKER(1; Current method name; {})", source)
        self.assertNotIn("CLOSE WINDOW", source)
        self.assertRegex(source, r"If \(Count parameters=0\)\s+CALL WORKER\(1; Current method name; \{\}\)\s+Else\s+ARRAY LONGINT")
        self.assertLess(source.index("WINDOW LIST"), source.index("Open form window"))

    def test_document_field_expressions_and_wizard_keys_are_preserved(self):
        import json
        resources = DEMO / "Resources"
        english = (resources / "EditorTemplates/Invoice_Fieldlist.txt").read_text().splitlines()
        japanese = (resources / "ja.lproj/Invoice_Fieldlist.txt").read_text().splitlines()
        self.assertEqual([row.split("\t")[0] for row in english],
                         [row.split("\t")[0] for row in japanese])
        translations = resources / "4DWP_Wizard/Translations"
        self.assertIn("ja.json", {path.name for path in translations.iterdir()})
        original = json.loads((translations / "DE.json").read_text())
        translated = json.loads((translations / "ja.json").read_text())
        for group in ("tables", "fields", "formulas"):
            self.assertEqual([row["original"] for row in original[group]],
                             [row["original"] for row in translated[group]])


if __name__ == "__main__":
    unittest.main()
