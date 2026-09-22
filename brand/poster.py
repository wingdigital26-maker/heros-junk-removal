"""Poster pipeline for the house piece.
Takes the transparent 1500x1150 hero render, crops to the alpha bounds with a margin, pads that crop to the
1400:1309 box the page reserves for it, and writes img/house-hero.webp (1400 wide), img/house-hero-sm.webp
(700 wide) and img/house-hero.png. Prints the crop rectangle in the full frame, which house-scene.js needs
for camera.setViewOffset so the live canvas lands pixel for pixel on the poster.

  python brand/poster.py brand/out/v4/house-hero.png
"""
import sys, os
from PIL import Image, ImageDraw, ImageFilter

SRC = sys.argv[1]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "img")
ASPECT = 1400 / 1309
MARGIN = 26

im = Image.open(SRC).convert("RGBA")
FW, FH = im.size

# contact shadow under the plinth, matching the one house-scene.js draws in the live scene so the crossfade holds
a = im.getchannel("A").point(lambda v: 255 if v > 8 else 0)
full = a.getbbox()
foot = a.crop((0, full[3] - 70, FW, full[3])).getbbox()       # the bottom 70px of the object: the plinth's foot
fx0, fx1 = foot[0], foot[2]
cx, bottom = (fx0 + fx1) / 2, full[3]
sw = (fx1 - fx0) * 1.02
sh = sw * 0.13
sh_layer = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
d = ImageDraw.Draw(sh_layer)
d.ellipse((cx - sw / 2, bottom - sh * 0.62, cx + sw / 2, bottom + sh * 0.38), fill=(14, 20, 32, 120))
sh_layer = sh_layer.filter(ImageFilter.GaussianBlur(16))
im = Image.alpha_composite(sh_layer, im)
bbox = im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
x0, y0, x1, y1 = bbox
x0 -= MARGIN; y0 -= MARGIN; x1 += MARGIN; y1 += MARGIN
w, h = x1 - x0, y1 - y0
# pad to the page aspect: extra height goes ABOVE (the plinth stays on the box floor, where style.css draws its
# shadow pool), extra width is split so the plinth centre lands near 47 percent of the box like that pool
if w / h < ASPECT:
    nw = round(h * ASPECT)
    x0 = round(cx - nw * 0.47)
    if x0 > bbox[0] - MARGIN: x0 = bbox[0] - MARGIN
    if x0 + nw < bbox[2] + MARGIN: x0 = bbox[2] + MARGIN - nw
    w = nw
else:
    nh = round(w / ASPECT); y0 -= (nh - h); h = nh
x1, y1 = x0 + w, y0 + h
# never crop outside the frame: paste onto a transparent canvas if the pad runs past the edge
canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
canvas.paste(im, (-x0, -y0))
big = canvas.resize((1400, 1309), Image.LANCZOS)
big.save(os.path.join(IMG, "house-hero.png"), optimize=True)
big.save(os.path.join(IMG, "house-hero.webp"), quality=86, method=6)
big.resize((700, 654), Image.LANCZOS).save(os.path.join(IMG, "house-hero-sm.webp"), quality=82, method=6)
print(f"frame {FW}x{FH}  crop x={x0} y={y0} w={w} h={h}  -> setViewOffset({FW}, {FH}, {x0}, {y0}, {w}, {h})")
for n in ("house-hero.png", "house-hero.webp", "house-hero-sm.webp"):
    print(n, os.path.getsize(os.path.join(IMG, n)))
