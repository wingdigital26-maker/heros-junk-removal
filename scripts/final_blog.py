#!/usr/bin/env python3
"""
Re-runnable builder: brings every blog post (and blog/index.html) up to the
homepage's approved look (assets/final.css + a new assets/pages-blog.css).

Never edits: page words, headings, FAQ answers, prices, blog text, internal
links, <head>/SEO/JSON-LD/canonical. Only restructures wrapper HTML around
the untouched <article class="post"> block, swaps stylesheet/script links,
and adds new sections (hero image, 2 reviews, keep-reading, contact band)
built from real site assets (brand/reviews.json, img/, img/p/).

Run: python scripts/final_blog.py
"""
import re
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog"
REVIEWS = json.loads((ROOT / "brand" / "reviews.json").read_text(encoding="utf-8"))["reviews"]

_DIMS_CACHE = {}


def img_dims(rel_src: str):
    """Pixel dims for a blog-relative image path like '../img/p/foo.webp' (avoids layout shift / W20)."""
    if rel_src not in _DIMS_CACHE:
        local = (BLOG / rel_src).resolve()
        with Image.open(local) as im:
            _DIMS_CACHE[rel_src] = im.size
    return _DIMS_CACHE[rel_src]

PHONE_TEL = "tel:+12142779069"
PHONE_SMS = "sms:+12142779069?&amp;body=Hi%2C%20here%20is%20a%20photo%20of%20what%20I%20need%20gone."
PHONE_DISPLAY = "(214) 277-9069"

# ---------------------------------------------------------------------------
# Per-post hero image (real assets only, chosen by topic). All paths are
# relative to blog/, i.e. "../img/..." on disk.
# ---------------------------------------------------------------------------
IMG = "../img/p/"
IMG_ROOT = "../img/"
HERO_IMAGE = {
    "above-ground-pool-removal": (IMG_ROOT + "hottub.jpg", "A hot tub or above-ground water feature staged for removal"),
    "after-the-estate-sale-what-is-left": (IMG + "estate-820.webp", "An estate cleanout in progress"),
    "apartment-junk-removal": (IMG + "job-curbside-pickup-820.webp", "Curbside pickup job"),
    "appliance-and-electronics-disposal-north-texas": (IMG + "appliance-820.webp", "Appliances ready for pickup"),
    "attic-cleanout-what-is-up-there": (IMG + "job-garage-clearout-900.webp", "A cleared space after a cleanout"),
    "brush-piles-tree-limbs-city-collection": (IMG + "yard-820.webp", "Yard debris removal"),
    "bulky-trash-the-city-skipped": (IMG + "rig-loaded-1100.webp", "Trailer loaded with junk ready to haul"),
    "clearing-a-room-for-a-hospital-bed": (IMG_ROOT + "crew-loading.jpg", "Crew loading the truck"),
    "clearing-rooms-before-foundation-or-plumbing-work": (IMG + "job-garage-clearout-900.webp", "A cleared space after a cleanout"),
    "closet-cleanout-clothes-soft-goods": (IMG + "card-furniture-820.webp", "Couch and furniture ready for pickup"),
    "construction-debris-after-a-remodel": (IMG_ROOT + "debris.jpg", "Construction debris removal"),
    "cribs-bunk-beds-outgrown-kids-room": (IMG + "card-furniture-820.webp", "Furniture ready for pickup"),
    "donate-furniture-dfw": (IMG + "card-furniture-820.webp", "Furniture ready for pickup"),
    "downsizing-a-parent-into-assisted-living": (IMG + "card-estate-820.webp", "An estate cleanout in progress"),
    "dumpster-rental-vs-junk-removal": (IMG + "rig-loaded-1100.webp", "Trailer loaded with junk ready to haul"),
    "estate-cleanout-checklist": (IMG + "estate-820.webp", "An estate cleanout in progress"),
    "eviction-cleanout-rental-property": (IMG + "job-curbside-pickup-820.webp", "Curbside pickup job"),
    "fence-and-deck-teardown-debris": (IMG_ROOT + "debris.jpg", "Construction debris removal"),
    "garage-cleanout-checklist": (IMG + "job-garage-cleanout-960.webp", "A garage stacked with items waiting for pickup"),
    "garage-shelving-workbench-removal": (IMG + "garage-820.webp", "Garage cleanout"),
    "guest-room-before-the-holidays": (IMG + "card-furniture-820.webp", "Furniture ready for pickup"),
    "hoa-violation-yard-cleanup": (IMG + "yard-820.webp", "Yard debris removal"),
    "hoarder-house-junk-removal": (IMG + "job-garage-clearout-900.webp", "A cleared space after a cleanout"),
    "home-office-furniture-after-back-to-the-office": (IMG + "card-furniture-820.webp", "Furniture ready for pickup"),
    "hot-tub-shed-playset-removal": (IMG_ROOT + "hottub.jpg", "Hot tub removal"),
    "how-junk-removal-works": (IMG + "card-sameday-820.webp", "Same-day junk removal"),
    "inherited-house-cleanout-keeping-it": (IMG + "estate-820.webp", "An estate cleanout in progress"),
    "mattress-disposal-dfw": (IMG + "card-furniture-820.webp", "Furniture ready for pickup"),
    "medical-equipment-removal-after-care-ends": (IMG_ROOT + "crew-loading.jpg", "Crew loading the truck"),
    "moving-out-what-to-haul-instead-of-moving": (IMG + "rig-loaded-1100.webp", "Trailer loaded with junk ready to haul"),
    "new-build-move-in-boxes-and-builder-leftovers": (IMG_ROOT + "debris.jpg", "Moving and construction leftovers"),
    "office-and-small-commercial-cleanouts": (IMG + "real-rig-960.webp", "Todd loading the trailer in a driveway"),
    "old-carpet-and-pad-after-flooring-install": (IMG_ROOT + "debris.jpg", "Flooring debris removal"),
    "old-furniture-removal-getting-it-out": (IMG + "card-furniture-820.webp", "Couch and furniture ready for pickup"),
    "old-grill-patio-furniture-end-of-season": (IMG + "yard-820.webp", "Yard and patio debris removal"),
    "out-of-state-cleanout-remote-owner": (IMG_ROOT + "house-hero-sm.webp", "A North Texas house ready for a cleanout"),
    "piano-pool-table-safe-removal": (IMG + "card-furniture-820.webp", "Furniture ready for pickup"),
    "previous-owner-left-it-behind": (IMG + "job-garage-clearout-900.webp", "A cleared space after a cleanout"),
    "rental-property-cleanout": (IMG + "job-curbside-pickup-820.webp", "Curbside pickup job"),
    "same-day-junk-removal-what-typical-means": (IMG + "card-sameday-820.webp", "Same-day junk removal"),
    "shed-cleanout-whats-inside": (IMG + "garage-820.webp", "A cleared storage space"),
    "slab-leak-soaked-carpet-drywall-furniture": (IMG_ROOT + "debris.jpg", "Water-damaged material removal"),
    "storage-unit-junk-removal": (IMG + "job-garage-clearout-900.webp", "A cleared space after a cleanout"),
    "treadmills-home-gyms-bonus-room": (IMG + "card-furniture-820.webp", "Furniture ready for pickup"),
    "water-heater-softener-utility-closet": (IMG + "appliance-820.webp", "Appliances ready for pickup"),
    "what-junk-removal-will-and-will-not-take": (IMG + "team-todd-nash-900.webp", "Todd and Nash with the truck and trailer"),
    "what-to-clear-before-listing-photos": (IMG_ROOT + "house-hero-sm.webp", "A North Texas house ready for listing photos"),
    "where-your-junk-goes-after-pickup": (IMG + "team-todd-nash-900.webp", "Todd and Nash with the truck and trailer"),
    "who-comes-to-your-house-junk-removal": (IMG + "team-todd-nash-900.webp", "Todd and Nash with the truck and trailer"),
    "workshop-hobby-room-cleanout": (IMG + "garage-820.webp", "A workshop cleared during a cleanout"),
}

# ---------------------------------------------------------------------------
# Reviews: preferred pair by topic keyword in the slug, else rotate defaults.
# ---------------------------------------------------------------------------
REVIEWS_BY_NAME = {r["name"]: r for r in REVIEWS}
DEFAULT_ROTATION = [
    ("Hamed AlAqeel", "Sophia Yang"),
    ("Calvin Mullinax Jr.", "charlie mclaren"),
    ("Boo Moerschell", "Dustin Trott"),
    ("Evan Wright", "p1xylz"),
]
KEYWORD_PAIRS = [
    (("garage", "shelving", "workbench"), ("Caden Boyd", "Calvin Mullinax Jr.")),
    (("appliance", "water-heater", "fridge", "refrigerator"), ("Dex. Camerón", "Boo Moerschell")),
    (("same-day", "how-junk-removal-works"), ("Hamed AlAqeel", "Hayden Hudnall")),
    (("estate", "downsizing", "inherited"), ("Calvin Mullinax Jr.", "Hamed AlAqeel")),
    (("price", "dumpster-rental"), ("Dustin Trott", "Dex. Camerón")),
]
AVATAR_COLORS = ["#B32A25", "#9E241F", "#c9736f"]


def initials(name: str) -> str:
    parts = [p for p in re.split(r"[.\s]+", name) if p]
    if len(parts) == 1:
        return parts[0][0].upper()
    return (parts[0][0] + parts[1][0]).upper()


def pick_reviews(slug: str, idx: int):
    for keys, pair in KEYWORD_PAIRS:
        if any(k in slug for k in keys):
            return [REVIEWS_BY_NAME[n] for n in pair]
    a, b = DEFAULT_ROTATION[idx % len(DEFAULT_ROTATION)]
    return [REVIEWS_BY_NAME[a], REVIEWS_BY_NAME[b]]


STAR_SVG = ('<svg viewBox="0 0 24 24" fill="currentColor"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 '
            '18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26"/></svg>')


def review_card_html(review, color_idx):
    stars = "\n            ".join([STAR_SVG] * review["stars"])
    tags = ", ".join(review.get("tags", []))
    color = AVATAR_COLORS[color_idx % len(AVATAR_COLORS)]
    return f'''        <article class="review-card" data-tags="{tags}">
          <div class="review-top">
            <span class="avatar" style="background:{color}">{initials(review["name"])}</span>
            <div class="review-who"><span class="name">{review["name"]}</span><span class="when">{review["when"]}</span></div>
          </div>
          <div class="review-stars">
            {stars}
          </div>
          <p class="review-text">{review["text"]}</p>
        </article>'''


# ---------------------------------------------------------------------------
# Build slug -> {title, tag, excerpt} from the existing blog/index.html cards
# (used for the "keep reading" fallback and the blog index rebuild).
# ---------------------------------------------------------------------------
def load_index_cards():
    html = (BLOG / "index.html").read_text(encoding="utf-8")
    chunks = html.split('<div class="card post-card">')[1:]
    cards = []
    for chunk in chunks:
        body = chunk.split("</div>\n      </div>")[0]
        tag = re.search(r'<span class="tag">([^<]*)</span>', body).group(1)
        href, title = re.search(r'<h2><a href="([^"]+)">([^<]*)</a></h2>', body).groups()
        excerpt = re.search(r'<h2>.*?</h2>\s*<p>(.*?)</p>', body, re.S).group(1).strip()
        meta = re.search(r'<p class="post-meta">([^<]*)</p>', body).group(1)
        cards.append({"slug": href, "title": title, "tag": tag, "excerpt": excerpt, "meta": meta})
    return cards


INDEX_CARDS = load_index_cards()
SLUG_INFO = {c["slug"]: c for c in INDEX_CARDS}
ALL_SLUGS = set(SLUG_INFO.keys())


def find_body_links(article_html: str):
    """Internal same-directory post links already inside the article body."""
    hrefs = re.findall(r'href="([^"]+)"', article_html)
    out = []
    for h in hrefs:
        if h.startswith(("http", "../", "#", "tel:", "sms:", "mailto:")):
            continue
        slug = h.split("#")[0]
        if slug in ALL_SLUGS and slug not in out:
            out.append(slug)
    return out


def keep_reading_slugs(this_slug: str, article_html: str):
    picks = [s for s in find_body_links(article_html) if s != this_slug][:3]
    if len(picks) < 3:
        tag = SLUG_INFO[this_slug]["tag"]
        neighbours = [c["slug"] for c in INDEX_CARDS if c["tag"] == tag and c["slug"] != this_slug and c["slug"] not in picks]
        picks += neighbours[: 3 - len(picks)]
    if len(picks) < 3:
        others = [c["slug"] for c in INDEX_CARDS if c["slug"] != this_slug and c["slug"] not in picks]
        picks += others[: 3 - len(picks)]
    return picks[:3]


def keep_reading_html(slugs, path_prefix=""):
    cards = []
    for s in slugs:
        info = SLUG_INFO[s]
        img_src, img_alt = HERO_IMAGE.get(s, (IMG_ROOT + "hero-junk.jpg", "Junk removal job"))
        w, h = img_dims(img_src)
        cards.append(f'''      <a class="svc-tile" href="{path_prefix}{s}">
        <img src="{path_prefix}{img_src}" alt="{img_alt}" width="{w}" height="{h}" loading="lazy">
        <div class="svc-tile-content"><div><h3>{info["title"]}</h3></div><span class="svc-tile-arrow"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17 17 7M7 7h10v10"/></svg></span></div>
      </a>''')
    return "\n".join(cards)


CONTACT_BAND = f'''<section class="contact-band" id="contact">
  <div class="wrap">
    <h2 class="reveal">Send the photo now.</h2>
    <p class="reveal">Open 7am to 8pm, every day. Text, call or email, whichever is easier.</p>
    <div class="cta-row reveal">
      <a class="btn-primary" href="{PHONE_SMS}">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>
        Text a photo
      </a>
      <a class="call-quiet" href="{PHONE_TEL}">Call {PHONE_DISPLAY}</a>
    </div>
    <p class="cities">Frisco, Plano, McKinney, Prosper, Allen, Little Elm &middot; <a href="../contact">Or use the contact page</a></p>
  </div>
</section>'''


def process_post(path: Path, idx: int):
    slug = path.stem
    html = path.read_text(encoding="utf-8")
    original = html

    # --- <head>: swap stylesheet, drop nothing else (SEO/JSON-LD untouched) ---
    html = html.replace('<link rel="stylesheet" href="../style.css?v=18">\n', "")
    html = html.replace(
        '<link rel="stylesheet" href="../assets/final.css?v=1">',
        '<link rel="stylesheet" href="../assets/final.css?v=1">\n<link rel="stylesheet" href="../assets/pages-blog.css?v=1">',
    )

    # --- post header: keep breadcrumb/H1/meta words, drop old icon + CTA row ---
    m = re.search(
        r'<div class="page-hero ph-blog">.*?</div>\s*</div>\s*</div>\n',
        html, re.S,
    )
    if not m:
        raise SystemExit(f"header block not found in {path}")
    header_block = m.group(0)
    breadcrumb = re.search(r'(<p class="breadcrumbs">.*?</p>)', header_block, re.S).group(1)
    h1 = re.search(r'(<h1>.*?</h1>)', header_block, re.S).group(1)
    meta_p = re.search(r'</h1>\s*(<p>.*?</p>)', header_block, re.S).group(1)

    img_src, img_alt = HERO_IMAGE.get(slug, (IMG_ROOT + "hero-junk.jpg", "Junk removal job in North Texas"))
    hero_w, hero_h = img_dims(img_src)
    new_header = f'''<div class="post-header">
  <div class="wrap">
    {breadcrumb}
    {h1}
    {meta_p.replace('<p>', '<p class="post-date-meta">')}
  </div>
</div>

<div class="wrap">
  <div class="post-hero-media">
    <img src="{img_src}" alt="{img_alt}" width="{hero_w}" height="{hero_h}" loading="eager" decoding="async">
  </div>
</div>
'''
    html = html[: m.start()] + new_header + html[m.end():]

    # --- wrap the untouched <article class="post"> in a width-constrained column ---
    art_m = re.search(r'(<section>\s*<div class="wrap">\s*)(<article class="post">.*?</article>)(\s*</div>\s*</section>)', html, re.S)
    if not art_m:
        raise SystemExit(f"article block not found in {path}")
    article_html = art_m.group(2)
    new_section = (
        '<section class="section post-section">\n  <div class="wrap">\n    <div class="post-col">\n      '
        + article_html
        + '\n    </div>\n  </div>\n</section>'
    )
    html = html[: art_m.start()] + new_section + html[art_m.end():]

    # --- reviews (2 cards matched to topic) ---
    reviews = pick_reviews(slug, idx)
    review_cards = "\n".join(review_card_html(r, i) for i, r in enumerate(reviews))
    reviews_section = f'''<section class="section post-reviews-section">
  <div class="wrap">
    <div class="section-head reveal">
      <h2>What people say about the work.</h2>
      <p>Google reviews, quoted as written.</p>
    </div>
    <div class="review-cards reveal-group">
{review_cards}
    </div>
  </div>
</section>'''

    # --- keep reading (3 related posts) ---
    slugs = keep_reading_slugs(slug, article_html)
    keep_section = f'''<section class="section keep-reading-section">
  <div class="wrap">
    <div class="section-head reveal">
      <h2>Keep reading.</h2>
    </div>
    <div class="svc-grid keep-grid reveal-group">
{keep_reading_html(slugs)}
    </div>
  </div>
</section>'''

    contact_m = re.search(r'<section class="section section--warm" id="contact">.*?</section>', html, re.S)
    if not contact_m:
        raise SystemExit(f"contact section not found in {path}")
    html = html[: contact_m.start()] + reviews_section + "\n\n" + keep_section + "\n\n" + CONTACT_BAND + html[contact_m.end():]

    # --- drop the 3D piece script + old load-progress bar/scripts ---
    html = re.sub(r'\n<div class="load-progress" aria-hidden="true">.*?</div>\n', "\n", html, flags=re.S)
    html = re.sub(r'\n<script>\n\(function\(\)\{var s=document\.getElementById\(\'lp\'\).*?</script>\n', "\n", html, flags=re.S)
    html = re.sub(r'\n<script>\n\(function\(\)\{var h=document\.querySelector\(\'header\.site\'\).*?</script>\n', "\n", html, flags=re.S)
    html = html.replace('<script src="../assets/piece.js" defer></script>\n', "")

    if html == original:
        print(f"  (no change) {path.name}")
        return
    path.write_text(html, encoding="utf-8")
    print(f"  wrote {path.name}")


def process_index():
    path = BLOG / "index.html"
    html = path.read_text(encoding="utf-8")

    html = html.replace('<link rel="stylesheet" href="../style.css?v=18">\n', "")
    html = html.replace(
        '<link rel="stylesheet" href="../assets/final.css?v=1">',
        '<link rel="stylesheet" href="../assets/final.css?v=1">\n<link rel="stylesheet" href="../assets/pages-blog.css?v=1">',
    )

    # header: breadcrumb + H1 + lead, drop old icon + CTA row
    m = re.search(r'<div class="page-hero ph-blog">.*?</div>\s*</div>\s*</div>\n', html, re.S)
    header_block = m.group(0)
    breadcrumb = re.search(r'(<p class="breadcrumbs">.*?</p>)', header_block, re.S).group(1)
    h1 = re.search(r'(<h1>.*?</h1>)', header_block, re.S).group(1)
    lead_p = re.search(r'</h1>\s*(<p>.*?</p>)', header_block, re.S).group(1)
    new_header = f'''<div class="post-header">
  <div class="wrap">
    {breadcrumb}
    {h1}
    {lead_p.replace('<p>', '<p class="post-date-meta">')}
  </div>
</div>
'''
    html = html[: m.start()] + new_header + html[m.end():]

    # drop the old <figure class="lede">...</figure>
    html = re.sub(r'<figure class="lede">.*?</figure>\n\n', "", html, flags=re.S)

    # add a hero image to every card (first post gets the "featured" wide card)
    parts = html.split('<div class="card post-card">')
    new_parts = [parts[0]]
    for i, chunk in enumerate(parts[1:]):
        inner, rest = chunk.split("\n      </div>", 1)
        featured = " featured" if i == 0 else ""
        href = re.search(r'<a href="([^"]+)">', inner).group(1)
        img_src, img_alt = HERO_IMAGE.get(href, (IMG_ROOT + "hero-junk.jpg", "Junk removal job in North Texas"))
        card_w, card_h = img_dims(img_src)
        loading = "eager" if i == 0 else "lazy"  # the featured card sits in the first viewport
        new_card = (
            f'<div class="card post-card{featured}">\n'
            f'        <a class="card-img" href="{href}" tabindex="-1" aria-hidden="true"><img src="{img_src}" alt="{img_alt}" width="{card_w}" height="{card_h}" loading="{loading}"></a>\n'
            f'        <div class="card-body">{inner}\n        </div>\n      </div>'
        )
        new_parts.append(new_card + rest)
    html = "".join(new_parts)

    # tag the grid wrapper for our own CSS (additive class, same markup)
    html = html.replace('<div class="grid-2" style="margin-top:0">', '<div class="grid-2 blog-grid" style="margin-top:0">')

    # contact band -> homepage markup
    html = re.sub(
        r'<section class="section section--warm" id="contact">.*?</section>',
        CONTACT_BAND,
        html, flags=re.S,
    )

    # drop the 3D piece script + old load-progress bar/scripts
    html = re.sub(r'\n<div class="load-progress" aria-hidden="true">.*?</div>\n', "\n", html, flags=re.S)
    html = re.sub(r'\n<script>\n\(function\(\)\{var s=document\.getElementById\(\'lp\'\).*?</script>\n', "\n", html, flags=re.S)
    html = re.sub(r'\n<script>\n\(function\(\)\{var h=document\.querySelector\(\'header\.site\'\).*?</script>\n', "\n", html, flags=re.S)
    html = html.replace('<script src="../assets/piece.js" defer></script>\n', "")

    path.write_text(html, encoding="utf-8")
    print("  wrote index.html")


def main():
    posts = sorted(p for p in BLOG.glob("*.html") if p.name != "index.html")
    print(f"Processing {len(posts)} posts...")
    for i, p in enumerate(posts):
        process_post(p, i)
    print("Processing blog/index.html...")
    process_index()


if __name__ == "__main__":
    main()
