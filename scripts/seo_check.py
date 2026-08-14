#!/usr/bin/env python3
"""Audit both UNAGITANI production sites with Python's standard library."""

from __future__ import annotations

import json
import sys
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

SITES = {
    "Corporate": "https://corporate.unagitani.com/",
    "Manju": "https://manju.unagitani.com/",
}
USER_AGENT = "UNAGITANI-SEO-Audit/1.0"


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.h1 = []
        self.meta: list[dict[str, str]] = []
        self.links: list[dict[str, str]] = []
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


def audit_site(label: str, base_url: str) -> int:
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
    for item in page.links:
        href = item.get("href", "")
        absolute = urljoin(base_url, href)
        if href and urlparse(absolute).netloc == urlparse(base_url).netloc:
            internal.append(absolute)
    failures += not check(bool(internal), "HTML internal links", str(len(set(internal))))
    return failures


def main() -> int:
    failures = sum(audit_site(label, url) for label, url in SITES.items())
    print(f"\nResult: {'PASS' if failures == 0 else f'{failures} failure(s)'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
