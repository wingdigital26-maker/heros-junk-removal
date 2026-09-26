#!/usr/bin/env python
"""Hero's Junk Removal: logo5, a flat wordmark + mark separate from the cube piece.

Three marks are laid out on one board (.visual/logo5/board.png) so Jack can compare them at
160px, in the header at 36px, as a 16px favicon and large on navy. The pick is written to
brand/logo5/mark.svg and rendered to the favicons + og image the site links to.

    python brand/logo5/build.py            # board + pick + favicons + og
    python brand/logo5/build.py --pick b   # override the pick

Pure SVG paths (no font in the mark). The wordmark is live Inter text on the site, so it is
rendered here by the browser (Playwright) rather than outlined.
"""
import argparse, pathlib, sys
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
BOARD_DIR = ROOT / '.visual' / 'logo5'
NAVY, RED, WHITE = '#14284B', '#D62A1E', '#FFFFFF'

# ---------------------------------------------------------------- the three marks (viewBox 64)
def mark_a(navy=NAVY, red=RED, white=WHITE):
    """House-H: a house silhouette whose body carries a bold H; the crossbar is red."""
    return (
        '<path fill="%s" d="M32 5 L60 29 V60 H4 V29 Z"/>'
        '<rect fill="%s" x="16" y="27" width="10" height="26"/>'
        '<rect fill="%s" x="38" y="27" width="10" height="26"/>'
        '<rect fill="%s" x="26" y="35" width="12" height="9"/>'
    ) % (navy, white, white, red)


def mark_b(navy=NAVY, red=RED, white=WHITE):
    """H-lift: two navy posts joined by a red up-chevron (the H, the roof, junk going up and out)."""
    return (
        '<rect fill="%s" x="8" y="6" width="13" height="52" rx="2"/>'
        '<rect fill="%s" x="43" y="6" width="13" height="52" rx="2"/>'
        '<path fill="%s" d="M32 20 L46 34 V45 L32 31 L18 45 V34 Z"/>'
    ) % (navy, navy, red)


def mark_c(navy=NAVY, red=RED, white=WHITE):
    """Shield-H: the old badge's heritage, flattened. Navy shield, white H, a red band through the crossbar."""
    shield = 'M32 3 L58 11 V32 C58 47 46 56 32 61 C18 56 6 47 6 32 V11 Z'
    return (
        '<clipPath id="s"><path d="%s"/></clipPath>'
        '<path fill="%s" d="%s"/>'
        '<rect clip-path="url(#s)" fill="%s" x="0" y="29" width="64" height="9"/>'
        '<rect fill="%s" x="18" y="17" width="9" height="31"/>'
        '<rect fill="%s" x="37" y="17" width="9" height="31"/>'
    ) % (shield, navy, shield, red, white, white)


MARKS = {'a': mark_a, 'b': mark_b, 'c': mark_c}
NAMES = {'a': 'A. House-H', 'b': 'B. H-lift', 'c': 'C. Shield-H'}


def svg(body, size=64, label="Hero's Junk Removal"):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="%d" height="%d" role="img" aria-label="%s">%s</svg>'
            % (size, size, label, body))


FONT = '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,400..800&display=swap" rel="stylesheet">'


def lockup(k, size=36, color=NAVY, apos=RED, weight=700, gap=None):
    gap = gap if gap is not None else round(size * 0.3)
    fs = round(size * 0.5)
    return ('<span style="display:inline-flex;align-items:center;gap:%dpx;color:%s;font-weight:%d;font-size:%dpx;letter-spacing:-0.03em;white-space:nowrap">%s'
            '<span>Hero<span style="color:%s">&rsquo;</span>s Junk Removal</span></span>'
            % (gap, color, weight, fs, svg(MARKS[k](), size), apos))


def board_html():
    cols = []
    for k in 'abc':
        inv = MARKS[k](navy=WHITE, red=RED, white=NAVY)
        cols.append('''
<div class="col">
  <h2>%s</h2>
  <div class="big">%s</div>
  <div class="row label">Header, 36px</div>
  <div class="row header">%s</div>
  <div class="row label">Favicon 16 / 32</div>
  <div class="row small">%s %s</div>
  <div class="row label">Footer on navy</div>
  <div class="navy">%s</div>
</div>''' % (NAMES[k], svg(MARKS[k](), 160), lockup(k, 36), svg(MARKS[k](), 16), svg(MARKS[k](), 32),
             '<span style="display:inline-flex;align-items:center;gap:22px;color:#fff;font-weight:800;font-size:44px;letter-spacing:-0.04em">%s<span>Hero<span style="color:%s">&rsquo;</span>s</span></span>' % (svg(inv, 72), RED)))
    return '''<!doctype html><html><head><meta charset="utf-8">%s<style>
body{margin:0;background:#fff;font-family:Inter,system-ui,sans-serif;color:%s;width:1440px;padding:40px 48px;box-sizing:border-box}
h1{font-size:14px;font-weight:600;letter-spacing:.02em;text-transform:uppercase;color:#5F6675;margin:0 0 28px}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:48px}
.col{border:1px solid #e6e6e6;border-radius:12px;padding:28px}
h2{font-size:20px;font-weight:700;letter-spacing:-0.02em;margin:0 0 20px}
.big{display:flex;justify-content:center;align-items:center;height:220px;background:#F7F5F1;border-radius:10px}
.row{display:flex;align-items:center;gap:16px;min-height:44px}
.label{font-size:12px;color:#5F6675;text-transform:uppercase;letter-spacing:.04em;margin-top:18px;min-height:0}
.header{border:1px solid #e6e6e6;border-radius:8px;padding:0 16px;height:72px}
.navy{background:%s;border-radius:10px;padding:32px 24px}
</style></head><body><h1>Hero&rsquo;s Junk Removal: logo5, three marks</h1><div class="grid">%s</div></body></html>''' % (FONT, NAVY, NAVY, ''.join(cols))


def og_html(k):
    return '''<!doctype html><html><head><meta charset="utf-8">%s<style>
body{margin:0;width:1200px;height:630px;background:#fff;font-family:Inter,system-ui,sans-serif;color:%s;display:flex;flex-direction:column;justify-content:space-between;padding:64px 72px;box-sizing:border-box}
.top{display:flex;align-items:center;gap:26px;font-weight:700;font-size:40px;letter-spacing:-0.03em}
h1{font-size:82px;font-weight:800;letter-spacing:-0.045em;line-height:1;margin:0}
.foot{display:flex;justify-content:space-between;align-items:flex-end;font-size:24px;color:#3B4252}
.foot b{color:%s;font-size:28px}
.bar{height:6px;background:%s;width:120px;margin-bottom:22px}
</style></head><body>
<div class="top">%s<span>Hero<span style="color:%s">&rsquo;</span>s Junk Removal</span></div>
<div><div class="bar"></div><h1>Text a photo of the pile.<br>Get a price back. It leaves.</h1></div>
<div class="foot"><span>Frisco, Plano, McKinney, Prosper, Allen and Little Elm. 7am to 8pm daily.</span><b>(214) 277-9069</b></div>
</body></html>''' % (FONT, NAVY, RED, RED, svg(MARKS[k](), 72), RED)


def icon_html(k, size, pad=0):
    return '<!doctype html><html><head><meta charset="utf-8"><style>body{margin:0;background:transparent}</style></head><body>%s</body></html>' % svg(MARKS[k](), size)


def touch_html(k):
    # 180px, white rounded tile so it reads on any phone wallpaper
    return ('<!doctype html><html><head><meta charset="utf-8"><style>body{margin:0;width:180px;height:180px;background:#fff;display:flex;align-items:center;justify-content:center}</style></head><body>%s</body></html>'
            % svg(MARKS[k](), 132))


def shoot(b, html, path, w, h, omit_bg=False):
    pg = b.new_page(viewport={'width': w, 'height': h}, device_scale_factor=1)
    pg.set_content(html, wait_until='networkidle')
    pg.wait_for_timeout(900)
    pg.screenshot(path=str(path), omit_background=omit_bg, clip={'x': 0, 'y': 0, 'width': w, 'height': h})
    pg.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pick', default='a')
    a = ap.parse_args()
    k = a.pick
    BOARD_DIR.mkdir(parents=True, exist_ok=True)
    for key, fn in MARKS.items():
        (HERE / f'mark-{key}.svg').write_text(svg(fn(), 64), encoding='utf-8')
    (HERE / 'mark.svg').write_text(svg(MARKS[k](), 64), encoding='utf-8')
    (HERE / 'mark-white.svg').write_text(svg(MARKS[k](navy=WHITE, red=RED, white=NAVY), 64), encoding='utf-8')
    (BOARD_DIR / 'board.html').write_text(board_html(), encoding='utf-8')
    with sync_playwright() as p:
        b = p.chromium.launch()
        shoot(b, board_html(), BOARD_DIR / 'board.png', 1440, 760)
        shoot(b, icon_html(k, 16), HERE / 'favicon-16.png', 16, 16, omit_bg=True)
        shoot(b, icon_html(k, 32), HERE / 'favicon-32.png', 32, 32, omit_bg=True)
        shoot(b, touch_html(k), HERE / 'apple-touch-icon.png', 180, 180)
        shoot(b, og_html(k), HERE / 'og.png', 1200, 630)
        b.close()
    print('pick', k, '-> brand/logo5/mark.svg, favicons, og.png; board at', BOARD_DIR / 'board.png')


if __name__ == '__main__':
    main()
