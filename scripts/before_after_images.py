#!/usr/bin/env python3
"""Web versions of Nash's before-and-after photos.

  timeout 150 python scripts/before_after_images.py

Reads img/before-after/src/<n>.jpg (the originals stay out of every page), fixes EXIF rotation, applies a
light auto-level only (no crops, no stretching, nothing faked) and writes
img/before-after/<job>-<before|after>-<i>-{640,1100}.webp at the photo's natural aspect. The originals are
640px on the long side, so the 1100 file is a Lanczos upscale kept for the srcset ladder.
"""
import os
from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'img', 'before-after', 'src')
OUT = os.path.join(ROOT, 'img', 'before-after')

# job -> (before photos, after photos), verified by eye: same walls, cabinets and floor in each pair
JOBS = {
    'garage':  (['24'], ['9']),
    'living':  (['18', '20', '21'], ['10', '11']),   # 19 duplicates 18 and is skipped
    'kitchen': (['22', '25', '26'], ['13']),
    'pantry':  (['23'], ['12']),
}
WIDTHS = (640, 1100)


def main():
    manifest = []
    for job, (befores, afters) in JOBS.items():
        for kind, names in (('before', befores), ('after', afters)):
            for i, n in enumerate(names, 1):
                im = Image.open(os.path.join(SRC, f'{n}.jpg'))
                im = ImageOps.exif_transpose(im).convert('RGB')
                im = ImageOps.autocontrast(im, cutoff=0.3, preserve_tone=True)
                w, h = im.size
                for W in WIDTHS:
                    H = round(h * W / w)
                    out = im.resize((W, H), Image.LANCZOS)
                    path = os.path.join(OUT, f'{job}-{kind}-{i}-{W}.webp')
                    out.save(path, 'WEBP', quality=82, method=6)
                    manifest.append((os.path.relpath(path, ROOT), W, H, n))
    for row in manifest:
        print('%-46s %4dx%-4d  from %s.jpg' % row)


if __name__ == '__main__':
    main()
