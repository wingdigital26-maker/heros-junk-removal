"""Swap every page's header/footer logo and favicons to logo6 (Nash's supplied logo). Idempotent."""
import re, pathlib
HDR = re.compile(r'(<a href="(\.\./|\./)" class="t-logo"[^>]*>)<svg class="t-mark".*?</svg><span class="t-logo-word">.*?(</a>)', re.S)
FTR = re.compile(r'(<a class="t-footer-brand" href="(\.\./|\./)"[^>]*>)<svg class="t-mark".*?</svg><span class="t-footer-wordmark">.*?(</a>)', re.S)
n = 0
for f in pathlib.Path('.').rglob('*.html'):
    if any(x in f.parts for x in ('.visual', 'node_modules', 'brand')): continue
    s = f.read_text(encoding='utf-8'); o = s
    def hdr(m):
        p = '' if m.group(2) == './' else '../'
        return m.group(1) + f'<img class="t-logo-img" src="{p}assets/logo6/lockup-h-navy.png" alt="" width="1011" height="240">' + m.group(3)
    def ftr(m):
        p = '' if m.group(2) == './' else '../'
        return m.group(1) + f'<img class="t-footer-logo" src="{p}assets/logo6/logo-white.png" alt="" width="652" height="589" loading="lazy">' + m.group(3)
    s = HDR.sub(hdr, s); s = FTR.sub(ftr, s)
    s = re.sub(r'(<link rel="icon" href="(?:\.\./)?assets/)logo5/mark\.svg" type="image/svg\+xml">', r'\1logo6/favicon-32.png" sizes="32x32" type="image/png">', s, count=1)
    s = s.replace('logo5/favicon-32.png" sizes="32x32"', 'logo6/icon-192.png" sizes="192x192"')
    s = s.replace('logo5/', 'logo6/')
    if s != o: f.write_text(s, encoding='utf-8'); n += 1
print('pages changed', n)
