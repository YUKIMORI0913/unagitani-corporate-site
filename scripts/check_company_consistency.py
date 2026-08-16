#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

root = Path(__file__).parents[1]
source = (root / "assets/js/company-data.js").read_text(encoding="utf-8")
homepage = (root / "index.html").read_text(encoding="utf-8")
match = re.search(r'<script type="application/ld\+json">(.*?)</script>', homepage, re.S)
if not match:
    print("[FAIL] homepage JSON-LD missing")
    sys.exit(1)
organization = json.loads(match.group(1))["@graph"][0]
checks = {
    "name": (r'name:\s*"([^"]+)"', organization["name"]),
    "telephone": (r'telephone:\s*"([^"]+)"', organization["telephone"]),
    "address": (r'address:\s*"([^"]+)"', "〒600-8223 京都府京都市下京区" + organization["address"]["streetAddress"]),
}
failures = []
for label, (pattern, structured_value) in checks.items():
    value = re.search(pattern, source)
    if not value or value.group(1) != structured_value:
        failures.append(label)
if failures:
    print("[FAIL] company data and JSON-LD mismatch: " + ", ".join(failures))
    sys.exit(1)
print("[PASS] company data and JSON-LD are consistent")
