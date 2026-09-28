#!/usr/bin/env python3
"""Tile screenshots into one contact sheet. Usage: blog_sheet.py out.png cols scale img1 img2 ..."""
import sys
from PIL import Image
out, cols, scale = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
ims = [Image.open(p) for p in sys.argv[4:]]
ims = [im.resize((int(im.width*scale), int(im.height*scale))) for im in ims]
w = max(i.width for i in ims); h = max(i.height for i in ims)
rows = (len(ims)+cols-1)//cols
sheet = Image.new("RGB", (cols*w+ (cols-1)*8, rows*h + (rows-1)*8), "#888")
for k, im in enumerate(ims):
    sheet.paste(im, ((k%cols)*(w+8), (k//cols)*(h+8)))
sheet.save(out)
print(out, sheet.size)
