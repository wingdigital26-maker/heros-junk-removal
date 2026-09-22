#!/usr/bin/env python
"""Give every page an action above the fold.

Measured 2026-09-22 (round 2): unifying the chrome removed the old black
.emergency-strip, which had been the only saturated call to action in the first
viewport on inner pages. conversion_lint then failed W1 ("no primary CTA or
input in the first viewport") on those pages, and 53 of 81 pages had no early
call to action at all. THE ONE CONVERSION for this site is a homeowner texting
a photo, so a page that offers no way to do that above the fold is broken for
its only job.

services/index.html already had the right pattern, so this copies it rather
than inventing one: a .btn-row holding the red primary "Text a photo, get a
price" and the quiet "Call" link. The nav's own CTA stays dark, so each page
still has exactly one FILLED primary per view (conversion rule B3/W2).

Usage:  python scripts/add_hero_cta.py [--apply]
"""
import argparse, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
HERO = re.compile(r'(<div class="page-hero[^"]*">.*?)(\n  </div>\n</div>)', re.S)
ROW = ('\n    <div class="btn-row">'
       '\n      <a class="btn btn-primary" href="sms:+12142779069?&amp;body='
       'Hi%2C%20here%20is%20a%20photo%20of%20what%20I%20need%20gone.">'
       'Text a photo, get a price</a>'
       '\n      <a class="btn btn-ghost" href="tel:+12142779069">'
       'Call (214) 277-9069</a>'
       '\n    </div>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()
    changed = skipped = nohero = 0
    for p in sorted(ROOT.rglob('*.html')):
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith(('.visual/', 'scripts/')) or rel == 'index.html':
            continue                      # the homepage hero is its own design
        s = p.read_text(encoding='utf-8')
        m = HERO.search(s)
        if not m:
            nohero += 1
            continue
        if 'btn-row' in m.group(1):
            skipped += 1
            continue
        s2 = s[:m.start()] + m.group(1) + ROW + m.group(2) + s[m.end():]
        changed += 1
        print('%-58s hero CTA added' % rel)
        if a.apply:
            p.write_text(s2, encoding='utf-8')
    print('\n%d added, %d already had one, %d had no .page-hero  (%s)'
          % (changed, skipped, nohero,
             'applied' if a.apply else 'dry run'))


if __name__ == '__main__':
    main()
