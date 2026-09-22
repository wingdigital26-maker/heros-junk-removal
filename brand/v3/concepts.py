"""Hero's Junk Removal - three NEW interactive-mark concepts, rendered for judgement.

Each must do all three jobs: read as junk removal, survive as a flat 32px mark, and
have a gesture built in that makes the interaction meaningful rather than decorative.

  gauge : a cube divided into eighths that FILLS. Not a metaphor - it is literally how
          Hero's prices a job (truck-fill fraction). The mark is the estimator.
          Interaction: drag to fill, it tells you your load size.
  hmono : the H monogram ASSEMBLING out of scattered junk fragments.
          Interaction: fragments scatter from the pointer, then re-form into the H.
  room  : a room corner with clutter lifting out of it, leaving clean space.
          Interaction: the clutter rises and fades, the space clears.

  blender --background --python concepts.py -- <gauge|hmono|room|all> <outdir>
"""
import bpy, sys, math, os, random

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
WHICH = (argv[0] if argv else "all").lower()
OUT = argv[1] if len(argv) > 1 else os.path.dirname(os.path.abspath(__file__))

INK = (0.022, 0.034, 0.055, 1.0)
RED = (0.55, 0.045, 0.035, 1.0)
PALE = (0.085, 0.10, 0.125, 1.0)   # mid steel: frames the pieces, never glares


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


def bevel(ob, width=0.035, segs=4):
    m = ob.modifiers.new("bev", "BEVEL")
    m.width = width
    m.segments = segs
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(40)
    m.harden_normals = True
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def box(name, loc, scale, material, rot=(0, 0, 0), bw=0.035):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(material)
    bevel(o, bw)
    return o


def frame(name, loc, w, d, h, thick, material):
    """An open outline of a slab: four thin bars. Reads as 'empty' next to a solid."""
    hx, hy = w / 2 - thick / 2, d / 2 - thick / 2
    for i, (dx, dy, sx, sy) in enumerate([
            (0, hy, w, thick), (0, -hy, w, thick),
            (hx, 0, thick, d - thick * 2), (-hx, 0, thick, d - thick * 2)]):
        box(f"{name}{i}", (loc[0] + dx, loc[1] + dy, loc[2]), (sx, sy, h), material, bw=0.012)


# ------------------------------------------------------------------ concept 1
def c_gauge(ink, red, pale):
    """A cube in eighths. The bottom three are full, the rest are empty frames.
    Fill level IS the price. The whole brand mark is the pricing mechanic."""
    W, D = 2.1, 2.1
    seg = 0.30
    gap = 0.055
    filled = 3
    for i in range(8):
        z = 0.22 + i * (seg + gap) + seg / 2
        if i < filled:
            box(f"full{i}", (0, 0, z), (W, D, seg), red if i == filled - 1 else ink, bw=0.03)
        else:
            frame(f"empty{i}", (0, 0, z), W, D, seg, 0.11, pale)


# ------------------------------------------------------------------ concept 2
def c_hmono(ink, red, pale):
    """The H assembling out of junk. Solid where it has formed, loose pieces still
    arriving. The gesture is chaos becoming order, which is the service."""
    unit = 0.40
    # H as a small grid: 5 rows tall, 3 cols, middle row bridges
    cells = []
    for r in range(5):
        for c in range(3):
            if c in (0, 2) or r == 2:
                cells.append((c, r))
    for (c, r) in cells:
        x = (c - 1) * unit * 1.08
        z = 0.30 + r * unit * 1.08
        accent = (c == 2 and r == 4)
        box(f"h{c}{r}", (x, 0, z), (unit, unit * 0.9, unit), red if accent else ink, bw=0.03)

    # loose fragments still flying in: this is what says ASSEMBLING, not just a letter
    random.seed(4)
    for i in range(7):
        ang = random.uniform(0, math.tau)
        rad = random.uniform(1.5, 2.6)
        box(f"loose{i}",
            (math.cos(ang) * rad, math.sin(ang) * rad * 0.5, random.uniform(0.4, 2.6)),
            (unit * random.uniform(0.5, 0.85),) * 3,
            ink if i % 3 else red,
            rot=(random.uniform(-0.8, 0.8), random.uniform(-0.8, 0.8), random.uniform(-0.8, 0.8)),
            bw=0.028)


# ------------------------------------------------------------------ concept 3
def c_room(ink, red, pale):
    """A room corner with clutter lifting out. Smaller and tighter than v1.
    The walls are a mid steel so they FRAME the pieces instead of glaring white,
    and one wall carries a doorway so it reads as a BUILDING, not an open box."""
    t = 0.13
    W, H = 2.0, 1.5          # smaller room than v1
    box("floor", (0, 0, t / 2), (W, W, t), ink, bw=0.035)

    # back wall, solid
    box("wallB", (0, W / 2 - t / 2, H / 2), (W, t, H), pale, bw=0.035)

    # left wall WITH a doorway cut into it: this is what says building
    door_w, door_h = 0.62, 0.98
    seg = (W - door_w) / 2
    for i, yy in enumerate((-(door_w / 2 + seg / 2), door_w / 2 + seg / 2)):
        box(f"wallL{i}", (-W / 2 + t / 2, yy, H / 2), (t, seg, H), pale, bw=0.035)
    box("lintel", (-W / 2 + t / 2, 0, door_h + (H - door_h) / 2),
        (t, door_w, H - door_h), pale, bw=0.035)

    # what is still on the floor, settled and low
    box("left0", (0.46, -0.34, 0.33), (0.58, 0.52, 0.52), ink, bw=0.035)

    # the clutter on its way out: FEWER and CHUNKIER than v1, so each block reads
    lift = [(0.02, 0.10, 1.28, 0.52), (0.26, 0.02, 1.90, 0.44), (-0.14, 0.18, 2.42, 0.36)]
    for i, (x, y, z, sc) in enumerate(lift):
        box(f"up{i}", (x, y, z), (sc, sc * 0.92, sc * 0.86),
            red if i == 0 else ink,
            rot=(0.30 - i * 0.22, -0.18 + i * 0.20, 0.42 - i * 0.30), bw=0.03)


CONCEPTS = {"gauge": c_gauge, "hmono": c_hmono, "room": c_room}
ORDER = ["gauge", "hmono", "room"]


def stage(height, dist):
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

    bpy.ops.object.camera_add(location=(-8.4 * dist, -10.0 * dist, 5.4 * dist))
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
for name in (ORDER if WHICH == "all" else [WHICH]):
    reset()
    ink = mat("ink", INK)
    red = mat("red", RED, metallic=0.5, rough=0.33)
    pale = mat("pale", PALE, metallic=0.08, rough=0.62)
    CONCEPTS[name](ink, red, pale)
    heights = {"gauge": 1.5, "hmono": 1.4, "room": 1.5}
    dists = {"gauge": 0.92, "hmono": 1.0, "room": 1.35}
    stage(heights[name], dists[name])
    bpy.context.scene.render.filepath = os.path.join(OUT, f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print("DONE", name)
