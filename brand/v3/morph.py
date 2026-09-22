"""Hero's Junk Removal - the MORPHING PIECE.

One single unit made of N identical fragments that re-forms into the things Hero's
actually hauls: a cube, a couch, a fridge, a mattress, and the loaded truck.
Same fragments every time, only their targets change. That is what makes it read as
ONE object transforming rather than several objects swapping.

This is the same architecture as the Wing Digital sculpture: fixed instance count,
per-target transform sets, lerp between them on the web.

Outputs:
  shapes.json   - every fragment's position/scale/colour per target, for three.js
  <target>.png  - a Blender preview of each form
  morph.glb     - the fragments in CUBE formation, for anyone who wants the mesh

  blender --background --python morph.py -- <target|all> <outdir>
"""
import bpy, sys, math, os, json

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
WHICH = (argv[0] if argv else "all").lower()
OUT = argv[1] if len(argv) > 1 else os.path.dirname(os.path.abspath(__file__))

INK = (0.022, 0.034, 0.055, 1.0)     # #0E1621
RED = (0.55, 0.045, 0.035, 1.0)      # #C2362F

N = 64          # fragment count, fixed across every target


# ---------------------------------------------------------------- shape volumes
# Each shape is a list of boxes: (cx,cy,cz, sx,sy,sz, accent?)
# Fragments are distributed across the boxes in proportion to volume, so the same
# 64 pieces can fill any of them.

def shape_cube():
    return [(0, 0, 1.1, 2.0, 2.0, 2.0, False)]


def shape_couch():
    return [
        (0.00, 0.00, 0.62, 2.60, 1.05, 0.34, False),   # seat
        (0.00, 0.46, 1.15, 2.60, 0.24, 0.80, False),   # back
        (-1.24, 0.00, 0.92, 0.28, 1.05, 0.62, True),   # left arm, accent
        (1.24, 0.00, 0.92, 0.28, 1.05, 0.62, False),   # right arm
        (0.00, 0.00, 0.22, 2.40, 0.95, 0.20, False),   # base
    ]


def shape_fridge():
    return [
        (0, 0, 1.30, 1.25, 1.05, 2.30, False),         # body
        (0, -0.56, 1.72, 1.15, 0.10, 1.30, True),      # upper door face, accent
        (0, -0.56, 0.66, 1.15, 0.10, 0.72, False),     # lower door face
    ]


def shape_mattress():
    return [
        (0, 0, 0.45, 2.70, 1.70, 0.42, False),         # the slab
        (0, 0, 0.70, 2.70, 1.70, 0.08, True),          # piped top edge, accent
    ]


def shape_truck():
    return [
        (0.00, 0.00, 0.62, 3.10, 1.10, 0.32, False),   # chassis
        (-1.05, 0.00, 1.16, 1.10, 1.00, 0.76, False),  # cab
        (0.70, 0.00, 1.02, 1.90, 1.04, 0.26, False),   # bed floor
        (0.70, 0.00, 1.20, 1.85, 1.06, 0.12, True),    # stripe, accent
        (0.70, 0.00, 1.60, 1.60, 0.92, 0.66, False),   # the load
    ]


SHAPES = {
    "cube": shape_cube, "couch": shape_couch, "fridge": shape_fridge,
    "mattress": shape_mattress, "truck": shape_truck,
}
ORDER = ["cube", "couch", "fridge", "mattress", "truck"]


def layout(boxes, n=N):
    """Distribute n fragments across the shape's boxes, proportional to volume.
    Fragments sit on a grid inside each box so the form reads solid, not scattered."""
    vols = [b[3] * b[4] * b[5] for b in boxes]
    total = sum(vols)
    counts = [max(1, round(n * v / total)) for v in vols]
    # reconcile rounding so the count is EXACTLY n, always
    while sum(counts) > n:
        counts[counts.index(max(counts))] -= 1
    while sum(counts) < n:
        counts[counts.index(max(counts))] += 1

    frags = []
    for (cx, cy, cz, sx, sy, sz, accent), c in zip(boxes, counts):
        # pick a grid close to cubic for this box's proportions
        best, bestscore = (1, 1, 1), 1e9
        for gx in range(1, c + 1):
            for gy in range(1, c // gx + 1):
                gz = max(1, round(c / (gx * gy)))
                if gx * gy * gz < c:
                    continue
                cell = (sx / gx, sy / gy, sz / gz)
                score = max(cell) / max(1e-6, min(cell)) + abs(gx * gy * gz - c)
                if score < bestscore:
                    best, bestscore = (gx, gy, gz), score
        gx, gy, gz = best
        made = 0
        for ix in range(gx):
            for iy in range(gy):
                for iz in range(gz):
                    if made >= c:
                        break
                    fx = cx + (ix + 0.5) / gx * sx - sx / 2
                    fy = cy + (iy + 0.5) / gy * sy - sy / 2
                    fz = cz + (iz + 0.5) / gz * sz - sz / 2
                    frags.append({
                        "p": [round(fx, 4), round(fy, 4), round(fz, 4)],
                        "s": [round(sx / gx, 4), round(sy / gy, 4), round(sz / gz, 4)],
                        "a": bool(accent),
                    })
                    made += 1
    return frags[:n]


# ---------------------------------------------------------------- blender build
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, rgba, metallic=0.88, rough=0.27):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = rgba
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    return m


def build(frags, ink, red, gap=0.055):
    for i, f in enumerate(frags):
        sx, sy, sz = f["s"]
        bpy.ops.mesh.primitive_cube_add(size=1, location=f["p"])
        o = bpy.context.object
        o.name = f"frag{i}"
        # shrink slightly so the seams between fragments stay visible. That gap is
        # what tells the eye this is MANY pieces, which is the whole point.
        o.scale = (max(0.04, sx - gap), max(0.04, sy - gap), max(0.04, sz - gap))
        bpy.ops.object.transform_apply(scale=True)
        o.data.materials.append(red if f["a"] else ink)
        m = o.modifiers.new("bev", "BEVEL")
        m.width = 0.022
        m.segments = 3
        m.limit_method = "ANGLE"
        m.angle_limit = math.radians(40)
        m.harden_normals = True
        for p in o.data.polygons:
            p.use_smooth = True


def stage(height=1.2, dist=1.0):
    bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, 0))
    gp = bpy.context.object
    gp.name = "ground"
    gp.data.materials.append(mat("bg", (0.90, 0.91, 0.93, 1), 0.0, 0.5))

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
    tgt.location = (0, 0, height)
    for l in (lamp("key", (-3.4, -4.8, 5.6), 1700, 7),
              lamp("rim", (5.0, 4.6, 3.4), 2600, 4),
              lamp("fill", (4.4, -5.4, 2.2), 420, 10)):
        l.constraints[0].target = tgt

    w = bpy.context.scene.world or bpy.data.worlds.new("W")
    bpy.context.scene.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.87, 0.89, 0.92, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 1.2

    bpy.ops.object.camera_add(location=(-9.6 * dist, -11.4 * dist, 5.8 * dist))
    cam = bpy.context.object
    cam.data.lens = 100
    c = cam.constraints.new("TRACK_TO")
    c.track_axis, c.up_axis, c.target = "TRACK_NEGATIVE_Z", "UP_Y", tgt
    bpy.context.scene.camera = cam

    s = bpy.context.scene
    s.render.engine = "BLENDER_EEVEE"
    s.render.resolution_x, s.render.resolution_y = 1200, 900
    try:
        s.eevee.use_raytracing = True
        s.eevee.taa_render_samples = 96
    except Exception:
        pass
    s.view_settings.look = "AgX - Medium High Contrast"
    s.view_settings.exposure = 0.4


os.makedirs(OUT, exist_ok=True)
targets = ORDER if WHICH == "all" else [WHICH]

# the data the web piece morphs between
data = {"n": N, "targets": {k: layout(SHAPES[k]()) for k in ORDER}}
with open(os.path.join(OUT, "shapes.json"), "w") as fh:
    json.dump(data, fh)
print("wrote shapes.json", {k: len(v) for k, v in data["targets"].items()})

for t in targets:
    reset()
    ink, red = mat("ink", INK), mat("red", RED, metallic=0.5, rough=0.33)
    build(data["targets"][t], ink, red)
    zs = [f["p"][2] for f in data["targets"][t]]
    stage(height=(min(zs) + max(zs)) / 2, dist=1.0)
    bpy.context.scene.render.filepath = os.path.join(OUT, f"{t}.png")
    bpy.ops.render.render(write_still=True)
    if t == "cube":
        bpy.context.scene.render.film_transparent = True
        bpy.data.objects["ground"].hide_render = True
        bpy.ops.object.select_all(action="SELECT")
        for n_ in ("ground", "key", "rim", "fill", "tgt"):
            if n_ in bpy.data.objects:
                bpy.data.objects[n_].select_set(False)
        bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "morph.glb"),
                                  export_format="GLB", use_selection=True,
                                  export_draco_mesh_compression_enable=True,
                                  export_apply=True)
    print("DONE", t)
