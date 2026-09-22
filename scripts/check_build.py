#!/usr/bin/env python3
"""
Build gate for the Hero's Junk Removal v2 site.

Fails (non-zero exit) if any of these is true anywhere in the v2 tree:
  1. an .html page has no tel: link anywhere on the page
  2. an element whose class or aria-label contains "call" has an href that is not tel:
  3. an .html page does not load assets/track.js
  4. an .html page contains a dollar sign immediately followed by a digit
  5. a v1 URL in MIGRATION_MAP.md marked KEEP IDENTICAL has no corresponding v2 file
     or matching rule in _redirects
  6. a content image filename (not the logo or mark) is used on more than one page

Run: python scripts/check_build.py   (from anywhere; paths are resolved relative to this file)
"""

import re
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent

# Filenames that are identity assets, not content photos, and are allowed on every page.
IDENTITY_IMAGE_NAMES = {
    "logo.svg",
    "logo-mark.svg",
    "logo.png",
    "logo-mark.png",
    "heros-logo-trim.png",
    "favicon.ico",
}


def find_html_files():
    # "brand" holds internal design tools (logo contact sheets, previews). They are never
    # served to customers, so the customer-facing rules below do not apply to them.
    SKIP = {"node_modules", "brand", ".git"}
    return sorted(p for p in ROOT.rglob("*.html") if not SKIP & set(p.parts))


def check_tel_links(html_files):
    """1. every page must have at least one tel: link."""
    failures = []
    for path in html_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if not re.search(r'href=["\']tel:', text):
            failures.append(str(path.relative_to(ROOT)))
    return failures


def check_call_elements(html_files):
    """2. any element whose class or aria-label contains "call" must have href="tel:...".
    Scans <a ...> tags for class= or aria-label= containing "call" (case-insensitive)."""
    failures = []
    tag_re = re.compile(r"<a\b[^>]*>", re.IGNORECASE)
    class_re = re.compile(r'class=["\']([^"\']*)["\']', re.IGNORECASE)
    aria_re = re.compile(r'aria-label=["\']([^"\']*)["\']', re.IGNORECASE)
    href_re = re.compile(r'href=["\']([^"\']*)["\']', re.IGNORECASE)
    for path in html_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for tag in tag_re.findall(text):
            cls_m = class_re.search(tag)
            aria_m = aria_re.search(tag)
            has_call = (cls_m and "call" in cls_m.group(1).lower()) or (
                aria_m and "call" in aria_m.group(1).lower()
            )
            if not has_call:
                continue
            href_m = href_re.search(tag)
            href = href_m.group(1) if href_m else ""
            if not href.startswith("tel:"):
                failures.append(
                    f"{path.relative_to(ROOT)}: {tag.strip()[:120]}  (href={href or 'MISSING'})"
                )
    return failures


def check_analytics(html_files):
    """3. every page must load assets/track.js."""
    failures = []
    for path in html_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if not re.search(r'src=["\'][^"\']*assets/track\.js["\']', text):
            failures.append(str(path.relative_to(ROOT)))
    return failures


def check_no_prices(html_files):
    """4. no page may contain a dollar sign immediately followed by a digit."""
    failures = []
    price_re = re.compile(r"\$\d")
    for path in html_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for m in price_re.finditer(text):
            start = max(0, m.start() - 25)
            end = min(len(text), m.end() + 15)
            snippet = text[start:end].replace("\n", " ")
            failures.append(f"{path.relative_to(ROOT)}: ...{snippet}...")
    return failures


def parse_migration_map():
    """Return list of (v1_url, v2_url) for rows marked KEEP IDENTICAL."""
    mm_path = ROOT / "MIGRATION_MAP.md"
    rows = []
    if not mm_path.exists():
        return rows, "MIGRATION_MAP.md not found at " + str(mm_path)
    text = mm_path.read_text(encoding="utf-8")
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4:
            continue
        if cells[0] in ("#", "---") or not cells[0].isdigit():
            continue
        v1_url = cells[1].strip("`")
        v2_url = cells[2].strip("`")
        status = cells[3]
        if status == "KEEP IDENTICAL":
            rows.append((v1_url, v2_url))
    return rows, None


def url_to_v2_path(v2_url):
    """Map a /path URL to the expected v2 file on disk."""
    p = v2_url.lstrip("/")
    if p == "" or p.endswith("/"):
        p = p + "index.html"
    elif not p.endswith(".html"):
        p = p + ".html"
    return ROOT / p


def load_redirects_sources():
    redirects_path = ROOT / "_redirects"
    sources = set()
    if not redirects_path.exists():
        return sources
    for line in redirects_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 2:
            sources.add(parts[0])
    return sources


def check_migration_coverage():
    """5. every KEEP IDENTICAL v1 URL must have a matching v2 file or a redirect rule."""
    rows, err = parse_migration_map()
    if err:
        return [err]
    redirect_sources = load_redirects_sources()
    failures = []
    for v1_url, v2_url in rows:
        v2_path = url_to_v2_path(v2_url)
        if v2_path.exists():
            continue
        if v1_url in redirect_sources or v2_url in redirect_sources:
            continue
        failures.append(f"v1 {v1_url}  ->  v2 {v2_url}  (missing: {v2_path.relative_to(ROOT)})")
    return failures


def check_duplicate_images(html_files):
    """6. content image filenames must not repeat across pages (logo/mark excluded)."""
    img_re = re.compile(r'src=["\']([^"\']+\.(?:jpg|jpeg|png|webp|gif|avif))["\']', re.IGNORECASE)
    usage = defaultdict(set)
    for path in html_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for src in img_re.findall(text):
            filename = src.rsplit("/", 1)[-1].lower()
            if filename in IDENTITY_IMAGE_NAMES:
                continue
            usage[filename].add(str(path.relative_to(ROOT)))
    failures = []
    for filename, pages in sorted(usage.items()):
        if len(pages) > 1:
            failures.append(f"{filename} used on {len(pages)} pages: {', '.join(sorted(pages))}")
    return failures


def report_section(title, failures, note=None):
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")
    if note:
        print(note)
    if not failures:
        print("  PASS - no issues found")
        return 0
    print(f"  FAIL - {len(failures)} issue(s):")
    for f in failures:
        print(f"    - {f}")
    return len(failures)


def main():
    html_files = find_html_files()
    total_fail = 0

    print(f"Hero's Junk Removal v2 build gate")
    print(f"Root: {ROOT}")
    print(f"HTML pages found: {len(html_files)}")

    total_fail += report_section(
        "1. Every page must have a tel: link", check_tel_links(html_files)
    )
    total_fail += report_section(
        '2. Every "call" element must link tel:', check_call_elements(html_files)
    )
    total_fail += report_section(
        "3. Every page must load assets/track.js", check_analytics(html_files)
    )
    total_fail += report_section(
        "4. No invented prices ($ + digit)", check_no_prices(html_files)
    )
    total_fail += report_section(
        "5. Every KEEP IDENTICAL v1 URL has a v2 file or redirect",
        check_migration_coverage(),
        note="Expected to show many misses until the full v2 rebuild ports every page. "
        "This section exists so nothing gets silently dropped as pages are added.",
    )
    total_fail += report_section(
        "6. No content image filename reused across pages", check_duplicate_images(html_files)
    )

    print(f"\n{'=' * 70}")
    if total_fail:
        print(f"BUILD GATE: FAILED ({total_fail} total issue(s) across all checks)")
        print("=" * 70)
        sys.exit(1)
    else:
        print("BUILD GATE: PASSED")
        print("=" * 70)
        sys.exit(0)


if __name__ == "__main__":
    main()
