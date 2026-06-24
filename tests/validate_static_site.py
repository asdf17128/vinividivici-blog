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
    "posts/codex-ssd-log-writes.html",
    "posts/building-bili-webos.html",
    "posts/claude-code-review.html",
    "posts/scenic-roads.html",
    "posts/webos-tv-app-skill.html",
    "posts/wechat-cli-automation.html",
    "nginx/blog.vinividivici.top.conf",
    "scripts/deploy-blog.sh",
    "README.md",
]

REQUIRED_TEXT = {
    "index.html": [
        "Siyuan",
        "blog.vinividivici.top",
        "bili-webos",
        "claude-code-review",
        "scenic-roads",
        "webos-tv-app-skill",
        "wechat-cli",
    ],
    "projects.html": [
        "https://github.com/asdf17128/bili-webos",
        "https://github.com/asdf17128/claude-code-review",
        "https://github.com/asdf17128/scenic-roads",
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

FORBIDDEN_TEXT = [
    "Yuan" + " Zhan",
    "yuan" + "zhan",
]

ARTICLE_DATES = {
    "posts/codex-ssd-log-writes.html": ("Jun 24, 2026", "Wed, 24 Jun 2026"),
    "posts/building-bili-webos.html": ("Jun 21, 2026", "Sun, 21 Jun 2026"),
    "posts/webos-tv-app-skill.html": ("Jun 13, 2026", "Sat, 13 Jun 2026"),
    "posts/wechat-cli-automation.html": ("Jun 9, 2026", "Tue, 09 Jun 2026"),
    "posts/scenic-roads.html": ("May 18, 2026", "Mon, 18 May 2026"),
    "posts/claude-code-review.html": ("May 6, 2026", "Wed, 06 May 2026"),
}

GOOGLE_AVATAR = "https://lh3.googleusercontent.com/a/ACg8ocIx_oHzmocFPwcHRI2j873ZTjMzYc1Z7jvggXq8jN-56OmH4BxE=s96-c"
OLD_GITHUB_AVATAR = "https://avatars.githubusercontent.com/u/7056394?v=4"


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


def assert_forbidden_text_absent() -> list[str]:
    errors = []
    for path in sorted(ROOT.rglob("*")):
        if ".git" in path.parts or not path.is_file():
            continue
        try:
            content = read(path)
        except UnicodeDecodeError:
            continue
        for snippet in FORBIDDEN_TEXT:
            if snippet in content:
                errors.append(f"{path.relative_to(ROOT)} contains forbidden text: {snippet}")
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
    if len(urls) < 6:
        return ["rss.xml should expose homepage and at least five articles"]
    return []


def assert_project_timeline_dates() -> list[str]:
    errors = []
    index = read(SITE / "index.html")
    feed = read(SITE / "rss.xml")
    sitemap = read(SITE / "sitemap.xml")
    for relative, (display_date, rss_date) in ARTICLE_DATES.items():
        article = read(SITE / relative)
        iso_date = {
            "Jun 21, 2026": "2026-06-21",
            "Jun 24, 2026": "2026-06-24",
            "Jun 13, 2026": "2026-06-13",
            "Jun 9, 2026": "2026-06-09",
            "May 18, 2026": "2026-05-18",
            "May 6, 2026": "2026-05-06",
        }[display_date]
        if display_date not in article:
            errors.append(f"{relative} missing project date {display_date}")
        if display_date not in index:
            errors.append(f"index.html missing project date {display_date}")
        if rss_date not in feed:
            errors.append(f"rss.xml missing project pubDate {rss_date}")
        sitemap_url = f"https://blog.vinividivici.top/{relative}"
        sitemap_entry = f"<loc>{sitemap_url}</loc>\n    <lastmod>{iso_date}</lastmod>"
        if sitemap_entry not in sitemap:
            errors.append(f"sitemap.xml missing {relative} lastmod {iso_date}")
    return errors


def assert_short_codex_note() -> list[str]:
    article = read(SITE / "posts/codex-ssd-log-writes.html")
    match = re.search(r'<article class="article-content">(.*?)</article>', article, re.S)
    if not match:
        return ["posts/codex-ssd-log-writes.html missing article content"]
    visible = re.sub(r"<[^>]+>", "", match.group(1))
    visible = re.sub(r"\s+", "", visible)
    if len(visible) > 100:
        return [f"posts/codex-ssd-log-writes.html body is {len(visible)} chars, expected <=100"]
    return []


def assert_google_avatar() -> list[str]:
    errors = []
    html_files = [SITE / "index.html", SITE / "about.html", *sorted((SITE / "posts").glob("*.html"))]
    for path in html_files:
        html = read(path)
        relative = path.relative_to(SITE)
        if OLD_GITHUB_AVATAR in html:
            errors.append(f"{relative} still uses GitHub avatar")
        if GOOGLE_AVATAR not in html:
            errors.append(f"{relative} missing Google avatar")
        if "GitHub avatar" in html:
            errors.append(f"{relative} still has GitHub avatar alt text")
    return errors


def main() -> int:
    checks = [
        assert_exists,
        assert_required_text,
        assert_forbidden_text_absent,
        assert_html_links,
        assert_feed,
        assert_project_timeline_dates,
        assert_short_codex_note,
        assert_google_avatar,
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
