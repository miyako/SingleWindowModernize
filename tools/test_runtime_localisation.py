"""Static contracts for the demo's runtime messages and dynamic display labels."""

import re
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1] / "demo" / "4D Invoice"
SOURCES = ROOT / "Project" / "Sources"
NS = {"x": "urn:oasis:names:tc:xliff:document:1.2"}
LANGUAGES = {"en": "EN", "ja": "JA", "de": "DE", "fr": "FR", "ES": "ES"}
PARENT_FILES = {
    "DatabaseMethods/onStartup.4dm",
    "Methods/Start_ORDAWindow.4dm",
    "Methods/FillData.4dm",
    "Classes/ORDA_Listbox.4dm",
    "Classes/Toolbar.4dm",
    "Classes/Toolbar_Setup.4dm",
    "Classes/Toolbar_Button.4dm",
}


class RuntimeLocalisationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resources = {}
        for folder, suffix in LANGUAGES.items():
            tree = ET.parse(ROOT / "Resources" / f"{folder}.lproj" / f"Messages{suffix}.xlf")
            assert tree.getroot().get("version") == "1.2"
            body = tree.find("x:file/x:body", NS)
            units = list(body)
            assert all(unit.tag == f"{{{NS['x']}}}trans-unit" for unit in units)
            entries = {}
            for unit in units:
                key = unit.get("id")
                assert key == unit.get("resname") and key.startswith("Runtime_")
                assert key not in entries
                entries[key] = (unit.findtext("x:source", namespaces=NS),
                                unit.findtext("x:target", namespaces=NS))
            cls.resources[folder] = entries

    def test_all_languages_have_matching_ids_and_placeholders(self):
        english = self.resources["en"]
        self.assertEqual(len(english), len({key.casefold() for key in english}))
        for language, entries in self.resources.items():
            self.assertEqual(english.keys(), entries.keys(), language)
            for key, (source, target) in entries.items():
                with self.subTest(language=language, key=key):
                    self.assertEqual(source, english[key][0])
                    self.assertTrue(target)
                    self.assertEqual(sorted(re.findall(r"\{\w+\}", source)),
                                     sorted(re.findall(r"\{\w+\}", target)))
                    if language != "ja":
                        self.assertEqual(source, target)

    def test_literal_runtime_ids_resolve_and_use_compatible_command(self):
        seen = set()
        for path in SOURCES.rglob("*.4dm"):
            if path.relative_to(SOURCES).as_posix() in PARENT_FILES:
                continue
            source = path.read_text()
            for key in re.findall(r'Get localized string(?::C991)?\("(Runtime_[^"]+)"\)', source):
                seen.add(key)
                self.assertIn(key, self.resources["en"], str(path))
            self.assertNotRegex(source, r'(?<!Get )Localized string(?::C991)?\("Runtime_')
            self.assertNotIn('":xliff:Runtime_', source)
        self.assertGreater(len(seen), 50)

    def test_dynamic_fields_cover_catalog_without_renaming_schema(self):
        catalog = ET.parse(SOURCES / "catalog.4DCatalog")
        for table in catalog.findall("table"):
            for field in table.findall("field"):
                key = f"Runtime_Field_{table.get('name')}_{field.get('name')}"
                self.assertIn(key, self.resources["ja"])
        editor = (SOURCES / "Classes/FieldListEditor.4dm").read_text()
        self.assertIn('"name"; $field;', editor)
        self.assertIn('"Runtime_Field_"+$class.getInfo().name+"_"+$field', editor)
        selector = (SOURCES / "Forms/FieldListORDA/method.4dm").read_text()
        self.assertIn('$class.hlCol.query("para=:1"; $el)', selector)
        self.assertNotIn('Find in list:C952(Form:C1466.source; $el;', selector)

    def test_invoice_field_labels_keep_original_expressions(self):
        rows = (ROOT / "Resources/EditorTemplates/Invoice_Fieldlist.txt").read_text().splitlines()
        for index, row in enumerate(rows, 1):
            expression, label = row.split("\t")
            self.assertTrue(expression)
            self.assertEqual(self.resources["en"][f"Runtime_InvoiceField_{index}"][0], label)
        source = (SOURCES / "Forms/Invoice_Editor/method.4dm").read_text()
        self.assertIn('"field"; $cells[0]; "name"; $label', source)
        self.assertIn('Get localized document path:C1105("Invoice_Fieldlist.txt")', source)
        self.assertIn('File:C1566($localizedPath; fk platform path)', source)
        self.assertIn('folder("EditorTemplates").file("Invoice_Fieldlist.txt")', source)
        self.assertIn("If (Not:C34($localizedLabels))", source)

    def test_translated_menu_labels_do_not_become_action_keys(self):
        source = (SOURCES / "Classes/INVOICES.4dm").read_text()
        actions = ["Classic Invoice", "New Invoice as PDF",
                   "New Invoice Color Paper", "New Invoice BW Paper"]
        dispatch = (SOURCES / "Methods/ORDA_Listbox_Method.4dm").read_text()
        for action in actions:
            self.assertIn(f'SET MENU ITEM PARAMETER:C1004($menu; -1; "{action}")', source)
            self.assertIn(f'($classname="{action}")', dispatch)
        columns = (SOURCES / "Forms/ORDAListbox/ObjectMethods/Listbox.4dm").read_text()
        self.assertIn('$missingFields.push($field)', columns)
        self.assertIn('$title : Text:=$missingFields[$select-5]', columns)
        self.assertIn('"this."+$title', columns)
        self.assertIn('OBJECT SET TITLE:C194(*; $title; $col[$select-1])', columns)

    def test_count_and_lock_templates_are_complete(self):
        expected = {
            "Runtime_CountClients": {"{selected}", "{total}"},
            "Runtime_CountInvoices": {"{selected}", "{total}"},
            "Runtime_CountProducts": {"{selected}", "{total}"},
            "Runtime_RecordLockedBy": {"{user}"},
            "Runtime_LockedClassic": {"{user}"},
            "Runtime_DeleteInvoices": {"{count}"},
            "Runtime_DeleteProducts": {"{count}"},
            "Runtime_DeleteInvoiceLines": {"{count}"},
        }
        for key, placeholders in expected.items():
            for entries in self.resources.values():
                self.assertEqual(placeholders, set(re.findall(r"\{\w+\}", entries[key][1])))

    def test_invoice_outputs_stamp_copies_not_stored_templates(self):
        source = (SOURCES / "Classes/Helper_Invoices.4dm").read_text()
        helper = source.split("Function outputDocument()", 1)[1].split("Function ", 1)[0]
        self.assertIn("$wp:=WP New:C1317(This:C1470.WP)", helper)
        self.assertIn('Get localized string:C991("Runtime_DemoOutputCaption")', helper)
        self.assertIn("WP SET TEXT($wp;", helper)
        self.assertNotIn("WP SET TEXT(This:C1470.WP;", source)
        self.assertEqual(source.count("var $wp : Object:=This:C1470.outputDocument()"), 3)
        self.assertIn("This:C1470.getPageImages()", source)

    def test_native_app_owned_print_headings_identify_fictional_demo_data(self):
        invoice = (SOURCES / "TableForms/2/OutputPrint/method.4dm").read_text()
        self.assertIn('Get localized string:C991("Runtime_InvoiceReportHeading")', invoice)
        self.assertIn('OBJECT SET FONT SIZE(*; "Text"; 20)', invoice)
        self.assertIn("\r", self.resources["ja"]["Runtime_InvoiceReportHeading"][1])
        for table, kind in [(1, "Clients"), (4, "Products")]:
            source = (SOURCES / f"TableForms/{table}/OutputPrint/ObjectMethods/dateTime.4dm").read_text()
            self.assertIn(f'Get localized string:C991("Runtime_{kind}ReportHeading")', source)
            self.assertIn("架空データ", self.resources["ja"][f"Runtime_{kind}ReportHeading"][1])


if __name__ == "__main__":
    unittest.main()
