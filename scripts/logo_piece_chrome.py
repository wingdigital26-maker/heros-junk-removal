"""
Put the travelling logo piece (assets/logo-piece/) on every inner page: the header's static
logo-mark.svg becomes the live-slot + Blender PNG fallback, the piece stylesheet and module are
linked, and the favicon becomes the cube logo. Inner pages have no docks, so the piece idles in
the header as the logo. Idempotent; the homepage (index.html) is hand-wired and skipped.

  python scripts/logo_piece_chrome.py
"""
import re, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
V = "1"
n = 0
for p in ROOT.rglob("*.html"):
    rel = p.relative_to(ROOT)
    if rel.parts[0].startswith(".") or rel.parts[0] in ("brand", "node_modules") or rel.as_posix() == "index.html":
        continue
    s = p.read_text(encoding="utf-8")
    m = re.search(r'<a href="[^"]*" class="t-logo"[^>]*><img src="([^"]*)assets/logo-mark\.svg\?v=2" alt="" width="28" height="28">', s)
    if not m:
        continue
    pre = m.group(1)
    s = s.replace(m.group(0), m.group(0).split("<img")[0] +
                  f'<span class="lp-slot" data-lp-home><img src="{pre}assets/logo-piece/logo-88.png" alt="" width="40" height="40"></span>')
    icons = (f'<link rel="icon" href="{pre}assets/logo-piece/favicon-32.png" sizes="32x32" type="image/png">\n'
             f'<link rel="icon" href="{pre}assets/logo-piece/favicon-16.png" sizes="16x16" type="image/png">\n'
             f'<link rel="apple-touch-icon" href="{pre}assets/logo-piece/apple-touch-icon.png">')
    s, k = re.subn(r'<link rel="icon"[^>]*>', lambda _m: icons, s, count=1)
    s = re.sub(r'\n?<link rel="icon"[^>]*logo-mark[^>]*>', '', s)
    if "logo-piece.css" not in s:
        s = re.sub(r'(<link rel="stylesheet" href="[^"]*trinity-pages\.css[^"]*">)',
                   r'\1' + f'\n<link rel="stylesheet" href="{pre}assets/logo-piece/logo-piece.css?v={V}">', s, count=1)
    if "logo-piece.js" not in s:
        s = s.replace("</body>", f'<script type="module" src="{pre}assets/logo-piece/logo-piece.js?v={V}"></script>\n</body>', 1)
    p.write_text(s, encoding="utf-8")
    n += 1
print("pages updated:", n)
