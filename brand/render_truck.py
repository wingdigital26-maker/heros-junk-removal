"""
render_truck.py -- studio render of the Hero's truck mark: navy metal body,
terracotta accent, three-quarter hero angle, on a transparent or soft-stone
gradient backdrop, matching the lighting rig convention from
wing-logo-3d/blender-pipeline/render_assets_v2.py (area-light 3-point,
AgX view transform, Cycles).

Run:
  blender.exe -b --factory-startup -P render_truck.py -- \
    --glb out/truck.glb --out renders/truck_v1.png --res 900 --bg transparent
"""
import bpy
import sys
import math
import os

def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    d = {"glb": "out/truck.glb", "out": "renders/truck.png", "res": 900, "bg": "transparent"}
    i = 0
    while i < len(argv):
        a = argv[i]
        key = a.lstrip("-")
        if key in d and i + 1 < len(argv):
            val = argv[i + 1]
            d[key] = int(val) if key == "res" else val
            i += 2
        else:
            i += 1
    return d

ARGS = parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
GLB = os.path.join(HERE, ARGS["glb"]) if not os.path.isabs(ARGS["glb"]) else ARGS["glb"]
OUT = os.path.join(HERE, ARGS["out"]) if not os.path.isabs(ARGS["out"]) else ARGS["out"]
os.makedirs(os.path.dirname(OUT), exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 200
scene.render.resolution_x = ARGS["res"]
scene.render.resolution_y = int(ARGS["res"] * 0.72)
scene.render.film_transparent = (ARGS["bg"] == "transparent")
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.image_settings.color_depth = '8'

try:
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
except Exception as ex:
    print(f"[render_truck] WARN: AgX look unavailable ({ex})")

try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for backend in ('ONEAPI', 'OPTIX', 'CUDA', 'HIP', 'METAL'):
        try:
            prefs.compute_device_type = backend
            prefs.get_devices()
            enabled = [d for d in prefs.devices if d.type == backend]
            if enabled:
                for d in enabled:
                    d.use = True
                scene.cycles.device = 'GPU'
                print(f"[render_truck] backend {backend}: enabled")
                break
        except Exception:
            continue
except Exception as ex:
    print(f"[render_truck] WARN: GPU enable skipped ({ex})")


def hex_rgb(h, a=1.0):
    h = h.lstrip("#")
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (lin(r), lin(g), lin(b), a)


def add_light(name, loc, energy, size, color, target=(0, 0, 0.3)):
    ld = bpy.data.lights.new(name, type='AREA')
    ld.energy = energy
    ld.size = size
    ld.color = color[:3]
    lo = bpy.data.objects.new(name, ld)
    lo.location = loc
    scene.collection.objects.link(lo)
    empty = bpy.data.objects.new(f"{name}_target", None)
    empty.location = target
    scene.collection.objects.link(empty)
    tt = lo.constraints.new('TRACK_TO')
    tt.target = empty
    tt.track_axis = 'TRACK_NEGATIVE_Z'
    tt.up_axis = 'UP_Y'
    return lo


# studio rig: bright soft key upper-left, cool terracotta-warm rim lower-right,
# gentle fill from camera side -- same family as the Wing rig, retuned warmer
# since this body is navy (darker base) with a warm accent, not Wing blue.
world = bpy.data.worlds.new("Studio")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if ARGS["bg"] == "transparent":
    bg.inputs[0].default_value = hex_rgb("EDE7DE")
    bg.inputs[1].default_value = 0.0
else:
    bg.inputs[0].default_value = hex_rgb("EDE7DE")
    bg.inputs[1].default_value = 1.0

add_light("Key", (-2.1, -2.0, 2.8), 900, 1.6, hex_rgb("FFF6EC"))
add_light("Rim", (2.2, 1.6, 1.0), 420, 1.2, hex_rgb("FFB37A"))
add_light("Fill", (0.2, -3.2, 1.8), 140, 3.2, hex_rgb("D9E2F0"))

# ground shadow catcher plane (soft cast shadow like the Wing reference)
bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0))
ground = bpy.context.active_object
ground.is_shadow_catcher = True

# import truck
bpy.ops.import_scene.gltf(filepath=GLB)
truck = None
for o in bpy.context.scene.objects:
    if o.type == 'MESH' and o.name.startswith("Heros"):
        truck = o
        break
if truck is None:
    for o in bpy.context.scene.objects:
        if o.type == 'MESH' and o != ground:
            truck = o
            break

# three-quarter hero angle: camera off to front-left-above, looking down slightly
cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 50
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
cam.location = (-4.6, -5.6, 2.7)
empty = bpy.data.objects.new("CamTarget", None)
empty.location = (0, 0, 0.3)
scene.collection.objects.link(empty)
tt = cam.constraints.new('TRACK_TO')
tt.target = empty
tt.track_axis = 'TRACK_NEGATIVE_Z'
tt.up_axis = 'UP_Y'

scene.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print(f"[render_truck] wrote {OUT} ({os.path.getsize(OUT)} bytes)")
