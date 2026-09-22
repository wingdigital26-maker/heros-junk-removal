"""
build_truck.py -- Hero's Junk Removal "truck mark": a stylised dump/hauling
truck built as ONE bmesh from big simple blocky masses (hood + cab + open,
tipped dump bed + 4 wheels), navy metal body with a single terracotta accent.
Everything is authored directly into one bmesh with explicit box-add helpers
(add box verts/faces by hand, not bpy.ops primitives + join) so there is no
per-object origin/transform-apply fragility -- every mass sits in one
consistent world-space coordinate system from the start.

Run:
  blender.exe -b --factory-startup -P build_truck.py -- --out out/truck_v1.glb \
    --variant v1 --tip 10 --cab boxy --accent rail
"""
import bpy
import bmesh
import sys
import math
import os
import json
from mathutils import Vector, Matrix

def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    d = {"out": "out/truck.glb", "tip": 10.0, "cab": "boxy",
         "bed_h": 1.0, "cab_len": 1.0, "accent": "rail", "variant": "v1"}
    i = 0
    while i < len(argv):
        a = argv[i]
        key = a.lstrip("-").replace("-", "_")
        if key in d and i + 1 < len(argv):
            val = argv[i + 1]
            if key in ("tip", "bed_h", "cab_len"):
                val = float(val)
            d[key] = val
            i += 2
        else:
            i += 1
    return d

ARGS = parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(HERE, ARGS["out"]) if not os.path.isabs(ARGS["out"]) else ARGS["out"]
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)


def hex_rgb(h):
    h = h.lstrip("#")
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (lin(r), lin(g), lin(b), 1.0)


def make_material(name, color, metallic=0.92, roughness=0.32):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


MAT_NAVY = make_material("NavyMetal", hex_rgb("1C2B3A"))
MAT_CLAY = make_material("ClayAccent", hex_rgb("D97A3D"), metallic=0.85, roughness=0.28)
MAT_CHAR = make_material("CharcoalTrim", hex_rgb("33383D"), metallic=0.9, roughness=0.4)
MATS = [MAT_NAVY, MAT_CLAY, MAT_CHAR]
MAT_IDX = {"navy": 0, "clay": 1, "char": 2}

bm = bmesh.new()
face_mat = []  # material index per face, appended in the same order faces are created


def add_box(cx, cy, cz, sx, sy, sz, mat="navy", rot_y_deg=0.0, pivot=None):
    """Axis-aligned box centered at (cx,cy,cz) with full size (sx,sy,sz),
    optional rotation about Y (pitch) around an explicit world-space pivot."""
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    local = [
        (-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
        (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz),
    ]
    pts = [(cx + p[0], cy + p[1], cz + p[2]) for p in local]
    if rot_y_deg:
        piv = pivot if pivot else (cx, cy, cz)
        rad = math.radians(rot_y_deg)
        cos_a, sin_a = math.cos(rad), math.sin(rad)
        rotated = []
        for x, y, z in pts:
            dx, dz = x - piv[0], z - piv[2]
            rx = dx * cos_a + dz * sin_a
            rz = -dx * sin_a + dz * cos_a
            rotated.append((piv[0] + rx, y, piv[2] + rz))
        pts = rotated
    verts = [bm.verts.new(p) for p in pts]
    faces_idx = [
        (0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
        (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0),
    ]
    mi = MAT_IDX[mat]
    for fi in faces_idx:
        f = bm.faces.new([verts[i] for i in fi])
        face_mat.append(mi)
    return verts


def add_cylinder(cx, cy, cz, radius, width, mat="char", segs=16):
    """Cylinder with its axis along Y (wheel axle), centered at (cx,cy,cz)."""
    ring_a, ring_b = [], []
    for k in range(segs):
        a = 2 * math.pi * k / segs
        y0 = cy - width / 2
        y1 = cy + width / 2
        x = cx + radius * math.cos(a)
        z = cz + radius * math.sin(a)
        ring_a.append(bm.verts.new((x, y0, z)))
        ring_b.append(bm.verts.new((x, y1, z)))
    mi = MAT_IDX[mat]
    bm.faces.new(ring_a[::-1]); face_mat.append(mi)
    bm.faces.new(ring_b); face_mat.append(mi)
    for k in range(segs):
        k2 = (k + 1) % segs
        f = bm.faces.new((ring_a[k], ring_a[k2], ring_b[k2], ring_b[k]))
        face_mat.append(mi)


# ---------------------------------------------------------------------------
# Layout: X = length (front at -X, rear/bed at +X), Y = width, Z = up, ground=0
# ---------------------------------------------------------------------------
CAB_LEN = 1.15 * ARGS["cab_len"]
BED_LEN = 2.0
WIDTH = 1.5
WHEEL_R = 0.36
CHASSIS_H = 0.16
CHASSIS_Z = WHEEL_R + CHASSIS_H / 2 - 0.02
BODY_BOTTOM = CHASSIS_Z + CHASSIS_H / 2
BED_WALL_H = 0.52 * ARGS["bed_h"]
TIP_DEG = ARGS["tip"]
CAB_STYLE = ARGS["cab"]
ACCENT = ARGS["accent"]

front_x = -CAB_LEN * 0.5 - 0.72  # hood front
rear_x = CAB_LEN * 0.5 + BED_LEN + 0.1  # bed rear

# hood -- a distinct low, long nose so the silhouette reads cab + hood, not one cube
hood_h = 0.34
hood_len = 0.86
hood_cx = front_x + hood_len / 2
add_box(hood_cx, 0, BODY_BOTTOM + hood_h / 2, hood_len, WIDTH * 0.82, hood_h, mat="navy")

# chassis rail spanning wheel to wheel, tucked entirely under hood+cab+bed (never overshoots)
chassis_front = front_x + 0.06
chassis_len = rear_x - chassis_front - 0.2
chassis_cx = (rear_x + chassis_front) / 2
add_box(chassis_cx, 0, CHASSIS_Z, chassis_len, WIDTH * 0.66, CHASSIS_H, mat="char")

# cab
cab_cx = hood_cx + hood_len / 2 + CAB_LEN * 0.5 - 0.02
if CAB_STYLE == "sloped":
    cab_h = 1.02
    add_box(cab_cx, 0, BODY_BOTTOM + cab_h / 2, CAB_LEN, WIDTH * 0.92, cab_h, mat="navy",
            rot_y_deg=-7, pivot=(cab_cx, 0, BODY_BOTTOM))
elif CAB_STYLE == "stubby":
    cab_h = 0.84
    cab_cx -= 0.08
    add_box(cab_cx, 0, BODY_BOTTOM + cab_h / 2, CAB_LEN * 0.82, WIDTH * 0.92, cab_h, mat="navy")
else:  # boxy
    cab_h = 0.96
    add_box(cab_cx, 0, BODY_BOTTOM + cab_h / 2, CAB_LEN, WIDTH * 0.92, cab_h, mat="navy")

# windshield glass hint: thin charcoal panel set into the cab's rear-top face
glass_x = cab_cx + CAB_LEN * 0.5 - 0.05 if CAB_STYLE != "sloped" else cab_cx + CAB_LEN * 0.42
add_box(glass_x, 0, BODY_BOTTOM + cab_h * 0.74, 0.05, WIDTH * 0.7, cab_h * 0.4, mat="char")

# dump bed: floor + 3 walls (front, left, right; open top and open rear),
# all tipped together about the rear-bottom pivot so it reads as "about to unload"
bed_cx0 = cab_cx + CAB_LEN * 0.5 + BED_LEN * 0.5 + 0.06
bed_floor_h = 0.14
bed_bottom_z = BODY_BOTTOM + 0.02
pivot = (bed_cx0 + BED_LEN / 2, 0, bed_bottom_z)

add_box(bed_cx0, 0, bed_bottom_z + bed_floor_h / 2, BED_LEN, WIDTH * 0.96, bed_floor_h,
        mat="navy", rot_y_deg=-TIP_DEG, pivot=pivot)
wall_cz = bed_bottom_z + bed_floor_h + BED_WALL_H / 2
add_box(bed_cx0 - BED_LEN / 2 + 0.06, 0, wall_cz, 0.12, WIDTH * 0.96, BED_WALL_H,
        mat="navy", rot_y_deg=-TIP_DEG, pivot=pivot)
add_box(bed_cx0, WIDTH * 0.96 / 2 - 0.045, wall_cz, BED_LEN, 0.09, BED_WALL_H,
        mat="navy", rot_y_deg=-TIP_DEG, pivot=pivot)
add_box(bed_cx0, -(WIDTH * 0.96 / 2 - 0.045), wall_cz, BED_LEN, 0.09, BED_WALL_H,
        mat="navy", rot_y_deg=-TIP_DEG, pivot=pivot)

# terracotta accent -- single accent family per variant
if ACCENT == "rail":
    rail_z = bed_bottom_z + bed_floor_h + BED_WALL_H + 0.035
    add_box(bed_cx0, WIDTH * 0.96 / 2 - 0.045, rail_z, BED_LEN, 0.06, 0.07,
            mat="clay", rot_y_deg=-TIP_DEG, pivot=pivot)
    add_box(bed_cx0, -(WIDTH * 0.96 / 2 - 0.045), rail_z, BED_LEN, 0.06, 0.07,
            mat="clay", rot_y_deg=-TIP_DEG, pivot=pivot)
elif ACCENT == "stripe":
    add_box(cab_cx - 0.1, WIDTH * 0.9 / 2 + 0.01, BODY_BOTTOM + 0.05, CAB_LEN + BED_LEN * 0.6,
            0.02, 0.09, mat="clay")
    add_box(cab_cx - 0.1, -(WIDTH * 0.9 / 2 + 0.01), BODY_BOTTOM + 0.05, CAB_LEN + BED_LEN * 0.6,
            0.02, 0.09, mat="clay")
else:  # chevron / bumper accent up front
    add_box(front_x - 0.06, 0, BODY_BOTTOM - 0.06, 0.10, WIDTH * 0.72, 0.16, mat="clay")

# wheels: front pair under hood/cab, rear pair under bed front
wheel_w = 0.22
wy = WIDTH * 0.96 / 2 + wheel_w / 2 - 0.04
front_wx = hood_cx - 0.02
rear_wx = bed_cx0 - BED_LEN * 0.28
for wx in (front_wx, rear_wx):
    for sign in (1, -1):
        add_cylinder(wx, sign * wy, WHEEL_R, WHEEL_R, wheel_w, mat="char", segs=18)

# ---------------------------------------------------------------------------
# finalize mesh
# ---------------------------------------------------------------------------
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
mesh = bpy.data.meshes.new("HerosTruckMark")
bm.to_mesh(mesh)
bm.free()
mesh.validate()
for m in MATS:
    mesh.materials.append(m)
for i, poly in enumerate(mesh.polygons):
    poly.material_index = face_mat[i]

obj = bpy.data.objects.new("HerosTruckMark", mesh)
bpy.context.scene.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

# a light bevel modifier for machined-metal facets, applied once at the end
bev = obj.modifiers.new("Bevel", 'BEVEL')
bev.width = 0.018
bev.segments = 2
bev.limit_method = 'ANGLE'
bev.angle_limit = math.radians(35)
bpy.ops.object.modifier_apply(modifier="Bevel")
bpy.ops.object.shade_smooth()
for f in obj.data.polygons:
    f.use_smooth = True
# keep hard edges readable: auto-smooth via custom split normals angle (Blender 5 API)
try:
    obj.data.use_auto_smooth = True
    obj.data.auto_smooth_angle = math.radians(35)
except Exception:
    pass

mesh = obj.data
xs = [v.co.x for v in mesh.vertices]
ys = [v.co.y for v in mesh.vertices]
zs = [v.co.z for v in mesh.vertices]
h = max(zs) - min(zs)
cx_all = (max(xs) + min(xs)) / 2.0
cy_all = (max(ys) + min(ys)) / 2.0
scale = 1.0 / h
for v in mesh.vertices:
    v.co.x = (v.co.x - cx_all) * scale
    v.co.y = (v.co.y - cy_all) * scale
    v.co.z = v.co.z * scale  # keep resting on z=0 (ground)
mesh.update()

n_tris = sum(len(p.vertices) - 2 for p in mesh.polygons)
print(f"[build_truck] variant={ARGS['variant']} tip={TIP_DEG} cab={CAB_STYLE} accent={ACCENT} "
      f"verts={len(mesh.vertices)} faces={len(mesh.polygons)} tris~{n_tris}")

export_kwargs = dict(
    filepath=OUT_PATH, use_selection=True, export_format='GLB',
    export_yup=True, export_apply=True, export_normals=True, export_materials='EXPORT',
)
try:
    bpy.ops.export_scene.gltf(**export_kwargs)
except TypeError as ex:
    print(f"[build_truck] WARN export kwarg mismatch ({ex}), retrying minimal")
    bpy.ops.export_scene.gltf(filepath=OUT_PATH, use_selection=True, export_format='GLB', export_yup=True)

blend_path = os.path.splitext(OUT_PATH)[0] + ".blend"
bpy.ops.wm.save_as_mainfile(filepath=blend_path)

result = {
    "variant": ARGS["variant"], "tip": TIP_DEG, "cab": CAB_STYLE, "accent": ACCENT,
    "verts": len(mesh.vertices), "faces": len(mesh.polygons), "tris_approx": n_tris,
    "out": OUT_PATH, "bytes": os.path.getsize(OUT_PATH) if os.path.exists(OUT_PATH) else -1,
}
print("BUILD_RESULT_JSON " + json.dumps(result))
