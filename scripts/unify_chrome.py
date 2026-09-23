#!/usr/bin/env python
"""Put every page of the Hero's v3 site on ONE header, ONE footer and ONE
type stack.

Measured problem this fixes (2026-09-22): index.html loaded style.css while the
other 80 pages loaded styles.css, carried a different nav ([Home, Services,
About, Blog] + a dark "Contact Us" pill instead of the homepage's [Services,
Areas, Blog, About] + a visible phone link + a red "Text a photo" pill), and
wore a black .emergency-strip announcement bar the homepage did not have. A
visitor clicking Services from the homepage landed on what read as a different
company's site.

The canonical nav and footer are index.html's, extracted at run time so this
script can never drift from the page it copies.

Usage:  python scripts/unify_chrome.py [--apply] [--only path,path]
Dry by default: it prints what it would change and writes nothing.
"""
import argparse, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

NAV_JS = """<script>
(function(){
  var nav=document.getElementById('nav'); if(!nav) return;
  var b=nav.querySelector('.burger');
  function solid(){ nav.classList.toggle('solid', window.scrollY>8); }
  addEventListener('scroll', solid, {passive:true}); solid();
  if(b){ b.addEventListener('click', function(){
    var open=nav.classList.toggle('menu-open');
    b.setAttribute('aria-expanded', open?'true':'false');
    document.body.classList.toggle('menu-locked', open);
  }); }
})();
</script>"""

SMS = ('sms:+12142779069?&amp;body=Hi%2C%20here%20is%20a%20photo%20of'
       '%20what%20I%20need%20gone.')


def pages():
    out = []
    for p in sorted(ROOT.rglob('*.html')):
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith(('.visual/', 'scripts/')):
            continue
        out.append(p)
    return out


def prefix(p):
    """'' for a page at the site root, '../' for one a directory down."""
    depth = len(p.relative_to(ROOT).parts) - 1
    return '../' * depth


def grab(text, pattern):
    m = re.search(pattern, text, re.S | re.I)
    if not m:
        sys.exit('could not find %s in index.html' % pattern)
    return m.group(0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--only', default='')
    a = ap.parse_args()

    home = (ROOT / 'index.html').read_text(encoding='utf-8')
    nav_tpl = grab(home, r'<nav id="nav".*?</nav>')
    foot_tpl = grab(home, r'<footer>.*?</footer>')

    targets = pages()
    if a.only:
        want = {s.strip() for s in a.only.split(',')}
        targets = [p for p in targets
                   if p.relative_to(ROOT).as_posix() in want]

    changed = 0
    for p in targets:
        rel = p.relative_to(ROOT).as_posix()
        s = orig = p.read_text(encoding='utf-8')
        pre = prefix(p)

        # --- chrome: rebuild nav + footer from the homepage's own markup -----
        nav = nav_tpl
        foot = foot_tpl
        for tpl_from, tpl_to in (
                ('href="assets/', 'href="%sassets/' % pre),
                ('src="assets/', 'src="%sassets/' % pre),
                ('href="services/', 'href="%sservices/' % pre),
                ('href="blog/', 'href="%sblog/' % pre),
                ('href="about"', 'href="%sabout"' % pre),
                ('href="contact"', 'href="%scontact"' % pre),
                ('href="./"', 'href="%s"' % (pre or './')),
                ('href="areas.html"', 'href="%sareas.html"' % pre)):
            nav = nav.replace(tpl_from, tpl_to)
            foot = foot.replace(tpl_from, tpl_to)

        # the old announcement bar duplicated the phone and the text CTA that
        # the unified nav already carries, which put two filled primaries in
        # one viewport (conversion rule B3/W2). It goes.
        s = re.sub(r'\s*<div class="emergency-strip">.*?</div>\s*', '\n', s,
                   flags=re.S)
        s = re.sub(r'<header class="site">.*?</header>', nav, s, flags=re.S)
        s = re.sub(r'<nav id="nav".*?</nav>', nav, s, flags=re.S)
        s = re.sub(r'<footer[^>]*>.*?</footer>', foot, s, flags=re.S)

        # --- head: v3 stylesheet last so it wins, self-hosted fonts ---------
        if 'href="%sstyle.css' % pre not in s:
            s = re.sub(r'(<link rel="stylesheet" href="%sstyles\.css"[^>]*>)'
                       % re.escape(pre),
                       r'\1\n<link rel="stylesheet" href="%sstyle.css?v=6">'
                       % pre, s)
        # inner pages carried an inline navy-truck data-URI favicon from the
        # pre-v3 palette, so the browser tab changed colour page to page.
        s = re.sub(r'<link rel="icon"[^>]*>',
                   '<link rel="icon" href="%sassets/logo-mark.svg" type="image/svg+xml">' % pre,
                   s, count=1)
        s = re.sub(r'\s*<link rel="preconnect" href="https://fonts\.(googleapis|gstatic)\.com"[^>]*>', '', s)
        s = re.sub(r'\s*<link rel="stylesheet" href="https://fonts\.googleapis\.com[^>]*>',
                   '\n<link rel="preload" href="%sassets/fonts/fraunces-600-latin.woff2" as="font" type="font/woff2" crossorigin>'
                   '\n<link rel="preload" href="%sassets/fonts/source-sans-3-latin.woff2" as="font" type="font/woff2" crossorigin>'
                   '\n<link rel="stylesheet" href="%sassets/fonts.css">' % (pre, pre, pre), s)

        # The unified nav's .burger and its .solid scrolled state are driven by
        # the homepage's script. Without it the mobile menu is dead on every
        # inner page, because the old markup used an inline onclick we removed.
        if "classList.toggle('solid'" not in s:
            s = s.replace("</body>", NAV_JS + "</body>", 1)

        if s != orig:
            changed += 1
            print('%-58s chrome unified' % rel)
            if a.apply:
                p.write_text(s, encoding='utf-8')

    print('\n%d/%d page(s) %s' % (changed, len(targets),
                                  'rewritten' if a.apply else 'would change (dry run)'))


if __name__ == '__main__':
    main()
