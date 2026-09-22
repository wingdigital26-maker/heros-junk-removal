"""Contact sheet for judging fragment density.

  python brand/contact_sheet.py brand/out/contact-sheet.png "label=path/to/render.png" "label=..." ...

Tiles the renders two per row at 900px wide each, with the label drawn along the top of every tile.
"""
import sys, os
from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1]
ITEMS = [a.split("=", 1) for a in sys.argv[2:]]
TW = 900
COLS = 2
tiles = []
for label, path in ITEMS:
    im = Image.open(path).convert("RGB")
    im = im.resize((TW, round(im.height * TW / im.width)), Image.LANCZOS)
    tiles.append((label, im))
TH = max(im.height for _, im in tiles) + 44
rows = (len(tiles) + COLS - 1) // COLS
sheet = Image.new("RGB", (TW * COLS + 12 * (COLS + 1), TH * rows + 12 * (rows + 1)), (238, 240, 244))
d = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype("arial.ttf", 26)
except Exception:
    font = ImageFont.load_default()
for i, (label, im) in enumerate(tiles):
    x = 12 + (i % COLS) * (TW + 12)
    y = 12 + (i // COLS) * (TH + 12)
    d.rectangle((x, y, x + TW, y + TH), fill=(255, 255, 255))
    d.text((x + 14, y + 8), label, fill=(20, 26, 40), font=font)
    sheet.paste(im, (x, y + 44))
sheet.save(OUT, optimize=True)
print(OUT, sheet.size, os.path.getsize(OUT))
