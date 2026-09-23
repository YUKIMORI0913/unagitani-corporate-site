#!/usr/bin/env python3
"""本番2サイトのSEO状態を標準ライブラリだけで監査します。

JavaScriptは実行しません。Googleが最初に取得する生のHTMLだけを見るため、
「ブラウザでは見えるがHTMLには無い」本文を検出できます。

    python3 scripts/seo_check.py
"""

from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

SITES = {
    "Corporate": {
        "base": "https://corporate.unagitani.com/",
        # JSを実行しない状態で、本文に必ず含まれていてほしい文字列
        "pages": {
            "/": ["株式会社UNAGITANI", "2025年9月期"],
            "/company/": ["代表取締役 森 佑紀", "古物商許可", "大黒町227番地"],
            "/business/": ["EC"],
            "/history/": ["2024年10月2日 株式会社UNAGITANI設立"],
            "/brands/": ["Electric UNAGI"],
            "/contact/": ["株式会社UNAGITANI"],
        },
    },
    "Manju": {
        "base": "https://manju.unagitani.com/",
        "pages": {
            "/": ["鰻谷饅頭", "ECLECTICISM"],
            "/gallery.html": ["photo-slot", "figcaption"],
        },
    },
}
USER_AGENT = "UNAGITANI-SEO-Audit/1.0"


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.h1 = []
        self.meta: list[dict[str, str]] = []
        self.links: list[dict[str, str]] = []
        self.anchors: list[dict[str, str]] = []
        self.scripts: list[tuple[dict[str, str], str]] = []
        self.images: list[dict[str, str]] = []
        self._capture: str | None = None
        self._text: list[str] = []
        self._script_attrs: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs) -> None:
        values = dict(attrs)
        if tag in {"title", "h1"}:
            self._capture, self._text = tag, []
        elif tag == "meta":
            self.meta.append(values)
        elif tag == "link":
            self.links.append(values)
        elif tag == "a":
            self.anchors.append(values)
        elif tag == "img":
            self.images.append(values)
        elif tag == "script":
            self._capture, self._text, self._script_attrs = "script", [], values

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != self._capture:
            return
        value = " ".join("".join(self._text).split())
        if tag == "title":
            self.title = value
        elif tag == "h1":
            self.h1.append(value)
        elif tag == "script":
            self.scripts.append((self._script_attrs, value))
        self._capture, self._text = None, []


def fetch(url: str) -> tuple[int, dict[str, str], bytes, str]:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=20) as response:
        return response.status, dict(response.headers.items()), response.read(), response.geturl()


def meta_value(page: PageParser, *, name: str) -> str:
    name = name.lower()
    for item in page.meta:
        key = (item.get("name") or item.get("property") or "").lower()
        if key == name:
            return item.get("content", "").strip()
    return ""


def canonical(page: PageParser) -> str:
    for item in page.links:
        if "canonical" in item.get("rel", "").lower().split():
            return item.get("href", "").strip()
    return ""


def check(condition: bool, label: str, detail: str = "") -> bool:
    marker = "PASS" if condition else "FAIL"
    print(f"  [{marker}] {label}" + (f": {detail}" if detail else ""))
    return condition


def audit_page(base_url: str, path: str, required: list[str]) -> int:
    """1ページ分の監査。requiredはJS無しのHTMLに含まれているべき文字列。"""
    url = urljoin(base_url, path.lstrip("/"))
    print(f"\n  {url}")
    try:
        status, headers, body, final_url = fetch(url)
    except (HTTPError, URLError, TimeoutError) as exc:
        check(False, "fetch", str(exc))
        return 1

    text = body.decode("utf-8", errors="replace")
    page = PageParser()
    page.feed(text)
    robots_value = meta_value(page, name="robots").lower()
    x_robots = headers.get("X-Robots-Tag", "").lower()
    missing = [needle for needle in required if needle not in text]

    results = [
        check(status == 200, "HTTP 200", str(status)),
        check(final_url.rstrip("/") == url.rstrip("/"), "リダイレクトなし", final_url),
        check(bool(page.title), "title", page.title),
        check(bool(meta_value(page, name="description")), "meta description"),
        check(canonical(page) == url, "canonical", canonical(page)),
        check(bool(page.h1), "h1", " | ".join(page.h1)),
        check("noindex" not in robots_value and "noindex" not in x_robots, "noindexなし"),
        check(bool(meta_value(page, name="og:url")), "OGP"),
        check(not missing, "JS無しで本文が存在", "不足: " + "、".join(missing) if missing else ""),
    ]
    return results.count(False)


def audit_site(label: str, config: dict) -> int:
    base_url = config["base"]
    failures = 0
    print(f"\n{label} — {base_url}")
    try:
        status, headers, body, final_url = fetch(base_url)
    except (HTTPError, URLError, TimeoutError) as exc:
        check(False, "homepage fetch", str(exc))
        return 1

    page = PageParser()
    page.feed(body.decode("utf-8", errors="replace"))
    expected = base_url
    robots_value = meta_value(page, name="robots").lower()
    x_robots = headers.get("X-Robots-Tag", "").lower()
    json_ld = []
    for attrs, value in page.scripts:
        if attrs.get("type", "").lower() == "application/ld+json":
            try:
                json_ld.append(json.loads(value))
            except json.JSONDecodeError:
                pass

    results = [
        check(status == 200, "HTTP 200", str(status)),
        check(final_url == expected, "final URL", final_url),
        check(bool(page.title), "title", page.title),
        check(bool(meta_value(page, name="description")), "meta description"),
        check(canonical(page) == expected, "canonical", canonical(page)),
        check(bool(page.h1), "h1", " | ".join(page.h1)),
        check("noindex" not in robots_value and "noindex" not in x_robots, "no noindex"),
        check(bool(json_ld), "valid JSON-LD"),
    ]
    failures += results.count(False)

    for path, content_label in (("robots.txt", "robots.txt"), ("sitemap.xml", "sitemap.xml")):
        url = urljoin(base_url, path)
        try:
            resource_status, _, resource_body, _ = fetch(url)
            text = resource_body.decode("utf-8", errors="replace")
            ok = resource_status == 200
            if path == "robots.txt":
                ok = ok and "disallow: /" not in text.lower() and urljoin(base_url, "sitemap.xml") in text
            else:
                ok = ok and base_url in text
            failures += not check(ok, content_label, url)
        except (HTTPError, URLError, TimeoutError) as exc:
            failures += not check(False, content_label, str(exc))

    internal = []
    for item in page.anchors:
        href = item.get("href", "")
        absolute = urljoin(base_url, href)
        if href and urlparse(absolute).netloc == urlparse(base_url).netloc:
            internal.append(absolute)
    failures += not check(bool(internal), "HTMLに内部リンクあり", str(len(set(internal))))

    for path, required in config["pages"].items():
        failures += audit_page(base_url, path, required)

    failures += audit_sitemap_urls(base_url)
    return failures


def audit_sitemap_urls(base_url: str) -> int:
    """sitemap.xml に載っている全URLが200を返すか確認します。"""
    try:
        _, _, body, _ = fetch(urljoin(base_url, "sitemap.xml"))
    except (HTTPError, URLError, TimeoutError) as exc:
        return not check(False, "sitemap取得", str(exc))
    urls = re.findall(r"<loc>(.*?)</loc>", body.decode("utf-8", errors="replace"))
    print(f"\n  sitemap.xml の {len(urls)} URL")
    failures = 0
    for url in urls:
        try:
            status, _, _, _ = fetch(url)
        except (HTTPError, URLError, TimeoutError) as exc:
            failures += not check(False, url, str(exc))
            continue
        failures += not check(status == 200, url, str(status))
    return failures


def main() -> int:
    failures = sum(audit_site(label, config) for label, config in SITES.items())
    print(f"\n結果: {'PASS' if failures == 0 else f'{failures} 件の失敗'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
