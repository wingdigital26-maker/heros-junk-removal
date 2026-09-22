"""Hero's Junk Removal - THE HOUSE, built from fragments that re-form.

One fixed set of fragments. "house" is formation zero: a small house that empties itself (four blocks
lift out through the door). Every other formation is the SAME fragments in other places: a couch, a
fridge, a map board, a message bubble, a loaded truck. Nothing is added or removed between forms, they
only move, so on the site it reads as one object transforming, driven by scroll.

Same architecture as the Wing sculpture and heros-v2/brand/v3/morph.py (fixed N, per-target transform
sets, lerp on the web), extended with a rotation and a colour per fragment per target, and with
fragments matched to target cells by SHAPE (six axis permutations tried per pair) so the real bevelled
house geometry is reused with small scale ratios instead of stretched.

v7 to v11 (2026-09-22), judged render by render:
  - studio environment: a procedural HDRI (gradient dome + softboxes) written as an EXR, so metal faces
    carry a gradient and the bevels catch a travelling highlight; the three area lamps stay for diffuse
  - slate walls are brushed metal now, with per-fragment micro tilt, lightness and roughness jitter
  - roof is two thick slabs over stepped gables; the walls are panels with hairline seams
  - the four leaving blocks have their own proportions (crate, tall, flat, small)
  - roof 2 x 2 panels per slope (3 x 2 read as solar panels), four gable steps (three read as a staircase)
  - bevel segments 2 (3 pushed the GLB to 134KB)

VARIANT A (2026-09-22, Jack's pick from the contact sheet, overruling v12): the v8 house is the shipped one.
  3 x 2 roof panels per slope, three gable steps, 0.014 seams, rounded 3-segment bevels: 68 fragments. The
  defaults below ARE variant A. The v11/v12 look is still reachable with roofnx=2 gables=4 gap=0.006 seg=2.
  Later than v8 and kept: the studio HDRI, the brushed walls, the leaving blocks' proportions, the formations
  (couch/fridge/map/message/truck are authored against the homepage sections, not the house), and:
  - jitter (lightness, roughness, micro tilt) is a HOUSE thing. In the other formations it is scaled by JIT_FORM
    so slate and ink cells stop reading as a noisy checkerboard up close
  - the studio floor is darker below the horizon (floor=) so the far roof slab's underside, which reflects the
    floor, stops showing as a pale wedge at the right gable
  - map: a flat tiled board with an ink route and one red pin, not a city block with a marker

  blender --background --python house.py -- <outdir> [form=house|couch|fridge|map|message|truck|all]
                                                     [glb] [hero] [fast] [json]
    (default form=house; "hero" = transparent 1500x1150 poster frame; "fast" = quick judging render)
"""
import bpy, sys, math, os, json
import numpy as np
from mathutils import Matrix, Quaternion, Euler, Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else os.path.dirname(os.path.abspath(__file__))
FLAGS = set(a for a in argv[1:] if "=" not in a)
KV = dict(a.split("=", 1) for a in argv[1:] if "=" in a)
FORM = KV.get("form", "house")
WANT_GLB = "glb" in FLAGS
WANT_HERO = "hero" in FLAGS
FAST = "fast" in FLAGS
WANT_JSON = "json" in FLAGS or WANT_GLB
NORENDER = "norender" in FLAGS
QUANT = int(KV.get("quant", "12"))

# ---------------------------------------------------------------- palette (linear)
LIFT = float(KV.get("lift", "1.0"))    # wall lightness multiplier (lift= override for variants)
# slate house, darker slate roof and plinth, near-black navy blocks, ONE red accent
COLORS = {
    0: (0.062 * LIFT, 0.074 * LIFT, 0.094 * LIFT, 1.0),   # slate walls
    1: (0.030, 0.037, 0.050, 1.0),   # roof / plinth, darker slate
    2: (0.014, 0.020, 0.036, 1.0),   # ink, the blocks
    3: (0.36, 0.024, 0.030, 1.0),    # the accent red
}
# metal / roughness per colour: walls brushed, blocks a touch glossier, red a lacquer
SURF = {0: (0.78, 0.34), 1: (0.80, 0.36), 2: (0.85, 0.28), 3: (0.40, 0.30)}

W, D, H = 2.30, 1.80, 1.45            # house body
T = 0.14                              # wall thickness
TD = 0.24                             # the door wall is thicker: the doorway gets real depth
DOOR_W, DOOR_H = 0.70, 1.02
BASE_H = 0.11
OVER = 0.32                           # roof overhang
ROOF_T = 0.16                         # roof slab thickness
ROOF_H = 0.84                         # ridge above the eave line
ROOF_NX, ROOF_NK = int(KV.get("roofnx", "3")), 2   # roof panels along the ridge (variant A: 3), down the slope
GAP = float(KV.get("gap", "0.014"))   # seam between panels (variant A: 0.014; v12 was 0.006)
SEG = int(KV.get("seg", "3"))         # bevel segments (variant A: 3, rounded; v11 was 2)
GABLES = int(KV.get("gables", "3"))   # gable steps per end (variant A: 3; v11 was 4)
JIT_FORM = float(KV.get("jit", "0.25"))  # jitter multiplier outside the house formation
FLOOR = float(KV.get("floor", "0.58"))   # studio dome brightness straight down (was 0.74)
BAND = float(KV.get("band", "2.4"))      # the low front softbox: what a down-and-front facing underside reflects
FILL = float(KV.get("fill", "260"))      # the front-left fill lamp energy

FORM_OFFSET = (0.75, -0.35, 0.0)      # where the non-house formations stand (house is at the origin)


def frag(p, s, c, rot=(0, 0, 0), bw=0.024, role="wall", name=None):
    q = Euler(rot, "XYZ").to_quaternion()
    return {"p": [round(v, 4) for v in p], "s": [round(v, 4) for v in s],
            "r": [round(q.x, 5), round(q.y, 5), round(q.z, 5), round(q.w, 5)],
            "c": c, "b": bw, "role": role, "name": name}


def grid(cx, cy, cz, sx, sy, sz, nx, ny, nz, c, bw, role, rot=(0, 0, 0), name=None, skip=()):
    out = []
    for ix in range(nx):
        for iy in range(ny):
            for iz in range(nz):
                if (ix, iy, iz) in skip:
                    continue
                out.append(frag((cx + (ix + 0.5) / nx * sx - sx / 2, cy + (iy + 0.5) / ny * sy - sy / 2,
                                 cz + (iz + 0.5) / nz * sz - sz / 2),
                                (sx / nx - GAP, sy / ny - GAP, sz / nz - GAP), c, rot, bw, role, name))
    return out


# ---------------------------------------------------------------- the house, as fragments
def house_fragments():
    z0 = BASE_H
    F = []
    # chamfered plinth, runs out past the door as the threshold: 3 x 2 slabs
    F += grid(0.09, 0, BASE_H / 2, W + 0.38, D + 0.20, BASE_H, 3, 2, 1, 1, 0.030, "base")
    # front wall: 4 x 3 panels, one panel is the window (ink, set in a little)
    F += grid(0, -D / 2 + T / 2, z0 + H / 2, W - 2 * T, T, H, 4, 1, 3, 0, 0.020, "wall", skip=((1, 0, 1),))
    win = frag((-1.01 + 0.505 * 1.5, -D / 2 + T / 2 + 0.035, z0 + H / 2), (0.505 - GAP, T - 0.07 - GAP, H / 3 - GAP), 2, bw=0.010, role="wall", name="window")
    F.append(win)
    # back wall 4 x 3, left wall 3 x 3
    F += grid(0, D / 2 - T / 2, z0 + H / 2, W - 2 * T, T, H, 4, 1, 3, 0, 0.020, "wall")
    F += grid(-W / 2 + T / 2, 0, z0 + H / 2, T, D, H, 1, 3, 3, 0, 0.020, "wall")
    # door wall (+X): two piers of two panels each, a lintel, a dark reveal set back in the opening
    pier = (D - DOOR_W) / 2
    xr = W / 2 - TD / 2
    for yy in (-(DOOR_W / 2 + pier / 2), DOOR_W / 2 + pier / 2):
        F += grid(xr, yy, z0 + DOOR_H / 2, TD, pier, DOOR_H, 1, 1, 2, 0, 0.020, "wall")
    F.append(frag((xr, 0, z0 + DOOR_H + (H - DOOR_H) / 2), (TD - GAP, D - GAP, H - DOOR_H - GAP), 0, bw=0.020, role="wall", name="lintel"))
    F.append(frag((W / 2 - TD - 0.03, 0, z0 + DOOR_H / 2), (0.06, DOOR_W - 0.05, DOOR_H - 0.02), 2, bw=0.010, role="wall", name="reveal"))

    # roof: two thick slabs at the pitch, 3 x 2 panels each, meeting at the ridge
    ze = z0 + H - 0.02                            # eave line
    half = D / 2 + OVER                           # eave reach from the ridge, in Y
    pitch = math.atan2(ROOF_H, half)
    slope_len = math.hypot(half, ROOF_H) + 0.10   # a little past the ridge so the two slabs close it
    for s in (-1, 1):                             # s=-1 front slope (-Y)
        n = Vector((0, s * math.sin(pitch), math.cos(pitch)))          # outward normal of the slope
        along = Vector((0, s * math.cos(pitch), -math.sin(pitch)))      # down the slope, from the ridge
        ridge = Vector((0, 0, ze + ROOF_H))
        for ix in range(ROOF_NX):
            for k in range(ROOF_NK):
                d = (k + 0.5) / ROOF_NK * slope_len - 0.05
                cpos = ridge + along * d + n * (ROOF_T / 2)
                cpos.x = (ix + 0.5) / ROOF_NX * (W + 2 * OVER) - (W + 2 * OVER) / 2
                F.append(frag(tuple(cpos), ((W + 2 * OVER) / ROOF_NX - GAP, slope_len / ROOF_NK - GAP, ROOF_T - GAP), 1,
                              rot=(-s * pitch, 0, 0), bw=0.016, role="roof"))
    # stepped gables under the slabs, at both ends, inside the wall line
    if GABLES == 3:
        rows = ((z0 + H, z0 + H + 0.28), (z0 + H + 0.28, z0 + H + 0.54), (z0 + H + 0.54, z0 + H + 0.76))
    else:
        rows = ((z0 + H, z0 + H + 0.20), (z0 + H + 0.20, z0 + H + 0.40), (z0 + H + 0.40, z0 + H + 0.58), (z0 + H + 0.58, z0 + H + 0.74))
    for sx_ in (-1, 1):
        for (za, zb) in rows:
            wid = min(D, 2 * half * (1 - (zb - ze) / ROOF_H) - 0.06)
            F.append(frag((sx_ * (W / 2 - T / 2), 0, (za + zb) / 2), (T - GAP, wid, zb - za - GAP), 0, bw=0.018, role="gable"))

    # one block still inside, seen through the door
    F.append(frag((0.72, -0.02, z0 + 0.26), (0.46, 0.46, 0.52), 2, rot=(0, 0, 0.35), bw=0.028, role="inside", name="inside"))
    # THE GESTURE: blocks leaving through the door to the right and up, each its own object
    arc = [
        ((2.42, -0.58, 0.80), (0.52, 0.46, 0.40), 2),    # a crate, low and wide
        ((2.92, -0.78, 1.62), (0.40, 0.38, 0.46), 3),    # the accent block, a touch tall
        ((3.28, -0.92, 2.44), (0.34, 0.36, 0.26), 2),    # flat
        ((3.52, -1.00, 3.16), (0.24, 0.22, 0.26), 2),    # small
    ]
    for i, (p, s, c) in enumerate(arc):
        F.append(frag(p, s, c, rot=(0.30 - i * 0.14, 0.20 - i * 0.16, -0.40 + i * 0.22), bw=0.026, role="lift", name=f"lift{i}"))

    # deterministic per-fragment jitter: micro tilt (rad), lightness, roughness. The web reads the same numbers.
    rng = np.random.default_rng(7)
    for i, f in enumerate(F):
        f["name"] = f["name"] or f"frag{i}"
        if f["role"] in ("wall", "roof", "gable", "base"):
            t = rng.uniform(-1, 1, 3) * math.radians(0.45)
            q = Quaternion((f["r"][3], f["r"][0], f["r"][1], f["r"][2]))
            q = q @ Euler(tuple(t), "XYZ").to_quaternion()
            f["r"] = [round(q.x, 5), round(q.y, 5), round(q.z, 5), round(q.w, 5)]
        f["v"] = [round(float(rng.uniform(-0.035, 0.035)), 4), round(float(rng.uniform(-0.06, 0.06)), 4)]
    return F


# ---------------------------------------------------------------- other formations (boxes, sitting on z=0)
# (cx, cy, cz, sx, sy, sz, colour, yaw_deg, cells) cells=None -> proportional to volume
def shape_couch():
    return [
        (-0.80, 0.00, 0.66, 0.92, 1.12, 0.34, 0, 0, None),   # three seat cushions
        (0.00, 0.00, 0.66, 0.92, 1.12, 0.34, 0, 0, None),
        (0.80, 0.00, 0.66, 0.92, 1.12, 0.34, 0, 0, None),
        (0.00, 0.50, 1.22, 2.80, 0.26, 0.86, 1, 0, None),    # back
        (-1.55, 0.00, 0.84, 0.30, 1.12, 0.74, 1, 0, 2),      # arms, two tall panels each
        (1.55, 0.00, 0.84, 0.30, 1.12, 0.74, 1, 0, 2),
        (0.00, 0.00, 0.30, 2.75, 1.05, 0.36, 2, 0, None),    # base, ink
        (0.85, 0.22, 1.06, 0.46, 0.14, 0.46, 3, 12, 1),      # ONE red throw pillow, leaning on the back
    ]


def shape_fridge():
    return [
        (0.00, 0.00, 1.32, 1.36, 1.10, 2.50, 0, 0, None),    # body
        (0.00, -0.62, 1.86, 1.28, 0.12, 1.32, 1, 0, None),   # upper door
        (0.00, -0.62, 0.66, 1.28, 0.12, 0.96, 1, 0, None),   # lower door
        (0.00, 0.00, 0.06, 1.20, 1.00, 0.12, 2, 0, None),    # plinth
        (-0.48, -0.72, 1.86, 0.08, 0.08, 0.90, 3, 0, 2),     # the red handle
    ]


def shape_map():
    """A map, not a city: a flat tiled board (4 x 3, all one low height), an ink route running across it in
    three legs, and one red pin standing on the route's end. Nothing on the board is taller than the route."""
    tiles = []
    for iy in range(3):
        for ix in range(4):
            tiles.append((-1.35 + ix * 0.90, -0.90 + iy * 0.90, 0.07, 0.86, 0.86, 0.14, 0, 0, None))
    # the route: three legs laid on the board, leg ends overlap so it reads as one line
    tiles.append((-1.10, -0.90, 0.20, 1.40, 0.20, 0.10, 2, 0, 2))     # west to east along the bottom row
    tiles.append((-0.40, -0.25, 0.20, 0.20, 1.50, 0.10, 2, 0, 2))     # north up the middle
    tiles.append((0.40, 0.40, 0.20, 1.80, 0.20, 0.10, 2, 0, 2))       # east to the pin
    tiles.append((1.35, 0.40, 0.20 + 0.52, 0.12, 0.12, 0.95, 2, 0, 1))          # pin post
    tiles.append((1.35, 0.40, 0.20 + 1.22, 0.50, 0.50, 0.50, 3, 45, 1))         # the red pin head, a diamond
    return tiles


def shape_message():
    return [
        (0.00, 0.00, 1.32, 3.10, 0.34, 1.90, 0, 0, None),       # the bubble, standing up, thin so the cells read as tiles
        (-1.05, 0.00, 0.36, 0.50, 0.34, 0.50, 0, 45, 4),        # the tail, a diamond hanging off the bottom left edge
        (-0.65, -0.26, 1.32, 0.42, 0.14, 0.42, 3, 0, 1),        # three red dots: "typing"
        (0.00, -0.26, 1.32, 0.42, 0.14, 0.42, 3, 0, 1),
        (0.65, -0.26, 1.32, 0.42, 0.14, 0.42, 3, 0, 1),
    ]


def shape_truck():
    return [
        (0.00, 0.00, 0.58, 3.60, 1.20, 0.32, 2, 0, None),      # chassis, ink
        (-1.25, 0.00, 1.18, 1.10, 1.10, 0.86, 0, 0, None),     # cab
        (0.80, 0.00, 0.98, 2.20, 1.16, 0.28, 1, 0, None),      # bed floor
        (0.80, 0.00, 1.18, 2.15, 1.20, 0.12, 3, 0, None),      # the red stripe
        (0.80, 0.00, 1.62, 1.90, 1.00, 0.76, 2, 0, None),      # the load
        (-1.25, 0.00, 0.20, 0.80, 1.30, 0.40, 2, 0, None),     # wheels, front axle
        (1.10, 0.00, 0.20, 0.80, 1.30, 0.40, 2, 0, None),      # wheels, rear axle
    ]


SHAPES = {"couch": shape_couch, "fridge": shape_fridge, "map": shape_map, "message": shape_message, "truck": shape_truck}
ORDER = ["house", "couch", "fridge", "map", "message", "truck"]


def layout(boxes, n):
    """Split n cells across the boxes (fixed counts honoured, the rest by volume), on a near-cubic grid per box."""
    fixed = sum(b[8] for b in boxes if b[8])
    free = [b for b in boxes if not b[8]]
    vols = [b[3] * b[4] * b[5] for b in free]
    total = sum(vols)
    counts = {id(b): max(1, round((n - fixed) * v / total)) for b, v in zip(free, vols)}
    while sum(counts.values()) > n - fixed:
        k = max(counts, key=counts.get); counts[k] -= 1
    while sum(counts.values()) < n - fixed:
        k = max(counts, key=counts.get); counts[k] += 1
    cells = []
    for b in boxes:
        cx, cy, cz, sx, sy, sz, col, yaw, fixedn = b
        c = fixedn or counts[id(b)]
        best, bestscore = (1, 1, 1), 1e9
        for gx in range(1, c + 1):
            for gy in range(1, c // gx + 1):
                gz = max(1, round(c / (gx * gy)))
                if gx * gy * gz < c:
                    continue
                cell = (sx / gx, sy / gy, sz / gz)
                score = max(cell) / max(1e-6, min(cell)) + 2.0 * abs(gx * gy * gz - c)
                if score < bestscore:
                    best, bestscore = (gx, gy, gz), score
        gx, gy, gz = best
        made = 0
        rot = Matrix.Rotation(math.radians(yaw), 3, "Z")
        for ix in range(gx):
            for iy in range(gy):
                for iz in range(gz):
                    if made >= c:
                        break
                    local = Vector(((ix + 0.5) / gx * sx - sx / 2, (iy + 0.5) / gy * sy - sy / 2, (iz + 0.5) / gz * sz - sz / 2))
                    p = Vector((cx, cy, cz)) + rot @ local
                    cells.append({"p": [p.x, p.y, p.z], "s": [sx / gx - GAP, sy / gy - GAP, sz / gz - GAP], "c": col, "yaw": yaw})
                    made += 1
    assert len(cells) == n, (len(cells), n)
    return cells


PERMS = [(0, 1, 2), (0, 2, 1), (1, 0, 2), (1, 2, 0), (2, 0, 1), (2, 1, 0)]


def perm_quat(perm):
    """Rotation that sends fragment local axis perm[i] onto world axis i (a box is symmetric, so a sign flip fixes parity)."""
    M = Matrix.Identity(3)
    for i in range(3):
        for j in range(3):
            M[i][j] = 1.0 if perm[i] == j else 0.0
    if M.determinant() < 0:
        for i in range(3):
            M[i][perm[0]] *= -1
    return M.to_quaternion()


def assign(frags, cells):
    """Give every house fragment a cell: biggest cells first, each takes the free fragment whose shape (in the best of
    six axis orders) needs the least stretching. Returns a per-fragment target list in fragment order."""
    order = sorted(range(len(cells)), key=lambda i: -np.prod(cells[i]["s"]))
    free = set(range(len(frags)))
    out = [None] * len(frags)
    for ci in order:
        cell = cells[ci]
        best = None
        for fi in free:
            fs = frags[fi]["s"]
            for perm in PERMS:
                cost = sum(abs(math.log(cell["s"][i] / fs[perm[i]])) for i in range(3))
                if best is None or cost < best[0]:
                    best = (cost, fi, perm)
        _, fi, perm = best
        free.discard(fi)
        fs = frags[fi]["s"]
        scale = [0, 0, 0]
        for i in range(3):
            scale[perm[i]] = cell["s"][i] / fs[perm[i]]
        q = Matrix.Rotation(math.radians(cell["yaw"]), 3, "Z").to_quaternion() @ perm_quat(perm)
        out[fi] = {"p": [round(v, 4) for v in cell["p"]], "k": [round(v, 4) for v in scale],
                   "r": [round(q.x, 5), round(q.y, 5), round(q.z, 5), round(q.w, 5)], "c": cell["c"]}
    return out


def formations(frags):
    """Every target as per-fragment records. The house target is the fragments themselves (scale 1)."""
    data = {"n": len(frags),
            "frags": [{"name": f["name"], "s": f["s"], "b": f["b"], "role": f["role"], "v": f["v"]} for f in frags],
            "targets": {"house": [{"p": f["p"], "k": [1, 1, 1], "r": f["r"], "c": f["c"]} for f in frags]}}
    ox, oy, oz = FORM_OFFSET
    for k in ORDER[1:]:
        cells = layout(SHAPES[k](), len(frags))
        for c in cells:
            c["p"] = [c["p"][0] + ox, c["p"][1] + oy, c["p"][2] + oz]
        data["targets"][k] = assign(frags, cells)
    return data


# ---------------------------------------------------------------- blender
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def make_material(name, rgba, metallic, rough, light=0.0, rough_off=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    r, g, bb, a = rgba
    f = 1 + light * 2.2
    b.inputs["Base Color"].default_value = (r * f, g * f, bb * f, a)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = max(0.06, rough + rough_off)
    if metallic > 0.3:
        b.inputs["Coat Weight"].default_value = 0.35 if metallic < 0.6 else 0.18
        b.inputs["Coat Roughness"].default_value = 0.12
    return m


def build(frags, targets, form):
    """Each fragment: a cube at its HOUSE size with a real bevel, then posed by the target's transform (position,
    rotation, scale ratio). That is exactly what the web does, so the renders and the live scene agree."""
    for i, f in enumerate(frags):
        t = targets[i]
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
        o = bpy.context.object
        o.name = f["name"]
        o.scale = f["s"]
        bpy.ops.object.transform_apply(scale=True)
        m = o.modifiers.new("bev", "BEVEL")
        m.width = min(f["b"], min(f["s"]) * 0.42)
        m.segments = SEG
        m.limit_method = "ANGLE"
        m.angle_limit = math.radians(38)
        m.harden_normals = True
        for p in o.data.polygons:
            p.use_smooth = True
        col = t["c"]
        met, rough = SURF[col]
        jit = 1.0 if form == "house" else JIT_FORM
        o.data.materials.append(make_material(f"m{i}", COLORS[col], met, rough, f["v"][0] * jit, f["v"][1] * jit))
        o.location = t["p"]
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion = (t["r"][3], t["r"][0], t["r"][1], t["r"][2])
        o.scale = t["k"]


# softboxes for the procedural HDRI: (direction xyz in Blender world, half-width deg, half-height deg, intensity, tint)
SOFTBOXES = [
    ((4.6, -5.6, 6.2), 30, 20, 3.5, (1.00, 1.00, 1.00)),    # key, front-right-high, over the door side (was 7.0: it is what the far slab's overhang face reflected as a pale wedge at the right gable; halved, walls unchanged)
    ((7.0, -3.0, 1.2), 5, 42, 9.0, (0.98, 0.99, 1.00)),     # tall strip right-front: the long travelling highlight
    ((-5.2, 4.8, 3.8), 5, 34, 6.5, (0.92, 0.95, 1.00)),     # rim strip back-left: the edge catch on ridge and eaves
    ((0.0, 0.0, 1.0), 48, 7, 3.2, (1.00, 1.00, 1.00)),      # overhead strip: top-edge catch along the ridge
    ((3.5, -6.5, -0.7), 46, 6, BAND, (0.96, 0.97, 1.00)),   # low front band: camera-facing faces reflect below the camera
    ((-5.0, -5.0, 1.6), 24, 16, 1.8, (0.95, 0.96, 1.00)),   # soft fill front-left, dim
]


def write_studio(path, wpx=768, hpx=384):
    """A hand-built HDRI: gradient dome (pale floor, mid horizon, dusk-grey sky) plus soft rectangles for the softboxes."""
    v, u = np.mgrid[0:hpx, 0:wpx]
    u = (u + 0.5) / wpx
    v = (v + 0.5) / hpx
    el = (v - 0.5) * math.pi
    az = (u - 0.5) * 2 * math.pi
    dx, dy, dz = -np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)
    # dome: floor FLOOR (0.58, the silver stage seen from below), horizon 0.42, zenith 0.20, a slow gradient so faces show a sweep
    t = np.clip(dz, -1, 1)
    sky = np.where(t < 0, 0.42 + (FLOOR - 0.42) * np.clip(-t, 0, 1) ** 0.7, 0.42 + (0.20 - 0.42) * np.clip(t, 0, 1) ** 0.8)
    img = np.stack([sky * 0.96, sky * 0.975, sky * 1.0], -1)
    SBM = [float(v) for v in KV.get("sb", "1,1,1,1,1,1").split(",")]   # per-softbox multipliers, for bisecting a reflection
    for (cd, hw, hh, inten, tint), mul in zip(SOFTBOXES, SBM):
        inten = inten * mul
        c = np.array(cd, float); c /= np.linalg.norm(c)
        up = np.array([0, 0, 1.0]) if abs(c[2]) < 0.95 else np.array([1.0, 0, 0])
        t1 = np.cross(up, c); t1 /= np.linalg.norm(t1)
        t2 = np.cross(c, t1)
        dot = dx * c[0] + dy * c[1] + dz * c[2]
        a1 = np.degrees(np.arctan2(dx * t1[0] + dy * t1[1] + dz * t1[2], np.maximum(dot, 1e-3)))
        a2 = np.degrees(np.arctan2(dx * t2[0] + dy * t2[1] + dz * t2[2], np.maximum(dot, 1e-3)))
        soft = 0.35
        m1 = np.clip((hw - np.abs(a1)) / (hw * soft), 0, 1)
        m2 = np.clip((hh - np.abs(a2)) / (hh * soft), 0, 1)
        m = (m1 * m1 * (3 - 2 * m1)) * (m2 * m2 * (3 - 2 * m2)) * (dot > 0)
        # a gentle falloff across the box so the reflection is a gradient, not a flat patch
        m = m * (1 - 0.35 * np.clip((a2 / max(hh, 1e-3)) * 0.5 + 0.5, 0, 1))
        for k in range(3):
            img[..., k] += m * inten * tint[k]
    im = bpy.data.images.new("studio", wpx, hpx, alpha=False, float_buffer=True)
    px = np.concatenate([img[::-1].reshape(-1, 3), np.ones((wpx * hpx, 1))], 1).astype(np.float32)   # blender rows go bottom-up
    im.pixels.foreach_set(px.ravel())
    im.filepath_raw = path
    im.file_format = "OPEN_EXR"
    im.save()
    return im


def stage(hero=False):
    if not hero:
        bpy.ops.mesh.primitive_plane_add(size=90, location=(0, 0, 0))
        gp = bpy.context.object
        gp.name = "ground"
        gp.data.materials.append(make_material("bg", (0.905, 0.915, 0.935, 1), 0.0, 0.5))

    def lamp(name, loc, energy, size):
        d = bpy.data.lights.new(name, "AREA")
        d.energy, d.size = energy, size
        o = bpy.data.objects.new(name, d)
        bpy.context.collection.objects.link(o)
        o.location = loc
        c = o.constraints.new("TRACK_TO")
        c.track_axis, c.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
        return o

    tgt = bpy.data.objects.new("tgt", None)
    bpy.context.collection.objects.link(tgt)
    tgt.location = (1.05, -0.40, 1.50)
    # the lamps carry the diffuse; the HDRI carries the reflections
    for l in (lamp("key", (4.6, -5.6, 6.2), 1100, 6),
              lamp("rim", (-5.2, 4.8, 3.8), 2000, 4),
              lamp("fill", (-4.8, -5.4, 2.2), FILL, 10)):
        l.constraints[0].target = tgt

    w = bpy.context.scene.world or bpy.data.worlds.new("W")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = write_studio(os.path.join(OUT, "studio.exr"))
    bg = nt.nodes["Background"]
    nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    bg.inputs[1].default_value = float(KV.get("env", "0.85"))

    bpy.ops.object.camera_add(location=(9.8, -11.6, 4.7))
    cam = bpy.context.object
    cam.data.lens = 105
    c = cam.constraints.new("TRACK_TO")
    c.track_axis, c.up_axis, c.target = "TRACK_NEGATIVE_Z", "UP_Y", tgt
    bpy.context.scene.camera = cam

    s = bpy.context.scene
    s.render.engine = "BLENDER_EEVEE"
    s.render.resolution_x = 1500 if hero else 1200
    s.render.resolution_y = 1150 if hero else 900
    if FAST:
        s.render.resolution_percentage = 66
    s.render.film_transparent = hero
    try:
        s.eevee.use_raytracing = True
        s.eevee.ray_tracing_options.resolution_scale = "1"
        s.eevee.taa_render_samples = 24 if FAST else (128 if hero else 64)
    except Exception:
        pass
    s.view_settings.look = "AgX - Medium High Contrast"
    s.view_settings.exposure = 0.10


# ---------------------------------------------------------------- run
os.makedirs(OUT, exist_ok=True)
FR = house_fragments()
DATA = formations(FR)
if WANT_JSON:
    with open(os.path.join(OUT, "shapes.json"), "w") as fh:
        json.dump(DATA, fh, separators=(",", ":"))
    print("wrote shapes.json n=%d targets=%s" % (DATA["n"], list(DATA["targets"])))

forms = ORDER if FORM == "all" else [FORM]
for form in forms:
    reset()
    build(FR, DATA["targets"][form], form)
    stage(hero=WANT_HERO)
    tag = "house" if form == "house" else form
    bpy.context.scene.render.filepath = os.path.join(OUT, f"{tag}-hero.png" if WANT_HERO else f"{tag}.png")
    if not NORENDER:
        bpy.ops.render.render(write_still=True)
    print("RENDERED", form)
    if WANT_GLB and form == "house":
        bpy.ops.object.select_all(action="SELECT")
        for n in ("ground", "key", "rim", "fill", "tgt", "Camera"):
            if n in bpy.data.objects:
                bpy.data.objects[n].select_set(False)
        bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "house.glb"),
                                  export_format="GLB", use_selection=True,
                                  export_draco_mesh_compression_enable=True, export_apply=True,
                                  export_draco_position_quantization=QUANT, export_draco_normal_quantization=8,
                                  export_materials="NONE" if "nomat" in FLAGS else "EXPORT")
        tris = sum(len(p.vertices) - 2 for o in bpy.data.objects if o.type == "MESH" and o.name != "ground"
                   for p in o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.polygons)
        print("TRIS", tris, "FRAGS", len(FR))
print("DONE house")
