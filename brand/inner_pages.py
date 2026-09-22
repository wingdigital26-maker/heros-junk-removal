"""Wire the house piece into every inner page (everything except index.html), idempotently.
  - piece.css after styles.css
  - the emergency strip gets an sms link next to the tel link, both 44px targets (piece.css)
  - the compact house mark goes first inside .page-hero .wrap
  - piece.js deferred before </body>
Titles, meta, H1 text and canonicals are never touched.

  python brand/inner_pages.py
"""
import os, re, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SMS = 'sms:+12142779069?&amp;body=Hi%2C%20here%20is%20a%20photo%20of%20what%20I%20need%20gone.'
MARK = ('<div class="hm" aria-hidden="true"><svg viewBox="0 0 34 32">'
        '<path class="hm-house" d="M2 29V14L13 4l11 10v7h-7v8Z"/>'
        '<rect class="hm-b hm-b3" x="27.2" y="4" width="3.2" height="3.2" rx=".7"/>'
        '<rect class="hm-b hm-b2" x="26.4" y="8" width="4.2" height="4.2" rx=".8"/>'
        '<rect class="hm-b hm-b1" x="25" y="13" width="6" height="6" rx="1"/>'
        '</svg></div>')

pages = [p for p in glob.glob(os.path.join(ROOT, "*.html")) + glob.glob(os.path.join(ROOT, "services", "*.html"))
         + glob.glob(os.path.join(ROOT, "blog", "*.html")) if os.path.basename(p) != "index.html" or os.path.dirname(p) != ROOT]

done = skipped = 0
for p in pages:
    s = open(p, encoding="utf-8").read()
    if "assets/piece.css" in s:
        skipped += 1; continue
    rel = "../" if os.path.dirname(p) != ROOT else ""
    n = s.count('<link rel="stylesheet" href="' + rel + 'styles.css">')
    if n != 1 or 'class="page-hero' not in s:
        print("SKIP (no styles.css link or page-hero):", p); continue
    s = s.replace('<link rel="stylesheet" href="' + rel + 'styles.css">',
                  '<link rel="stylesheet" href="' + rel + 'styles.css">\n<link rel="stylesheet" href="' + rel + 'assets/piece.css">')
    # strip: normalise the tel href and add the sms link
    s = re.sub(r'(<div class="emergency-strip">.*?)<a href="tel:2142779069">', r'\1<a href="tel:+12142779069">', s, count=1, flags=re.S)
    s = re.sub(r'(<div class="emergency-strip">.*?<a href="tel:\+12142779069">[^<]*</a>)',
               r'\1 <a class="strip-sms" href="' + SMS + '">Text a photo</a>', s, count=1, flags=re.S)
    # the mark, first inside the hero's wrap
    s = re.sub(r'(<div class="page-hero[^"]*">\s*<div class="wrap">)', r'\1\n    ' + MARK, s, count=1)
    s = s.replace('</body>', '<script src="' + rel + 'assets/piece.js" defer></script>\n</body>', 1)
    open(p, "w", encoding="utf-8").write(s)
    done += 1
print(f"patched {done}, already done {skipped}, total {len(pages)}")
