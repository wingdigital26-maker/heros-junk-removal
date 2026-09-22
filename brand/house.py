"""Hero's Junk Removal - THE HOUSE. The interactive hero piece and the logo, one idea.

A small house that empties itself: blocks lift out through the open door and rise away.
That gesture is the service, so the mark and the animation are the same thing.

Built better than the earlier "room corner":
  - a real house volume with a pitched roof, so it reads as a HOUSE at a glance
  - a proper doorway with depth and a recessed reveal, not a slot in a wall
  - window recesses to give the walls scale and catch the rim light
  - blocks streaming OUT THROUGH the door in an arc, shrinking as they go
  - matte walls against metallic blocks, so the two materials separate
  - a real ground plane shadow, staged like the Wing Digital sculpture

  blender --background --python house.py -- <outdir> [glb] [hero]
"""
import bpy, sys, math, os

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else os.path.dirname(os.path.abspath(__file__))
WANT_GLB = "glb" in argv
WANT_HERO = "hero" in argv

INK = (0.020, 0.030, 0.050, 1.0)      # near-black navy, the blocks
WALL = (0.062, 0.076, 0.098, 1.0)     # matte slate, the house
ROOF = (0.030, 0.038, 0.052, 1.0)     # darker, so the roof reads separately
RED = (0.55, 0.045, 0.035, 1.0)       # the single accent


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


def bevel(ob, width=0.030, segs=4):
    m = ob.modifiers.new("bev", "BEVEL")
    m.width = width
    m.segments = segs
    m.limit_method = "ANGLE"
    m.angle_limit = math.radians(38)
    m.harden_normals = True
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def box(name, loc, scale, material, rot=(0, 0, 0), bw=0.030):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(material)
    bevel(o, bw)
    return o


def prism(name, loc, w, d, h, material, bw=0.030):
    """A closed triangular prism for the roof. Built face by face so it is solid:
    an open shell here rendered as flat sails on an earlier attempt."""
    import bmesh
    me = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    bm = bmesh.new()
    hw, hd = w / 2, d / 2
    pts = [(-hw, -hd, 0), (hw, -hd, 0), (0, -hd, h),
           (-hw, hd, 0), (hw, hd, 0), (0, hd, h)]
    v = [bm.verts.new(p) for p in pts]
    bm.faces.new((v[0], v[1], v[2]))
    bm.faces.new((v[5], v[4], v[3]))
    bm.faces.new((v[0], v[3], v[4], v[1]))     # floor
    bm.faces.new((v[0], v[2], v[5], v[3]))     # left slope
    bm.faces.new((v[1], v[4], v[5], v[2]))     # right slope
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    ob.location = loc
    ob.data.materials.append(material)
    bevel(ob, bw)
    return ob


def build(wall, roof, ink, red):
    W, D, H = 2.30, 1.80, 1.45           # house body
    T = 0.14                             # wall thickness
    DOOR_W, DOOR_H = 0.68, 1.00

    # floor slab, slightly proud so the house sits on a base
    box("base", (0, 0, 0.055), (W + 0.16, D + 0.16, 0.11), roof, bw=0.022)

    # back and right walls, solid
    box("wallB", (0, D / 2 - T / 2, H / 2 + 0.11), (W, T, H), wall, bw=0.026)
    box("wallR", (W / 2 - T / 2, 0, H / 2 + 0.11), (T, D, H), wall, bw=0.026)

    # FRONT wall carries the door: two piers plus a lintel, so the opening has real depth
    pier = (W - DOOR_W) / 2
    for i, xx in enumerate((-(DOOR_W / 2 + pier / 2), DOOR_W / 2 + pier / 2)):
        box(f"pier{i}", (xx, -D / 2 + T / 2, H / 2 + 0.11), (pier, T, H), wall, bw=0.026)
    box("lintel", (0, -D / 2 + T / 2, 0.11 + DOOR_H + (H - DOOR_H) / 2),
        (DOOR_W, T, H - DOOR_H), wall, bw=0.026)
    # door reveal: a recessed darker jamb so the opening reads as a doorway, not a gap
    box("reveal", (0, -D / 2 + T * 1.35, 0.11 + DOOR_H / 2),
        (DOOR_W - 0.06, T * 0.5, DOOR_H), roof, bw=0.014)

    # window recesses on the two solid walls: they give the house scale
    box("winR", (W / 2 - T * 0.45, -0.28, 0.11 + H * 0.60), (T * 0.5, 0.52, 0.42), roof, bw=0.014)
    box("winB", (0.52, D / 2 - T * 0.45, 0.11 + H * 0.60), (0.52, T * 0.5, 0.42), roof, bw=0.014)

    # pitched roof, overhanging so it casts a line across the facade
    prism("roof", (0, 0, 0.11 + H), W + 0.22, D + 0.20, 0.82, roof, bw=0.026)

    # one block still inside, visible through the door
    box("inside", (0.10, 0.16, 0.11 + 0.30), (0.52, 0.48, 0.46), ink, bw=0.028)

    # THE GESTURE: blocks leaving through the door in an arc, shrinking as they go.
    # Named lift0..lift3 so the web piece can animate exactly these.
    arc = [
        (-1.35, -1.55, 0.72, 0.50, False),
        (-2.25, -2.05, 1.52, 0.42, True),      # the accent block
        (-3.05, -2.45, 2.42, 0.33, False),
        (-3.65, -2.75, 3.30, 0.25, False),
    ]
    for i, (x, y, z, sc, accent) in enumerate(arc):
        box(f"lift{i}", (x, y, z), (sc, sc * 0.92, sc * 0.88),
            red if accent else ink,
            rot=(0.34 - i * 0.16, -0.22 + i * 0.18, 0.46 - i * 0.24), bw=0.026)


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
    tgt.location = (-0.85, -0.70, 1.35)
    for l in (lamp("key", (-4.0, -5.4, 6.0), 2000, 8),
              lamp("rim", (5.4, 4.8, 3.6), 3000, 4.5),
              lamp("fill", (4.6, -5.6, 2.4), 480, 11)):
        l.constraints[0].target = tgt

    w = bpy.context.scene.world or bpy.data.worlds.new("W")
    bpy.context.scene.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.87, 0.89, 0.92, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 1.25

    bpy.ops.object.camera_add(location=(-10.8, -12.8, 6.4))
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
        s.eevee.taa_render_samples = 128 if hero else 80
    except Exception:
        pass
    s.view_settings.look = "AgX - Medium High Contrast"
    s.view_settings.exposure = 0.42


reset()
wall = mat("wall", WALL, metallic=0.06, rough=0.62)   # matte: the house
roof = mat("roof", ROOF, metallic=0.10, rough=0.55)
ink = mat("ink", INK, metallic=0.88, rough=0.26)      # metallic: the blocks
red = mat("red", RED, metallic=0.45, rough=0.32)
build(wall, roof, ink, red)
stage(hero=WANT_HERO)

os.makedirs(OUT, exist_ok=True)
bpy.context.scene.render.filepath = os.path.join(OUT, "house-hero.png" if WANT_HERO else "house.png")
bpy.ops.render.render(write_still=True)

if WANT_GLB:
    bpy.ops.object.select_all(action="SELECT")
    for n in ("ground", "key", "rim", "fill", "tgt"):
        if n in bpy.data.objects:
            bpy.data.objects[n].select_set(False)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "house.glb"),
                              export_format="GLB", use_selection=True,
                              export_draco_mesh_compression_enable=True, export_apply=True)
print("DONE house")
