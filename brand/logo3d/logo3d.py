"""Hero's Junk Removal - LOGO exploration, reusing house.py's cube/bevel/material approach at a
coarser pitch so the shapes read as icons (a couch is a couch, a trailer is a trailer). Does not
import or modify brand/house.py; the small pieces of shared code (unit cube + bevel, principled
material with the object-colour multiply trick, voxelising a box into near-cubic cells) are copied
here in simplified form since house.py runs top-level code on import.

Three logo directions, each rendered twice (transparent + on the #1C1917 header colour):
  1 = couch      : simplified house + a RED voxel couch sliding out the open door
  2 = trailer    : house + a small ink dump trailer beside it, red cubes arcing door -> trailer
  3 = clean      : minimal near-front isometric house, open door, a tidy stream of red cubes
                   stepping out and up - the most badge-like

Usage:
  blender -b --factory-startup -P brand/logo3d/logo3d.py -- <outdir> [dir=1|2|3|all]
"""
import bpy, sys, math, os
import numpy as np
from mathutils import Euler, Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else os.path.dirname(os.path.abspath(__file__))
KV = dict(a.split("=", 1) for a in argv[1:] if "=" in a)
DIRS = ["1", "2", "3"] if KV.get("dir", "all") == "all" else [KV.get("dir", "1")]

os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(11)

INK = (0.028, 0.033, 0.042)     # #1C1917-ish in linear-leaning value, ink voxels
SLATE = (0.10, 0.115, 0.14)     # lighter body slate so the silhouette reads against dark
RED = (0.42, 0.045, 0.045)      # brand red, #B32A25-ish, brightened a touch for a key light hit
HEADER = (0.011, 0.0095, 0.0085)  # #1C1917 in approx linear

PITCH = 0.42   # coarse: fewer, bigger voxels than house.py's 0.18


def cells_of(center, size, pitch=None, jit=0.0, rot=(0, 0, 0)):
    """Split a box into near-cubic cells at pitch, in a LOCAL frame that is then rotated by `rot`
    (Euler XYZ) about its own centre and translated to `center`. Returns (pos, cellsize, quat) so
    tilted groups (the roof) are made of cells that are themselves tilted, not axis-aligned cubes
    dropped at sloped positions (which reads as a staircase, not a plane)."""
    pitch = pitch or PITCH
    n = [max(1, int(round(size[i] / pitch))) for i in range(3)]
    R = Euler(rot, "XYZ").to_matrix()
    q = R.to_quaternion()
    out = []
    for ix in range(n[0]):
        for iy in range(n[1]):
            for iz in range(n[2]):
                local = [(idx + 0.5) / n[i] * size[i] - size[i] / 2 for i, idx in enumerate((ix, iy, iz))]
                p = Vector(center) + R @ Vector(local)
                cell = [size[i] / n[i] - 0.008 for i in range(3)]
                if jit:
                    k = 1.0 - rng.uniform(0, jit)
                    cell = [c * k for c in cell]
                out.append((tuple(p), tuple(cell), tuple(q)))
    return out


def unit_cube():
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    o = bpy.context.object
    o.name = "frag"
    m = o.modifiers.new("bev", "BEVEL")
    m.width = 0.075
    m.segments = 2
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(38)
    m.harden_normals = True
    for p in o.data.polygons:
        p.use_smooth = True
    bpy.ops.object.modifier_apply(modifier="bev")
    o.hide_render = True
    o.hide_viewport = True
    return o


def make_material(name, rgb, metallic=0.15, rough=0.42):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    return m


def place(mesh, mats, cells, colkey):
    coll = bpy.context.collection
    objs = []
    for i, cell in enumerate(cells):
        p, s = cell[0], cell[1]
        q = cell[2] if len(cell) > 2 else (1, 0, 0, 0)
        o = bpy.data.objects.new(f"c{colkey}_{i}", mesh)
        coll.objects.link(o)
        o.location = p
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion = q
        o.scale = s
        o.material_slots[0].link = "OBJECT"
        o.material_slots[0].material = mats[colkey]
        objs.append(o)
    return objs


# ---------------------------------------------------------------- the three builds
def build_house_shell(mesh, mats, door_w=0.52, door_h=0.70, roof_rise=0.46, w=1.55, d=1.25, h=0.72):
    """A simple gabled box with an open doorway cut in the +X (door) face, built from FEW, BIG
    voxels (pitch ~0.42) so it reads as a chunky house icon rather than a brick wall. Front wall
    is two piers + a lintel above the open door; roof is two ridge-meeting slabs of properly
    tilted cells (not axis-aligned cubes at sloped positions, which reads as stairs)."""
    z0 = 0.09
    cells = []
    # plinth
    cells += cells_of((0, 0, z0 / 2), (w + 0.14, d + 0.14, z0), pitch=z0)
    # back wall (-X) and the two side walls, each 1 cell thick x 2 cells tall
    cells += cells_of((-w / 2 + PITCH / 2, 0, z0 + h / 2), (PITCH, d, h), pitch=PITCH * 0.98)
    cells += cells_of((0, -d / 2 + PITCH / 2, z0 + h / 2), (w - PITCH, PITCH, h), pitch=PITCH * 0.98)
    cells += cells_of((0, d / 2 - PITCH / 2, z0 + h / 2), (w - PITCH, PITCH, h), pitch=PITCH * 0.98)
    # front (door) wall: two piers + a lintel above the opening
    pier = (d - door_w) / 2
    for yy in (-(door_w / 2 + pier / 2), door_w / 2 + pier / 2):
        cells += cells_of((w / 2 - PITCH / 2, yy, z0 + door_h / 2), (PITCH, pier, door_h), pitch=max(pier, door_h))
    cells += cells_of((w / 2 - PITCH / 2, 0, z0 + door_h + (h - door_h) / 2), (PITCH, d, h - door_h), pitch=max(d, h - door_h))
    # dark doorway reveal, set back, so the opening reads as a hole not a flat colour
    reveal = cells_of((w / 2 - PITCH * 0.9, 0, z0 + door_h / 2), (PITCH * 0.25, door_w - 0.04, door_h - 0.03), pitch=door_h)
    # gabled roof: two slabs of tilted cells meeting at the ridge, sized to sit right on the wall top
    ze = z0 + h
    half = d / 2 + 0.10
    pitch_ang = math.atan2(roof_rise, half)
    slope_len = math.hypot(half, roof_rise) + 0.03
    roof_t = 0.14
    roof_cells = []
    n_along = max(2, int(round(slope_len / 0.32)))
    for s in (-1, 1):
        n = Vector((0, s * math.sin(pitch_ang), math.cos(pitch_ang)))
        along = Vector((0, s * math.cos(pitch_ang), -math.sin(pitch_ang)))
        ridge = Vector((0, 0, ze + roof_rise))
        center = ridge + along * (slope_len / 2) + n * (roof_t / 2)
        roof_cells += cells_of(tuple(center), (w + 0.24, slope_len, roof_t),
                                rot=(-s * pitch_ang, 0, 0), pitch=max(slope_len / n_along, roof_t))
    place(mesh, mats, cells, "wall")
    place(mesh, mats, reveal, "ink")
    place(mesh, mats, roof_cells, "roof")
    return {"z0": z0, "h": h, "w": w, "d": d, "door_h": door_h, "door_w": door_w, "door_x": w / 2}


def build_couch(mesh, mats, house):
    """A red voxel couch: a low seat slab, a taller back slab set behind it, two arm blocks. Built
    from a handful of big cells (2x2ish per part) so the couch silhouette reads on its own -
    seat + back + two arms - sliding out through the open doorway."""
    z0, dx = house["z0"], house["door_x"]
    seat_z = z0 + 0.15
    cx0 = dx + 0.62
    seat = cells_of((cx0, 0.0, seat_z), (0.60, 0.86, 0.22), pitch=0.30)
    back = cells_of((cx0 - 0.19, 0.0, seat_z + 0.28), (0.22, 0.86, 0.40), pitch=0.28)
    arm_a = cells_of((cx0, -0.43, seat_z + 0.14), (0.60, 0.16, 0.32), pitch=0.30)
    arm_b = cells_of((cx0, 0.43, seat_z + 0.14), (0.60, 0.16, 0.32), pitch=0.30)
    place(mesh, mats, seat + back + arm_a + arm_b, "red")


def build_trailer(mesh, mats, house):
    """A small ink dump trailer close beside the house: an open tray (bottom + 4 low walls) on two
    chunky wheels, and a thin hitch bar reaching toward the house corner, so the whole thing reads
    as one parked trailer rather than scattered blocks. An arc of red cubes lifts out of the
    doorway and drops into the tray, so the load reads as travelling house -> trailer."""
    z0, dx, d = house["z0"], house["door_x"], house["d"]
    tx, ty = dx + 1.15, d / 2 + 0.50
    tray_z = z0 + 0.30
    bed = cells_of((tx, ty, tray_z), (0.82, 0.52, 0.09), pitch=0.42)
    wall_ny = cells_of((tx, ty - 0.265, tray_z + 0.135), (0.82, 0.07, 0.19), pitch=0.42)
    wall_py = cells_of((tx, ty + 0.265, tray_z + 0.135), (0.82, 0.07, 0.19), pitch=0.42)
    wall_nx = cells_of((tx - 0.415, ty, tray_z + 0.135), (0.06, 0.52, 0.19), pitch=0.52)
    wall_px = cells_of((tx + 0.415, ty, tray_z + 0.135), (0.06, 0.52, 0.19), pitch=0.52)
    hitch = cells_of(((tx - 0.42 + dx + 0.22) / 2, ty * 0.30, z0 + 0.09), (tx - 0.42 - (dx + 0.22), 0.08, 0.08), pitch=0.6)
    place(mesh, mats, bed + wall_ny + wall_py + wall_nx + wall_px + hitch, "ink")
    for wy in (ty - 0.30, ty + 0.30):
        wheel = cells_of((tx + 0.18, wy, z0 + 0.11), (0.22, 0.13, 0.22), pitch=0.16)
        place(mesh, mats, wheel, "roof")
    arc_pts = [
        (dx + 0.20, 0.10, z0 + 0.34, 0.16),
        (dx + 0.42, 0.28, z0 + 0.54, 0.155),
        (dx + 0.66, 0.42, z0 + 0.66, 0.15),
        (dx + 0.90, 0.50, z0 + 0.66, 0.15),
        (tx - 0.10, ty - 0.08, tray_z + 0.20, 0.16),
    ]
    for x, y, z, s in arc_pts:
        place(mesh, mats, cells_of((x, y, z), (s, s, s), pitch=s), "red")


def build_clean(mesh, mats, house):
    """Minimal badge version: a tidy single-file stream of red cubes stepping out and up from the
    doorway, shrinking slightly as they rise, like the house being emptied one piece at a time."""
    z0, dx = house["z0"], house["door_x"]
    steps = [
        (dx + 0.20, 0.0, z0 + 0.24, 0.22),
        (dx + 0.46, 0.0, z0 + 0.48, 0.19),
        (dx + 0.70, 0.0, z0 + 0.76, 0.16),
        (dx + 0.90, 0.0, z0 + 1.06, 0.13),
        (dx + 1.05, 0.0, z0 + 1.34, 0.10),
    ]
    for x, y, z, s in steps:
        place(mesh, mats, cells_of((x, y, z), (s, s, s), pitch=s), "red")


BUILDERS = {"1": build_couch, "2": build_trailer, "3": build_clean}


def scene_bbox():
    """World-space centre and radius of every mesh object currently in the scene (skips the
    hidden prototype cube), so framing adapts automatically to whatever a build placed."""
    bpy.context.view_layer.update()
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for o in bpy.context.collection.objects:
        if o.type != "MESH" or o.hide_viewport:
            continue
        for corner in o.bound_box:
            wp = o.matrix_world @ Vector(corner)
            lo.x, lo.y, lo.z = min(lo.x, wp.x), min(lo.y, wp.y), min(lo.z, wp.z)
            hi.x, hi.y, hi.z = max(hi.x, wp.x), max(hi.y, wp.y), max(hi.z, wp.z)
    center = (lo + hi) / 2
    radius = max((hi - lo).x, (hi - lo).y, (hi - lo).z) / 2
    return tuple(center), radius


# ---------------------------------------------------------------- lighting / camera / render
def light(name, loc, energy, size, target):
    d = bpy.data.lights.new(name, "AREA")
    d.energy, d.size = energy, size
    o = bpy.data.objects.new(name, d)
    bpy.context.collection.objects.link(o)
    o.location = loc
    c = o.constraints.new("TRACK_TO")
    c.track_axis, c.up_axis, c.target = "TRACK_NEGATIVE_Z", "UP_Y", target
    return o


def setup_scene(transparent, center, radius):
    s = bpy.context.scene
    s.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE"
    s.render.resolution_x = 1024
    s.render.resolution_y = 1024
    s.render.film_transparent = transparent
    try:
        s.eevee.taa_render_samples = 96
        s.eevee.use_raytracing = True
    except Exception:
        pass
    s.view_settings.view_transform = "AgX"
    s.view_settings.look = "AgX - Medium High Contrast"
    s.view_settings.exposure = 0.15

    tgt = bpy.data.objects.new("tgt", None)
    bpy.context.collection.objects.link(tgt)
    tgt.location = center
    light("key", (center[0] + radius * 1.6, center[1] - radius * 2.0, center[2] + radius * 2.3), 900, radius * 2.2, tgt)
    light("rim", (center[0] - radius * 1.9, center[1] + radius * 1.7, center[2] + radius * 1.6), 1400, radius * 1.6, tgt)
    light("fill", (center[0] - radius * 1.6, center[1] - radius * 1.9, center[2] + radius * 0.9), 260, radius * 3.0, tgt)

    w = bpy.context.scene.world or bpy.data.worlds.new("W")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    if transparent:
        bg.inputs[0].default_value = (0, 0, 0, 1)
        bg.inputs[1].default_value = 0.0
    else:
        bg.inputs[0].default_value = (*HEADER, 1.0)
        bg.inputs[1].default_value = 1.0

    # camera: elevated 3/4, isometric-ish, framed so the object fills ~75% of a square frame
    az, el = math.radians(-38), math.radians(30)
    cam_dir = Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
    dist = radius / math.tan(math.radians(12.5))  # tight fov -> object fills ~75-80% of the square frame
    cam_loc = Vector(center) + cam_dir * dist
    bpy.ops.object.camera_add(location=cam_loc)
    cam = bpy.context.object
    cam.data.lens = 50
    c = cam.constraints.new("TRACK_TO")
    c.track_axis, c.up_axis, c.target = "TRACK_NEGATIVE_Z", "UP_Y", tgt
    s.camera = cam


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def render_one(direction, transparent):
    reset()
    mesh = unit_cube().data
    mesh.materials.append(None)
    mats = {
        "wall": make_material("wall", SLATE, 0.12, 0.46),
        "ink": make_material("ink", INK, 0.15, 0.40),
        "roof": make_material("roof", INK, 0.15, 0.42),
        "red": make_material("red", RED, 0.10, 0.34),
    }
    house = build_house_shell(mesh, mats)
    BUILDERS[direction](mesh, mats, house)

    center, radius = scene_bbox()
    setup_scene(transparent, center, radius)
    suffix = "transparent" if transparent else "header"
    path = os.path.join(OUT, f"dir{direction}-{suffix}.png")
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("RENDERED", path, flush=True)


for d in DIRS:
    render_one(d, transparent=True)
    render_one(d, transparent=False)

print("DONE logo3d")
