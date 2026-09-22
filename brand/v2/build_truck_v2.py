"""
build_truck_v2.py -- Hero's Junk Removal truck mark, take 2.
Fixes vs build_truck.py: long low stance, heavy bevels via subsurf-free bevel modifier
with more segments, wheels with tyre+recessed hub as two materials/radii, studio 3-point
lighting + HDRI-ish world gradient, Cycles render, terracotta on ONE element only.

Run:
  blender.exe -b --python build_truck_v2.py -- --out v2/renders/iter1.png --variant 1 \
    --tip 22 --stance long --abstraction 0.5
"""
import bpy, bmesh, sys, math, os, json
from mathutils import Vector

def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    d = {"out": "renders/iter1.png", "variant": "1", "tip": 20.0,
         "stance": "long", "abstraction": 0.5, "glb": "", "render": "1"}
    i = 0
    while i < len(argv):
        a = argv[i]; key = a.lstrip("-").replace("-", "_")
        if key in d and i + 1 < len(argv):
            val = argv[i+1]
            if key in ("tip", "abstraction"): val = float(val)
            d[key] = val; i += 2
        else: i += 1
    return d

ARGS = parse_args()
HERE = os.path.dirname(os.path.abspath(__file__))
def outpath(p): return p if os.path.isabs(p) else os.path.join(HERE, p)
OUT_PNG = outpath(ARGS["out"])
os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

def hex_rgb(h):
    h = h.lstrip("#")
    r,g,b = int(h[0:2],16)/255, int(h[2:4],16)/255, int(h[4:6],16)/255
    lin = lambda c: c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4
    return (lin(r), lin(g), lin(b), 1.0)

def make_mat(name, color, metallic=0.9, roughness=0.3, var=0.05):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metallic
    # slight roughness variation via noise texture
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 8.0
    mapr = nt.nodes.new("ShaderNodeMapRange")
    mapr.inputs["To Min"].default_value = max(0.0, roughness-var)
    mapr.inputs["To Max"].default_value = roughness+var
    nt.links.new(noise.outputs["Fac"], mapr.inputs["Value"])
    nt.links.new(mapr.outputs["Result"], bsdf.inputs["Roughness"])
    return mat

MAT_NAVY = make_mat("NavyMetal", hex_rgb("1C2B3A"), 0.9, 0.28)
MAT_CLAY = make_mat("ClayAccent", hex_rgb("D97A3D"), 0.85, 0.32, var=0.03)
MAT_CHAR = make_mat("Charcoal", hex_rgb("2B2E32"), 0.85, 0.4)
MAT_TYRE = make_mat("Tyre", hex_rgb("14161A"), 0.1, 0.7)
MAT_HUB = make_mat("Hub", hex_rgb("8A9199"), 0.85, 0.22, var=0.03)
MATS = [MAT_NAVY, MAT_CLAY, MAT_CHAR, MAT_TYRE, MAT_HUB]
MIDX = {"navy":0, "clay":1, "char":2, "tyre":3, "hub":4}

bm = bmesh.new()
face_mat = []

def add_box(cx, cy, cz, sx, sy, sz, mat="navy", rot_y_deg=0.0, pivot=None):
    hx,hy,hz = sx/2, sy/2, sz/2
    local = [(-hx,-hy,-hz),(hx,-hy,-hz),(hx,hy,-hz),(-hx,hy,-hz),
             (-hx,-hy,hz),(hx,-hy,hz),(hx,hy,hz),(-hx,hy,hz)]
    pts = [(cx+p[0], cy+p[1], cz+p[2]) for p in local]
    if rot_y_deg:
        piv = pivot if pivot else (cx,cy,cz)
        rad = math.radians(rot_y_deg); ca,sa = math.cos(rad), math.sin(rad)
        rotated=[]
        for x,y,z in pts:
            dx,dz = x-piv[0], z-piv[2]
            rx = dx*ca+dz*sa; rz=-dx*sa+dz*ca
            rotated.append((piv[0]+rx, y, piv[2]+rz))
        pts = rotated
    verts=[bm.verts.new(p) for p in pts]
    idx=[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
    mi = MIDX[mat]
    for fi in idx:
        bm.faces.new([verts[i] for i in fi]); face_mat.append(mi)
    return verts

def add_wheel(cx, cy, cz, radius, width, mat_tyre="tyre", mat_hub="hub", segs=24):
    """Wheel with distinct tyre ring (outer) and recessed hub disc (inner, inset in Y)."""
    hub_r = radius*0.62
    hub_inset = width*0.18
    # tyre: cylinder
    ring_a, ring_b = [], []
    for k in range(segs):
        a = 2*math.pi*k/segs
        y0, y1 = cy-width/2, cy+width/2
        x = cx+radius*math.cos(a); z = cz+radius*math.sin(a)
        ring_a.append(bm.verts.new((x,y0,z))); ring_b.append(bm.verts.new((x,y1,z)))
    mi = MIDX[mat_tyre]
    bm.faces.new(ring_a[::-1]); face_mat.append(mi)
    bm.faces.new(ring_b); face_mat.append(mi)
    for k in range(segs):
        k2=(k+1)%segs
        bm.faces.new((ring_a[k],ring_a[k2],ring_b[k2],ring_b[k])); face_mat.append(mi)
    # hub: smaller recessed disc, inset from each face -> reads as depth/hub distinction
    for y_face, sign in ((cy-width/2+hub_inset, -1), (cy+width/2-hub_inset, 1)):
        hub_ring = []
        for k in range(segs):
            a = 2*math.pi*k/segs
            x = cx+hub_r*math.cos(a); z = cz+hub_r*math.sin(a)
            hub_ring.append(bm.verts.new((x,y_face,z)))
        center = bm.verts.new((cx, y_face, cz))
        mi2 = MIDX[mat_hub]
        for k in range(segs):
            k2=(k+1)%segs
            f = bm.faces.new((hub_ring[k], hub_ring[k2], center)) if sign>0 else bm.faces.new((hub_ring[k2], hub_ring[k], center))
            face_mat.append(mi2)

# ---------------------------------------------------------------------------
# Layout tuned for a LONG LOW stance (fix #1): longer wheelbase, lower cab,
# smaller wheel radius relative to length, hood extended for purpose.
# ---------------------------------------------------------------------------
STANCE = ARGS["stance"]
TIP = ARGS["tip"]
ABS = ARGS["abstraction"]  # 0 = more literal, 1 = more pure-form

length_mult = 1.35 if STANCE == "long" else 1.0
WHEEL_R = 0.30
WHEEL_W = 0.20
CHASSIS_H = 0.11
CHASSIS_Z = WHEEL_R + CHASSIS_H/2 - 0.015
BODY_BOTTOM = CHASSIS_Z + CHASSIS_H/2
WIDTH = 1.35

HOOD_LEN = 1.05 * length_mult
HOOD_H = 0.46
CAB_LEN = 0.95
CAB_H = 0.50          # LOW cab -- fix for toy proportions
BED_LEN = 1.75 * length_mult
BED_WALL_H = 0.40
BED_FLOOR_H = 0.10

# ONE continuous low unibody from front to rear -- this is the fix for the
# floating/disconnected masses seen in iter1-4. Hood, cab and bed floor are all
# the SAME body block (varying only in height via a stepped top), so nothing
# gaps or floats. Only the bed's side walls are a separate tipping element.
front_x = -(HOOD_LEN + CAB_LEN + BED_LEN)/2 - 0.05
rear_x = front_x + HOOD_LEN + CAB_LEN + BED_LEN
hood_cx = front_x + HOOD_LEN/2
cab_cx = front_x + HOOD_LEN + CAB_LEN/2
bed_cx0 = front_x + HOOD_LEN + CAB_LEN + BED_LEN/2

body_len = HOOD_LEN + CAB_LEN + BED_LEN
body_cx = (front_x + rear_x)/2
# low continuous deck (hood height) running the full length, unibody spine
add_box(body_cx, 0, BODY_BOTTOM+HOOD_H/2, body_len, WIDTH*0.80, HOOD_H, mat="navy")
# cab mass sits directly on top of the deck, flush, no gap
if ABS < 0.7:
    add_box(cab_cx, 0, BODY_BOTTOM+HOOD_H+CAB_H/2, CAB_LEN, WIDTH*0.90, CAB_H, mat="navy")

chassis_len = body_len - 0.2
add_box(body_cx, 0, CHASSIS_Z - 0.02, chassis_len, WIDTH*0.42, CHASSIS_H*0.55, mat="char")

# dump bed side walls -- the ONLY tipping element, hinged at the rear-top edge
# of the unibody deck. THE TIP is the lead gesture.
bed_bottom_z = BODY_BOTTOM + HOOD_H
pivot = (rear_x, 0, bed_bottom_z)
wall_cz = bed_bottom_z + BED_WALL_H/2
add_box(bed_cx0, WIDTH*0.94/2-0.04, wall_cz, BED_LEN, 0.08, BED_WALL_H,
        mat="navy", rot_y_deg=-TIP, pivot=pivot)
add_box(bed_cx0, -(WIDTH*0.94/2-0.04), wall_cz, BED_LEN, 0.08, BED_WALL_H,
        mat="navy", rot_y_deg=-TIP, pivot=pivot)

# single terracotta accent: the top rail of ONE side wall only (asymmetric, confident)
rail_z = bed_bottom_z + BED_WALL_H + 0.03
add_box(bed_cx0, WIDTH*0.94/2-0.04, rail_z, BED_LEN, 0.055, 0.06,
        mat="clay", rot_y_deg=-TIP, pivot=pivot)

# wheels: long wheelbase, front pair under hood, rear pair under bed
wy = WIDTH*0.80/2 + WHEEL_W/2 - 0.01
front_wx = hood_cx + 0.05
rear_wx = bed_cx0 + BED_LEN*0.18
for wx in (front_wx, rear_wx):
    for sign in (1, -1):
        add_wheel(wx, sign*wy, WHEEL_R, WHEEL_R, WHEEL_W)

# ---------------------------------------------------------------------------
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
mesh = bpy.data.meshes.new("HerosTruckMark")
bm.to_mesh(mesh); bm.free(); mesh.validate()
for m in MATS: mesh.materials.append(m)
for i,p in enumerate(mesh.polygons): p.material_index = face_mat[i]

obj = bpy.data.objects.new("HerosTruckMark", mesh)
scene.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

bev = obj.modifiers.new("Bevel", 'BEVEL')
bev.width = 0.028
bev.segments = 4
bev.limit_method = 'ANGLE'
bev.angle_limit = math.radians(35)
bpy.ops.object.modifier_apply(modifier="Bevel")
bpy.ops.object.shade_smooth()
for f in obj.data.polygons: f.use_smooth = True
try:
    obj.data.use_auto_smooth = True
    obj.data.auto_smooth_angle = math.radians(35)
except Exception:
    pass

mesh = obj.data
xs=[v.co.x for v in mesh.vertices]; zs=[v.co.z for v in mesh.vertices]; ys=[v.co.y for v in mesh.vertices]
h = max(zs)-min(zs); cx_all=(max(xs)+min(xs))/2; cy_all=(max(ys)+min(ys))/2
scale = 1.0/h
for v in mesh.vertices:
    v.co.x=(v.co.x-cx_all)*scale; v.co.y=(v.co.y-cy_all)*scale; v.co.z=v.co.z*scale
mesh.update()

n_tris = sum(len(p.vertices)-2 for p in mesh.polygons)

# ---------------------------------------------------------------------------
# Ground plane (for contact shadow) + studio lighting rig + Cycles
# ---------------------------------------------------------------------------
bpy.ops.mesh.primitive_plane_add(size=20, location=(0,0,0))
ground = bpy.context.active_object
ground.name = "Ground"
gmat = bpy.data.materials.new("GroundMat")
gmat.use_nodes = True
gmat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.93,0.93,0.94,1)
gmat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
ground.data.materials.append(gmat)

world = bpy.data.worlds.new("Studio")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.80,0.81,0.83,1)
bg.inputs["Strength"].default_value = 1.0

def add_light(name, ltype, loc, energy, size=1.0, rot=None):
    d = bpy.data.lights.new(name, ltype)
    d.energy = energy
    if ltype == 'AREA':
        d.size = size
    o = bpy.data.objects.new(name, d)
    o.location = loc
    if rot: o.rotation_euler = rot
    scene.collection.objects.link(o)
    return o

add_light("Key", 'AREA', (2.4, -2.6, 2.4), 900, size=1.6, rot=(math.radians(55), 0, math.radians(35)))
add_light("Rim", 'AREA', (-2.2, 2.0, 1.6), 700, size=1.2, rot=(math.radians(65), 0, math.radians(-130)))
add_light("Fill", 'AREA', (0.5, -3.0, 0.6), 500, size=3.0, rot=(math.radians(80), 0, math.radians(10)))
add_light("Top", 'AREA', (0.0, 0.0, 3.2), 300, size=2.5, rot=(0, 0, 0))

xs2=[v.co.x for v in mesh.vertices]; ys2=[v.co.y for v in mesh.vertices]; zs2=[v.co.z for v in mesh.vertices]
obj_len = max(xs2)-min(xs2)
obj_h = max(zs2)-min(zs2)
obj_target = Vector(((max(xs2)+min(xs2))/2.0, (max(ys2)+min(ys2))/2.0, min(zs2)+obj_h*0.42))
print(f"[cam] obj_len={obj_len:.3f} obj_h={obj_h:.3f} target={tuple(obj_target)}")

cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 40
cam = bpy.data.objects.new("Cam", cam_data)
dist = obj_len * 1.7
cam.location = (obj_target.x + dist*0.62, obj_target.y - dist*0.85, obj_target.z + dist*0.42)
scene.collection.objects.link(cam)
scene.camera = cam
direction = obj_target - cam.location
rot_quat = direction.to_track_quat('-Z', 'Y')
cam.rotation_euler = rot_quat.to_euler()

scene.render.engine = 'CYCLES'
try:
    scene.cycles.device = 'GPU'
except Exception:
    pass
scene.cycles.samples = 128
scene.render.resolution_x = 900
scene.render.resolution_y = 650
scene.render.film_transparent = False
scene.view_settings.view_transform = 'AgX' if 'AgX' in [t.name for t in bpy.types.ColorManagedViewSettings.bl_rna.properties['view_transform'].enum_items] else 'Standard'

if ARGS.get("render", "1") == "1":
    scene.render.filepath = OUT_PNG
    bpy.ops.render.render(write_still=True)

if ARGS.get("glb"):
    glb_path = outpath(ARGS["glb"])
    os.makedirs(os.path.dirname(glb_path), exist_ok=True)
    ground.hide_render = True
    obj.select_set(True)
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=glb_path, use_selection=True, export_format='GLB',
                               export_yup=True, export_apply=True)
    blend_path = os.path.splitext(glb_path)[0] + ".blend"
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)

result = {"variant": ARGS["variant"], "tip": TIP, "stance": STANCE, "abstraction": ABS,
          "verts": len(mesh.vertices), "faces": len(mesh.polygons), "tris_approx": n_tris,
          "png": OUT_PNG}
print("BUILD_RESULT_JSON " + json.dumps(result))
