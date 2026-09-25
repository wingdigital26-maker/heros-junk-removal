#!/usr/bin/env python3
"""Restructure services/*.html bodies to the new homepage look.

Re-runnable. Reads each page's existing body content (page-hero, rail-body
sections, FAQ, aside card), keeps every word, and re-emits it using the
homepage's classes from assets/final.css plus assets/pages-svc.css.

Usage: python scripts/final_services.py
"""
import re
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SVC = ROOT / "services"
REVIEWS = json.loads((ROOT / "brand" / "reviews.json").read_text(encoding="utf-8"))["reviews"]

PHONE = "+12142779069"
SMS_HREF = "sms:+12142779069?&amp;body=Hi%2C%20here%20is%20a%20photo%20of%20what%20I%20need%20gone."
TEL_HREF = "tel:+12142779069"

STAR_SVG = '<svg viewBox="0 0 24 24" fill="currentColor"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26"/></svg>'
ARROW_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17 17 7M7 7h10v10"/></svg>'
SMS_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>'
CALL_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg>'

CORE8 = [
    ("furniture-removal", "Furniture removal", "Couches, dressers, beds", "img/p/card-furniture-820.webp", "img/p/card-furniture-480.webp"),
    ("appliance-removal", "Appliance removal", "Fridges, washers, dryers", "img/p/appliance-820.webp", "img/p/appliance-480.webp"),
    ("garage-cleanouts", "Garage cleanouts", "Down to the slab", "img/p/garage-820.webp", "img/p/garage-480.webp"),
    ("estate-cleanouts", "Estate cleanouts", "Whole house", "img/p/estate-820.webp", "img/p/estate-480.webp"),
    ("hot-tub-removal", "Hot tub removal", "Broken down and hauled", "img/hottub.jpg", None),
    ("yard-debris", "Yard debris", "Limbs, fence, brush", "img/p/yard-820.webp", "img/p/yard-480.webp"),
    ("construction-debris", "Construction debris", "After the remodel", "img/debris.jpg", None),
    ("same-day-junk-removal", "Same-day removal", "Often, when schedule allows", "img/p/card-sameday-820.webp", "img/p/card-sameday-480.webp"),
]

REVIEW_SETS = {
    "appliance": [5, 0, 8],
    "furniture": [0, 1, 3],
    "garage": [2, 0, 4],
    "estate": [4, 3, 0],
    "hottub": [8, 9, 10],
    "yard": [3, 9, 10],
    "samesameday": [0, 1, 4],
    "city": [3, 10, 9],
    "index": [0, 4, 3],
}

AVATAR_COLORS = ["#B32A25", "#9E241F", "#c9736f"]


def category_for(slug: str) -> str:
    if slug == "index":
        return "index"
    if "appliance" in slug:
        return "appliance"
    if "garage" in slug:
        return "garage"
    if "estate" in slug:
        return "estate"
    if "yard" in slug:
        return "yard"
    if "hot-tub" in slug:
        return "hottub"
    if "construction" in slug:
        return "yard"
    if "same-day" in slug:
        return "samesameday"
    if "furniture" in slug or "couch" in slug or "mattress" in slug:
        return "furniture"
    if slug.startswith("junk-removal-"):
        return "city"
    return "city"


PHOTO_DIMS = {
    "img/p/card-furniture-820.webp": (820, 547),
    "img/p/appliance-820.webp": (820, 547),
    "img/p/garage-820.webp": (820, 547),
    "img/p/card-estate-820.webp": (820, 547),
    "img/p/yard-820.webp": (820, 547),
    "img/hottub.jpg": (1300, 867),
    "img/debris.jpg": (1300, 867),
    "img/p/card-sameday-820.webp": (820, 547),
    "img/p/real-rig-960.webp": (960, 640),
    "img/p/rig-loaded-1100.webp": (1100, 733),
}


def photo_for(slug: str):
    """Returns (src, srcset_480, alt) relative to img/, no leading '../'."""
    if "appliance" in slug:
        return ("img/p/appliance-820.webp", "img/p/appliance-480.webp", "Appliances ready for pickup")
    if "garage" in slug:
        return ("img/p/garage-820.webp", "img/p/garage-480.webp", "Garage cleanout in progress")
    if "estate" in slug:
        return ("img/p/card-estate-820.webp", "img/p/card-estate-480.webp", "Estate cleanout")
    if "yard" in slug:
        return ("img/p/yard-820.webp", "img/p/yard-480.webp", "Yard debris removal")
    if "hot-tub" in slug:
        return ("img/hottub.jpg", None, "Hot tub removal")
    if "construction" in slug:
        return ("img/debris.jpg", None, "Construction debris removal")
    if "same-day" in slug:
        return ("img/p/card-sameday-820.webp", "img/p/card-sameday-480.webp", "Same-day junk removal")
    if "furniture" in slug or "couch" in slug or "mattress" in slug:
        return ("img/p/card-furniture-820.webp", "img/p/card-furniture-480.webp", "Furniture ready for pickup")
    if slug.startswith("junk-removal-") or slug == "index":
        # city / overview pages alternate between the two real-rig photos
        h = int(hashlib.md5(slug.encode()).hexdigest(), 16)
        if h % 2 == 0:
            return ("img/p/real-rig-960.webp", "img/p/real-rig-480.webp", "Todd loading the trailer on a North Texas driveway")
        return ("img/p/rig-loaded-1100.webp", "img/p/rig-loaded-480.webp", "Trailer loaded with junk ready to haul")
    return ("img/p/rig-loaded-1100.webp", "img/p/rig-loaded-480.webp", "Trailer loaded with junk ready to haul")


def initials(name: str) -> str:
    parts = [p for p in re.split(r"[\s.]+", name) if p]
    letters = [p[0].upper() for p in parts if p[0].isalpha()][:2]
    return "".join(letters) if letters else "?"


def build_review_card(idx: int, color: str) -> str:
    r = REVIEWS[idx]
    stars = "".join(STAR_SVG for _ in range(r["stars"]))
    tags = "".join(f'<span class="tag-pill">{t[0].upper() + t[1:]}</span>' for t in r["tags"][:3])
    return f'''<article class="review-card" data-tags="{",".join(r["tags"])}">
          <div class="review-top">
            <span class="avatar" style="background:{color}">{initials(r["name"])}</span>
            <div class="review-who"><span class="name">{r["name"]}</span><span class="when">{r["when"]}</span></div>
          </div>
          <div class="review-stars">{stars}</div>
          <p class="review-text">{r["text"]}</p>
          <div class="tag-pills">{tags}</div>
        </article>'''


def build_reviews_section(slug: str) -> str:
    cat = category_for(slug)
    idxs = REVIEW_SETS.get(cat, REVIEW_SETS["city"])
    cards = "\n        ".join(build_review_card(i, AVATAR_COLORS[n % 3]) for n, i in enumerate(idxs))
    return f'''<section class="svc-reviews">
  <div class="wrap">
    <div class="section-head reveal">
      <h2>What people say after the truck leaves.</h2>
      <p>Real Google reviews, quoted as written.</p>
    </div>
    <div class="svc-review-grid reveal-group">
        {cards}
    </div>
  </div>
</section>'''


def build_other_services(slug: str) -> str:
    names = [c[0] for c in CORE8]
    if slug in names:
        i = names.index(slug)
        rotated = CORE8[i + 1:] + CORE8[:i]
        picks = rotated[:4]
    else:
        h = int(hashlib.md5(slug.encode()).hexdigest(), 16) % 8
        rotated = CORE8[h:] + CORE8[:h]
        picks = rotated[:4]
    tiles = []
    for slug8, title, sub, img, img480 in picks:
        srcset = f' srcset="../{img480} 480w, ../{img} 820w" sizes="(max-width:560px) 100vw, 25vw"' if img480 else ""
        tiles.append(f'''<a class="svc-tile" href="{slug8}.html">
        <img src="../{img}"{srcset} alt="{title}" loading="lazy">
        <div class="svc-tile-content"><div><h3>{title}</h3><p>{sub}</p></div><span class="svc-tile-arrow">{ARROW_SVG}</span></div>
      </a>''')
    tiles_html = "\n      ".join(tiles)
    return f'''<section class="svc-other">
  <div class="wrap">
    <div class="section-head reveal">
      <h2>Other services.</h2>
      <p>If this is not quite the job, one of these probably is.</p>
    </div>
    <div class="svc-other-grid reveal-group">
      {tiles_html}
    </div>
  </div>
</section>'''


CONTACT_BAND = f'''<section class="contact-band" id="contact">
  <div class="wrap">
    <h2 class="reveal">Send the photo now.</h2>
    <p class="reveal">Open 7am to 8pm, every day. Text, call or email, whichever is easier.</p>
    <div class="cta-row reveal">
      <a class="btn-primary" href="{SMS_HREF}">
        {SMS_ICON}
        Text a photo
      </a>
      <a class="call-quiet" href="{TEL_HREF}">Call (214) 277-9069</a>
    </div>
    <p class="cities">Frisco, Plano, McKinney, Prosper, Allen, Little Elm &middot; <a href="../contact">Or use the contact page</a></p>
  </div>
</section>'''

ASIDE_CARD = '''<aside class="svc-aside-card">
        <h2>Send the photo now</h2>
        <p>Open 7am to 8pm, every day. Text a photo and we text back a firm price before anyone drives out.</p>
        <a class="btn-primary" href="{sms}">
          {icon}
          Text a photo
        </a>
      </aside>'''.format(sms=SMS_HREF, icon=SMS_ICON)


def extract(pattern, text, flags=re.DOTALL):
    m = re.search(pattern, text, flags)
    return m.group(1) if m else None


def transform_index_body(body_main: str) -> str:
    """services/index.html lists every service + every city instead of one
    topic. Turn its rows--photo nav into a homepage-style svc-grid, keep the
    by-city list (now hairline-styled by the generic <ul> pass), same words."""
    nav_match = re.search(r'<nav class="rows rows--photo"[^>]*>(.*?)</nav>', body_main, re.DOTALL)
    if not nav_match:
        return body_main
    nav_inner = nav_match.group(1)
    links = re.findall(
        r'<a href="([^"]+)"><img src="([^"]+)"[^>]*srcset="([^"]*)"[^>]*alt="([^"]*)"[^>]*>'
        r'<span>([^<]+)\s*<small>(.*?)</small></span></a>',
        nav_inner,
        re.DOTALL,
    )
    not_sure = re.search(r'<a href="([^"]+)"><span>([^<]+)\s*<small>(.*?)</small></span></a>\s*$', nav_inner, re.DOTALL)

    # The homepage's svc-tile overlay text (final.css, not editable here) is
    # only readable at homepage-short lengths ("Couches, dressers, beds").
    # This page's own service descriptions are full sentences, so listing
    # them as photo-tile overlays reliably fails WCAG contrast low on the
    # gradient. A plain hairline list (the same component as the by-city
    # list right below it) keeps every original word, fully legible, no
    # image-overlay contrast risk.
    full_list_items = []
    for href, img, srcset, alt, title, desc in links:
        dims = ' width="820" height="547"' if img.endswith("-820.webp") else ""
        full_list_items.append(
            f'<li><a href="{href}.html">'
            f'<img class="svc-list-thumb" src="{img}" srcset="{srcset}" sizes="64px"{dims} alt="" loading="lazy">'
            f'<span><strong>{title.strip()}</strong> {desc}</span></a></li>'
        )
    full_list = '<ul class="svc-list svc-list--photo">' + "".join(full_list_items) + '</ul>'

    tail = ""
    if not_sure:
        href, title, desc = not_sure.groups()
        tail = f'\n    <p class="svc-not-sure"><a href="{href}"><strong>{title.strip()}</strong> {desc}</a></p>'

    replacement = full_list + tail
    return body_main[: nav_match.start()] + replacement + body_main[nav_match.end():]


def process(path: Path):
    text = path.read_text(encoding="utf-8")
    slug = path.stem  # e.g. 'furniture-removal' or 'index'

    breadcrumbs = extract(r'<p class="breadcrumbs">(.*?)</p>', text)
    h1 = extract(r"<h1>(.*?)</h1>", text)
    # lead paragraph: the <p> right after h1, before the cta-row div
    lead = extract(r"</h1>\s*<p>(.*?)</p>\s*<div class=\"cta-row\">", text)

    # main body content lives in rail-body > section > .wrap
    rail_body = extract(r'<div class="rail-body">\s*<section>\s*<div class="wrap">(.*?)</div>\s*</section>\s*</div>', text)
    if rail_body is None:
        raise SystemExit(f"Could not locate rail-body content in {path}")

    # peel off the FAQ block if present
    faq_items_html = None
    m = re.search(r'<h2>Frequently [Aa]sked [Qq]uestions</h2>\s*<div class="faq">(.*?)</div>\s*$', rail_body, re.DOTALL)
    body_main = rail_body
    if m:
        faq_items_html = m.group(1)
        body_main = rail_body[: m.start()].rstrip()

    if slug == "index":
        body_main = transform_index_body(body_main)

    # style tweaks that keep every word: callout -> svc-callout, bare <ul> -> svc-list
    body_main = body_main.replace('<div class="callout">', '<div class="svc-callout">')
    body_main = body_main.replace("<ul>", '<ul class="svc-list">')

    faq_section = ""
    if faq_items_html:
        # each <details><summary>Q</summary><p>A</p></details> -> wrap answer in .faq-body
        def wrap_faq(m):
            summary, body = m.group(1), m.group(2)
            return f'<details><summary>{summary}</summary><div class="faq-body">{body}</div></details>'

        faq_list = re.sub(
            r"<details><summary>(.*?)</summary>(.*?)</details>",
            wrap_faq,
            faq_items_html,
            flags=re.DOTALL,
        )
        faq_section = f'''<section class="svc-faq" id="faq">
  <div class="wrap">
    <div class="faq-grid">
      <div class="reveal">
        <h2 style="font-size:clamp(28px,3.4vw,40px);">Before you text.</h2>
        <p style="margin-top:12px;color:var(--muted);font-size:17px;line-height:1.55;">Common questions before you send the photo.</p>
      </div>
      <div class="faq-list reveal">{faq_list}
      </div>
    </div>
  </div>
</section>'''

    src, src480, alt = photo_for(slug)
    srcset = f' srcset="../{src480} 480w, ../{src} 820w" sizes="(max-width:900px) 88vw, 40vw"' if src480 else ""
    dims = PHOTO_DIMS.get(src, (820, 547))
    dims_attr = f' width="{dims[0]}" height="{dims[1]}"'

    hero = f'''<section class="svc-hero">
  <div class="wrap svc-hero-grid">
    <div class="svc-hero-copy">
      <p class="svc-breadcrumbs">{breadcrumbs}</p>
      <h1>{h1}</h1>
      <p class="svc-hero-lead">{lead}</p>
      <div class="cta-row">
        <a class="btn-primary" href="{SMS_HREF}">
          {SMS_ICON}
          Text a photo
        </a>
        <a class="call-quiet" href="{TEL_HREF}">
          {CALL_ICON}
          Call (214) 277-9069
        </a>
      </div>
      <div class="rating-line">
        <span class="stars">{"".join(STAR_SVG for _ in range(5))}</span>
        <span><strong>4.9</strong> on Google</span>
      </div>
    </div>
    <div class="svc-hero-photo">
      <div class="video-window">
        <img src="../{src}"{srcset}{dims_attr} alt="{alt}" loading="eager" fetchpriority="high">
        <div class="scrim"></div>
      </div>
    </div>
  </div>
</section>'''

    body_section = f'''<section class="svc-body">
  <div class="wrap svc-body-grid">
    <div class="svc-content">{body_main}
    </div>
    {ASIDE_CARD}
  </div>
</section>'''

    reviews_section = build_reviews_section(slug)
    other_section = "" if slug == "index" else build_other_services(slug)

    new_main_inner = "\n\n".join(
        s for s in [hero, body_section, reviews_section, faq_section, other_section, CONTACT_BAND] if s
    )

    # splice into the full document, replacing everything between <main ...> and </main>
    new_text, n = re.subn(
        r'(<main id="main" tabindex="-1">).*?(</main>)',
        lambda m: m.group(1) + "\n" + new_main_inner + "\n" + m.group(2),
        text,
        flags=re.DOTALL,
    )
    if n != 1:
        raise SystemExit(f"Could not splice <main> in {path}")

    # drop style.css link
    new_text = re.sub(r'<link rel="stylesheet" href="\.\./style\.css\?v=\d+">\n?', "", new_text)
    # add pages-svc.css right after final.css link
    new_text = re.sub(
        r'(<link rel="stylesheet" href="\.\./assets/final\.css\?v=1">)',
        r'\1\n<link rel="stylesheet" href="../assets/pages-svc.css?v=1">',
        new_text,
        count=1,
    )
    # drop piece.js script tag (3D voxel piece dropped site-wide per Jack's call)
    new_text = re.sub(r'<script src="\.\./assets/piece\.js" defer></script>\n?', "", new_text)
    # drop the old load-progress bar + its inline script (final.js already
    # handles header scroll state; load-progress had no equivalent in the
    # new design and is not part of the homepage look)
    new_text = re.sub(
        r'<div class="load-progress"[^>]*>.*?</div>\s*<script>\s*\(function\(\)\{var s=document\.getElementById\(\'lp\'\).*?\}\)\(\);\s*</script>\n?',
        "",
        new_text,
        flags=re.DOTALL,
    )
    # drop the vestigial header-scroll inline script block (final.js covers
    # `.site-header.scrolled` already; the old selector `header.site` never
    # even matched this markup)
    new_text = re.sub(
        r"<script>\s*\(function\(\)\{var h=document\.querySelector\('header\.site'\);.*?\}\)\(\);\s*</script>\n?",
        "",
        new_text,
        flags=re.DOTALL,
    )

    path.write_text(new_text, encoding="utf-8")
    return True


def main():
    pages = sorted(SVC.glob("*.html"))
    done = []
    for p in pages:
        process(p)
        done.append(p.name)
    print(f"Rewrote {len(done)} pages:")
    for d in done:
        print(" -", d)


if __name__ == "__main__":
    main()
