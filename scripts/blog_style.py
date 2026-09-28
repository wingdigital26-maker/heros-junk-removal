#!/usr/bin/env python3
"""
Site11: bring every blog post and blog/index.html in line with the approved
inner-page look (service pages). Re-runnable and idempotent.

Never edits post words, headings text, links, images, or <head> SEO/JSON-LD.
Only: drops the duplicate pre-chrome stylesheet links, rebuilds the wrapper
around the untouched <article class="post"> (warm page header, two-column body
with a sticky "Send the photo now" aside + table of contents), adds ids to h2s
for the contents list, and on the index adds topic filter chips.

Run: python scripts/blog_style.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog"

SMS = "sms:+12142779069?&amp;body=Hi%2C%20here%20is%20a%20photo%20of%20what%20I%20need%20gone."
TEL = "tel:+12142779069"
CAM_SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
           'stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>'
           '<circle cx="12" cy="13" r="4"/></svg>')


def slugify(text: str) -> str:
    s = re.sub(r"<[^>]+>", "", text)
    s = re.sub(r"&[a-z]+;|&#\d+;", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:60] or "section"


def strip_tags(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()


def drop_duplicate_head_links(html: str) -> str:
    """Remove stylesheet/font links that sit before the chrome-managed block."""
    m = re.search(r"<!-- trinity:head -->", html)
    if not m:
        return html
    head, rest = html[:m.start()], html[m.start():]
    head = re.sub(r'\n<link href="https://fonts\.googleapis\.com/css2[^>]*>(?=\n)', "", head)
    head = re.sub(r'\n<link rel="stylesheet" href="\.\./assets/(trinity|trinity-pages|logo-piece/logo-piece)\.css\?v=\d+">(?=\n)', "", head)
    return head + rest


def add_h2_ids(article: str):
    """Give each h2 an id (if missing) and return (article, [(id, text)])."""
    toc = []

    def rep(m):
        attrs, inner = m.group(1), m.group(2)
        if "id=" in attrs:
            hid = re.search(r'id="([^"]+)"', attrs).group(1)
        else:
            hid = slugify(inner)
            base, n = hid, 2
            while any(hid == t[0] for t in toc):
                hid = f"{base}-{n}"; n += 1
            attrs = f' id="{hid}"' + attrs
        toc.append((hid, strip_tags(inner)))
        return f"<h2{attrs}>{inner}</h2>"

    article = re.sub(r"<h2([^>]*)>(.*?)</h2>", rep, article, flags=re.S)
    return article, toc


def build_post(html: str) -> str:
    html = drop_duplicate_head_links(html)
    # Whole region from <main> to just before the reviews section.
    m = re.search(r'<main id="main" tabindex="-1">\n(.*?)(?=<section class="section post-reviews-section">)', html, re.S)
    if not m:
        return html
    region = m.group(1)
    crumb = re.search(r'<p class="breadcrumbs">.*?</p>', region, re.S).group(0)
    h1 = re.search(r"<h1>.*?</h1>", region, re.S).group(0)
    meta = re.search(r'<p class="post-date-meta">.*?</p>', region, re.S).group(0)
    # plain meta line: date + read time, no middle dots
    meta = re.sub(r"\s*&middot;\s*", ". ", meta)
    meta = re.sub(r"(\d+) min read", "A " + chr(92) + "1 minute read.", meta)
    meta = meta.replace("..", ".")
    art = re.search(r'<article class="post">.*?</article>', region, re.S).group(0)
    # the post's own photo leads the page: the first in-post figure moves up to the header slot
    fig = re.search(r'\s*<figure class="post-figure">\s*(<img[^>]*>)\s*</figure>', art, re.S)
    if fig:
        hero = fig.group(1)
        art = art[:fig.start()] + art[fig.end():]
    else:
        hero = re.search(r'(?:<div class="post-hero-media[^"]*">|<figure class="post-hero-media[^"]*">)\s*(<img[^>]*>)', region, re.S).group(1)
    hero = re.sub(r'\s(loading|fetchpriority|decoding)="[^"]*"', "", hero)
    hero = hero.replace("<img ", '<img loading="eager" fetchpriority="high" decoding="async" ', 1)
    art, toc = add_h2_ids(art)

    toc_html = ""
    if len(toc) >= 4:
        items = "\n".join(f'          <li><a href="#{hid}">{txt}</a></li>' for hid, txt in toc)
        toc_html = f'''      <nav class="post-toc" aria-label="In this guide">
        <span class="post-toc-h">In this guide</span>
        <ol>
{items}
        </ol>
      </nav>
'''

    new = f'''<section class="post-header">
  <div class="wrap">
    {crumb}
    {h1}
    {meta}
  </div>
</section>
<section class="post-body">
  <div class="wrap post-body-grid">
    <div class="post-col">
      <figure class="post-hero-media">
        {hero}
      </figure>
      {art}
    </div>
    <aside class="post-aside">
{toc_html}      <div class="svc-aside-card">
        <span class="dock" data-form="camera" data-size="M" data-phone aria-hidden="true"></span>
        <h2>Send the photo now</h2>
        <p>Open 7am to 8pm, every day. Text a photo and we text back a firm price before anyone drives out.</p>
        <a class="btn-primary" href="{SMS}">
          {CAM_SVG}
          Text a photo
        </a>
        <a class="call-quiet" href="{TEL}">Call (214) 277-9069</a>
      </div>
    </aside>
  </div>
</section>
'''
    return html[:m.start(1)] + new + html[m.end(1):]


# ---------------------------------------------------------------- index
TOPIC_MAP = {
    "how": ("How it works", ["how it works", "how the work runs", "how we work", "comparison"]),
    "haul": ("What we haul", ["what we haul", "furniture", "around the house", "backyard", "yard and outdoor", "disposal rules", "donation"]),
    "cleanouts": ("Cleanouts and estates", ["cleanouts", "estate and family", "estate and downsizing", "moving"]),
}


def topic_key(label: str) -> str:
    l = label.strip().lower()
    for key, (_, names) in TOPIC_MAP.items():
        if l in names:
            return key
    return "haul"


def build_index(html: str) -> str:
    html = drop_duplicate_head_links(html)
    # data-topic on every card (idempotent)
    def card(m):
        tag = re.search(r'<span class="tag">([^<]*)</span>', m.group(0))
        key = topic_key(tag.group(1)) if tag else "haul"
        return f'<div class="card post-card" data-topic="{key}">' + m.group(0)[len('<div class="card post-card">'):]
    html = re.sub(r'<div class="card post-card"( data-topic="[a-z]+")?>', lambda m: '<div class="card post-card">', html)
    html = re.sub(r'<div class="card post-card">.*?<span class="tag">[^<]*</span>', card, html, flags=re.S)
    # filter chips before the grid (idempotent)
    html = re.sub(r'[ \t]*<div class="post-filter".*?</div>\n', "", html, flags=re.S)
    chips = '\n'.join(f'      <button type="button" class="post-chip" data-filter="{k}">{v[0]}</button>' for k, v in TOPIC_MAP.items())
    block = f'''<div class="post-filter" role="group" aria-label="Filter guides by topic">
      <button type="button" class="post-chip is-on" data-filter="all" aria-pressed="true">All guides</button>
{chips}
    </div>
'''
    html = html.replace('<div class="grid-2 blog-grid" style="margin-top:0">', block + '    <div class="grid-2 blog-grid" style="margin-top:0">', 1)
    if 'assets/blog.js' not in html:
        html = html.replace('<script src="../assets/trinity.js?v=12" defer></script>',
                            '<script src="../assets/trinity.js?v=12" defer></script>\n<script src="../assets/blog.js?v=1" defer></script>', 1)
    return html


def main():
    n = 0
    for f in sorted(BLOG.glob("*.html")):
        src = f.read_text(encoding="utf-8")
        out = build_index(src) if f.name == "index.html" else build_post(src)
        if out != src:
            f.write_text(out, encoding="utf-8", newline="\n")
            n += 1
    print("updated", n, "files")


if __name__ == "__main__":
    main()
