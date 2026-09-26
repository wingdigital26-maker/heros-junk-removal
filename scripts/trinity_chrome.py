#!/usr/bin/env python
"""Put every inner page on the homepage's (Trinity) chrome and design language.

Pages: 404.html, about.html, areas.html, contact.html, services/*.html, blog/*.html.

What it does to each page (re-runnable: a page already on the Trinity chrome gets
its header/footer refreshed from index.html, nothing else changes twice):

  head    drop fonts.css, final.css, pages-*.css and the Fraunces / Source Sans
          preloads; add Inter (Google Fonts) + assets/trinity.css + assets/trinity-pages.css.
          Title, meta, canonical, JSON-LD and everything else stays byte-for-byte.
  chrome  <header class="site-header"> + <nav class="mobile-menu">  ->  index.html's <header class="t-header">
          <footer class="site-footer"> + <div class="call-bar">     ->  index.html's <footer class="t-footer">
  scripts drop assets/final.js and assets/piece.js; add assets/trinity.js.
  links   homepage sections -> /#services etc.; extensionless internal links
          (about, contact, ../blog/some-post) -> the .html file that exists, so every
          link resolves on a plain static server too. Link WORDS never change.

The header/footer markup is extracted from index.html at run time, so the inner
pages can never drift from the homepage.

Usage:  python scripts/trinity_chrome.py [--apply] [--only path,path]
Dry by default: prints what it would change and writes nothing.
"""
import argparse, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CSS_V = '13'
JS_V = '9'

OLD_HEADER_RE = re.compile(r'<header class="site-header" id="site-header">.*?</header>\s*(<nav class="mobile-menu" aria-label="Mobile">.*?</nav>\s*)?', re.S)
NEW_HEADER_RE = re.compile(r'<header class="t-header">.*?</header>\s*', re.S)
OLD_FOOTER_RE = re.compile(r'<footer class="site-footer">.*?</footer>\s*(<div class="call-bar">.*?</div>\s*)?', re.S)
NEW_FOOTER_RE = re.compile(r'<footer class="t-footer">.*?</footer>\s*', re.S)
DROP_HEAD = [
    re.compile(r'<link rel="stylesheet" href="(?:\.\./)?assets/fonts\.css">\s*'),
    re.compile(r'<link rel="stylesheet" href="(?:\.\./)?assets/final\.css[^"]*">\s*'),
    re.compile(r'<link rel="stylesheet" href="(?:\.\./)?assets/pages-[a-z]+\.css[^"]*">\s*'),
    re.compile(r'<link rel="preload" href="(?:\.\./)?assets/fonts/[^"]+" as="font"[^>]*>\s*'),
]
DROP_SCRIPTS = [
    re.compile(r'<script src="(?:\.\./)?assets/final\.js[^"]*" defer></script>\s*'),
    re.compile(r'<script src="(?:\.\./)?assets/piece\.js[^"]*" defer></script>\s*'),
]
TRINITY_HEAD_RE = re.compile(r'<!-- trinity:head -->.*?<!-- /trinity:head -->\s*', re.S)
TRINITY_JS_RE = re.compile(r'<script src="(?:\.\./)?assets/trinity\.js[^"]*" defer></script>\s*')


def grab(text, pattern):
    m = re.search(pattern, text, re.S)
    if not m:
        sys.exit('could not find %s in index.html' % pattern)
    return m.group(0)


def pages():
    out = [ROOT / r for r in ('404.html', 'about.html', 'areas.html', 'contact.html') if (ROOT / r).exists()]
    out += sorted((ROOT / 'services').glob('*.html'))
    out += sorted((ROOT / 'blog').glob('*.html'))
    return out


def prefix(p):
    return '../' * (len(p.relative_to(ROOT).parts) - 1)


def chrome_urls(tpl, pre):
    """Rewrite href/src in the homepage chrome for a page `pre` deep."""
    def fix(m):
        attr, url = m.group(1), m.group(2)
        if url.startswith(('http://', 'https://', 'tel:', 'sms:', 'mailto:')):
            return m.group(0)
        if url.startswith('#'):
            return '%s="/%s"' % (attr, url)            # homepage sections: /#services, /#reviews ...
        if url == './':
            return '%s="%s"' % (attr, pre or './')
        if url.startswith(('assets/', 'services/', 'blog/', 'img/')) or url in ('about.html', 'contact.html'):
            return '%s="%s%s"' % (attr, pre, url)
        return m.group(0)
    return re.sub(r'(href|src)="([^"]*)"', fix, tpl)


def mark_current(html, p):
    rel = p.relative_to(ROOT).as_posix()
    target = {'about.html': 'about.html', 'contact.html': 'contact.html'}.get(rel)
    if not target:
        return html
    for nav in ('t-nav', 't-mobile-menu'):
        html = re.sub(r'(<nav class="%s"[^>]*>.*?)<a href="%s">' % (nav, re.escape(target)),
                      lambda m: m.group(1) + '<a href="%s" aria-current="page">' % target, html, count=1, flags=re.S)
    return html


def fix_body_links(s, p):
    """Extensionless internal links -> the .html file that exists (href only)."""
    here = p.parent

    def fix(m):
        url = m.group(1)
        if url.startswith(('http:', 'https:', 'tel:', 'sms:', 'mailto:', '#', '/', 'data:')) or url in ('', './', '../'):
            return m.group(0)
        path, sep, frag = url.partition('#')
        if not path or path.endswith(('/', '.html')) or '.' in path.rsplit('/', 1)[-1]:
            return m.group(0)
        cand = (here / (path + '.html')).resolve()
        if cand.exists() and ROOT in cand.parents:
            return 'href="%s.html%s%s"' % (path, sep, frag)
        return m.group(0)
    return re.sub(r'href="([^"]*)"', fix, s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--only', default='')
    a = ap.parse_args()

    home = (ROOT / 'index.html').read_text(encoding='utf-8')
    header_tpl = grab(home, r'<header class="t-header">.*?</header>')
    footer_tpl = grab(home, r'<footer class="t-footer">.*?</footer>')

    targets = pages()
    if a.only:
        want = {x.strip() for x in a.only.split(',')}
        targets = [p for p in targets if p.relative_to(ROOT).as_posix() in want]

    changed = 0
    for p in targets:
        rel = p.relative_to(ROOT).as_posix()
        s = orig = p.read_text(encoding='utf-8')
        pre = prefix(p)
        header = mark_current(chrome_urls(header_tpl, pre), p) + '\n\n'
        footer = chrome_urls(footer_tpl, pre) + '\n'

        # chrome
        if OLD_HEADER_RE.search(s):
            s = OLD_HEADER_RE.sub(lambda m: header, s, count=1)
        elif NEW_HEADER_RE.search(s):
            s = NEW_HEADER_RE.sub(lambda m: header, s, count=1)
        else:
            sys.exit('%s: no header found' % rel)
        if OLD_FOOTER_RE.search(s):
            s = OLD_FOOTER_RE.sub(lambda m: footer, s, count=1)
        elif NEW_FOOTER_RE.search(s):
            s = NEW_FOOTER_RE.sub(lambda m: footer, s, count=1)
        else:
            sys.exit('%s: no footer found' % rel)

        # head
        for r in DROP_HEAD:
            s = r.sub('', s)
        s = TRINITY_HEAD_RE.sub('', s)
        head_block = ('<!-- trinity:head -->\n'
                      '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
                      '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
                      '<link href="https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,400..800&display=swap" rel="stylesheet">\n'
                      '<link rel="stylesheet" href="%sassets/trinity.css?v=%s">\n'
                      '<link rel="stylesheet" href="%sassets/trinity-pages.css?v=%s">\n'
                      '<!-- /trinity:head -->\n') % (pre, CSS_V, pre, CSS_V)
        s = s.replace('</head>', head_block + '</head>', 1)

        # scripts
        for r in DROP_SCRIPTS:
            s = r.sub('', s)
        s = TRINITY_JS_RE.sub('', s)
        s = s.replace('</body>', '<script src="%sassets/trinity.js?v=%s" defer></script>\n</body>' % (pre, JS_V), 1)

        # links in the body
        s = fix_body_links(s, p)

        if s != orig:
            changed += 1
            print('%-60s %s' % (rel, 'updated' if a.apply else 'would update'))
            if a.apply:
                p.write_text(s, encoding='utf-8', newline='')
    print('%d page(s) %s' % (changed, 'updated' if a.apply else 'would change (dry run; pass --apply)'))


if __name__ == '__main__':
    main()
