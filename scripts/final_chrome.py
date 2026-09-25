#!/usr/bin/env python
"""Put every page EXCEPT index.html and contact.html on the NEW site chrome
(header/mobile-menu/call-bar/footer) that index.html and contact.html already
carry, plus the final.css / final.js pair that styles it.

Old chrome (still on 404.html, about.html, areas.html, services/*.html,
blog/*.html): a bare `<nav id="nav" aria-label="Site">...</nav>`, a bare
`<footer>...</footer>`, `style.css` only.

New chrome (index.html, contact.html): `<header class="site-header"
id="site-header">...</header>` + `<nav class="mobile-menu" ...>...</nav>` +
`<div class="call-bar">...</div>` + `<footer class="site-footer">...</footer>`,
`style.css` AND `final.css` (final.css last), plus `final.js`.

The canonical markup is extracted from index.html at run time so this script
can never drift from the page it copies (same approach as unify_chrome.py).

Usage:  python scripts/final_chrome.py [--apply] [--only path,path]
Dry by default: it prints what it would change and writes nothing.
"""
import argparse, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

OLD_NAV_RE = re.compile(r'<nav id="nav" aria-label="Site">.*?</nav>\s*', re.S)
OLD_FOOTER_RE = re.compile(r'<footer>.*?</footer>', re.S)
CALLBAR_RE = re.compile(r'<div class="call-bar">.*?</div>', re.S)

# the burger/scroll script unify_chrome.py appended for the OLD #nav chrome.
# It's a no-op once #nav is gone (guarded by `if(!nav) return`) but it is
# chrome-only dead weight now that final.js drives the new .site-header
# burger, so it comes out.
OLD_NAV_JS_RE = re.compile(
    r'<script>\s*\(function\(\)\{\s*var nav=document\.getElementById\(\'nav\'\);.*?\}\)\(\);\s*</script>\s*',
    re.S)

STYLE_LINK_RE = re.compile(r'<link rel="stylesheet" href="((?:\.\./)?style\.css[^"]*)">')
PIECE_SCRIPT_RE = re.compile(r'<script src="(?:\.\./)?assets/piece\.js" defer></script>')


def grab(text, pattern):
    m = re.search(pattern, text, re.S)
    if not m:
        sys.exit('could not find %s in index.html' % pattern)
    return m.group(0)


def pages():
    out = []
    for rel in ['404.html', 'about.html', 'areas.html']:
        p = ROOT / rel
        if p.exists():
            out.append(p)
    out += sorted((ROOT / 'services').glob('*.html'))
    out += sorted((ROOT / 'blog').glob('*.html'))
    return out


def prefix(p):
    depth = len(p.relative_to(ROOT).parts) - 1
    return '../' * depth


def rewrite_urls(template, pre):
    """Rewrite href=/src= inside an extracted chrome template for a page
    living `pre` deep (`''` at root, `'../'` one folder down)."""

    def fix(m):
        attr, url = m.group(1), m.group(2)
        if url.startswith(('http://', 'https://', 'tel:', 'sms:', 'mailto:', '#')):
            if url.startswith('#'):
                # homepage-only sections: #services / #reviews / #work / #faq
                return '%s="%sindex.html%s"' % (attr, pre, url)
            return m.group(0)
        if url == './':
            return '%s="%s"' % (attr, pre if pre else './')
        if url.startswith(('assets/', 'services/', 'blog/')):
            return '%s="%s%s"' % (attr, pre, url)
        if url in ('about', 'contact'):
            return '%s="%s%s"' % (attr, pre, url)
        return m.group(0)

    return re.sub(r'(href|src)="([^"]*)"', fix, template)


def set_aria_current(nav_html, rel):
    """Mark the matching top-nav link aria-current="page" where the new nav
    actually carries a link to this page (About / Contact only -- the rest
    of the primary nav is homepage anchors, and Services/Areas/Blog pages
    aren't in the header nav at all)."""
    label = {'about.html': 'about', 'contact.html': 'contact'}.get(rel)
    if not label:
        return nav_html
    pat = re.compile(r'(<a href="[^"]*\b%s(?:\.html)?")>' % re.escape(label))
    return pat.sub(lambda m: '%s aria-current="page">' % m.group(1), nav_html, count=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--only', default='')
    a = ap.parse_args()

    home = (ROOT / 'index.html').read_text(encoding='utf-8')
    header_tpl = grab(home, r'<header class="site-header" id="site-header">.*?</header>')
    mobile_tpl = grab(home, r'<nav class="mobile-menu" aria-label="Mobile">.*?</nav>')
    callbar_tpl = grab(home, r'<div class="call-bar">.*?</div>')
    footer_tpl = grab(home, r'<footer class="site-footer">.*?</footer>')

    targets = pages()
    if a.only:
        want = {s.strip() for s in a.only.split(',')}
        targets = [p for p in targets if p.relative_to(ROOT).as_posix() in want]

    changed = 0
    for p in targets:
        rel = p.relative_to(ROOT).as_posix()
        s = orig = p.read_text(encoding='utf-8')
        pre = prefix(p)

        header = rewrite_urls(header_tpl, pre)
        mobile = rewrite_urls(mobile_tpl, pre)
        callbar = rewrite_urls(callbar_tpl, pre)
        footer = rewrite_urls(footer_tpl, pre)

        rel_base = p.name  # e.g. 'about.html', matched against about/contact
        header = set_aria_current(header, rel_base)
        mobile = set_aria_current(mobile, rel_base)

        new_chrome = header + '\n\n' + mobile + '\n'

        if OLD_NAV_RE.search(s):
            s = OLD_NAV_RE.sub(lambda m: new_chrome, s, count=1)
        elif '<header class="site-header"' not in s:
            sys.exit('%s: could not find old <nav id="nav"> chrome to replace' % rel)

        if OLD_FOOTER_RE.search(s):
            s = OLD_FOOTER_RE.sub(lambda m: footer, s, count=1)
        elif '<footer class="site-footer"' not in s:
            sys.exit('%s: could not find old <footer> to replace' % rel)

        if CALLBAR_RE.search(s):
            s = CALLBAR_RE.sub(lambda m: callbar, s, count=1)
        else:
            # no call bar yet on this page: drop it right after the footer
            s = s.replace(footer, footer + '\n' + callbar, 1)

        # --- head: final.css after the existing style.css link, once --------
        final_css_href = '%sassets/final.css?v=1' % pre
        if final_css_href not in s:
            s = STYLE_LINK_RE.sub(
                lambda m: m.group(0) + '\n<link rel="stylesheet" href="%s">' % final_css_href,
                s, count=1)

        # --- body: final.js before </body>, once -----------------------------
        final_js_src = '%sassets/final.js?v=1' % pre
        if final_js_src not in s:
            s = s.replace('</body>', '<script src="%s" defer></script>\n</body>' % final_js_src, 1)

        # old #nav burger/solid script: dead weight now that #nav is gone
        s = OLD_NAV_JS_RE.sub('', s)

        # piece.js: keep only if the body still references the house mark
        # or any of the other selectors piece.js drives (main sections /
        # cards / blog posts / cta-band all still exist post-chrome-swap,
        # so this only strips the tag on the rare page with none of them).
        if PIECE_SCRIPT_RE.search(s):
            body_after_main = s.split('<main', 1)[-1]
            still_used = bool(re.search(
                r'class="hm"|main section|main \.card|article\.post|cta-band', body_after_main))
            if not still_used:
                s = PIECE_SCRIPT_RE.sub('', s)

        if s != orig:
            changed += 1
            print('%-58s chrome -> final' % rel)
            if a.apply:
                p.write_text(s, encoding='utf-8')
        else:
            print('%-58s unchanged' % rel)

    print('\n%d/%d page(s) %s' % (changed, len(targets),
                                  'rewritten' if a.apply else 'would change (dry run)'))


if __name__ == '__main__':
    main()
