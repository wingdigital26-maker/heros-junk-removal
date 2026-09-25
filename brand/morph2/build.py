"""
Hero's Junk Removal - morph2: ONE object of ~1,600 identical navy cubes that
rearranges into a HOUSE, a PICKUP + TRAILER, a COUCH and a slab-serif H.

Each target is modelled in Blender as a small stack of clean closed solids
(boxes, prisms, cylinders) combined with ordered add/subtract ops. The solid is
voxel-sampled on a unit grid, only SURFACE voxels are kept, the scale of each
shape is searched so every form has as close to N surface cubes as possible,
and the few spare cubes are tucked inside (hidden). Point sets are then
matched form-to-form (greedy nearest) so the morph flows.

Run (from repo root):
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --factory-startup \
      -P brand/morph2/build.py -- [--n 1600] [--stage all|shapes|posters] [--forms house,truck]

Outputs:
  assets/piece2/shapes.json          {n, cube, forms:{house:[x,y,z,...],...}}  (three.js Y-up)
  assets/piece2/poster-<form>.webp   1600x1200 transparent Eevee stills
"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix

# ------------------------------------------------------------------ args ----
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(name, default):
    if name in argv:
        i = argv.index(name)
        if i + 1 < len(argv):
            return argv[i + 1]
    return default

N = int(arg("--n", "1600"))
STAGE = arg("--stage", "all")
ONLY = [f for f in arg("--forms", "").split(",") if f]
SAMPLES = int(arg("--samples", "64"))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "assets", "piece2")
os.makedirs(OUT, exist_ok=True)
FORMS = ["house", "truck", "couch", "h"]
YAW = {"house": 30, "truck": 14, "couch": 24, "h": 24}   # poster camera yaw (deg, from front towards +X)
NAVY = "#14284B"
CUBE = 1.0          # voxel pitch in output units
CUBE_FILL = 0.92    # rendered cube edge relative to pitch (seams give definition)

# --------------------------------------------------------- mesh helpers ----
def _obj_from_bm(bm, name):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob

def box(x0, x1, y0, y1, z0, z1, name="box"):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(x1 - x0, y1 - y0, z1 - z0), verts=bm.verts)
    bmesh.ops.translate(bm, vec=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), verts=bm.verts)
    return _obj_from_bm(bm, name)

def cyl_y(cx, cz, r, y0, y1, name="cyl", seg=48):
    """Cylinder whose axis runs along Blender Y (depth) - wheels."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=y1 - y0)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'X'))
    bmesh.ops.translate(bm, vec=(cx, (y0 + y1) / 2, cz), verts=bm.verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj_from_bm(bm, name)

def gable(x0, x1, z0, zapex, y0, y1, name="roof"):
    """Triangular prism: triangle in X-Z (base x0..x1 at z0, apex at centre), extruded along Y."""
    bm = bmesh.new()
    xm = (x0 + x1) / 2
    tri0 = [bm.verts.new((x0, y0, z0)), bm.verts.new((x1, y0, z0)), bm.verts.new((xm, y0, zapex))]
    tri1 = [bm.verts.new((x0, y1, z0)), bm.verts.new((x1, y1, z0)), bm.verts.new((xm, y1, zapex))]
    bm.faces.new(tri0[::-1]); bm.faces.new(tri1)
    for a, b in ((0, 1), (1, 2), (2, 0)):
        bm.faces.new((tri0[a], tri0[b], tri1[b], tri1[a]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _obj_from_bm(bm, name)

# --------------------------------------------------------- the 4 models ----
# Blender units, Z up, front of every object faces -Y (towards the camera),
# ground at z=0. Roughly 1 unit ~ 1 cube before the scale search.
def model_house():
    ops = []
    A = lambda o: ops.append(("+", o)); S = lambda o: ops.append(("-", o))
    A(box(-9, 9, -7, 7, 0, 11, "walls"))
    A(gable(-10.5, 10.5, 10.5, 20.5, -8, 8, "roof"))
    A(box(4.2, 7.0, -1.0, 2.0, 14, 22, "chimney"))
    A(box(-3.0, 3.0, -8.0, -7.0, 0, 0.9, "step"))
    # openings cut into the front (-Y) face: door + two windows + gable window
    S(box(-2.0, 2.0, -9, -5.4, 0.9, 8.0, "door"))
    S(box(-7.2, -3.8, -9, -5.4, 4.0, 7.8, "winL"))
    S(box(3.8, 7.2, -9, -5.4, 4.0, 7.8, "winR"))
    S(box(-1.6, 1.6, -9, -6.4, 13.0, 16.2, "gableWin"))
    # side (+X) face windows
    S(box(7.4, 10, -4.6, -1.2, 4.0, 7.8, "sideWin1"))
    S(box(7.4, 10, 1.2, 4.6, 4.0, 7.8, "sideWin2"))
    return ops

def model_truck():
    ops = []
    A = lambda o: ops.append(("+", o)); S = lambda o: ops.append(("-", o))
    W = 4.2
    WR, WZ = 3.35, 3.35          # wheel radius / hub height
    B = 4.0                    # body underside
    # pickup: nose points +X. Bed and cab are split by a one-cube groove above the chassis.
    A(box(0, 22.2, -W, W, B, 6.0, "chassis"))
    A(box(0, 8.0, -W, W, B, 10.6, "bed"))
    A(box(8.9, 14.8, -W, W, B, 16.0, "cab"))
    A(box(14.4, 22.2, -W, W, B, 10.4, "hood"))
    S(box(1.3, 6.8, -W + 1.3, W - 1.3, 6.4, 12, "bedHollow"))         # open bed
    S(box(9.9, 13.8, -W - 1, -W + 1.1, 11.6, 15.0, "cabWinNear"))     # side glass
    S(box(9.9, 13.8, W - 1.1, W + 1, 11.6, 15.0, "cabWinFar"))
    S(box(13.7, 16, -W + 1.0, W - 1.0, 11.4, 15.0, "windshield"))
    S(box(21.2, 24, -W + 1.2, W - 1.2, 7.6, 9.2, "grille"))
    # wheel arches then wheels (wheels stand one cube proud of the body so they read round)
    for cx in (4.0, 18.2):
        S(cyl_y(cx, WZ, WR + 0.8, -W - 1, W + 1, "arch"))
    for cx in (4.0, 18.2):
        A(cyl_y(cx, WZ, WR, -W - 1.0, W + 1.0, "wheel"))
        S(cyl_y(cx, WZ, 1.5, -W - 2.0, -W - 0.1, "hub"))             # hub recess reads "wheel"
        S(cyl_y(cx, WZ, 1.5, W + 0.1, W + 2.0, "hubFar"))
    # hitch + small open trailer
    A(box(-4.4, 0.2, -0.8, 0.8, 4.6, 6.0, "hitch"))
    A(box(-16.0, -4.2, -W + 0.3, W - 0.3, 3.8, 8.8, "trailer"))
    S(box(-14.7, -5.5, -W + 1.6, W - 1.6, 5.2, 12, "trailerHollow"))
    S(cyl_y(-10.1, 3.0, 3.8, -W - 1, W + 1, "tArch"))
    A(cyl_y(-10.1, 3.0, 3.0, -W - 0.8, W + 0.8, "tWheel"))
    S(cyl_y(-10.1, 3.0, 1.3, -W - 2.0, -W + 0.1, "tHub"))
    return ops

def model_couch():
    ops = []
    A = lambda o: ops.append(("+", o)); S = lambda o: ops.append(("-", o))
    A(box(-14.5, 14.5, -6.0, 5.5, 1.8, 6.2, "base"))
    A(box(-17.6, -14.0, -6.6, 5.5, 1.8, 11.0, "armL"))
    A(box(14.0, 17.6, -6.6, 5.5, 1.8, 11.0, "armR"))
    A(box(-14.5, 14.5, 2.4, 5.5, 6.0, 16.0, "back"))
    for x0, x1 in ((-14.0, -5.3), (-4.3, 4.3), (5.3, 14.0)):
        A(box(x0, x1, -6.4, 2.6, 6.0, 9.0, "seat"))       # seat cushions, grooves between
        A(box(x0, x1, 0.4, 2.8, 8.9, 15.2, "pillow"))     # back cushions
    for x in (-16.6, 14.6):
        for y in (-5.8, 3.4):
            A(box(x, x + 2.0, y, y + 2.0, 0, 1.9, "leg"))
    return ops

def model_h():
    ops = []
    A = lambda o: ops.append(("+", o)); S = lambda o: ops.append(("-", o))
    D = 3.2
    A(box(-10.5, -4.5, -D, D, 0, 25, "stemL"))
    A(box(4.5, 10.5, -D, D, 0, 25, "stemR"))
    A(box(-4.6, 4.6, -D, D, 10.4, 15.0, "bar"))
    for x0, x1 in ((-14.0, -1.8), (1.8, 14.0)):
        A(box(x0, x1, -D, D, 0, 3.4, "serifB"))
        A(box(x0, x1, -D, D, 21.6, 25, "serifT"))
    return ops

MODELS = {"house": model_house, "truck": model_truck, "couch": model_couch, "h": model_h}

# ------------------------------------------------------------ voxeliser ----
def make_testers(ops):
    """Every primitive is convex, so a point is inside iff it is behind every face plane.
    (Exact and fast; nearest-face sign tests misfire at sharp roof eaves.)"""
    out = []
    for sign, ob in ops:
        me = ob.data
        C = np.array([p.center[:] for p in me.polygons])
        Nn = np.array([p.normal[:] for p in me.polygons])
        V = np.array([v.co[:] for v in me.vertices])
        # make sure normals point outward (away from the centroid)
        cen = V.mean(0)
        flip = ((C - cen) * Nn).sum(1) < 0
        Nn[flip] *= -1
        out.append((sign, (C, Nn), V.min(0), V.max(0)))
    return out

def inside_one(planes, mn, mx, pts):
    C, Nn = planes
    d = (pts[:, None, :] - C[None, :, :]) * Nn[None, :, :]
    return np.all(d.sum(-1) < 0, axis=1)

def voxelise(testers, s):
    """Occupancy on a unit grid of the model scaled by s. Returns (grid bool[X,Y,Z], origin)."""
    mn = np.min([t[2] for t in testers if t[0] == "+"], axis=0) * s
    mx = np.max([t[3] for t in testers if t[0] == "+"], axis=0) * s
    lo = np.floor(mn) - 1
    hi = np.ceil(mx) + 1
    xs, ys, zs = [np.arange(lo[k] + 0.5, hi[k], 1.0) for k in range(3)]
    G = np.stack(np.meshgrid(xs, ys, zs, indexing="ij"), -1)
    pts_world = G.reshape(-1, 3)
    pts_model = pts_world / s + 1.3e-4     # tiny offset so no sample sits exactly on a face
    occ = np.zeros(len(pts_model), bool)
    for sign, bvh, a, b in testers:
        ins = inside_one(bvh, a, b, pts_model)
        occ = (occ | ins) if sign == "+" else (occ & ~ins)
    return occ.reshape(G.shape[:3]), G

def surface_of(occ):
    """Occupied voxels touching empty space through a face, edge or corner (26-nbhd).
    The edge/corner cases fill the inner corners of stair-steps so the hollow
    shell never shows see-through gaps at grazing angles."""
    pad = np.pad(occ, 1)
    X, Y, Z = occ.shape
    nb_empty = np.zeros_like(occ)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == dy == dz == 0:
                    continue
                nb_empty |= ~pad[1 + dx:1 + dx + X, 1 + dy:1 + dy + Y, 1 + dz:1 + dz + Z]
    return occ & nb_empty

def sample_form(name):
    ops = MODELS[name]()
    testers = make_testers(ops)
    # search scale so the surface count is the largest value <= N
    lo, hi = 0.4, 2.5
    best = None
    for _ in range(22):
        s = (lo + hi) / 2
        occ, G = voxelise(testers, s)
        cnt = int(surface_of(occ).sum())
        if cnt <= N:
            best = (s, occ, G, cnt); lo = s
        else:
            hi = s
    s, occ, G, cnt = best
    surf = surface_of(occ)
    pts = G[surf]
    interior = G[occ & ~surf]
    need = N - len(pts)
    if need > 0:
        # hide spare cubes inside, nearest the centroid so they never peek out
        c = pts.mean(0)
        if len(interior):
            order = np.argsort(np.linalg.norm(interior - c, axis=1))
            extra = interior[order[:need]]
        else:
            extra = np.zeros((0, 3))
        while len(extra) < need:                 # thin shape: stack duplicates
            extra = np.vstack([extra, pts[: need - len(extra)]])
        pts = np.vstack([pts, extra[:need]])
    print(f"[morph2] {name}: scale={s:.3f} surface={cnt} padded={need} total={len(pts)}")
    for _, ob in ops:
        bpy.data.objects.remove(ob, do_unlink=True)
    return pts, cnt

# ------------------------------------------------------------- matching ----
def greedy_match(src, dst):
    """Return perm so dst[perm[i]] is paired with src[i]; greedy global nearest."""
    a = src - src.mean(0); b = dst - dst.mean(0)
    # compare shapes at similar size
    a = a / (np.abs(a).max() + 1e-9); b = b / (np.abs(b).max() + 1e-9)
    D = ((a[:, None, :] - b[None, :, :]) ** 2).sum(-1).astype(np.float32)
    order = np.argsort(D, axis=None)
    n = len(src)
    used_a = np.zeros(n, bool); used_b = np.zeros(n, bool)
    perm = np.full(n, -1)
    left = n
    for k in order:
        i, j = divmod(int(k), n)
        if used_a[i] or used_b[j]:
            continue
        perm[i] = j; used_a[i] = used_b[j] = True
        left -= 1
        if left == 0:
            break
    return perm

def to_three(p):
    """Blender (x, y-depth, z-up) -> three.js (x, y-up, z-front); centre X/Z, ground at y=0."""
    q = np.stack([p[:, 0], p[:, 2], -p[:, 1]], 1)
    q[:, 0] -= (q[:, 0].min() + q[:, 0].max()) / 2
    q[:, 2] -= (q[:, 2].min() + q[:, 2].max()) / 2
    q[:, 1] -= q[:, 1].min() - 0.5      # bottom cube centre at 0.5 -> sits on y=0
    return q

def build_shapes():
    raw = {}
    for f in FORMS:
        pts, _ = sample_form(f)
        raw[f] = to_three(pts)
    # base order: house sorted bottom->top, left->right; each next form matched to the previous
    h = raw["house"]
    order = np.lexsort((h[:, 2], h[:, 0], h[:, 1]))
    ordered = {"house": h[order]}
    prev = ordered["house"]
    for f in FORMS[1:]:
        perm = greedy_match(prev, raw[f])
        ordered[f] = raw[f][perm]
        prev = ordered[f]
    data = {"n": N, "cube": CUBE, "fill": CUBE_FILL,
            "forms": {f: [round(float(v), 2) for v in ordered[f].reshape(-1)] for f in FORMS}}
    with open(os.path.join(OUT, "shapes.json"), "w") as fh:
        json.dump(data, fh, separators=(",", ":"))
    print("[morph2] wrote shapes.json")
    return ordered

# -------------------------------------------------------------- posters ----
def hex_lin(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4) for x in c) + (1.0,)

def clear_scene():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)

def satin_material():
    m = bpy.data.materials.new("navy_satin")
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = hex_lin(NAVY)
    bsdf.inputs["Roughness"].default_value = 0.42
    for key, val in (("Coat Weight", 0.25), ("Coat Roughness", 0.3), ("Specular IOR Level", 0.5)):
        if key in bsdf.inputs:
            bsdf.inputs[key].default_value = val
    return m

def rounded_cube_mesh(edge):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=edge)
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=edge * 0.11, segments=3, affect='EDGES', profile=0.5)
    me = bpy.data.meshes.new("rcube")
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    return me

def blur2d(img, sigma):
    r = int(sigma * 3) + 1
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2); k /= k.sum()
    img = np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), 0, img)
    return np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), 1, img)

def contact_shadow_image(P, name, px=12, margin=14):
    """Soft contact shadow from the voxel footprint: cubes near the ground count most."""
    mn = P.min(0); mx = P.max(0)
    x0, x1 = mn[0] - margin, mx[0] + margin
    z0, z1 = mn[2] - margin, mx[2] + margin
    W = int((x1 - x0) * px); H = int((z1 - z0) * px)
    acc = np.zeros((H, W), np.float32)
    for x, y, z in P:
        w = math.exp(-(y - 0.5) / 2.5)
        cx = int((x - x0) * px); cz = int((z - z0) * px)
        h = int(px * 0.5)
        acc[max(cz - h, 0):cz + h, max(cx - h, 0):cx + h] += w
    acc = np.clip(acc, 0, 1)
    tight = blur2d(acc, px * 0.6)
    wide = blur2d(acc, px * 3.5)
    a = np.clip(0.55 * tight + 0.45 * wide * 1.4, 0, 1) ** 0.9
    img = bpy.data.images.new(f"shadow_{name}", W, H, alpha=True)
    rgba = np.zeros((H, W, 4), np.float32); rgba[..., 3] = a
    # image rows run bottom->top in Blender = +z(three) towards -y(blender) ... flip so front is front
    img.pixels.foreach_set(rgba[::-1].reshape(-1))
    img.pack()
    return img, (x0, x1, z0, z1)

def shadow_plane(img, ext, strength=0.6):
    x0, x1, z0, z1 = ext
    bpy.ops.mesh.primitive_plane_add(size=1, location=((x0 + x1) / 2, -(z0 + z1) / 2, 0.001))
    g = bpy.context.active_object
    g.scale = (x1 - x0, z1 - z0, 1)
    m = bpy.data.materials.new("shadow"); m.use_nodes = True
    if hasattr(m, "surface_render_method"):
        m.surface_render_method = "BLENDED"
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img; tex.extension = "CLIP"
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = strength
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs[0].default_value = (0.006, 0.01, 0.02, 1)
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(tex.outputs["Alpha"], mul.inputs[0])
    nt.links.new(mul.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1]); nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    g.data.materials.append(m)
    g.visible_shadow = False
    return g

def render_posters(shapes):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = 1600, 1200
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "WEBP"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.image_settings.quality = 88
    try:
        sc.view_settings.view_transform = "AgX"
        sc.view_settings.look = "AgX - Base Contrast"
    except Exception:
        try:
            sc.view_settings.look = "None"
        except Exception:
            pass
    ee = sc.eevee
    ee.taa_render_samples = SAMPLES
    for k, v in (("use_raytracing", True), ("use_shadows", True), ("shadow_ray_count", 3),
                 ("shadow_step_count", 12), ("use_gtao", True), ("fast_gi_method", "GLOBAL_ILLUMINATION")):
        if hasattr(ee, k):
            try:
                setattr(ee, k, v)
            except Exception:
                pass
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.86, 0.88, 0.92, 1); bg.inputs[1].default_value = 0.25

    mat = satin_material()
    mesh = rounded_cube_mesh(CUBE * CUBE_FILL)
    mesh.materials.append(mat)

    for f in shapes:
        if ONLY and f not in ONLY:
            continue
        clear_scene()
        P = shapes[f]
        for i, (x, y, z) in enumerate(P):            # three (x, y-up, z-front) -> blender (x, -z, y)
            ob = bpy.data.objects.new(f"c{i}", mesh)
            ob.location = (x, -z, y)
            sc.collection.objects.link(ob)
        mn = P.min(0) - 0.5; mx = P.max(0) + 0.5
        size = mx - mn
        ctr = Vector(((mn[0] + mx[0]) / 2, -(mn[2] + mx[2]) / 2, (mn[1] + mx[1]) / 2))
        img, ext = contact_shadow_image(P, f)
        shadow_plane(img, ext)
        # camera: 3/4 from front-right, slightly above; fit the bbox then add margin
        cam_d = bpy.data.cameras.new("cam"); cam_d.lens = 85
        cam = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(cam); sc.camera = cam
        yaw, pitch = math.radians(YAW.get(f, 26)), math.radians(12 if f == "truck" else 17)
        dirv = Vector((math.sin(yaw) * math.cos(pitch), -math.cos(yaw) * math.cos(pitch), math.sin(pitch)))
        cam.location = ctr + dirv * 200
        cam.rotation_euler = (-dirv).to_track_quat('-Z', 'Y').to_euler()
        bpy.context.view_layer.update()
        corners = []
        for cx in (mn[0], mx[0]):
            for cy in (mn[1], mx[1]):
                for cz in (mn[2], mx[2]):
                    corners += [cx, -cz, cy]
        loc, _ = cam.camera_fit_coords(bpy.context.evaluated_depsgraph_get(), corners)
        loc = Vector(loc)
        cam.location = loc + (loc - ctr).normalized() * (loc - ctr).length * 0.30
        # lights scale with the object
        R = max(size) * 0.5
        def area(name, off, energy, size_, color):
            L = bpy.data.lights.new(name, "AREA"); L.energy = energy; L.size = size_; L.color = color
            o = bpy.data.objects.new(name, L); sc.collection.objects.link(o)
            o.location = ctr + Vector(off)
            o.rotation_euler = (ctr - o.location).to_track_quat('-Z', 'Y').to_euler()
            return o
        k = R * R          # inverse-square: keep irradiance constant whatever the object size
        area("top", (-0.4 * R, -0.6 * R, 3.6 * R), 250 * k, 3.0 * R, (1.0, 0.98, 0.95))
        area("key", (-2.6 * R, -2.8 * R, 1.6 * R), 170 * k, 2.0 * R, (1.0, 0.97, 0.93))
        area("rim", (2.4 * R, 3.2 * R, 1.8 * R), 520 * k, 1.0 * R, (1.0, 0.76, 0.52))
        area("fill", (3.4 * R, -1.2 * R, 0.6 * R), 60 * k, 2.4 * R, (0.80, 0.87, 1.0))
        sc.render.filepath = os.path.join(OUT, f"poster-{f}.webp")
        bpy.ops.render.render(write_still=True)
        print(f"[morph2] rendered poster-{f}.webp")

# ----------------------------------------------------------------- main ----
if __name__ == "__main__":
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if STAGE in ("all", "shapes"):
        shapes = build_shapes()
    else:
        d = json.load(open(os.path.join(OUT, "shapes.json")))
        shapes = {f: np.array(d["forms"][f]).reshape(-1, 3) for f in FORMS}
    if STAGE in ("all", "posters"):
        render_posters(shapes)
