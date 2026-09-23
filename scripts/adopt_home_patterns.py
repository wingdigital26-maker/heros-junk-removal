#!/usr/bin/env python
"""FRONTIER R9/R11/R12/R13: put the inner pages' BODY on the homepage's patterns.

Jack's direction call, 2026-09-22: the homepage patterns win. Round 4's two
Fable judges independently scored Craft and Beauty at 3 and named one root
cause: below the unified chrome, inner pages still ran a second design system.

This migrates the MARKUP to the classes style.css already defines, rather than
importing the legacy look into the v3 sheet:
  btn-primary -> btn--primary      (legacy .btn is uppercase + old font stack)
  btn-ghost   -> btn--quiet
  btn-row     -> cta-row
  section.cta-band -> the homepage's warm "Send the photo now." closer, so the
      last thing on every page is THE ONE CONVERSION (text a photo) instead of
      a vague "Contact Us".

Usage:  python scripts/adopt_home_patterns.py [--apply]
"""
import argparse, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def prefix(p):
    return '../' * (len(p.relative_to(ROOT).parts) - 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()

    home = (ROOT / 'index.html').read_text(encoding='utf-8')
    m = re.search(r'<section class="section section--warm" id="contact">.*?</section>',
                  home, re.S)
    if not m:
        sys.exit('homepage closer not found')
    closer_tpl = m.group(0)

    n_btn = n_row = n_closer = 0
    changed = 0
    for p in sorted(ROOT.rglob('*.html')):
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith(('.visual/', 'scripts/')) or rel == 'index.html':
            continue
        s = orig = p.read_text(encoding='utf-8')
        pre = prefix(p)

        closer = closer_tpl.replace('href="services/', 'href="%sservices/' % pre)
        closer = closer.replace('href="about"', 'href="%sabout"' % pre)
        closer = closer.replace('href="contact"', 'href="%scontact"' % pre)

        s, k = re.subn(r'<section class="cta-band">.*?</section>', closer, s, flags=re.S)
        n_closer += k

        for a_, b_ in (('btn btn-primary', 'btn btn--primary'),
                       ('btn btn-ghost', 'btn btn--quiet'),
                       ('btn btn-teal', 'btn btn--quiet')):
            s, k = re.subn(re.escape(a_), b_, s)
            n_btn += k
        # .btn-row -> .cta-row, keeping any inline style attribute intact
        s, k = re.subn(r'class="btn-row"', 'class="cta-row"', s)
        n_row += k
        s, k2 = re.subn(r'class="btn-row"(\s+style=)', r'class="cta-row"\1', s)
        n_row += k2

        if s != orig:
            changed += 1
            if a.apply:
                p.write_text(s, encoding='utf-8')

    print('%d page(s) changed  (%s)' % (changed, 'applied' if a.apply else 'dry run'))
    print('  buttons remapped : %d' % n_btn)
    print('  btn-row -> cta-row: %d' % n_row)
    print('  cta-band -> warm closer: %d' % n_closer)


if __name__ == '__main__':
    main()
