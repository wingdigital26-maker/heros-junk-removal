"""Hero's Junk Removal - THE HOUSE, v2: many small fragments, ONE instanced geometry.

v1 (house_v1.py) exported 68 separate bevelled meshes, each its own object and material. That is 68 draw calls
animated every frame, and it still read as a dozen blocks. v2 keeps the SAME house (same macro boxes, same
camera, same studio, same palette) but voxelises every part of it into near-cubic cells at one pitch, so the
house is built from ~1,000 pieces, and ships ONE unit cube plus a data table of per-instance transforms per
formation. The web draws it as one THREE.InstancedMesh. Contract: brand/PIECE_CONTRACT.md.

Rules kept from v1: six formations (house, couch, fridge, map, message, truck), the same N in each, nothing
added or removed, only moved; one red accent; house state still a clean silhouette at 32px.

  blender --background --python brand/house.py -- <outdir> [form=house|...|all] [glb] [json] [hero] [fast]
                                                          [pitch=0.13] [norender]
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
PITCH = float(KV.get("pitch", "0.18"))       # nominal cell size, world units. 0.24 ~ 500, 0.20 ~ 850, 0.18 ~ 1100, 0.17 ~ 1300
SPREAD = float(KV.get("spread", "1.06"))     # how far the leaving clusters open up (1 = tight block)
SIZE_JIT = float(KV.get("sjit", "0.03"))     # per-cell size variation (0.03 = cells are 97..100 percent of the cell)

# ---------------------------------------------------------------- palette (linear), unchanged from v1
COLORS = {
    0: (0.062, 0.074, 0.094),   # slate walls
    1: (0.030, 0.037, 0.050),   # roof / plinth, darker slate
    2: (0.014, 0.020, 0.036),   # ink, the blocks
    3: (0.36, 0.024, 0.030),    # the accent red
}
SURF = {0: (0.78, 0.34), 1: (0.80, 0.36), 2: (0.85, 0.28), 3: (0.40, 0.30)}
ROLES = ["base", "wall", "window", "reveal", "lintel", "roof", "gable", "inside", "lift"]
JIT_FORM = 0.25
FLOOR = 0.58
BAND = 2.4
FILL = 260

W, D, H = 2.30, 1.80, 1.45
T = 0.14
TD = 0.24
DOOR_W, DOOR_H = 0.70, 1.02
BASE_H = 0.11
OVER = 0.32
ROOF_T = 0.16
ROOF_H = 0.84
GAP = 0.004                                  # seam between cells: near touching, the bevels draw the seam
FORM_OFFSET = (0.75, -0.35, 0.0)
ORDER = ["house", "couch", "fridge", "map", "message", "truck"]

rng = np.random.default_rng(7)


# ---------------------------------------------------------------- voxelise one box into cells
def cells_of(center, size, col, role, rot=(0, 0, 0), group=0, pitch=None, spread=1.0, tilt=0.45, minn=(1, 1, 1), brick=None):
    """Split a box into near-cubic cells at PITCH. rot is applied about the box centre (roof slopes). spread > 1
    opens the cluster up around its centre. brick=(run_axis, row_axis): every other row along row_axis is offset
    half a cell along run_axis, with half cells at both ends, so seams never line up through the part."""
    pitch = pitch or PITCH
    n = [max(minn[i], int(round(size[i] / pitch))) for i in range(3)]
    R = Euler(rot, "XYZ").to_matrix()
    base_q = R.to_quaternion()
    out = []
    ra, rw = brick if brick else (None, None)
    for ix in range(n[0]):
        for iy in range(n[1]):
            for iz in range(n[2]):
                idx = [ix, iy, iz]
                if brick and idx[rw] % 2 == 1 and idx[ra] == 0:
                    # an offset row: n+1 cells, the first and last half width. Emit them all from the idx[ra]==0 slot.
                    slots = []
                    cw = size[ra] / n[ra]
                    for k in range(n[ra] + 1):
                        if k == 0:
                            slots.append((-size[ra] / 2 + cw / 4, cw / 2))
                        elif k == n[ra]:
                            slots.append((size[ra] / 2 - cw / 4, cw / 2))
                        else:
                            slots.append((-size[ra] / 2 + k * cw, cw))
                elif brick and idx[rw] % 2 == 1:
                    continue
                else:
                    slots = [((idx[ra] + 0.5) / n[ra] * size[ra] - size[ra] / 2, size[ra] / n[ra])] if brick else [None]
                for slot in slots:
                    local = [(idx[i] + 0.5) / n[i] * size[i] - size[i] / 2 for i in range(3)]
                    cell = [size[i] / n[i] - GAP for i in range(3)]
                    if slot:
                        local[ra] = slot[0]
                        cell[ra] = slot[1] - GAP
                    p = Vector(center) + R @ (Vector(local) * spread)
                    k = 1.0 - rng.uniform(0, SIZE_JIT)
                    s = [c * k for c in cell]
                    t = rng.uniform(-1, 1, 3) * math.radians(tilt if spread == 1.0 else 5.0)
                    q = base_q @ Euler(tuple(t), "XYZ").to_quaternion()
                    out.append({"p": [p.x, p.y, p.z], "s": s, "r": [q.x, q.y, q.z, q.w], "c": col,
                                "role": ROLES.index(role), "g": group,
                                "j": [float(rng.uniform(-0.035, 0.035)), float(rng.uniform(-0.06, 0.06))]})
    return out


def house_cells():
    z0 = BASE_H
    F = []
    # plinth, runs out past the door as the threshold
    F += cells_of((0.09, 0, BASE_H / 2), (W + 0.38, D + 0.20, BASE_H), 1, "base")
    # front wall with a window opening: three wall bands around a window cell block
    fy = -D / 2 + T / 2
    wx0, wx1 = -0.51, -0.005                       # the window's x span (v1: panel 1 of 4 at row 1 of 3)
    wz0, wz1 = z0 + H / 3, z0 + 2 * H / 3
    F += cells_of(((-W / 2 + T + wx0) / 2, fy, z0 + H / 2), (wx0 - (-W / 2 + T), T, H), 0, "wall", brick=(0, 2))            # left of window
    F += cells_of(((wx1 + W / 2 - T) / 2, fy, z0 + H / 2), (W / 2 - T - wx1, T, H), 0, "wall", brick=(0, 2))               # right of window
    F += cells_of(((wx0 + wx1) / 2, fy, (z0 + wz0) / 2), (wx1 - wx0, T, wz0 - z0), 0, "wall", brick=(0, 2))               # under window
    F += cells_of(((wx0 + wx1) / 2, fy, (wz1 + z0 + H) / 2), (wx1 - wx0, T, z0 + H - wz1), 0, "wall", brick=(0, 2))        # over window
    F += cells_of(((wx0 + wx1) / 2, fy + 0.035, (wz0 + wz1) / 2), (wx1 - wx0, T - 0.07, wz1 - wz0), 2, "window")
    # back wall, left wall
    F += cells_of((0, D / 2 - T / 2, z0 + H / 2), (W - 2 * T, T, H), 0, "wall", brick=(0, 2))
    F += cells_of((-W / 2 + T / 2, 0, z0 + H / 2), (T, D, H), 0, "wall", brick=(1, 2))
    # door wall (+X): two piers, a lintel, a dark reveal set back in the opening
    pier = (D - DOOR_W) / 2
    xr = W / 2 - TD / 2
    for yy in (-(DOOR_W / 2 + pier / 2), DOOR_W / 2 + pier / 2):
        F += cells_of((xr, yy, z0 + DOOR_H / 2), (TD, pier, DOOR_H), 0, "wall", brick=(1, 2))
    F += cells_of((xr, 0, z0 + DOOR_H + (H - DOOR_H) / 2), (TD, D, H - DOOR_H), 0, "lintel", brick=(1, 2))
    F += cells_of((W / 2 - TD - 0.03, 0, z0 + DOOR_H / 2), (0.06, DOOR_W - 0.05, DOOR_H - 0.02), 2, "reveal", minn=(1, 3, 4))
    # roof: two thick slabs at the pitch, meeting at the ridge
    ze = z0 + H - 0.02
    half = D / 2 + OVER
    pitch = math.atan2(ROOF_H, half)
    slope_len = math.hypot(half, ROOF_H) + 0.10
    for s in (-1, 1):
        n = Vector((0, s * math.sin(pitch), math.cos(pitch)))
        along = Vector((0, s * math.cos(pitch), -math.sin(pitch)))
        ridge = Vector((0, 0, ze + ROOF_H))
        c = ridge + along * (slope_len / 2 - 0.05) + n * (ROOF_T / 2)
        F += cells_of(tuple(c), (W + 2 * OVER, slope_len, ROOF_T), 1, "roof", rot=(-s * pitch, 0, 0), brick=(0, 1))
    # stepped gables under the slabs, at both ends
    rows = ((z0 + H, z0 + H + 0.28), (z0 + H + 0.28, z0 + H + 0.54), (z0 + H + 0.54, z0 + H + 0.76))
    for sx_ in (-1, 1):
        for (za, zb) in rows:
            wid = min(D, 2 * half * (1 - (zb - ze) / ROOF_H) - 0.06)
            F += cells_of((sx_ * (W / 2 - T / 2), 0, (za + zb) / 2), (T, wid, zb - za), 0, "gable", brick=(1, 2))
    # one block still inside, seen through the door
    F += cells_of((0.72, -0.02, z0 + 0.26), (0.46, 0.46, 0.52), 2, "inside", rot=(0, 0, 0.35), group=5)
    # THE GESTURE: blocks leaving through the door to the right and up. Each is now a cluster that has opened up
    arc = [
        ((2.42, -0.58, 0.80), (0.52, 0.46, 0.40), 2),
        ((2.92, -0.78, 1.62), (0.40, 0.38, 0.46), 3),
        ((3.28, -0.92, 2.44), (0.34, 0.36, 0.26), 2),
        ((3.52, -1.00, 3.16), (0.24, 0.22, 0.26), 2),
    ]
    for i, (p, s, c) in enumerate(arc):
        F += cells_of(p, s, c, "lift", rot=(0.30 - i * 0.14, 0.20 - i * 0.16, -0.40 + i * 0.22), group=i + 1,
                      pitch=PITCH * 0.6, spread=SPREAD + 0.03 * i, minn=(2, 2, 2))
    return F


# ---------------------------------------------------------------- other formations (boxes on z=0), v1 shapes
def shape_couch():
    return [
        (-0.80, 0.00, 0.66, 0.92, 1.12, 0.34, 0, 0, None),
        (0.00, 0.00, 0.66, 0.92, 1.12, 0.34, 0, 0, None),
        (0.80, 0.00, 0.66, 0.92, 1.12, 0.34, 0, 0, None),
        (0.00, 0.50, 1.22, 2.80, 0.26, 0.86, 1, 0, None),
        (-1.55, 0.00, 0.84, 0.30, 1.12, 0.74, 1, 0, None),
        (1.55, 0.00, 0.84, 0.30, 1.12, 0.74, 1, 0, None),
        (0.00, 0.00, 0.30, 2.75, 1.05, 0.36, 2, 0, None),
        (0.85, 0.22, 1.06, 0.46, 0.14, 0.46, 3, 12, None),      # ONE red throw pillow
    ]


def shape_fridge():
    return [
        (0.00, 0.00, 1.32, 1.36, 1.10, 2.50, 0, 0, None),
        (0.00, -0.62, 1.86, 1.28, 0.12, 1.32, 1, 0, None),
        (0.00, -0.62, 0.66, 1.28, 0.12, 0.96, 1, 0, None),
        (0.00, 0.00, 0.06, 1.20, 1.00, 0.12, 2, 0, None),
        (-0.48, -0.72, 1.86, 0.08, 0.08, 0.90, 3, 0, None),     # the red handle
    ]


def shape_map():
    tiles = []
    for iy in range(3):
        for ix in range(4):
            tiles.append((-1.35 + ix * 0.90, -0.90 + iy * 0.90, 0.07, 0.86, 0.86, 0.14, 0, 0, None))
    tiles.append((-1.10, -0.90, 0.20, 1.40, 0.20, 0.10, 2, 0, None))
    tiles.append((-0.40, -0.25, 0.20, 0.20, 1.50, 0.10, 2, 0, None))
    tiles.append((0.40, 0.40, 0.20, 1.80, 0.20, 0.10, 2, 0, None))
    tiles.append((1.35, 0.40, 0.20 + 0.52, 0.12, 0.12, 0.95, 2, 0, None))
    tiles.append((1.35, 0.40, 0.20 + 1.22, 0.50, 0.50, 0.50, 3, 45, None))
    return tiles


def shape_message():
    return [
        (0.00, 0.00, 1.32, 3.10, 0.34, 1.90, 0, 0, None),
        (-1.05, 0.00, 0.36, 0.50, 0.34, 0.50, 0, 45, None),
        (-0.65, -0.26, 1.32, 0.42, 0.14, 0.42, 3, 0, None),
        (0.00, -0.26, 1.32, 0.42, 0.14, 0.42, 3, 0, None),
        (0.65, -0.26, 1.32, 0.42, 0.14, 0.42, 3, 0, None),
    ]


def shape_truck():
    return [
        (0.00, 0.00, 0.58, 3.60, 1.20, 0.32, 2, 0, None),
        (-1.25, 0.00, 1.18, 1.10, 1.10, 0.86, 0, 0, None),
        (0.80, 0.00, 0.98, 2.20, 1.16, 0.28, 1, 0, None),
        (0.80, 0.00, 1.18, 2.15, 1.20, 0.12, 3, 0, None),
        (0.80, 0.00, 1.62, 1.90, 1.00, 0.76, 2, 0, None),
        (-1.25, 0.00, 0.20, 0.80, 1.30, 0.40, 2, 0, None),
        (1.10, 0.00, 0.20, 0.80, 1.30, 0.40, 2, 0, None),
    ]


SHAPES = {"couch": shape_couch, "fridge": shape_fridge, "map": shape_map, "message": shape_message, "truck": shape_truck}


def shell(boxes, pitch):
    """Only the surface cells of every box (the interior was never visible). Returns (surface, interior) lists."""
    surf, inner = [], []
    for b in boxes:
        cx, cy, cz, sx, sy, sz, col, yaw, _ = b
        g = [max(1, int(round(d / pitch))) for d in (sx, sy, sz)]
        rot = Matrix.Rotation(math.radians(yaw), 3, "Z")
        q0 = rot.to_quaternion()
        gx, gy, gz = g
        for ix in range(gx):
            for iy in range(gy):
                for iz in range(gz):
                    local = Vector(((ix + 0.5) / gx * sx - sx / 2, (iy + 0.5) / gy * sy - sy / 2, (iz + 0.5) / gz * sz - sz / 2))
                    p = Vector((cx, cy, cz)) + rot @ local
                    k = 1.0 - rng.uniform(0, SIZE_JIT)
                    t = rng.uniform(-1, 1, 3) * math.radians(0.45)
                    q = q0 @ Euler(tuple(t), "XYZ").to_quaternion()
                    cell = {"p": [p.x, p.y, p.z], "s": [(sx / gx - GAP) * k, (sy / gy - GAP) * k, (sz / gz - GAP) * k],
                            "r": [q.x, q.y, q.z, q.w], "c": col}
                    on_surface = ix in (0, gx - 1) or iy in (0, gy - 1) or iz in (0, gz - 1)
                    (surf if on_surface else inner).append(cell)
    return surf, inner


def layout(boxes, n):
    """Exactly n cells: the formation's surface at the coarsest pitch (from 0.5 to 1.6 times the house pitch)
    whose shell count fits under n, then the rest parked where they cannot be seen: first at interior grid
    positions, then (if the shape has no interior left) as near-zero-size duplicates inside random surface
    cells. Every visible face is complete; the parked cells are still real instances that fly with the rest."""
    best = None
    for k in range(60):
        pitch = PITCH * 0.5 * (1.6 / 0.5) ** (k / 59)      # finest first: the first pitch that fits is the densest
        surf, inner = shell(boxes, pitch)
        if len(surf) <= n:
            best = (pitch, surf, inner)
            break
    pitch, surf, inner = best
    cells = list(surf)
    rng.shuffle(inner)
    cells += inner[: n - len(cells)]
    parked = 0
    while len(cells) < n:
        c = dict(surf[int(rng.integers(len(surf)))])
        c["s"] = [0.002, 0.002, 0.002]
        cells.append(c)
        parked += 1
    print("  layout pitch %.3f surface %d interior %d parked %d" % (pitch, len(surf), min(len(inner), n - len(surf)), parked))
    assert len(cells) == n
    return cells


def sort_key(c):
    p = c["p"]
    return p[2] * 1.0 + p[0] * 0.55 + p[1] * 0.25


def assign(house, cells):
    """Rank matching: both sets sorted along the same diagonal, house fragment i takes the cell of equal rank. With
    identical geometry any mapping works; this one makes the morph sweep across the object instead of scrambling."""
    hi = sorted(range(len(house)), key=lambda i: sort_key(house[i]))
    ci = sorted(range(len(cells)), key=lambda i: sort_key(cells[i]))
    out = [None] * len(house)
    for a, b in zip(hi, ci):
        out[a] = cells[b]
    return out


def formations(house):
    n = len(house)
    forms = {"house": house}
    ox, oy, oz = FORM_OFFSET
    for k in ORDER[1:]:
        cells = layout(SHAPES[k](), n)
        for c in cells:
            c["p"] = [c["p"][0] + ox, c["p"][1] + oy, c["p"][2] + oz]
        forms[k] = assign(house, cells)
    return forms


def to_json(house, forms):
    Q = {"p": 1000, "s": 1000, "r": 32767, "j": 1000}
    data = {"v": 2, "n": len(house), "pitch": PITCH, "forms": ORDER, "q": Q,
            "colors": [list(COLORS[i]) for i in range(4)], "surf": [list(SURF[i]) for i in range(4)],
            "roles": ROLES, "role": [c["role"] for c in house], "group": [c["g"] for c in house],
            "jit": [int(round(v * Q["j"])) for c in house for v in c["j"]], "f": {}}
    for k in ORDER:
        F = forms[k]
        data["f"][k] = {
            "p": [int(round(v * Q["p"])) for c in F for v in c["p"]],
            "s": [max(1, int(round(v * Q["s"]))) for c in F for v in c["s"]],
            "r": [int(round(v * Q["r"])) for c in F for v in c["r"]],
            "c": [c["c"] for c in F],
        }
    return data


# ---------------------------------------------------------------- blender
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def unit_cube():
    """The one geometry: a 1 x 1 x 1 cube with a bevel of 0.08 of the side, 2 segments, smooth."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    o = bpy.context.object
    o.name = "frag"
    m = o.modifiers.new("bev", "BEVEL")
    m.width = 0.08
    m.segments = 2
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(38)
    m.harden_normals = True
    for p in o.data.polygons:
        p.use_smooth = True
    bpy.ops.object.modifier_apply(modifier="bev")
    return o


def make_material(name, rgb, metallic, rough):
    """Base colour and roughness take the OBJECT colour: rgb multiplies lightness, alpha carries the roughness
    offset (0.5 = none). One material per colour index, shared by every instance of that colour."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    if metallic > 0.3:
        b.inputs["Coat Weight"].default_value = 0.35 if metallic < 0.6 else 0.18
        b.inputs["Coat Roughness"].default_value = 0.12
    info = nt.nodes.new("ShaderNodeObjectInfo")
    mul = nt.nodes.new("ShaderNodeMix")
    mul.data_type = "RGBA"
    mul.blend_type = "MULTIPLY"
    mul.inputs[0].default_value = 1.0
    mul.inputs[6].default_value = (*rgb, 1.0)
    nt.links.new(info.outputs["Color"], mul.inputs[7])
    nt.links.new(mul.outputs[2], b.inputs["Base Color"])
    # roughness = rough + (alpha - 0.5) * 0.24  (alpha 0..1 spans -0.12..+0.12)
    sub = nt.nodes.new("ShaderNodeMath"); sub.operation = "SUBTRACT"; sub.inputs[1].default_value = 0.5
    sc = nt.nodes.new("ShaderNodeMath"); sc.operation = "MULTIPLY"; sc.inputs[1].default_value = 0.24
    add = nt.nodes.new("ShaderNodeMath"); add.operation = "ADD"; add.inputs[1].default_value = rough
    mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MAXIMUM"; mx.inputs[1].default_value = 0.06
    nt.links.new(info.outputs["Alpha"], sub.inputs[0])
    nt.links.new(sub.outputs[0], sc.inputs[0])
    nt.links.new(sc.outputs[0], add.inputs[0])
    nt.links.new(add.outputs[0], mx.inputs[0])
    nt.links.new(mx.outputs[0], b.inputs["Roughness"])
    return m


def build(house, F, form):
    proto = unit_cube()
    mesh = proto.data
    mesh.materials.append(None)
    mats = {i: make_material(f"c{i}", COLORS[i], *SURF[i]) for i in range(4)}
    jit = 1.0 if form == "house" else JIT_FORM
    coll = bpy.context.collection
    for i, c in enumerate(F):
        o = bpy.data.objects.new(f"f{i}", mesh)
        coll.objects.link(o)
        o.location = c["p"]
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion = (c["r"][3], c["r"][0], c["r"][1], c["r"][2])
        o.scale = c["s"]
        o.material_slots[0].link = "OBJECT"
        o.material_slots[0].material = mats[c["c"]]
        L = 1 + house[i]["j"][0] * 2.2 * jit
        o.color = (L, L, L, 0.5 + house[i]["j"][1] * jit / 0.12 * 0.5)
    proto.hide_render = True
    proto.hide_viewport = True
    return proto


SOFTBOXES = [
    ((4.6, -5.6, 6.2), 30, 20, 3.5, (1.00, 1.00, 1.00)),
    ((7.0, -3.0, 1.2), 5, 42, 9.0, (0.98, 0.99, 1.00)),
    ((-5.2, 4.8, 3.8), 5, 34, 6.5, (0.92, 0.95, 1.00)),
    ((0.0, 0.0, 1.0), 48, 7, 3.2, (1.00, 1.00, 1.00)),
    ((3.5, -6.5, -0.7), 46, 6, BAND, (0.96, 0.97, 1.00)),
    ((-5.0, -5.0, 1.6), 24, 16, 1.8, (0.95, 0.96, 1.00)),
]


def write_studio(path, wpx=768, hpx=384):
    v, u = np.mgrid[0:hpx, 0:wpx]
    u = (u + 0.5) / wpx
    v = (v + 0.5) / hpx
    el = (v - 0.5) * math.pi
    az = (u - 0.5) * 2 * math.pi
    dx, dy, dz = -np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)
    t = np.clip(dz, -1, 1)
    sky = np.where(t < 0, 0.42 + (FLOOR - 0.42) * np.clip(-t, 0, 1) ** 0.7, 0.42 + (0.20 - 0.42) * np.clip(t, 0, 1) ** 0.8)
    img = np.stack([sky * 0.96, sky * 0.975, sky * 1.0], -1)
    for (cd, hw, hh, inten, tint) in SOFTBOXES:
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
        m = m * (1 - 0.35 * np.clip((a2 / max(hh, 1e-3)) * 0.5 + 0.5, 0, 1))
        for k in range(3):
            img[..., k] += m * inten * tint[k]
    im = bpy.data.images.new("studio", wpx, hpx, alpha=False, float_buffer=True)
    px = np.concatenate([img[::-1].reshape(-1, 3), np.ones((wpx * hpx, 1))], 1).astype(np.float32)
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
        bg = bpy.data.materials.new("bg"); bg.use_nodes = True
        bg.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.905, 0.915, 0.935, 1)
        bg.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.5
        gp.data.materials.append(bg)

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
    for l in (lamp("key", (4.6, -5.6, 6.2), 1100, 6), lamp("rim", (-5.2, 4.8, 3.8), 2000, 4), lamp("fill", (-4.8, -5.4, 2.2), FILL, 10)):
        l.constraints[0].target = tgt
    w = bpy.context.scene.world or bpy.data.worlds.new("W")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = write_studio(os.path.join(OUT, "studio.exr"))
    bgn = nt.nodes["Background"]
    nt.links.new(env.outputs["Color"], bgn.inputs["Color"])
    bgn.inputs[1].default_value = 0.85
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
HOUSE = house_cells()
FORMS = formations(HOUSE)
print("FRAGS", len(HOUSE), "pitch", PITCH, "roles", {r: sum(1 for c in HOUSE if c["role"] == ROLES.index(r)) for r in ROLES})
if WANT_JSON:
    data = to_json(HOUSE, FORMS)
    with open(os.path.join(OUT, "shapes.json"), "w") as fh:
        json.dump(data, fh, separators=(",", ":"))
    print("wrote shapes.json n=%d bytes=%d" % (data["n"], os.path.getsize(os.path.join(OUT, "shapes.json"))))

forms = ORDER if FORM == "all" else [FORM]
for form in forms:
    reset()
    proto = build(HOUSE, FORMS[form], form)
    stage(hero=WANT_HERO)
    bpy.context.scene.render.filepath = os.path.join(OUT, f"{form}-hero.png" if WANT_HERO else f"{form}.png")
    if not NORENDER:
        bpy.ops.render.render(write_still=True)
    print("RENDERED", form, flush=True)
    if WANT_GLB and form == forms[0]:
        proto.hide_render = False
        proto.hide_viewport = False
        proto.data.materials.clear()
        bpy.ops.object.select_all(action="DESELECT")
        proto.select_set(True)
        bpy.context.view_layer.objects.active = proto
        bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "house.glb"), export_format="GLB", use_selection=True,
                                  export_apply=True, export_materials="NONE", export_draco_mesh_compression_enable=False)
        print("GLB bytes", os.path.getsize(os.path.join(OUT, "house.glb")), "tris", sum(len(p.vertices) - 2 for p in proto.data.polygons))
print("DONE house")
