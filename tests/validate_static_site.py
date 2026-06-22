#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"

REQUIRED_FILES = [
    "index.html",
    "projects.html",
    "about.html",
    "rss.xml",
    "assets/styles.css",
    "posts/building-bili-webos.html",
    "posts/webos-tv-app-skill.html",
    "posts/wechat-cli-automation.html",
    "nginx/blog.vinividivici.top.conf",
    "scripts/deploy-blog.sh",
    "README.md",
]

REQUIRED_TEXT = {
    "index.html": [
        "Yuan Zhan",
        "blog.vinividivici.top",
        "bili-webos",
        "webos-tv-app-skill",
        "wechat-cli",
    ],
    "projects.html": [
        "https://github.com/asdf17128/bili-webos",
        "https://github.com/asdf17128/webos-tv-app-skill",
        "https://github.com/asdf17128/wechat-cli",
    ],
    "nginx/blog.vinividivici.top.conf": [
        "location /sub/",
        "proxy_pass http://127.0.0.1:8443",
        "root /var/www/blog",
    ],
    "scripts/deploy-blog.sh": [
        "rsync",
        "/var/www/blog/",
    ],
}


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.stylesheets: list[str] = []
        self.titles: list[str] = []
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        if tag == "a" and attr.get("href"):
            self.links.append(attr["href"])
        if tag == "link" and attr.get("rel") == "stylesheet" and attr.get("href"):
            self.stylesheets.append(attr["href"])
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.titles.append(data.strip())


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_exists() -> list[str]:
    errors = []
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).exists() and not (SITE / relative).exists():
            errors.append(f"missing {relative}")
    return errors


def assert_required_text() -> list[str]:
    errors = []
    for relative, snippets in REQUIRED_TEXT.items():
        candidates = [ROOT / relative, SITE / relative]
        path = next((item for item in candidates if item.exists()), None)
        if path is None:
            errors.append(f"cannot inspect missing {relative}")
            continue
        content = read(path)
        for snippet in snippets:
            if snippet not in content:
                errors.append(f"{relative} missing text: {snippet}")
    return errors


def resolve_link(source: Path, href: str) -> Path | None:
    parsed = urlparse(href)
    if parsed.scheme or href.startswith("#") or href.startswith("mailto:"):
        return None
    clean = href.split("#", 1)[0].split("?", 1)[0]
    if not clean:
        return None
    if clean.startswith("/"):
        return SITE / clean.lstrip("/")
    return (source.parent / clean).resolve()


def assert_html_links() -> list[str]:
    errors = []
    for path in sorted(SITE.rglob("*.html")):
        parser = LinkParser()
        parser.feed(read(path))
        if not parser.titles or not any(title for title in parser.titles):
            errors.append(f"{path.relative_to(ROOT)} missing title")
        for href in parser.stylesheets + parser.links:
            target = resolve_link(path, href)
            if target is not None and not target.exists():
                errors.append(
                    f"{path.relative_to(ROOT)} broken link {href} -> {target.relative_to(ROOT)}"
                )
    return errors


def assert_feed() -> list[str]:
    feed = SITE / "rss.xml"
    if not feed.exists():
        return ["missing rss.xml"]
    content = read(feed)
    urls = re.findall(r"<link>(https://blog\.vinividivici\.top/?[^<]*)</link>", content)
    if len(urls) < 4:
        return ["rss.xml should expose homepage and at least three articles"]
    return []


def main() -> int:
    checks = [
        assert_exists,
        assert_required_text,
        assert_html_links,
        assert_feed,
    ]
    errors: list[str] = []
    for check in checks:
        errors.extend(check())
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("static blog validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
