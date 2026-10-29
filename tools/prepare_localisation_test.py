"""Generate a tool4d resource-resolution test from the demo's locale files."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
checks = []
for folder in ("en", "de", "fr", "ES", "ja"):
    targets = {}
    for path in sorted((root / "demo/4D Invoice/Resources" / f"{folder}.lproj").glob("*.xlf")):
        for unit in ET.parse(path).getroot().iter():
            if unit.tag.rsplit("}", 1)[-1] != "trans-unit":
                continue
            key = unit.get("resname") or unit.get("id")
            target = next((e for e in unit if e.tag.rsplit("}", 1)[-1] == "target"), None)
            if key is None or target is None or key.startswith("Common"):
                continue
            text = "".join(target.itertext())
            if key in targets and targets[key] != text:
                raise ValueError(f"Conflicting locale target {folder}/{key}")
            targets[key] = text
    checks.extend({"locale": folder.lower(), "key": key, "expected": text}
                  for key, text in sorted(targets.items()))

payload = json.dumps(checks, ensure_ascii=False, separators=(",", ":"))
code = [
    '//%attributes = {"invisible":true}',
    'var $payload : Text:=""',
]
for start in range(0, len(payload), 1000):
    code.append('$payload:=$payload+' + json.dumps(payload[start:start+1000], ensure_ascii=False))
code.extend([
    'var $checks : Collection:=JSON Parse($payload)',
    'var $check : Object',
    'var $locale; $actual; $actualLocale : Text',
    'var $result : Object:=New object("checked"; $checks.length; "failed"; 0; "failures"; New collection)',
    'For each ($check; $checks)',
    '  If ($locale#$check.locale)',
    '    $locale:=$check.locale',
    '    SET DATABASE LOCALIZATION($locale; *)',
    '    $actualLocale:=Lowercase(Get database localization(Current localization))',
    '    If (($actualLocale#$locale) & (Position($locale+"-"; $actualLocale)#1))',
    '      $result.failed:=$result.failed+1',
    '      $result.failures.push("Locale selection failed: "+$locale+" -> "+Get database localization(Current localization))',
    '    End if',
    '  End if',
    '  $actual:=Get localized string:C991($check.key)',
    '  If ($actual#$check.expected)',
    '    $result.failed:=$result.failed+1',
    '    If ($result.failures.length<20)',
    '      $result.failures.push(New object("locale"; $locale; "key"; $check.key; "expected"; $check.expected; "actual"; $actual))',
    '    End if',
    '  End if',
    'End for each',
    '$result.passed:=($result.failed=0)',
    'File("/PACKAGE/agent-test.txt").setText(JSON Stringify($result; *))',
    'QUIT 4D',
])
output = root / "build/resource-smoke.4dm"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text("\n".join(code) + "\n", encoding="utf-8")
print(f"{len(checks)} resource checks -> {output}")
