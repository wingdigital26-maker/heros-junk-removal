import re, json, os, glob, sys
from html.parser import HTMLParser

ROOT = r"C:\Users\wjack\heros-v3"
BLOG = os.path.join(ROOT, "blog")

files = sorted(glob.glob(os.path.join(BLOG, "*.html")))
posts = [f for f in files if os.path.basename(f) != "index.html"]
index_file = os.path.join(BLOG, "index.html")

def read(f):
    with open(f, "r", encoding="utf-8") as fh:
        return fh.read()

issues = []

def check_titles_desc(f, html, name):
    titles = re.findall(r"<title>(.*?)</title>", html, re.S)
    if len(titles) != 1:
        issues.append(f"{name}: {len(titles)} <title> tags")
    descs = re.findall(r'<meta name="description" content="(.*?)"', html)
    if len(descs) != 1:
        issues.append(f"{name}: {len(descs)} meta description tags")
    return titles, descs

all_titles = {}
all_descs = {}

for f in files:
    html = read(f)
    name = os.path.relpath(f, ROOT).replace("\\", "/")
    titles, descs = check_titles_desc(f, html, name)
    if titles:
        all_titles.setdefault(titles[0], []).append(name)
    if descs:
        all_descs.setdefault(descs[0], []).append(name)

    # canonical
    canon = re.findall(r'<link rel="canonical" href="(.*?)"', html)
    if len(canon) != 1:
        issues.append(f"{name}: {len(canon)} canonical tags")

    # h1 count
    h1s = re.findall(r"<h1[ >]", html)
    if len(h1s) != 1:
        issues.append(f"{name}: {len(h1s)} h1 tags")

    # heading skip check (only within main/article content, roughly whole body)
    heads = re.findall(r"<h([1-6])[ >]", html)
    heads = [int(x) for x in heads]
    prev = 0
    for h in heads:
        if prev != 0 and h > prev + 1:
            issues.append(f"{name}: heading skip from h{prev} to h{h}")
        prev = h

    # em dash
    if "\u2014" in html:
        cnt = html.count("\u2014")
        issues.append(f"{name}: {cnt} em dash(es)")

    # "estimate" as Hero's own promise (rough heuristic, flag all then filter manually)
    for m in re.finditer(r"estimate", html, re.I):
        start = max(0, m.start()-80)
        end = min(len(html), m.end()+80)
        snippet = html[start:end].replace("\n", " ")
        issues.append(f"{name}: 'estimate' context: ...{snippet}...")

    # JSON-LD parse
    for jm in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            json.loads(jm.group(1))
        except Exception as e:
            issues.append(f"{name}: JSON-LD parse error: {e}")

    # images: width/height/alt
    for im in re.finditer(r"<img\b([^>]*)>", html):
        attrs = im.group(1)
        if 'width=' not in attrs or 'height=' not in attrs:
            issues.append(f"{name}: img missing width/height: {attrs[:80]}")
        if 'alt=' not in attrs:
            issues.append(f"{name}: img missing alt: {attrs[:80]}")

    # internal hrefs resolve on disk
    for hm in re.finditer(r'href="([^"]+)"', html):
        href = hm.group(1)
        if href.startswith("http") or href.startswith("mailto:") or href.startswith("tel:") or href.startswith("sms:") or href.startswith("#"):
            continue
        # strip query/hash
        path = href.split("#")[0].split("?")[0]
        if not path:
            continue
        target = os.path.normpath(os.path.join(os.path.dirname(f), path))
        candidates = [target, target + ".html", os.path.join(target, "index.html")]
        if not any(os.path.exists(c) for c in candidates):
            issues.append(f"{name}: broken href {href}")

print("=== duplicate titles ===")
for t, names in all_titles.items():
    if len(names) > 1:
        print(t, "->", names)

print("=== duplicate descriptions ===")
for d, names in all_descs.items():
    if len(names) > 1:
        print(d[:60], "->", names)

print(f"\n=== {len(issues)} issues ===")
for i in issues:
    print(i)
