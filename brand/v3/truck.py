"""Hero's Junk Removal - truck mark + icon, Blender 5.2, EEVEE.

Fixes the two earlier failures:
  - every mass gets a HEAVY multi-segment bevel so edges catch light (that is what reads as metal)
  - real wheels: a torus tyre plus a recessed hub, inset into the body, never a flat disc
  - three point rig with a strong RIM light behind, plus a bright world, so the form has drama
  - long low stance, not a stubby toy

Usage:
  blender --background --python truck.py -- <variant> <outdir>
"""
import bpy, sys, math, os

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
VARIANT = argv[0] if argv else "1"
OUT = argv[1] if len(argv) > 1 else os.path.dirname(os.path.abspath(__file__))

NAVY = (0.022, 0.034, 0.055, 1.0)      # #0E1621 near-black navy
CLAY = (0.55, 0.045, 0.035, 1.0)       # #C2362F signal red
TYRE = (0.022, 0.026, 0.032, 1.0)

# variant knobs: (bed tip degrees, chassis length, cab height, bed length, abstraction)
V = {
    "1": dict(tip=26, clen=2.55, cabh=0.72, blen=1.45, wheel=0.40, gap=0.06),
    "2": dict(tip=40, clen=2.55, cabh=0.66, blen=1.50, wheel=0.40, gap=0.06),
    "3": dict(tip=0, clen=2.75, cabh=0.60, blen=1.60, wheel=0.38, gap=0.05),
    "4": dict(tip=32, clen=2.30, cabh=0.86, blen=1.30, wheel=0.44, gap=0.07),
    "5": dict(tip=50, clen=2.60, cabh=0.70, blen=1.40, wheel=0.40, gap=0.06),
    "6": dict(tip=22, clen=3.00, cabh=0.56, blen=1.75, wheel=0.36, gap=0.05),
}[VARIANT]


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, rgba, metallic=0.9, rough=0.28):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = rgba
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    return m


def bevel(ob, width=0.045, segs=5):
    m = ob.modifiers.new("bev", "BEVEL")
    m.width = width
    m.segments = segs
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(40)
    m.harden_normals = True
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def box(name, loc, scale, material, rot=(0, 0, 0), bw=0.05):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    ob = bpy.context.object
    ob.name = name
    ob.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    ob.data.materials.append(material)
    bevel(ob, bw)
    return ob


def wheel(name, loc, r, mnavy, mtyre):
    """Solid tyre with a recessed hub. A ring reads as a hole at small sizes."""
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=r * 0.52, location=loc,
                                        vertices=48, rotation=(0, math.radians(90), 0))
    t = bpy.context.object
    t.name = name + "_tyre"
    t.data.materials.append(mtyre)
    bevel(t, r * 0.16, 5)

    for sgn in (1, -1):
        bpy.ops.mesh.primitive_cylinder_add(
            radius=r * 0.52, depth=r * 0.16, vertices=32,
            location=(loc[0], loc[1] + sgn * r * 0.30, loc[2]),
            rotation=(0, math.radians(90), 0))
        h = bpy.context.object
        h.name = f"{name}_hub{sgn}"
        h.data.materials.append(mnavy)
        bevel(h, r * 0.05, 4)
    return t


def build():
    reset()
    navy = mat("navy", NAVY)
    clay = mat("clay", CLAY, metallic=0.55, rough=0.34)
    tyre = mat("tyre", TYRE, metallic=0.1, rough=0.62)

    clen, cabh, blen = V["clen"], V["cabh"], V["blen"]
    wr, gap = V["wheel"], V["gap"]
    W = 1.05                      # body width
    deck = wr * 1.16              # deck height above ground

    # chassis: long, low, purposeful
    box("chassis", (0, 0, deck), (clen, W, 0.30), navy, bw=0.07)

    # cab: sits forward, tall enough to read, chamfered hard
    cabx = -clen * 0.42
    box("cab", (cabx, 0, deck + 0.15 + cabh / 2), (clen * 0.34, W * 0.99, cabh), navy, bw=0.09)


    # dump bed: hinges at the TAIL and rises toward the cab, the way a real tipper does.
    # Pivoting around the bed centre made it float, so the centre is solved from the hinge.
    tip = math.radians(V["tip"])
    BL, BH = blen / 2.0, 0.31                 # bed half length, half height
    px = clen / 2.0 - 0.10                    # hinge sits just inside the tail
    pz = deck + 0.15                          # hinge sits on the chassis top
    ct, st = math.cos(tip), math.sin(tip)
    cx = px - (BL * ct - BH * st)
    cz = pz + (BL * st + BH * ct)

    bed = box("bed", (cx, 0, cz), (blen, W * 0.98, 0.62), navy,
              rot=(0, tip, 0), bw=0.08)

    # the single clay accent: a thin stripe down the bed flank
    box("rail", (cx, 0, cz), (blen * 0.995, W * 1.012, 0.10), clay,
        rot=(0, tip, 0), bw=0.02)


    # THE LOAD. Jack's note 2026-09-22: a bare truck reads as "truck removal" / a trucking
    # company. Junk piled above the bed sides is what makes the category unmistakable, and it
    # is also what every competitor's empty truck fails to say.
    import random
    random.seed(7)
    bedtop = cz + 0.31
    for i in range(9):
        fx = (i / 8.0 - 0.5) * blen * 0.82
        sx = random.uniform(0.17, 0.34)
        sy = random.uniform(0.20, 0.42)
        sz = random.uniform(0.18, 0.34)
        jz = bedtop + sz * 0.30 - random.uniform(0.06, 0.20)
        box(f"load{i}", (cx + fx, random.uniform(-0.20, 0.20), jz),
            (sx, sy, sz), clay if i == 4 else navy,
            rot=(random.uniform(-0.5, 0.5), random.uniform(-0.4, 0.4),
                 random.uniform(-0.9, 0.9)), bw=0.028)

    # wheels, inset so they belong to the body
    wy = W / 2 - 0.02
    for i, wx in enumerate((-clen * 0.36, clen * 0.34)):
        for sgn in (1, -1):
            wheel(f"w{i}{sgn}", (wx, sgn * wy, wr), wr, navy, tyre)

    # ---------- staging ----------
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
    gp = bpy.context.object
    gp.name = "ground"
    gp.data.materials.append(mat("bg", (0.90, 0.91, 0.93, 1), metallic=0.0, rough=0.55))

    # three point rig. the rim light is what sells the bevels.
    def lamp(name, loc, energy, size, kind="AREA"):
        d = bpy.data.lights.new(name, kind)
        d.energy = energy
        if kind == "AREA":
            d.size = size
        o = bpy.data.objects.new(name, d)
        bpy.context.collection.objects.link(o)
        o.location = loc
        c = o.constraints.new("TRACK_TO")
        c.track_axis = "TRACK_NEGATIVE_Z"
        c.up_axis = "UP_Y"
        return o

    key = lamp("key", (-3.2, -4.4, 5.2), 1400, 7)
    rim = lamp("rim", (4.6, 4.2, 3.0), 2200, 4)      # behind, catches every bevel
    fill = lamp("fill", (4.0, -5.0, 2.0), 380, 9)

    tgt = bpy.data.objects.new("tgt", None)
    bpy.context.collection.objects.link(tgt)
    tgt.location = (0, 0, deck + 0.4)
    for l in (key, rim, fill):
        l.constraints[0].target = tgt

    w = bpy.context.scene.world
    if w is None:
        w = bpy.data.worlds.new("W")
        bpy.context.scene.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.86, 0.88, 0.91, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 1.15

    bpy.ops.object.camera_add(location=(-7.6, -9.2, 4.6))
    cam = bpy.context.object
    cam.data.lens = 105
    c = cam.constraints.new("TRACK_TO")
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    c.target = tgt
    bpy.context.scene.camera = cam

    s = bpy.context.scene
    s.render.engine = "BLENDER_EEVEE"
    s.render.resolution_x = 1100
    s.render.resolution_y = 780
    s.render.film_transparent = False
    try:
        s.eevee.use_raytracing = True
        s.eevee.taa_render_samples = 64
    except Exception:
        pass
    s.view_settings.look = "AgX - Medium High Contrast"
    s.view_settings.exposure = 0.35


def render(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


build()
os.makedirs(OUT, exist_ok=True)
if os.environ.get("HJR_HERO"):
    s = bpy.context.scene
    s.render.resolution_x = 1600
    s.render.resolution_y = 1100
    s.render.film_transparent = True
    try:
        s.eevee.taa_render_samples = 128
    except Exception:
        pass
    for o in bpy.data.objects:
        if o.name == "ground":
            o.hide_render = True
    cam = s.camera
    cam.location = (-8.0, -9.0, 3.9)
    cam.data.lens = 105
    render(os.path.join(OUT, "hero.png"))
elif os.environ.get("HJR_ICON"):
    s = bpy.context.scene
    s.render.resolution_x = 640
    s.render.resolution_y = 640
    s.render.film_transparent = True
    for o in bpy.data.objects:
        if o.name == "ground":
            o.hide_render = True
    cam = s.camera
    cam.location = (-8.2, -9.4, 4.4)
    cam.data.lens = 88
    render(os.path.join(OUT, "icon.png"))
else:
    render(os.path.join(OUT, f"v{VARIANT}.png"))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, f"v{VARIANT}.blend"))
for o in bpy.data.objects:
    if o.name == "ground":
        o.hide_render = True
        o.select_set(False)
bpy.ops.object.select_all(action="SELECT")
bpy.data.objects["ground"].select_set(False)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f"v{VARIANT}.glb"),
                          export_format="GLB", use_selection=True,
                          export_draco_mesh_compression_enable=True,
                          export_apply=True)
print("DONE", VARIANT)
