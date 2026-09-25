"""
Hero's Junk Removal - ONE-shape cube morph logo.
24 small rounded cubes, fixed colours, four formations (house / truck / couch / H).
Run:
  blender -b --factory-startup -P morph.py -- --mode stills
  blender -b --factory-startup -P morph.py -- --mode video
"""
import bpy, math, sys, os, json, random
from mathutils import Vector

# ---------------------------------------------------------------- args ----
argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
MODE = "stills"
for i, a in enumerate(argv):
    if a == "--mode" and i + 1 < len(argv):
        MODE = argv[i + 1]

OUT = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------- palette ----
def hex_to_lin(h):
    h = h.lstrip('#')
    r, g, b = (int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))
    def to_lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (to_lin(r), to_lin(g), to_lin(b), 1.0)

PAL = {
    "RED":    hex_to_lin("#B32A25"),
    "CORAL":  hex_to_lin("#E0483E"),
    "YELLOW": hex_to_lin("#F2B33D"),
    "INK":    hex_to_lin("#1C1917"),
    "CREAM":  hex_to_lin("#F7F5F1"),
}

# ---------------------------------------------------------- cube layout ---
# Each formation = dict of color -> list of (col, row) grid cells.
# Index order WITHIN a color list is the fixed identity of that cube across
# every formation (cube #0 of RED is always the same physical cube).

# Stepped gable house: roof pops in red, coral walls, yellow door, ink window.
HOUSE = {
    "RED":    [(3,5),(2,4),(3,4),(4,4),(1,3),(2,3),(3,3),(4,3),(5,3)],
    "CORAL":  [(1,0),(4,0),(5,0),(1,1),(1,2),(2,2),(3,2)],
    "YELLOW": [(2,0),(3,0),(2,1),(3,1)],
    "INK":    [(4,1),(5,1),(4,2),(5,2)],
}

# Boxy pickup: solid red cab w/ yellow windshield band, flat coral bed,
# ink wheels sitting right on the ground line.
TRUCK = {
    "RED":    [(0,1),(1,1),(2,1),(3,1),(1,2),(2,2),(3,2),(1,3),(3,3)],
    "CORAL":  [(4,1),(5,1),(6,1),(7,1),(8,1),(4,2),(5,2)],
    "YELLOW": [(2,3),(1,4),(2,4),(3,4)],
    "INK":    [(1,0),(2,0),(6,0),(7,0)],
}

# Couch: low seat, taller yellow/coral backrest, arms clearly tallest, short ink feet.
COUCH = {
    "RED":    [(0,0),(0,1),(0,2),(0,3),(6,0),(6,1),(6,2),(6,3),(3,3)],
    "CORAL":  [(1,0),(2,0),(3,0),(4,0),(5,0),(2,2),(4,2)],
    "YELLOW": [(2,1),(3,1),(4,1),(3,2)],
    "INK":    [(0,-1),(2,-1),(4,-1),(6,-1)],
}

# Real H: two tall bars, ONE clean crossbar with genuine open space above/below,
# leftover cubes become a small ground-line accent under the letter.
LETTER_H = {
    "RED":    [(0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(0,7),(0,8)],
    "CORAL":  [(4,1),(4,2),(4,3),(4,4),(4,5),(4,6),(4,7)],
    "YELLOW": [(1,4),(2,4),(3,4),(2,-1)],
    "INK":    [(4,0),(4,8),(1,-1),(3,-1)],
}

FORMATIONS = [
    ("house", HOUSE),
    ("truck", TRUCK),
    ("couch", COUCH),
    ("h", LETTER_H),
]

COLOR_ORDER = ["RED", "CORAL", "YELLOW", "INK"]
N_TOTAL = sum(len(HOUSE[c]) for c in COLOR_ORDER)
for name, f in FORMATIONS:
    n = sum(len(f[c]) for c in COLOR_ORDER)
    assert n == N_TOTAL, f"{name} has {n} cubes, expected {N_TOTAL}"
    for c in COLOR_ORDER:
        assert len(f[c]) == len(HOUSE[c]), f"{name}/{c} count mismatch"
    cells = [cell for c in COLOR_ORDER for cell in f[c]]
    assert len(cells) == len(set(cells)), f"{name} has overlapping cells"

PITCH = 1.05

def grid_to_world(formation):
    """flatten formation dict to N_TOTAL (x,y,z) world positions, centered."""
    pts = []
    colors = []
    for c in COLOR_ORDER:
        for (col, row) in formation[c]:
            pts.append(Vector((col * PITCH, 0.0, row * PITCH)))
            colors.append(c)
    xs = [p.x for p in pts]; zs = [p.z for p in pts]
    cx = (min(xs) + max(xs)) / 2.0
    cz = (min(zs) + max(zs)) / 2.0
    pts = [Vector((p.x - cx, 0.0, p.z - cz)) for p in pts]
    return pts, colors

WORLD = {}
CUBE_COLORS = None
for name, f in FORMATIONS:
    pts, colors = grid_to_world(f)
    WORLD[name] = pts
    CUBE_COLORS = colors  # identical across formations by construction

# ------------------------------------------------------------- scene -----
def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for coll in list(bpy.data.collections):
        bpy.data.collections.remove(coll)

def set_engine():
    scene = bpy.context.scene
    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except Exception:
        try:
            scene.render.engine = 'BLENDER_EEVEE'
        except Exception:
            pass
    try:
        scene.view_settings.view_transform = 'AGX'
    except Exception:
        pass
    scene.render.film_transparent = True

def make_material(name, rgba, rough=0.28):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba
    if "Roughness" in bsdf.inputs:
        bsdf.inputs["Roughness"].default_value = rough
    for key in ("IOR", "IOR Level"):
        if key in bsdf.inputs:
            try:
                bsdf.inputs[key].default_value = 1.45
            except Exception:
                pass
    for key in ("Coat Weight", "Clearcoat"):
        if key in bsdf.inputs:
            try:
                bsdf.inputs[key].default_value = 0.25
            except Exception:
                pass
    return mat

def make_cubes():
    mats = {c: make_material("mat_" + c, PAL[c]) for c in COLOR_ORDER}
    cubes = []
    size = 0.86
    bpy.ops.mesh.primitive_cube_add(size=size, location=(0, 0, 0))
    base = bpy.context.active_object
    base.name = "cube_base"
    bpy.ops.object.shade_smooth()
    bev = base.modifiers.new("bevel", 'BEVEL')
    bev.width = 0.16
    bev.segments = 4
    bev.limit_method = 'ANGLE'
    bev.angle_limit = math.radians(35)
    base.data.materials.append(mats["RED"])
    cubes.append(base)
    for i in range(1, N_TOTAL):
        ob = base.copy()
        ob.data = base.data.copy()
        ob.name = f"cube_{i:02d}"
        bpy.context.collection.objects.link(ob)
        cubes.append(ob)
    for i, ob in enumerate(cubes):
        color = CUBE_COLORS[i]
        ob.data.materials.clear()
        ob.data.materials.append(mats[color])
        ob.location = WORLD["house"][i]
    return cubes

def look_at(ob, target, loc):
    ob.location = loc
    direction = (Vector(target) - Vector(loc))
    quat = direction.to_track_quat('-Z', 'Y')
    ob.rotation_euler = quat.to_euler()

def make_camera():
    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = 12.5
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.collection.objects.link(cam)
    look_at(cam, (0, 0, 0), (7.6, -10.6, 6.4))
    bpy.context.scene.camera = cam
    return cam

def make_lights():
    def area(name, loc, target, energy, size, color=(1, 1, 1)):
        d = bpy.data.lights.new(name, 'AREA')
        d.energy = energy
        d.size = size
        d.color = color
        ob = bpy.data.objects.new(name, d)
        bpy.context.collection.objects.link(ob)
        look_at(ob, target, loc)
        return ob
    area("key", (5.5, -7.5, 8.5), (0, 0, 0.6), 900, 6.0, (1.0, 0.97, 0.9))
    area("rim", (-4.5, 6.0, 6.5), (0, 0, 0.6), 500, 5.0, (1.0, 0.55, 0.45))
    area("fill", (-3.0, -6.0, 1.5), (0, 0, 0.6), 140, 6.0, (0.85, 0.9, 1.0))
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("world")
        bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.5, 0.5, 0.52, 1.0)
        bg.inputs[1].default_value = 0.25

def make_shadow_blob():
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 0.35, -4.1))
    plane = bpy.context.active_object
    plane.name = "shadow_blob"
    plane.rotation_euler = (math.radians(90), 0, 0)
    plane.scale = (5.6, 2.4, 1.0)
    mat = bpy.data.materials.new("shadow_mat")
    mat.use_nodes = True
    for attr, val in (("blend_method", 'BLEND'), ("surface_render_method", 'BLENDED'),
                      ("shadow_method", 'NONE'), ("show_transparent_back", False)):
        try:
            setattr(mat, attr, val)
        except Exception:
            pass
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    transp = nt.nodes.new("ShaderNodeBsdfTransparent")
    diff = nt.nodes.new("ShaderNodeBsdfDiffuse")
    diff.inputs["Color"].default_value = (0.02, 0.015, 0.012, 1.0)
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (0, 0, 0, 0)
    grad = nt.nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = 'QUADRATIC_SPHERE'
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs['Location'].default_value = (0.5, 0.5, 0.5)
    mapping.inputs['Scale'].default_value = (2.0, 2.0, 2.0)
    nt.links.new(coord.outputs['Generated'], mapping.inputs['Vector'])
    nt.links.new(mapping.outputs['Vector'], grad.inputs['Vector'])
    soften = nt.nodes.new("ShaderNodeMath")
    soften.operation = 'MULTIPLY'
    soften.inputs[1].default_value = 0.22
    nt.links.new(grad.outputs['Color'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Alpha'], soften.inputs[0])
    nt.links.new(soften.outputs['Value'], mix.inputs['Fac'])
    nt.links.new(transp.outputs['BSDF'], mix.inputs[1])
    nt.links.new(diff.outputs['BSDF'], mix.inputs[2])
    nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
    plane.data.materials.append(mat)
    return plane

def set_shadow_blob_for(plane, name):
    if plane is None:
        return
    pts = WORLD[name]
    zmin = min(p.z for p in pts)
    xspan = max(p.x for p in pts) - min(p.x for p in pts)
    plane.location = (0, 0.35, zmin - 0.55)
    plane.scale = (max(3.4, xspan * 0.72), 2.6, 1.0)

# --------------------------------------------------------------- build ---
clear_scene()
set_engine()
cubes = make_cubes()
cam = make_camera()
make_lights()
blob = None  # no fake shadow plane -- transparent film only, clean silhouette

scene = bpy.context.scene
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
try:
    scene.eevee.taa_render_samples = 64
except Exception:
    pass
try:
    scene.eevee.use_gtao = True
except Exception:
    pass

# ------------------------------------------------------------- stills ----
def render_stills():
    for idx, (name, _) in enumerate(FORMATIONS, start=1):
        for i, ob in enumerate(cubes):
            ob.location = WORLD[name][i]
            ob.rotation_euler = (0, 0, 0)
        set_shadow_blob_for(blob, name)
        scene.render.filepath = os.path.join(OUT, f"form-{idx}-{name}.png")
        bpy.ops.render.render(write_still=True)
        print("rendered", scene.render.filepath)

def write_shapes_json():
    data = {
        "pitch": PITCH,
        "cube_size": 0.86,
        "colors": {c: PAL[c][:3] for c in COLOR_ORDER},
        "cube_colors": CUBE_COLORS,
        "formations": {
            name: [[round(p.x, 4), round(p.y, 4), round(p.z, 4)] for p in WORLD[name]]
            for name, _ in FORMATIONS
        },
        "order": [n for n, _ in FORMATIONS],
    }
    with open(os.path.join(OUT, "shapes.json"), "w") as f:
        json.dump(data, f, indent=2)
    print("wrote shapes.json")

# -------------------------------------------------------------- video ----
FPS = 24
HOLD = 0.8
MOVE = 0.9
ARC_H = 1.1
STAGGER = 0.14

def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)

random.seed(7)
CUBE_JITTER = [random.uniform(-1, 1) for _ in range(N_TOTAL)]

def render_video():
    scene.render.resolution_x = 720
    scene.render.resolution_y = 720
    try:
        scene.eevee.taa_render_samples = 24
    except Exception:
        pass
    frames_dir = os.path.join(OUT, "frames")
    os.makedirs(frames_dir, exist_ok=True)

    segs = []
    seq = [WORLD[n] for n, _ in FORMATIONS] + [WORLD[FORMATIONS[0][0]]]
    seq_names = [n for n, _ in FORMATIONS] + [FORMATIONS[0][0]]
    for i in range(len(FORMATIONS)):
        segs.append(("hold", seq[i], seq[i], HOLD, seq_names[i]))
        segs.append(("move", seq[i], seq[i + 1], MOVE, seq_names[i] + "->" + seq_names[i+1]))

    total_time = sum(s[3] for s in segs)
    n_frames = int(round(total_time * FPS))
    print(f"total {total_time:.2f}s -> {n_frames} frames")

    frame_idx = 0
    t_acc = 0.0
    for kind, start_pts, end_pts, dur, label in segs:
        n_this = max(1, int(round(dur * FPS)))
        for k in range(n_this):
            local_t = k / max(1, n_this - 1) if n_this > 1 else 1.0
            for i, ob in enumerate(cubes):
                if kind == "hold":
                    ob.location = start_pts[i]
                    ob.rotation_euler = (0, 0, 0)
                else:
                    st = STAGGER * (0.4 + 0.6 * (i / N_TOTAL))
                    tt = (local_t - 0) / (1 - st) if st < 1 else local_t
                    tt = max(0.0, min(1.0, (local_t - st * 0.0)))
                    # simple per-cube phase offset within the move window
                    phase = max(0.0, min(1.0, (k / max(1, n_this - 1)) - 0))
                    e = ease(max(0.0, min(1.0, (phase * (1 + STAGGER) - STAGGER * (i / N_TOTAL)))))
                    a = start_pts[i]
                    b = end_pts[i]
                    pos = a.lerp(b, e)
                    lift = ARC_H * math.sin(math.pi * e)
                    pos = Vector((pos.x, pos.y - lift * 0.35, pos.z + lift))
                    ob.location = pos
                    wob = math.sin(math.pi * e) * 0.35 * CUBE_JITTER[i]
                    ob.rotation_euler = (wob * 0.6, wob, wob * 0.4)
            set_shadow_blob_for(blob, seq_names[0])
            scene.render.filepath = os.path.join(frames_dir, f"f{frame_idx:04d}.png")
            bpy.ops.render.render(write_still=True)
            frame_idx += 1
        t_acc += dur
    print("rendered", frame_idx, "frames to", frames_dir)

if MODE == "stills":
    render_stills()
    write_shapes_json()
elif MODE == "video":
    render_video()
else:
    render_stills()
    write_shapes_json()
    render_video()

print("DONE mode=", MODE)
