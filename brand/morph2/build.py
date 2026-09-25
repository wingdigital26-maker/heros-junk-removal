"""
Hero's Junk Removal - morph2: ONE object of 1,600 small cubes that rearranges
into a HOUSE, a PICKUP + TRAILER, a COUCH and a slab-serif H. Every cube also
carries a real-world colour + PBR finish per formation (brick, shingle, glass,
paint, rubber, chrome, linen, walnut...), so each form reads as a real object.

Each target is modelled in Blender as a stack of clean convex solids (boxes,
extruded convex polygons, cylinders) combined with ordered add / subtract ops,
plus "paint" volumes that colour whatever surface cubes fall inside them.
The solid is voxel-sampled on a unit grid and only the VISIBLE surface is kept
(cubes that face the front, top or sides; the back and underside are never seen
from the 3/4 camera, so their budget goes to finer detail). The scale of each
shape is searched so every form has as close to N cubes as possible, spare
cubes hide inside, and point sets are matched form-to-form (greedy nearest).

Run (from repo root):
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --factory-startup \
      -P brand/morph2/build.py -- [--n 1600] [--stage all|shapes|posters] [--forms house,truck] [--samples 64]

Outputs:
  assets/piece2/shapes.json   {n, cube, fill, mats:[[rough,metal],..],
                               forms:{house:[x,y,z,...]}, colors:{house:[0xRRGGBB,...]},
                               pbr:{house:[matIndex,...]}}      (three.js Y-up, sRGB ints)
  assets/piece2/poster-<form>.webp   1600x1200 transparent Eevee stills (fallback)
"""
import bpy, bmesh, sys, os, json, math, colorsys
import numpy as np
from mathutils import Vector, Matrix

# ------------------------------------------------------------------ args ----
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(name, default):
    if name in argv:
        i = argv.index(name)
        if i + 1 < len(argv):
            return argv[i + 1]
    return default

N = int(arg("--n", "1600"))
STAGE = arg("--stage", "all")
ONLY = [f for f in arg("--forms", "").split(",") if f]
SAMPLES = int(arg("--samples", "64"))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "assets", "piece2")
os.makedirs(OUT, exist_ok=True)
FORMS = ["house", "truck", "couch", "h"]
YAW = {"house": 30, "truck": 22, "couch": 24, "h": 20}   # poster camera yaw (deg, from front towards +X)
CUBE = 1.0          # voxel pitch in output units
CUBE_FILL = 0.97    # rendered cube edge relative to pitch: hairline seams, reads as a solid object
BEVEL = 0.05        # bevel radius (fraction of the edge)

# --------------------------------------------------------------- finishes ----
# name: (sRGB hex, roughness, metalness, per-cube tone jitter)
MATS = {
    "brick":    ("#8E4331", 0.88, 0.0, 0.10),
    "mortar":   ("#B9AFA3", 0.9, 0.0, 0.03),
    "shingle":  ("#3A3D42", 0.8, 0.0, 0.06),
    "trim":     ("#F3F1EC", 0.5, 0.0, 0.01),
    "siding":   ("#E6E1D6", 0.6, 0.0, 0.02),
    "glass":    ("#7FA3BD", 0.06, 0.35, 0.03),
    "door":     ("#8C1C1E", 0.32, 0.0, 0.0),
    "concrete": ("#C4C0B8", 0.92, 0.0, 0.04),
    "paint":    ("#AFB5BD", 0.28, 0.55, 0.0),     # silver pickup
    "tyre":     ("#1E1F21", 0.92, 0.0, 0.02),
    "hub":      ("#9EA3A9", 0.3, 0.85, 0.0),
    "chrome":   ("#B9BEC4", 0.14, 0.95, 0.0),
    "grille":   ("#3C4046", 0.35, 0.7, 0.0),
    "tint":     ("#1F2A33", 0.05, 0.4, 0.0),
    "lamp":     ("#E9EEF2", 0.08, 0.3, 0.0),
    "tail":     ("#C0231C", 0.25, 0.0, 0.0),
    "rocker":   ("#34373C", 0.6, 0.2, 0.0),
    "liner":    ("#2A2C2F", 0.9, 0.0, 0.02),
    "steel":    ("#4A5058", 0.5, 0.55, 0.03),
    "wood":     ("#8A6240", 0.82, 0.0, 0.09),
    "linen":    ("#7C8A6B", 0.95, 0.0, 0.025),    # sage upholstery
    "seam":     ("#5F6B53", 0.95, 0.0, 0.02),
    "walnut":   ("#4A3222", 0.5, 0.0, 0.03),
    "navy":     ("#14284B", 0.42, 0.05, 0.0),
    "red":      ("#D62A1E", 0.38, 0.0, 0.0),
}
MAT_NAMES = list(MATS)

# --------------------------------------------------------- mesh helpers ----
def _obj_from_bm(bm, name):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob

def box(x0, x1, y0, y1, z0, z1, name="box"):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(x1 - x0, y1 - y0, z1 - z0), verts=bm.verts)
    bmesh.ops.translate(bm, vec=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), verts=bm.verts)
    return _obj_from_bm(bm, name)

def cyl_y(cx, cz, r, y0, y1, name="cyl", seg=48):
    """Cylinder whose axis runs along Blender Y (depth) - wheels."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=y1 - y0)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'X'))
    bmesh.ops.translate(bm, vec=(cx, (y0 + y1) / 2, cz), verts=bm.verts)
    return _obj_from_bm(bm, name)

def prism_xz(poly, y0, y1, name="prism"):
    """Convex polygon in X-Z (profile view), extruded along Y."""
    bm = bmesh.new()
    a = [bm.verts.new((x, y0, z)) for x, z in poly]
    b = [bm.verts.new((x, y1, z)) for x, z in poly]
    bm.faces.new(a); bm.faces.new(b[::-1])
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((a[i], a[j], b[j], b[i]))
    return _obj_from_bm(bm, name)

def gable(x0, x1, z0, zapex, y0, y1, name="roof"):
    return prism_xz([(x0, z0), (x1, z0), ((x0 + x1) / 2, zapex)], y0, y1, name)

# --------------------------------------------------------- the 4 models ----
# Blender units, Z up, front of every object faces -Y (towards the camera),
# ground at z=0. ops: ("+", obj, material) | ("-", obj) | ("p", obj, material)
class Ops(list):
    def A(self, o, m): self.append(("+", o, m))
    def S(self, o): self.append(("-", o, None))
    def P(self, o, m): self.append(("p", o, m))

def model_house():
    o = Ops()
    o.A(box(-9, 9, -7, 7, 0, 11, "walls"), "brick")
    o.A(gable(-10.5, 10.5, 10.5, 20.5, -8, 8, "roof"), "shingle")
    o.A(box(4.2, 7.0, -1.0, 2.0, 14, 22, "chimney"), "brick")
    o.A(box(-3.0, 3.0, -8.2, -7.0, 0, 0.9, "step"), "concrete")
    wins = [(-7.2, -3.8, 4.0, 7.8), (3.8, 7.2, 4.0, 7.8)]
    o.S(box(-2.0, 2.0, -9, -5.6, 0.9, 8.0, "door"))
    for x0, x1, z0, z1 in wins:
        o.S(box(x0, x1, -9, -5.6, z0, z1, "win"))
    o.S(box(-1.6, 1.6, -9, -6.6, 13.0, 16.2, "gableWin"))
    side = [(-4.6, -1.2), (1.2, 4.6)]
    for y0, y1 in side:
        o.S(box(7.4, 10, y0, y1, 4.0, 7.8, "sideWin"))
    # paint: foundation course, siding in the gable, white trim, glass, red door
    o.P(box(-9.6, 9.6, -8.5, 8.5, 0, 0.95), "concrete")
    o.P(box(4.0, 7.2, -1.2, 2.2, 21.1, 22.5), "shingle")                 # chimney cap
    for x0, x1, z0, z1 in wins:
        o.P(box(x0 - 0.6, x1 + 0.6, -9, -6.2, z0 - 0.6, z1 + 0.6), "trim")
        o.P(box(x0, x1, -9, -4.0, z0, z1), "glass")
    o.P(box(-2.6, 2.6, -9, -6.2, 0.9, 8.6), "trim")
    o.P(box(-2.0, 2.0, -9, -4.0, 0.9, 8.0), "door")
    o.P(gable(-9.3, 9.3, 10.4, 19.3, -9, -6.9, "gableBrick"), "brick")
    o.P(box(-2.2, 2.2, -9, -7.4, 12.4, 16.8), "trim")
    o.P(box(-1.6, 1.6, -9, -5.0, 13.0, 16.2), "glass")
    for y0, y1 in side:
        o.P(box(8.2, 10, y0 - 0.6, y1 + 0.6, 3.4, 8.4), "trim")
        o.P(box(6.4, 10, y0, y1, 4.0, 7.8), "glass")
    return o

def model_truck():
    """Full-size pickup (nose +X) towing a small open utility trailer. ~1 unit = 20 cm."""
    o = Ops()
    W = 5.0
    WR, WZ = 2.35, 2.35
    FX, RX = 24.8, 6.2                 # front / rear axle
    # body
    o.A(box(10.4, 20.6, -W, W, 2.0, 7.2, "cabLow"), "paint")
    o.A(prism_xz([(20.4, 2.0), (29.8, 2.0), (29.8, 6.2), (29.0, 7.0), (20.4, 7.3)], -W, W, "hood"), "paint")
    o.A(prism_xz([(10.6, 7.0), (20.6, 7.0), (17.2, 10.6), (11.0, 10.6)], -W + 0.35, W - 0.35, "cabTop"), "paint")
    o.A(box(0, 10.0, -W, W, 2.2, 7.3, "bed"), "paint")
    o.S(box(0.95, 9.1, -W + 0.95, W - 0.95, 3.6, 12, "bedHollow"))
    o.A(box(-0.8, 0.4, -W + 0.3, W - 0.3, 1.7, 3.2, "rearBumper"), "chrome")
    o.A(box(29.4, 30.8, -W + 0.2, W - 0.2, 1.5, 3.7, "frontBumper"), "chrome")
    for y0, y1 in ((-W - 0.95, -W), (W, W + 0.95)):
        o.A(box(18.4, 19.6, y0, y1, 7.4, 8.5, "mirror"), "paint")
    # wheel arches, then tyres on each side (not a solid axle)
    for cx in (RX, FX):
        o.S(cyl_y(cx, WZ, WR + 0.8, -W - 2, W + 2, "arch"))
    for cx in (RX, FX):
        o.A(cyl_y(cx, WZ, WR, -W - 0.35, -W + 2.4, "tyre"), "tyre")
        o.A(cyl_y(cx, WZ, WR, W - 2.4, W + 0.35, "tyre"), "tyre")
    # trailer on a hitch
    o.A(box(-5.2, -0.6, -0.5, 0.5, 2.5, 3.3, "tongue"), "steel")
    o.A(box(-17.2, -5.0, -4.3, 4.3, 2.6, 6.6, "trailer"), "steel")
    o.S(box(-16.25, -5.95, -3.35, 3.35, 3.6, 12, "trailerHollow"))
    # outboard wheels under fenders (no arch into the bed)
    o.A(cyl_y(-11.1, 1.8, 1.8, -6.1, -4.4, "tTyre"), "tyre")
    o.A(cyl_y(-11.1, 1.8, 1.8, 4.4, 6.1, "tTyre"), "tyre")
    o.A(box(-13.5, -8.7, -6.2, -4.3, 3.9, 4.6, "fender"), "steel")
    o.A(box(-13.5, -8.7, 4.3, 6.2, 3.9, 4.6, "fender"), "steel")
    # paint: glasshouse with pillars and roof, lamps, grille, rocker, bed liner, hubs
    o.P(prism_xz([(10.4, 7.35), (20.8, 7.35), (17.3, 10.9), (10.8, 10.9)], -W - 1, W + 1, "glassArea"), "tint")
    o.P(box(10.0, 17.4, -W - 1, W + 1, 9.75, 11.5), "paint")              # roof skin
    o.P(box(14.5, 15.3, -W - 1, W + 1, 7.0, 11.5), "paint")               # B-pillar
    o.P(box(10.0, 11.6, -W - 1, W + 1, 7.0, 11.5), "paint")               # C-pillar
    o.P(box(29.0, 31.5, -3.1, 3.1, 3.7, 6.1), "grille")
    for y0, y1 in ((-W - 1, -3.3), (3.3, W + 1)):
        o.P(box(29.0, 31.5, y0, y1, 4.6, 6.1), "lamp")
        o.P(box(-1.2, 0.7, y0 if y0 < 0 else 3.9, -3.9 if y0 < 0 else y1, 4.2, 6.9), "tail")
    o.P(box(10.4, 20.6, -W - 1, W + 1, 1.9, 2.85), "rocker")
    o.P(box(0.95, 9.1, -W + 0.95, W - 0.95, 1.5, 3.65), "liner")
    for cx in (RX, FX):
        o.P(cyl_y(cx, WZ, 1.15, -W - 2, -W + 0.5, "hub"), "hub")
        o.P(cyl_y(cx, WZ, 1.15, W - 0.5, W + 2, "hub"), "hub")
    o.P(cyl_y(-11.1, 1.8, 0.85, -7, -5.6, "tHub"), "hub")
    o.P(box(-16.25, -5.95, -3.35, 3.35, 3.0, 3.65), "wood")               # bed boards
    for y0, y1 in ((-4.9, -3.4), (3.4, 4.9)):
        o.P(box(-17.9, -16.5, y0, y1, 4.7, 5.8), "tail")
    return o

def model_couch():
    o = Ops()
    o.A(box(-14.5, 14.5, -6.0, 5.5, 1.8, 6.2, "base"), "linen")
    o.A(box(-17.6, -14.0, -6.6, 5.5, 1.8, 11.0, "armL"), "linen")
    o.A(box(14.0, 17.6, -6.6, 5.5, 1.8, 11.0, "armR"), "linen")
    o.A(box(-14.5, 14.5, 2.4, 5.5, 6.0, 16.0, "back"), "linen")
    splits = ((-14.0, -5.3), (-4.3, 4.3), (5.3, 14.0))
    for x0, x1 in splits:
        o.A(box(x0, x1, -6.4, 2.6, 6.0, 9.0, "seat"), "linen")
        o.A(box(x0, x1, 0.4, 2.8, 8.9, 15.2, "pillow"), "linen")
    for x in (-16.6, 14.6):
        for y in (-5.8, 3.4):
            o.A(box(x, x + 2.0, y, y + 2.0, 0, 1.9, "leg"), "walnut")
    # seams: between cushions, along the seat front and the arm tops
    for xs in (-5.3, 4.3):
        o.P(box(xs - 0.55, xs + 1.55, -8, 3.2, 5.5, 16), "seam")
    o.P(box(-14.6, 14.6, -8, -5.5, 5.6, 6.5), "seam")
    for x0, x1 in ((-17.7, -13.9), (13.9, 17.7)):
        o.P(box(x0, x1, -7.5, 6, 10.2, 11.2), "seam")
    return o

def model_h():
    o = Ops()
    D = 3.2
    o.A(box(-10.5, -4.5, -D, D, 0, 25, "stemL"), "navy")
    o.A(box(4.5, 10.5, -D, D, 0, 25, "stemR"), "navy")
    o.A(box(-4.6, 4.6, -D, D, 10.4, 15.0, "bar"), "navy")
    for x0, x1 in ((-14.0, -1.8), (1.8, 14.0)):
        o.A(box(x0, x1, -D, D, 0, 3.4, "serifB"), "navy")
        o.A(box(x0, x1, -D, D, 21.6, 25, "serifT"), "navy")
    # red inline down each stem and across the bar, on the front face only
    F = (-D - 1, -D + 0.9)
    o.P(box(-8.05, -6.95, F[0], F[1], 2.2, 22.8), "red")
    o.P(box(6.95, 8.05, F[0], F[1], 2.2, 22.8), "red")
    o.P(box(-8.05, 8.05, F[0], F[1], 12.15, 13.25), "red")
    return o

MODELS = {"house": model_house, "truck": model_truck, "couch": model_couch, "h": model_h}

# ------------------------------------------------------------ voxeliser ----
def make_testers(ops):
    """Every primitive is convex, so a point is inside iff it is behind every face plane."""
    out = []
    for sign, ob, mat in ops:
        me = ob.data
        C = np.array([p.center[:] for p in me.polygons])
        Nn = np.array([p.normal[:] for p in me.polygons])
        V = np.array([v.co[:] for v in me.vertices])
        cen = V.mean(0)
        flip = ((C - cen) * Nn).sum(1) < 0
        Nn[flip] *= -1
        out.append((sign, (C, Nn), V.min(0), V.max(0), mat))
    return out

def inside_one(planes, pts):
    C, Nn = planes
    d = ((pts[:, None, :] - C[None, :, :]) * Nn[None, :, :]).sum(-1)
    return np.all(d < 0, axis=1)

def voxelise(testers, s):
    mn = np.min([t[2] for t in testers if t[0] == "+"], axis=0) * s
    mx = np.max([t[3] for t in testers if t[0] == "+"], axis=0) * s
    lo = np.floor(mn) - 1
    hi = np.ceil(mx) + 1
    xs, ys, zs = [np.arange(lo[k] + 0.5, hi[k], 1.0) for k in range(3)]
    G = np.stack(np.meshgrid(xs, ys, zs, indexing="ij"), -1)
    pm = G.reshape(-1, 3) / s + 1.3e-4
    occ = np.zeros(len(pm), bool)
    for sign, planes, a, b, _ in testers:
        if sign == "p":
            continue
        ins = inside_one(planes, pm)
        occ = (occ | ins) if sign == "+" else (occ & ~ins)
    return occ.reshape(G.shape[:3]), G

def visible_surface(occ):
    """Occupied voxels touching empty space towards the front (-Y), the top (+Z) or
    the sides (+-X), including edge/corner contacts so stair-steps never gap.
    Back (+Y) and underside (-Z) faces are never seen from the 3/4 camera."""
    pad = np.pad(occ, 1)
    X, Y, Z = occ.shape
    nb = np.zeros_like(occ)
    for dx in (-1, 0, 1):
        for dy in (-1, 0):
            for dz in (0, 1):
                if dx == dy == dz == 0:
                    continue
                nb |= ~pad[1 + dx:1 + dx + X, 1 + dy:1 + dy + Y, 1 + dz:1 + dz + Z]
    return occ & nb

def paint(testers, s, pts, seed):
    """Material per point: last add-op containing it, then paint volumes in order."""
    pm = pts / s + 1.3e-4
    mat = np.full(len(pts), -1)
    for sign, planes, a, b, m in testers:
        if sign in ("+", "p"):
            ins = inside_one(planes, pm)
            mat[ins] = MAT_NAMES.index(m)
    mat[mat < 0] = MAT_NAMES.index(testers[0][4])
    rng = np.random.default_rng(seed)
    cols = []
    for k, mi in enumerate(mat):
        hexv, _, _, jit = MATS[MAT_NAMES[mi]]
        r, g, b = (int(hexv[i:i + 2], 16) / 255 for i in (1, 3, 5))
        if jit:
            h, l, sat = colorsys.rgb_to_hls(r, g, b)
            l = min(1, max(0, l * (1 + rng.uniform(-jit, jit))))
            r, g, b = colorsys.hls_to_rgb(h, l, sat)
        cols.append((int(round(r * 255)) << 16) | (int(round(g * 255)) << 8) | int(round(b * 255)))
    return mat, np.array(cols)

def sample_form(name):
    ops = MODELS[name]()
    testers = make_testers(ops)
    lo, hi = 0.4, 3.0
    best = None
    for _ in range(22):
        s = (lo + hi) / 2
        occ, G = voxelise(testers, s)
        cnt = int(visible_surface(occ).sum())
        if cnt <= N:
            best = (s, occ, G, cnt); lo = s
        else:
            hi = s
    s, occ, G, cnt = best
    surf = visible_surface(occ)
    pts = G[surf]
    hidden = G[occ & ~surf]
    need = N - len(pts)
    if need > 0:
        # spare cubes hide inside the solid, nearest the centroid so they never peek out
        c = pts.mean(0)
        extra = hidden[np.argsort(np.linalg.norm(hidden - c, axis=1))[:need]] if len(hidden) else np.zeros((0, 3))
        while len(extra) < need:
            extra = np.vstack([extra, pts[: need - len(extra)]])
        pts = np.vstack([pts, extra[:need]])
    mat, cols = paint(testers, s, pts, seed=FORMS.index(name) + 11)
    print(f"[morph2] {name}: scale={s:.3f} visible={cnt} padded={need} total={len(pts)}")
    for _, ob, _ in ops:
        bpy.data.objects.remove(ob, do_unlink=True)
    return pts, mat, cols

# ------------------------------------------------------------- matching ----
def greedy_match(src, dst):
    """Return perm so dst[perm[i]] is paired with src[i]; greedy global nearest."""
    a = src - src.mean(0); b = dst - dst.mean(0)
    a = a / (np.abs(a).max() + 1e-9); b = b / (np.abs(b).max() + 1e-9)
    D = ((a[:, None, :] - b[None, :, :]) ** 2).sum(-1).astype(np.float32)
    order = np.argsort(D, axis=None)
    n = len(src)
    used_a = np.zeros(n, bool); used_b = np.zeros(n, bool)
    perm = np.full(n, -1)
    left = n
    for k in order:
        i, j = divmod(int(k), n)
        if used_a[i] or used_b[j]:
            continue
        perm[i] = j; used_a[i] = used_b[j] = True
        left -= 1
        if left == 0:
            break
    return perm

def to_three(p):
    """Blender (x, y-depth, z-up) -> three.js (x, y-up, z-front); centre X/Z, ground at y=0."""
    q = np.stack([p[:, 0], p[:, 2], -p[:, 1]], 1)
    q[:, 0] -= (q[:, 0].min() + q[:, 0].max()) / 2
    q[:, 2] -= (q[:, 2].min() + q[:, 2].max()) / 2
    q[:, 1] -= q[:, 1].min() - 0.5
    return q

def build_shapes():
    raw = {}
    for f in FORMS:
        pts, mat, cols = sample_form(f)
        raw[f] = (to_three(pts), mat, cols)
    h, hm, hc = raw["house"]
    order = np.lexsort((h[:, 2], h[:, 0], h[:, 1]))
    ordered = {"house": (h[order], hm[order], hc[order])}
    prev = ordered["house"][0]
    for f in FORMS[1:]:
        p, m, c = raw[f]
        perm = greedy_match(prev, p)
        ordered[f] = (p[perm], m[perm], c[perm])
        prev = ordered[f][0]
    data = {"n": N, "cube": CUBE, "fill": CUBE_FILL, "bevel": BEVEL,
            "mats": [[MATS[m][1], MATS[m][2]] for m in MAT_NAMES],
            "forms": {f: [round(float(v), 2) for v in ordered[f][0].reshape(-1)] for f in FORMS},
            "colors": {f: [int(v) for v in ordered[f][2]] for f in FORMS},
            "pbr": {f: [int(v) for v in ordered[f][1]] for f in FORMS}}
    with open(os.path.join(OUT, "shapes.json"), "w") as fh:
        json.dump(data, fh, separators=(",", ":"))
    print("[morph2] wrote shapes.json")
    return data

# -------------------------------------------------------------- posters ----
def srgb_lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def clear_scene():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)

def cube_material():
    """One material; colour from the object's colour, roughness/metal from object properties."""
    m = bpy.data.materials.new("cube")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    info = nt.nodes.new("ShaderNodeObjectInfo")
    nt.links.new(info.outputs["Color"], bsdf.inputs["Base Color"])
    for prop, sock in (("rough", "Roughness"), ("metal", "Metallic")):
        at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_type = "OBJECT"; at.attribute_name = prop
        nt.links.new(at.outputs["Fac"], bsdf.inputs[sock])
    return m

def rounded_cube_mesh(edge):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=edge)
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=edge * BEVEL, segments=2, affect='EDGES', profile=0.5)
    me = bpy.data.meshes.new("rcube")
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    return me

def blur2d(img, sigma):
    r = int(sigma * 3) + 1
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2); k /= k.sum()
    img = np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), 0, img)
    return np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), 1, img)

def contact_shadow_image(P, name, px=12, margin=14):
    """Soft contact shadow from the voxel footprint: cubes near the ground count most."""
    mn = P.min(0); mx = P.max(0)
    x0, x1 = mn[0] - margin, mx[0] + margin
    z0, z1 = mn[2] - margin, mx[2] + margin
    W = int((x1 - x0) * px); H = int((z1 - z0) * px)
    acc = np.zeros((H, W), np.float32)
    for x, y, z in P:
        w = math.exp(-(y - 0.5) / 2.5)
        cx = int((x - x0) * px); cz = int((z - z0) * px)
        h = int(px * 0.5)
        acc[max(cz - h, 0):cz + h, max(cx - h, 0):cx + h] += w
    acc = np.clip(acc, 0, 1)
    a = np.clip(0.55 * blur2d(acc, px * 0.6) + 0.45 * blur2d(acc, px * 3.5) * 1.4, 0, 1) ** 0.9
    img = bpy.data.images.new(f"shadow_{name}", W, H, alpha=True)
    rgba = np.zeros((H, W, 4), np.float32); rgba[..., 3] = a
    img.pixels.foreach_set(rgba[::-1].reshape(-1))
    img.pack()
    return img, (x0, x1, z0, z1)

def shadow_plane(img, ext, strength=0.55):
    x0, x1, z0, z1 = ext
    bpy.ops.mesh.primitive_plane_add(size=1, location=((x0 + x1) / 2, -(z0 + z1) / 2, 0.001))
    g = bpy.context.active_object
    g.scale = (x1 - x0, z1 - z0, 1)
    m = bpy.data.materials.new("shadow"); m.use_nodes = True
    if hasattr(m, "surface_render_method"):
        m.surface_render_method = "BLENDED"
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img; tex.extension = "CLIP"
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = strength
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = (0.01, 0.01, 0.012, 1)
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(tex.outputs["Alpha"], mul.inputs[0])
    nt.links.new(mul.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    g.data.materials.append(m)
    g.visible_shadow = False
    return g

def render_posters(data):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = 1600, 1200
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "WEBP"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.image_settings.quality = 88
    try:
        sc.view_settings.view_transform = "AgX"
        sc.view_settings.look = "AgX - Base Contrast"
    except Exception:
        pass
    ee = sc.eevee
    ee.taa_render_samples = SAMPLES
    for k, v in (("use_raytracing", True), ("use_shadows", True), ("shadow_ray_count", 3),
                 ("shadow_step_count", 12), ("fast_gi_method", "GLOBAL_ILLUMINATION")):
        if hasattr(ee, k):
            try:
                setattr(ee, k, v)
            except Exception:
                pass
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.9, 0.91, 0.93, 1); bg.inputs[1].default_value = 0.45

    mat = cube_material()
    mesh = rounded_cube_mesh(CUBE * CUBE_FILL)
    mesh.materials.append(mat)
    mats = data["mats"]

    for f in FORMS:
        if ONLY and f not in ONLY:
            continue
        clear_scene()
        P = np.array(data["forms"][f]).reshape(-1, 3)
        C = data["colors"][f]; M = data["pbr"][f]
        for i, (x, y, z) in enumerate(P):            # three (x, y-up, z-front) -> blender (x, -z, y)
            ob = bpy.data.objects.new(f"c{i}", mesh)
            ob.location = (x, -z, y)
            c = C[i]
            ob.color = (srgb_lin(((c >> 16) & 255) / 255), srgb_lin(((c >> 8) & 255) / 255), srgb_lin((c & 255) / 255), 1)
            ob["rough"], ob["metal"] = mats[M[i]]
            sc.collection.objects.link(ob)
        mn = P.min(0) - 0.5; mx = P.max(0) + 0.5
        size = mx - mn
        ctr = Vector(((mn[0] + mx[0]) / 2, -(mn[2] + mx[2]) / 2, (mn[1] + mx[1]) / 2))
        img, ext = contact_shadow_image(P, f)
        shadow_plane(img, ext)
        cam_d = bpy.data.cameras.new("cam"); cam_d.lens = 85
        cam = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(cam); sc.camera = cam
        yaw, pitch = math.radians(YAW.get(f, 26)), math.radians(13 if f == "truck" else 17)
        dirv = Vector((math.sin(yaw) * math.cos(pitch), -math.cos(yaw) * math.cos(pitch), math.sin(pitch)))
        cam.location = ctr + dirv * 200
        cam.rotation_euler = (-dirv).to_track_quat('-Z', 'Y').to_euler()
        bpy.context.view_layer.update()
        corners = []
        for cx in (mn[0], mx[0]):
            for cy in (mn[1], mx[1]):
                for cz in (mn[2], mx[2]):
                    corners += [cx, -cz, cy]
        loc, _ = cam.camera_fit_coords(bpy.context.evaluated_depsgraph_get(), corners)
        loc = Vector(loc)
        cam.location = loc + (loc - ctr).normalized() * (loc - ctr).length * 0.30
        R = max(size) * 0.5
        def area(name, off, energy, size_, color):
            L = bpy.data.lights.new(name, "AREA"); L.energy = energy; L.size = size_; L.color = color
            o = bpy.data.objects.new(name, L); sc.collection.objects.link(o)
            o.location = ctr + Vector(off)
            o.rotation_euler = (ctr - o.location).to_track_quat('-Z', 'Y').to_euler()
            return o
        k = R * R          # inverse-square: keep irradiance constant whatever the object size
        area("top", (-0.4 * R, -0.6 * R, 3.6 * R), 115 * k, 3.0 * R, (1.0, 0.98, 0.95))
        area("key", (-2.6 * R, -2.8 * R, 1.6 * R), 85 * k, 2.0 * R, (1.0, 0.97, 0.93))
        area("rim", (2.4 * R, 3.2 * R, 1.8 * R), 260 * k, 1.0 * R, (1.0, 0.82, 0.64))
        area("fill", (3.4 * R, -1.2 * R, 0.6 * R), 40 * k, 2.4 * R, (0.84, 0.89, 1.0))
        sc.render.filepath = os.path.join(OUT, f"poster-{f}.webp")
        bpy.ops.render.render(write_still=True)
        print(f"[morph2] rendered poster-{f}.webp")

# ----------------------------------------------------------------- main ----
if __name__ == "__main__":
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if STAGE in ("all", "shapes"):
        data = build_shapes()
    else:
        data = json.load(open(os.path.join(OUT, "shapes.json")))
    if STAGE in ("all", "posters"):
        render_posters(data)
