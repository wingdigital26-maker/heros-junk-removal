"""Hero's Junk Removal - THE HOUSE. The interactive hero piece and the logo, one idea.

A small house that empties itself: blocks lift out through the open door and rise away.
That gesture is the service, so the mark and the animation are the same thing.

v2 (2026-09-22), six renders judged one by one (a chimney was tried in v5 and reverted: noise at 32px):
  - a CLOSED house: four walls, so it reads as a solid object, not a cut-open dollhouse
  - the door is on the right face, the blocks leave to the right and up: the same layout as the
    flat mark (door bottom right, block to the right), so poster, live scene and logo agree
  - the blocks leave THROUGH the doorway and clear the silhouette instead of hovering over the facade
  - a deeper doorway: the door wall is thicker, with a stone threshold in front of it
  - a wider roof overhang with a fascia board, a chamfered plinth, one window on the front
  - matte slate walls that stay dark under the stage light; a deeper, less pink accent red
  - lower world light and exposure so the walls read as a solid, not pale grey

  blender --background --python house.py -- <outdir> [glb] [hero]
"""
import bpy, sys, math, os

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else os.path.dirname(os.path.abspath(__file__))
WANT_GLB = "glb" in argv
WANT_HERO = "hero" in argv

INK = (0.018, 0.026, 0.045, 1.0)      # near-black navy, the blocks
WALL = (0.055, 0.066, 0.086, 1.0)     # matte slate, the house
ROOF = (0.024, 0.030, 0.042, 1.0)     # darker, so the roof reads separately
RED = (0.34, 0.022, 0.030, 1.0)       # the single accent, deep not pink

W, D, H = 2.30, 1.80, 1.45            # house body
T = 0.14                              # wall thickness
TD = 0.24                             # the door wall is thicker: the doorway gets real depth
DOOR_W, DOOR_H = 0.70, 1.02
BASE_H = 0.11
OVER = 0.32                           # roof overhang


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, rgba, metallic=0.85, rough=0.28):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = rgba
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    return m


def bevel(ob, width=0.030, segs=3):
    m = ob.modifiers.new("bev", "BEVEL")
    m.width = width
    m.segments = segs
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(38)
    m.harden_normals = True
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def box(name, loc, scale, material, rot=(0, 0, 0), bw=0.030, segs=3):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(material)
    bevel(o, bw, segs)
    return o


def prism(name, loc, w, d, h, material, bw=0.030):
    """A closed triangular prism for the roof, ridge running along X."""
    import bmesh
    me = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    bm = bmesh.new()
    hw, hd = w / 2, d / 2
    pts = [(-hw, -hd, 0), (hw, -hd, 0), (hw, 0, h),
           (-hw, hd, 0), (hw, hd, 0), (-hw, 0, h)]
    v = [bm.verts.new(p) for p in pts]
    bm.faces.new((v[0], v[1], v[2], v[5]))     # front slope
    bm.faces.new((v[4], v[3], v[5], v[2]))     # back slope
    bm.faces.new((v[0], v[3], v[4], v[1]))     # underside
    bm.faces.new((v[0], v[5], v[3]))           # left gable
    bm.faces.new((v[1], v[4], v[2]))           # right gable
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    ob.location = loc
    ob.data.materials.append(material)
    bevel(ob, bw)
    return ob


def build(wall, roof, ink, red):
    z0 = BASE_H
    # chamfered plinth the house sits on
    box("base", (0.09, 0, BASE_H / 2), (W + 0.38, D + 0.20, BASE_H), roof, bw=0.034, segs=2)   # runs out past the door: the threshold

    # three solid walls: front (-Y), back (+Y), left (-X)
    box("wallF", (0, -D / 2 + T / 2, z0 + H / 2), (W - 2 * T, T, H), wall, bw=0.024)
    box("wallB", (0, D / 2 - T / 2, z0 + H / 2), (W - 2 * T, T, H), wall, bw=0.024)
    box("wallL", (-W / 2 + T / 2, 0, z0 + H / 2), (T, D, H), wall, bw=0.024)

    # RIGHT wall carries the door: two piers and a lintel, thicker than the others so the opening has depth
    pier = (D - DOOR_W) / 2
    xr = W / 2 - TD / 2
    for i, yy in enumerate((-(DOOR_W / 2 + pier / 2), DOOR_W / 2 + pier / 2)):
        box(f"pier{i}", (xr, yy, z0 + H / 2), (TD, pier, H), wall, bw=0.024)
    box("lintel", (xr, 0, z0 + DOOR_H + (H - DOOR_H) / 2), (TD, DOOR_W, H - DOOR_H), wall, bw=0.024)
    # dark reveal set back in the opening, and a threshold stone in front of it
    box("reveal", (W / 2 - TD - 0.03, 0, z0 + DOOR_H / 2), (0.06, DOOR_W - 0.05, DOOR_H), roof, bw=0.012, segs=2)

    # one window on the front wall, and a small one beside the door
    box("winF", (-0.40, -D / 2 - 0.012, z0 + H * 0.58), (0.50, 0.03, 0.44), ink, bw=0.008, segs=2)

    # pitched roof with a real overhang, and a fascia board along the eaves so the edge catches light
    roof_h = 0.86
    prism("roof", (0, 0, z0 + H - 0.02), W + 2 * OVER, D + 2 * OVER, roof_h, roof, bw=0.028)
    for s in (-1, 1):
        box(f"fascia{'F' if s < 0 else 'B'}", (0, s * (D / 2 + OVER - 0.03), z0 + H - 0.06),
            (W + 2 * OVER - 0.02, 0.06, 0.12), wall, bw=0.012, segs=2)

    # one block still inside, seen through the door
    box("inside", (0.72, -0.02, z0 + 0.26), (0.46, 0.46, 0.52), ink, rot=(0, 0, 0.35), bw=0.028)

    # THE GESTURE: blocks leaving through the door to the right and up, shrinking as they go.
    # Named lift0..lift3 so the web piece animates exactly these.
    arc = [
        (2.42, -0.58, 0.80, 0.50, False),
        (2.92, -0.78, 1.62, 0.42, True),      # the accent block
        (3.28, -0.92, 2.44, 0.33, False),
        (3.52, -1.00, 3.16, 0.25, False),
    ]
    for i, (x, y, z, sc, accent) in enumerate(arc):
        box(f"lift{i}", (x, y, z), (sc, sc * 0.92, sc * 0.88),
            red if accent else ink,
            rot=(0.30 - i * 0.14, 0.20 - i * 0.16, -0.40 + i * 0.22), bw=0.026)


def stage(hero=False):
    if not hero:
        bpy.ops.mesh.primitive_plane_add(size=90, location=(0, 0, 0))
        gp = bpy.context.object
        gp.name = "ground"
        gp.data.materials.append(mat("bg", (0.905, 0.915, 0.935, 1), 0.0, 0.5))

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
    # key front-right-high (the door side), rim back-left so the roof ridge and eaves get an edge, soft fill front-left
    for l in (lamp("key", (4.6, -5.6, 6.2), 1500, 7),
              lamp("rim", (-5.2, 4.8, 3.8), 2600, 4.5),
              lamp("fill", (-4.8, -5.4, 2.2), 380, 11)):
        l.constraints[0].target = tgt

    w = bpy.context.scene.world or bpy.data.worlds.new("W")
    bpy.context.scene.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.80, 0.83, 0.88, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.55

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
    s.render.film_transparent = hero
    try:
        s.eevee.use_raytracing = True
        s.eevee.taa_render_samples = 128 if hero else 64
    except Exception:
        pass
    s.view_settings.look = "AgX - Medium High Contrast"
    s.view_settings.exposure = 0.10


reset()
wall = mat("wall", WALL, metallic=0.04, rough=0.66)   # matte: the house
roof = mat("roof", ROOF, metallic=0.08, rough=0.58)
ink = mat("ink", INK, metallic=0.80, rough=0.36)      # metallic: the blocks
red = mat("red", RED, metallic=0.35, rough=0.38)
build(wall, roof, ink, red)
stage(hero=WANT_HERO)

os.makedirs(OUT, exist_ok=True)
bpy.context.scene.render.filepath = os.path.join(OUT, "house-hero.png" if WANT_HERO else "house.png")
bpy.ops.render.render(write_still=True)

if WANT_GLB:
    bpy.ops.object.select_all(action="SELECT")
    for n in ("ground", "key", "rim", "fill", "tgt", "Camera"):
        if n in bpy.data.objects:
            bpy.data.objects[n].select_set(False)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "house.glb"),
                              export_format="GLB", use_selection=True,
                              export_draco_mesh_compression_enable=True, export_apply=True)
    tris = sum(len(p.vertices) - 2 for o in bpy.data.objects if o.type == "MESH" and o.name != "ground"
               for p in o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.polygons)
    print("TRIS", tris)
print("DONE house")
