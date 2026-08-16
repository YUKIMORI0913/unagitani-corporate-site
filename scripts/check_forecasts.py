#!/usr/bin/env python3
import re
import sys
from datetime import date
from pathlib import Path

source = (Path(__file__).parents[1] / "assets/js/company-data.js").read_text(encoding="utf-8")
deadlines = re.findall(r'type:\s*"forecast"[^}]*reviewAfter:\s*"(\d{4}-\d{2}-\d{2})"', source)
if not deadlines:
    print("[FAIL] forecast data must include reviewAfter")
    sys.exit(1)
expired = [value for value in deadlines if date.fromisoformat(value) < date.today()]
if expired:
    print("[FAIL] expired forecast review date: " + ", ".join(expired))
    sys.exit(1)
print("[PASS] forecast review dates: " + ", ".join(deadlines))
