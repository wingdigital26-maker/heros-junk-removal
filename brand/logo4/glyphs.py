"""
Hero's logo4 glyphs: every form is a hand-laid cube icon, drawn row by row.

Each character is one cube column seen from the front. The letter picks the colour
and how deep the column runs (z layers; z=1 is the front face, the camera looks down -z):

  N navy, 2 deep        F navy, 3 deep (stands proud)   n navy, recessed (back 2)
  D deep navy, 2 deep   R red, 2 deep                   r red, 3 deep (proud)
  W warm white, 2 deep  w warm white, recessed 1 (back plate only)
  . empty

Pure python (no bpy), so the layout can be previewed and tested outside Blender.
"""
import math

HEX = {"navy": 0x14284B, "deep": 0x0C1A33, "red": 0xD62A1E, "white": 0xF3EEE4}
KEY = {
    "N": ("navy", (0, 1)), "F": ("navy", (0, 1, 2)), "n": ("navy", (-1, 0)),
    "D": ("deep", (0, 1)), "R": ("red", (0, 1)), "r": ("red", (0, 1, 2)),
    "W": ("white", (0, 1)), "w": ("white", (-1,)),
}

# ---- the logo: a house whose body is a bold H. The top notch of the H is a recessed
# warm-white window, the bottom notch is the open front door. Red roof chevron with eaves,
# warm-white chimney.
LOGO = [
    "........r........",
    ".......rrr.......",
    "......RRNRR.WW...",
    ".....RRNNNRRWW...",
    "....RRNNNNNRR....",
    "...RRNNNNNNNRR...",
    "..RRNNNNNNNNNRR..",
    ".RRNNNNNNNNNNNRR.",
    "RR.NNNNwwwNNNN.RR",
    "...NNNNwwwNNNN...",
    "...NNNNwwwNNNN...",
    "...FFFFFFFFFFF...",
    "...FFFFFFFFFFF...",
    "...NNNN...NNNN...",
    "...NNNN...NNNN...",
    "...NNNN...NNNN...",
    "...NNNN...NNNN...",
]

# ---- truck: tall box truck facing right. Box body with a proud red stripe, a separate cab with a
# slanted warm-white windshield, headlamp, red bumper, and big round wheels with white hubs.
TRUCK = [
    "NNNNNNNNNNNNNN........",
    "NNNNNNNNNNNNNN........",
    "NNNNNNNNNNNNNN.NNNN...",
    "NNNNNNNNNNNNNN.NWWWN..",
    "rrrrrrrrrrrrrr.NWWWWN.",
    "NNNNNNNNNNNNNN.NNNNNNN",
    "NNNNNNNNNNNNNN.NNNNNNW",
    "NNNNNNNNNNNNNNNNNNNNNr",
    "NN.DDD.NNNNNNNN.DDD.Nr",
    "..DDDDD........DDDDD..",
    "..DDWDD........DDWDD..",
    "..DDDDD........DDDDD..",
    "...DDD..........DDD...",
]

# ---- couch: deep-navy back set behind, navy arms stand proud, two red seat cushions
COUCH = [
    "..nnnnnnnnnnn..",
    "..nnnnnnnnnnn..",
    "..nnnnnnnnnnn..",
    "FF.nnnnnnnnn.FF",
    "FFFnnnnnnnnnFFF",
    "FFrrrrr.rrrrrFF",
    "FFrrrrr.rrrrrFF",
    "FFNNNNNNNNNNNFF",
    "FFNNNNNNNNNNNFF",
    ".DD.........DD.",
]


def _disc(w, h, cx, cy, rules):
    """Rasterise concentric rules [(radius, char)] (first match wins) onto a w x h grid."""
    rows = []
    for y in range(h):
        s = ""
        for x in range(w):
            d = math.hypot(x - cx, y - cy)
            ch = "."
            for r, c in rules:
                if d <= r:
                    ch = c
                    break
            s += ch
        rows.append(s)
    return rows


def _pin():
    w, h = 15, 18
    cx, cy, R = 7, 6.5, 6.9
    rows = _disc(w, h, cx, cy, [(1.3, "r"), (3.0, "w"), (R, "N")])
    out = []
    for y, row in enumerate(rows):
        row = list(row)
        if y > cy:  # the tail: tangent lines from the circle down to the tip
            tip = h - 1
            half = max(0.0, R * (tip - y) / (tip - cy)) * 0.98
            for x in range(w):
                if abs(x - cx) <= half + 0.25 and row[x] == ".":
                    row[x] = "N"
        out.append("".join(row))
    return out


# ---- star: hand laid, broad arms, legs taper to points, proud red core
STAR = [
    "........R........",
    ".......RRR.......",
    ".......RRR.......",
    "......RRRRR......",
    "......RRRRR......",
    "RRRRRRRRRRRRRRRRR",
    ".RRRRRRrrrRRRRRR.",
    "..RRRRrrrrrRRRR..",
    "...RRRrrrrrRRR...",
    "....RRRrrrRRR....",
    "....RRRRRRRRR....",
    "...RRRRRRRRRRR...",
    "...RRRRR.RRRRR...",
    "..RRRR.....RRRR..",
    "..RRR.......RRR..",
    ".RR...........RR.",
]


def _camera():
    w, h = 17, 13
    rows = [["."] * w for _ in range(h)]
    for y in range(3, h):
        for x in range(w):
            if (y in (3, h - 1)) and x in (0, w - 1):
                continue                     # softened corners
            rows[y][x] = "N"
    for x in range(5, 11):               # top hump over the lens
        rows[1][x] = rows[2][x] = "N"
    for x in range(12, 15):              # red shutter button
        rows[2][x] = "r"
    for x in range(1, 3):                # warm-white flash
        rows[4][x] = "W"
    cx, cy = 8, 7.6
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - cx, y - cy)
            if d <= 1.25:
                rows[y][x] = "n"
            elif d <= 2.45:
                rows[y][x] = "D"
            elif d <= 3.75 and y >= 3:
                rows[y][x] = "W"
    return ["".join(r) for r in rows]


# ---- moving box: navy carton, proud lid band, red tape down the middle, warm-white label
BOX = [
    "FFFFFFFrrFFFFFFF",
    "FFFFFFFrrFFFFFFF",
    ".NNNNNNrrNNNNNN.",
    ".NNNNNNrrNNNNNN.",
    ".NNNNNNrrNNNNNN.",
    ".NNNNNNNNNNNNNN.",
    ".NNNNNNNNNNNNNN.",
    ".NNNNNNNNNNNNNN.",
    ".NNNNNNNNNNNNNN.",
    ".NNNNNNNNNNNNNN.",
    ".NNNNNNNNNNNNNN.",
    ".DDDDDDDDDDDDDD.",
]

# ---- H: the Hero's letter, bold posts, proud red crossbar
H = [
    "FFFF.....FFFF",
    "NNNN.....NNNN",
    "NNNN.....NNNN",
    "NNNN.....NNNN",
    "NNNN.....NNNN",
    "NNNNrrrrrNNNN",
    "NNNNrrrrrNNNN",
    "NNNNrrrrrNNNN",
    "NNNN.....NNNN",
    "NNNN.....NNNN",
    "NNNN.....NNNN",
    "NNNN.....NNNN",
    "DDDD.....DDDD",
]

PIN, CAMERA = _pin(), _camera()

GLYPHS = {
    "house": LOGO, "truck": TRUCK, "couch": COUCH, "pin": PIN,
    "star": STAR, "camera": CAMERA, "h": H, "box": BOX,
}
# forms the engine can dock as (dock API data-form). Dark docks are recoloured at runtime.
REVERSE = {}
FORMS = ["house", "pin", "truck", "couch", "star", "camera", "h", "box"]


def cells(name):
    """-> list of (x, y, z, colourName), x right, y up, centred on the glyph box."""
    src, swap = (name, {}) if name in GLYPHS else REVERSE[name]
    rows = GLYPHS[src]
    h = len(rows); w = max(len(r) for r in rows)
    out = []
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == ".":
                continue
            col, zs = KEY[ch]
            col = swap.get(col, col)
            for z in zs:
                out.append((i - (w - 1) / 2, (h - 1) / 2 - j, z - 0.5, col))
    return out, w, h


if __name__ == "__main__":
    for f in FORMS:
        c, w, h = cells(f)
        print(f, w, "x", h, "cubes", len(c))
