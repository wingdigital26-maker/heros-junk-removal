"""Build Hero's logo6 assets from Nash's supplied logo (black background JPG/WEBP).
Black is the background everywhere, so near-black pixels become transparent (un-premultiplied over black).
Outputs: logo-white.png (original colours, for dark backgrounds), logo-navy.png (white parts -> brand navy,
for light backgrounds), mark crops + favicons + og image."""
import sys
import numpy as np
from PIL import Image
SRC = sys.argv[1]
OUT = 'assets/logo6/'
NAVY = np.array([20, 40, 75], float)
im = np.asarray(Image.open(SRC).convert('RGB')).astype(float)
mx = im.max(axis=2)
alpha = np.clip((mx - 18) / 50.0, 0, 1)
rgb = np.where(alpha[..., None] > 0, np.clip(im / np.maximum(alpha, 1e-3)[..., None], 0, 255), 0)
ys, xs = np.where(alpha > 0.05)
pad = 8
box = (max(xs.min() - pad, 0), max(ys.min() - pad, 0), xs.max() + pad + 1, ys.max() + pad + 1)
def save(rgbarr, name):
    a = np.dstack([rgbarr, alpha * 255]).astype(np.uint8)
    img = Image.fromarray(a, 'RGBA').crop(box)
    img.save(OUT + name, optimize=True)
    return img
white = save(rgb, 'logo-white.png')
c = rgb
sat = (c.max(axis=2) - c.min(axis=2)) / np.maximum(c.max(axis=2), 1)
w = np.clip((0.35 - sat) / 0.2, 0, 1)
# keep white blobs that sit inside the blue field (the star) white
from scipy import ndimage
lab, n = ndimage.label((w > 0.5) & (alpha > 0.5))
for i in range(1, n + 1):
    comp = lab == i
    ring = ndimage.binary_dilation(comp, iterations=4) & ~ndimage.binary_dilation(comp, iterations=1)
    rr = c[ring]
    if len(rr) and ((rr[:, 2] > rr[:, 0] + 20) & (alpha[ring] > 0.5)).mean() > 0.7:
        w[ndimage.binary_dilation(comp, iterations=2)] = 0
w = w[..., None]
navy = save(c * (1 - w) + NAVY * w, 'logo-navy.png')
print('lockup', white.size, 'box', box)
# mark = can + H (rows above the HERO'S wordmark): find the gap row between mark and wordmark
rows = (alpha[box[1]:box[3], box[0]:box[2]] > 0.3).sum(axis=1)
h = len(rows)
gap = next(y for y in range(int(h * 0.45), int(h * 0.75)) if rows[y] == 0)
print('mark ends at', gap)
for src, name in ((white, 'mark-white'), (navy, 'mark-navy')):
    m = src.crop((0, 0, src.width, gap))
    m = m.crop(m.getbbox())
    s = max(m.size) + 16
    sq = Image.new('RGBA', (s, s), (0, 0, 0, 0)); sq.paste(m, ((s - m.width) // 2, (s - m.height) // 2), m)
    sq.save(OUT + name + '.png', optimize=True)
    if name == 'mark-navy':
        for px, fn in ((16, 'favicon-16.png'), (32, 'favicon-32.png'), (192, 'icon-192.png')):
            sq.resize((px, px), Image.LANCZOS).save(OUT + fn)
        # apple touch: original white mark on navy plate
    if name == 'mark-white':
        plate = Image.new('RGBA', (180, 180), (20, 40, 75, 255))
        t = sq.resize((150, 150), Image.LANCZOS); plate.paste(t, (15, 15), t)
        plate.convert('RGB').save(OUT + 'apple-touch-icon.png')
og = Image.new('RGB', (1200, 630), (20, 40, 75))
t = white.copy(); t.thumbnail((900, 520), Image.LANCZOS)
og.paste(t, ((1200 - t.width) // 2, (630 - t.height) // 2), t)
og.save(OUT + 'og.png', optimize=True)
# horizontal lockup for the header: mark left, wordmark right (same artwork, rearranged)
for src, name in ((white, 'lockup-h-white.png'), (navy, 'lockup-h-navy.png')):
    m = src.crop((0, 0, src.width, gap)); m = m.crop(m.getbbox())
    wd = src.crop((0, gap, src.width, src.height)); wd = wd.crop(wd.getbbox())
    th = int(m.height * 0.78)
    wd = wd.resize((int(wd.width * th / wd.height), th), Image.LANCZOS)
    sp = int(m.height * 0.12)
    out = Image.new('RGBA', (m.width + sp + wd.width, m.height), (0, 0, 0, 0))
    out.paste(m, (0, 0), m); out.paste(wd, (m.width + sp, (m.height - th) // 2), wd)
    out.thumbnail((1200, 240), Image.LANCZOS)
    out.save(OUT + name, optimize=True)
    print(name, out.size)
