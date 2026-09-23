#!/usr/bin/env python3
"""静的HTMLへ共通ヘッダー・フッターと会社情報を焼き込みます。

`assets/js/main.js` はこれまでヘッダー、フッター、会社概要、売上高、沿革を
ブラウザ上で組み立てていました。検索エンジンが最初に取得する生のHTMLには
これらが含まれないため、新規ドメインではインデックス登録が遅れます。

このスクリプトは `assets/js/company-data.js` を唯一の情報源として、
同じ内容を各HTMLへ書き込みます。`--check` を付けると書き込みを行わず、
コミット済みHTMLが現在のデータと一致しているかだけを検証します。

    python3 scripts/render_static.py          # 書き込み
    python3 scripts/render_static.py --check  # 差分検査のみ
"""

from __future__ import annotations

import json
import re
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

NAV_ITEMS = [
    ("/company/", "Company"),
    ("/business/", "Business"),
    ("/message/", "Message"),
    ("/compliance/", "Compliance"),
    ("/history/", "History"),
    ("/brands/", "Brands"),
    ("/news/", "News"),
    ("/contact/", "Contact"),
]

# フッターはサイト内の全ページを網羅します。ヘッダーに出さない /about/ を
# ここに含めないと、どこからもリンクされない孤立ページになります。
FOOTER_ITEMS = [
    ("/about/", "About"),
    ("/company/", "Company"),
    ("/business/", "Business"),
    ("/brands/", "Brands"),
    ("/message/", "Message"),
    ("/history/", "History"),
    ("/news/", "News"),
    ("/compliance/", "Compliance"),
    ("/privacy/", "Privacy"),
    ("/contact/", "Contact"),
]

PROFILE_FIELDS = [
    ("商号", "name"),
    ("英文商号", "nameEn"),
    ("代表者", "representative"),
    ("所在地", "address"),
    ("創業", "founded"),
    ("法人設立", "incorporated"),
    ("資本金", "capital"),
    ("法人番号", "corporateNumber"),
    ("事業内容", "business"),
    ("決算期", "fiscalYearEnd"),
    ("従業員数", "employees"),
    ("主要取引銀行", "banks"),
    ("古物商許可", "license"),
    ("適格請求書発行事業者登録番号", "invoiceRegistrationNumber"),
    ("主要販売チャネル", "channels"),
    ("主な取扱メーカー", "manufacturers"),
    ("公式サイト", "website"),
]

STYLESHEET = '<link rel="stylesheet" href="/assets/css/phase1.css">'

DEFAULT_OG_IMAGE = "https://corporate.unagitani.com/assets/images/ecommerce-operations.png"
SITE_NAME = "株式会社UNAGITANI"


def load_company_data() -> dict:
    """company-data.js のオブジェクトリテラルをJSONとして読み込みます。"""
    source = (ROOT / "assets/js/company-data.js").read_text(encoding="utf-8")
    match = re.search(r"Object\.freeze\((\{.*\})\);?\s*$", source, re.S)
    if not match:
        raise SystemExit("[FAIL] company-data.js の形式を解釈できません")
    literal = match.group(1)
    literal = re.sub(r"(?m)^(\s*)([A-Za-z_][A-Za-z0-9_]*):", r'\1"\2":', literal)
    literal = re.sub(r"\{\s*([A-Za-z_][A-Za-z0-9_]*):", r'{"\1":', literal)
    literal = re.sub(r",\s*([A-Za-z_][A-Za-z0-9_]*):", r',"\1":', literal)
    literal = re.sub(r",(\s*[}\]])", r"\1", literal)
    return json.loads(literal)


def is_empty(value) -> bool:
    return value is None or value == "" or (isinstance(value, list) and not value)


def as_text(value) -> str:
    return "、".join(value) if isinstance(value, list) else str(value)


def find_element(html: str, marker: str) -> tuple[int, int, int] | None:
    """markerを含む開始タグを探し、開始タグ終端と閉じタグ位置を返します。"""
    for candidate in re.finditer(r"<(\w+)[^>]*>", html):
        if marker in candidate.group(0):
            match = candidate
            break
    else:
        return None
    tag = match.group(1)
    cursor = match.end()
    depth = 1
    pattern = re.compile(rf"</?{tag}\b", re.I)
    while depth:
        step = pattern.search(html, cursor)
        if not step:
            raise SystemExit(f"[FAIL] {marker} の閉じタグが見つかりません")
        depth += -1 if step.group(0).startswith("</") else 1
        cursor = step.end()
    close = html.rindex("<", match.end(), cursor)
    return match.start(), match.end(), close


def replace_inner(html: str, marker: str, inner: str, required: bool = False) -> str:
    found = find_element(html, marker)
    if not found:
        if required:
            raise SystemExit(f"[FAIL] {marker} を持つ要素がありません")
        return html
    _, open_end, close_start = found
    return html[:open_end] + inner + html[close_start:]


def render_header(path: str) -> str:
    links = "".join(
        '<li><a {current}class="{cls}" href="{href}">{label}</a></li>'.format(
            current='aria-current="page" ' if href == path else "",
            cls="nav-cta" if href == "/contact/" else "",
            href=href,
            label=label,
        )
        for href, label in NAV_ITEMS
    )
    return (
        '<div class="wrap header-inner"><a class="logo" href="/"><i></i>UNAGITANI</a>'
        '<button class="menu" type="button" aria-expanded="false" aria-controls="nav">メニュー</button>'
        '<nav id="nav" aria-label="メインナビゲーション">'
        f'<ul class="nav-list">{links}</ul></nav></div>'
    )


def render_footer() -> str:
    links = "".join(f'<a href="{href}">{label}</a>' for href, label in FOOTER_ITEMS)
    return (
        '<div class="wrap"><div class="footer-top"><div>'
        '<a class="logo" href="/"><i></i>UNAGITANI</a><p>株式会社UNAGITANI</p></div>'
        f'<nav class="footer-nav" aria-label="フッターナビ">{links}</nav></div>'
        '<p class="copyright">© UNAGITANI Co., Ltd.</p></div>'
    )


def render_profile(company: dict) -> str:
    rows = []
    for label, key in PROFILE_FIELDS:
        value = company.get(key)
        if is_empty(value):
            continue
        rows.append(f"<dt>{escape(label)}</dt><dd>{escape(as_text(value))}</dd>")
    return "".join(rows)


def render_financials(highlights: list[dict]) -> str:
    return "".join(
        '<article class="financial-card financial-card--{type}">'
        "<p>{fiscalYear}</p><strong>{revenue}</strong><span>{label}</span></article>".format(
            type=escape(item["type"]),
            fiscalYear=escape(item["fiscalYear"]),
            revenue=escape(item["revenue"]),
            label=escape(item["label"]),
        )
        for item in highlights
    )


def render_history(history: list[dict]) -> str:
    return "".join(
        '<article class="history-item"><time>{year}</time><ul>{events}</ul></article>'.format(
            year=escape(item["year"]),
            events="".join(f"<li>{escape(event)}</li>" for event in item["events"]),
        )
        for item in history
    )


def apply(html: str, data: dict, path: str) -> str:
    company = data["company"]
    html = replace_inner(html, 'class="site-header"', render_header(path), required=True)
    html = replace_inner(html, 'class="site-footer"', render_footer(), required=True)
    html = replace_inner(html, "data-company-profile", render_profile(company))
    html = replace_inner(html, "data-financial-highlights", render_financials(data["financialHighlights"]))
    html = replace_inner(html, "data-history", render_history(data["history"]))

    field = re.compile(r'<(\w+)[^>]*\bdata-company-field="([^"]+)"[^>]*>')
    cursor = 0
    while True:
        match = field.search(html, cursor)
        if not match:
            break
        tag, key = match.group(1), match.group(2)
        close = html.index(f"</{tag}>", match.end())
        value = company.get(key)
        if is_empty(value):
            cursor = close
            continue
        html = html[: match.end()] + escape(as_text(value)) + html[close:]
        cursor = match.end() + len(escape(as_text(value)))

    html = ensure_ogp(html)

    if STYLESHEET not in html:
        html = html.replace(
            '<link rel="stylesheet" href="/assets/css/style.css">',
            '<link rel="stylesheet" href="/assets/css/style.css">' + STYLESHEET,
            1,
        )
    return html


def ensure_ogp(html: str) -> str:
    """OGP/Twitterカードの不足分を、既存のtitle・description・canonicalから補います。"""
    if "og:url" in html:
        return html
    title = re.search(r"<title>(.*?)</title>", html, re.S)
    description = re.search(r'<meta name="description" content="(.*?)"', html, re.S)
    canonical = re.search(r'<link rel="canonical" href="(.*?)"', html)
    if not (title and canonical):
        return html
    tags = (
        f'<meta property="og:title" content="{title.group(1)}">'
        f'<meta property="og:description" content="{description.group(1) if description else ""}">'
        '<meta property="og:type" content="website">'
        f'<meta property="og:url" content="{canonical.group(1)}">'
        f'<meta property="og:image" content="{DEFAULT_OG_IMAGE}">'
        f'<meta property="og:site_name" content="{SITE_NAME}">'
        '<meta name="twitter:card" content="summary_large_image">'
    )
    return html.replace(canonical.group(0), canonical.group(0) + tags, 1)


def page_path(file: Path) -> str:
    relative = file.relative_to(ROOT).as_posix().removesuffix("index.html")
    return "/" + relative


def main() -> int:
    check_only = "--check" in sys.argv
    data = load_company_data()
    drifted: list[str] = []

    for file in sorted(ROOT.glob("**/*.html")):
        if ".git" in file.parts:
            continue
        original = file.read_text(encoding="utf-8")
        rendered = apply(original, data, page_path(file))
        if rendered == original:
            continue
        if check_only:
            drifted.append(file.relative_to(ROOT).as_posix())
        else:
            file.write_text(rendered, encoding="utf-8")
            print(f"[WRITE] {file.relative_to(ROOT)}")

    if check_only:
        if drifted:
            print("[FAIL] 静的HTMLが company-data.js と一致していません: " + ", ".join(drifted))
            print("       python3 scripts/render_static.py を実行してください")
            return 1
        print("[PASS] 静的HTMLは company-data.js と一致しています")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
