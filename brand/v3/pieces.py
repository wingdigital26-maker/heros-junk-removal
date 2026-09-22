"""Hero's Junk Removal - logo directions 1 and 3 as 3D interactive hero pieces.

  piece A = candidate 01-truck: the loaded truck reduced to bold geometric masses,
            led by the triangular junk mound. Literal, instantly legible.
  piece B = candidate 03-cleared-space: an open crate with a block lifted out of it.
            Abstract. Reads as "something got removed", which is the actual service.
            This one is built to ANIMATE: the blocks lift out and settle back.

Both staged on the cool silver backdrop with a real contact shadow, matching the
Wing Digital sculpture's staging.

  blender --background --python pieces.py -- <A|B> <outdir> [glb]
"""
import bpy, sys, math, os

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
PIECE = (argv[0] if argv else "A").upper()
OUT = argv[1] if len(argv) > 1 else os.path.dirname(os.path.abspath(__file__))
WANT_GLB = "glb" in argv

INK = (0.022, 0.034, 0.055, 1.0)     # #0E1621
RED = (0.55, 0.045, 0.035, 1.0)      # #C2362F
STEEL = (0.16, 0.19, 0.23, 1.0)


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


def bevel(ob, width=0.05, segs=5):
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


def wedge(name, loc, w, d, h, material, bw=0.05):
    """A triangular prism: the junk mound that tops the truck."""
    import bmesh
    me = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    bm = bmesh.new()
    hw, hd = w / 2, d / 2
    front = [(-hw, -hd, 0), (hw, -hd, 0), (0, -hd, h)]
    back = [(-hw, hd, 0), (hw, hd, 0), (0, hd, h)]
    fv = [bm.verts.new(v) for v in front]
    bv = [bm.verts.new(v) for v in back]
    bm.faces.new(fv)
    bm.faces.new(bv[::-1])
    for i in range(3):
        j = (i + 1) % 3
        bm.faces.new((fv[i], fv[j], bv[j], bv[i]))
    bm.to_mesh(me)
    bm.free()
    ob.location = loc
    ob.data.materials.append(material)
    bevel(ob, bw)
    return ob


def piece_a(ink, red):
    """Candidate 1: the loaded truck, bold geometric masses."""
    box("chassis", (0, 0, 0.62), (3.3, 1.15, 0.34), ink, bw=0.08)
    box("cab", (-1.12, 0, 1.18), (1.15, 1.05, 0.80), ink, bw=0.10)
    box("bedfloor", (0.72, 0, 1.00), (2.0, 1.08, 0.26), ink, bw=0.07)
    box("stripe", (0.72, 0, 1.00), (1.99, 1.10, 0.09), red, bw=0.02)
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1.35, radius2=0, depth=1.30,
                                    location=(0.78, 0, 1.78),
                                    rotation=(0, 0, math.radians(45)))
    mo = bpy.context.object
    mo.name = "mound"
    mo.scale = (1.0, 0.72, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    mo.data.materials.append(ink)
    bevel(mo, 0.06, 4)
    for wx in (-1.05, 1.08):
        for sy in (1, -1):
            bpy.ops.mesh.primitive_cylinder_add(
                radius=0.50, depth=0.34, vertices=48,
                location=(wx, sy * 0.60, 0.50), rotation=(0, math.radians(90), 0))
            t = bpy.context.object
            t.data.materials.append(mat(f"t{wx}{sy}", (0.02, 0.024, 0.03, 1), 0.1, 0.6))
            bevel(t, 0.08, 5)
    return 0.0


def piece_b(ink, red):
    """Candidate 3: the crate, with blocks lifting out of it.
    The gesture IS the service: the box empties itself."""
    t = 0.16          # wall thickness
    W, D, H = 2.4, 1.9, 1.5
    box("floor", (0, 0, t / 2), (W, D, t), ink, bw=0.045)
    box("wallL", (-W / 2 + t / 2, 0, H / 2), (t, D, H), ink, bw=0.045)
    box("wallR", (W / 2 - t / 2, 0, H / 2), (t, D, H), ink, bw=0.045)
    box("wallB", (0, D / 2 - t / 2, H / 2), (W - t * 2, t, H), ink, bw=0.045)
    box("wallF", (0, -D / 2 + t / 2, H * 0.34), (W - t * 2, t, H * 0.68), ink, bw=0.045)

    # what is left inside, low
    box("rest0", (-0.42, 0.12, 0.42), (0.78, 0.72, 0.56), ink, bw=0.05)
    box("rest1", (0.52, -0.18, 0.34), (0.62, 0.66, 0.42), ink, bw=0.05)

    # the lifted blocks: the idea. In the web piece these animate up and settle back.
    lifts = [
        ("lift0", (0.30, 0.10, 2.05), (0.74, 0.70, 0.62), (0.22, -0.18, 0.42), red),
        ("lift1", (1.32, -0.24, 2.72), (0.56, 0.54, 0.50), (-0.30, 0.26, -0.34), ink),
        ("lift2", (-0.62, -0.30, 2.95), (0.46, 0.46, 0.44), (0.40, 0.18, 0.60), ink),
    ]
    for name, loc, sc, rot, m in lifts:
        o = box(name, loc, sc, m, rot=rot, bw=0.05)
        o["lift"] = True
    return 0.0


def stage(kind):
    bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, 0))
    gp = bpy.context.object
    gp.name = "ground"
    gp.data.materials.append(mat("bg", (0.90, 0.91, 0.93, 1), 0.0, 0.5))

    def lamp(name, loc, energy, size):
        d = bpy.data.lights.new(name, "AREA")
        d.energy = energy
        d.size = size
        o = bpy.data.objects.new(name, d)
        bpy.context.collection.objects.link(o)
        o.location = loc
        c = o.constraints.new("TRACK_TO")
        c.track_axis = "TRACK_NEGATIVE_Z"
        c.up_axis = "UP_Y"
        return o

    key = lamp("key", (-3.4, -4.8, 5.6), 1700, 7)
    rim = lamp("rim", (5.0, 4.6, 3.4), 2600, 4)
    fill = lamp("fill", (4.4, -5.4, 2.2), 420, 10)
    tgt = bpy.data.objects.new("tgt", None)
    bpy.context.collection.objects.link(tgt)
    tgt.location = (0, 0, 1.2 if kind == "A" else 1.4)
    for l in (key, rim, fill):
        l.constraints[0].target = tgt

    w = bpy.context.scene.world or bpy.data.worlds.new("W")
    bpy.context.scene.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.87, 0.89, 0.92, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 1.2

    cam_loc = (-11.4, -13.6, 6.6) if kind == "A" else (-10.2, -12.4, 7.0)
    bpy.ops.object.camera_add(location=cam_loc)
    cam = bpy.context.object
    cam.data.lens = 100
    c = cam.constraints.new("TRACK_TO")
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    c.target = tgt
    bpy.context.scene.camera = cam

    s = bpy.context.scene
    s.render.engine = "BLENDER_EEVEE"
    s.render.resolution_x = 1200
    s.render.resolution_y = 900
    try:
        s.eevee.use_raytracing = True
        s.eevee.taa_render_samples = 96
    except Exception:
        pass
    s.view_settings.look = "AgX - Medium High Contrast"
    s.view_settings.exposure = 0.4


reset()
ink, red = mat("ink", INK), mat("red", RED, metallic=0.5, rough=0.33)
(piece_a if PIECE == "A" else piece_b)(ink, red)
stage(PIECE)
os.makedirs(OUT, exist_ok=True)
bpy.context.scene.render.filepath = os.path.join(OUT, f"piece{PIECE}.png")
bpy.ops.render.render(write_still=True)

if WANT_GLB:
    bpy.context.scene.render.film_transparent = True
    bpy.data.objects["ground"].hide_render = True
    bpy.ops.object.select_all(action="SELECT")
    bpy.data.objects["ground"].select_set(False)
    for n in ("key", "rim", "fill", "tgt"):
        if n in bpy.data.objects:
            bpy.data.objects[n].select_set(False)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, f"piece{PIECE}.glb"),
                              export_format="GLB", use_selection=True,
                              export_draco_mesh_compression_enable=True, export_apply=True)
print("DONE", PIECE)
