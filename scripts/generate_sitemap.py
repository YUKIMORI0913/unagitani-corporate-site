#!/usr/bin/env python3
"""公開中のHTMLから sitemap.xml を生成します。

`lastmod` は各ファイルの最終コミット日をそのまま使います。手で書いた日付は
すぐ古くなり、Googleは信用しなくなるためです。`--check` は書き込みを行わず、
コミット済みの sitemap.xml が現在の内容と一致するかだけを検証します。

    python3 scripts/generate_sitemap.py          # 書き込み
    python3 scripts/generate_sitemap.py --check  # 差分検査のみ
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://corporate.unagitani.com"

# 上から順に重要度の高いページ。ここにない公開ページは末尾へ自動追加します。
PREFERRED_ORDER = [
    "/",
    "/about/",
    "/company/",
    "/business/",
    "/brands/",
    "/message/",
    "/history/",
    "/compliance/",
    "/news/",
    "/contact/",
    "/privacy/",
]


def last_modified(file: Path) -> str:
    result = subprocess.run(
        ["git", "log", "-1", "--format=%ad", "--date=short", "--", str(file.relative_to(ROOT))],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def page_url(file: Path) -> str:
    return "/" + file.relative_to(ROOT).as_posix().removesuffix("index.html")


def build() -> str:
    pages = {page_url(f): f for f in ROOT.glob("**/*.html") if ".git" not in f.parts}
    ordered = [path for path in PREFERRED_ORDER if path in pages]
    ordered += sorted(path for path in pages if path not in PREFERRED_ORDER)

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for path in ordered:
        modified = last_modified(pages[path])
        entry = f"  <url><loc>{BASE_URL}{path}</loc>"
        if modified:
            entry += f"<lastmod>{modified}</lastmod>"
        lines.append(entry + "</url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def main() -> int:
    sitemap = ROOT / "sitemap.xml"
    generated = build()
    if "--check" in sys.argv:
        if sitemap.read_text(encoding="utf-8") != generated:
            print("[FAIL] sitemap.xml が公開ページと一致していません")
            print("       python3 scripts/generate_sitemap.py を実行してください")
            return 1
        print("[PASS] sitemap.xml は公開ページと一致しています")
        return 0
    sitemap.write_text(generated, encoding="utf-8")
    print(f"[WRITE] sitemap.xml ({generated.count('<url>')} URL)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
