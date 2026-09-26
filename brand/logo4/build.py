"""
Hero's logo4: the travelling cube logo.

One set of N bevelled cubes, hand laid (see glyphs.py) into seven icons: the house-H logo,
a pin, a truck, a couch, a star, a camera and the reversed logo for the navy footer.
This script pads every form to the same N (spare cubes hide directly behind the face),
matches cubes form to form (nearest position, same colour preferred) so morphs read as a
rearrangement, writes the runtime data and renders the stills from Blender.

Run (from repo root):
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --factory-startup \
      -P brand/logo4/build.py -- [--stage all|shapes|renders] [--samples 64]

Outputs (assets/logo-piece/):
  shapes.json      {n, forms:{name:[x,y,z,..]}, colors:{name:[0xRRGGBB,..]}, dims:{name:[w,h]}}
                   three.js space: x right, y up, z towards the viewer, 1 unit = 1 cube
  logo.png         512x512 transparent still of the logo (header fallback, og use)
  logo-88.png      88x88 (the 44px header slot at 2x)
  logo-rev-88.png  reversed logo for dark backgrounds
  favicon-16.png, favicon-32.png, apple-touch-icon.png (180)
"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import glyphs  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(name, default):
    return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else default

STAGE = arg("--stage", "all")
SAMPLES = int(arg("--samples", "64"))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "assets", "logo-piece")
os.makedirs(OUT, exist_ok=True)
FILL, BEVEL = 0.86, 0.22      # piece5: slightly smaller cubes (wider seams), softer rounder bevel
DARK = {0x14284B: 0xF3EEE4, 0x0C1A33: 0xC9CED8, 0xF3EEE4: 0x14284B}   # navy docks: recolour, red stays


# ------------------------------------------------------------------ shapes ----
def padded(name, n):
    c, w, h = glyphs.cells(name)
    P = [list(p[:3]) for p in c]
    C = [glyphs.HEX[p[3]] for p in c]
    if len(P) < n:
        # spare cubes stack straight behind the face, centre first, so they are never seen
        back = {}
        for (x, y, z), col in zip(P, C):
            if (x, y) not in back or z < back[(x, y)][0]:
                back[(x, y)] = (z, col)
        order = sorted(back, key=lambda k: (k[0] ** 2 + k[1] ** 2, k))
        depth = 1
        while len(P) < n:
            for k in order:
                if len(P) >= n:
                    break
                z, col = back[k]
                P.append([k[0], k[1], z - depth]); C.append(col)
            depth += 1
    return np.array(P, float), C, w, h


def match(A, CA, B, CB):
    """Reorder B so cube i of A goes to B[perm[i]]: greedy global nearest, colour kept when it can be."""
    sa = max(np.ptp(A[:, 0]), np.ptp(A[:, 1])) + 1
    sb = max(np.ptp(B[:, 0]), np.ptp(B[:, 1])) + 1
    a = A / sa; b = B / sb
    d = np.linalg.norm(a[:, None, :2] - b[None, :, :2], axis=2) + 0.02 * np.abs(a[:, None, 2] - b[None, :, 2])
    d += 0.18 * (np.array(CA)[:, None] != np.array(CB)[None, :])
    n = len(A)
    order = np.argsort(d, axis=None)
    ua = np.zeros(n, bool); ub = np.zeros(n, bool); perm = np.full(n, -1)
    left = n
    for idx in order:
        i, j = divmod(int(idx), n)
        if ua[i] or ub[j]:
            continue
        perm[i] = j; ua[i] = ub[j] = True; left -= 1
        if not left:
            break
    return perm


def build_shapes():
    """piece5: every form in its own order + a nearest-cube matching for every pair of forms.
    The engine chains the docks of a page in scroll order and uses perms["a|b"][i] = the index in b
    that cube i of a flies to (the b->a direction is the inverse)."""
    n = max(len(glyphs.cells(f)[0]) for f in glyphs.FORMS)
    data = {"n": n, "fill": FILL, "bevel": BEVEL, "forms": {}, "colors": {}, "dims": {}, "perms": {},
            "dark": {hex(k): v for k, v in DARK.items()}}
    arr = {}
    for f in glyphs.FORMS:
        P, C, w, h = padded(f, n)
        arr[f] = (P, C)
        data["forms"][f] = [round(float(v), 2) for v in P.reshape(-1)]
        data["colors"][f] = [int(c) for c in C]
        data["dims"][f] = [w, h]
    F = glyphs.FORMS
    for i, a in enumerate(F):
        for b in F[i + 1:]:
            data["perms"][f"{a}|{b}"] = [int(x) for x in match(arr[a][0], arr[a][1], arr[b][0], arr[b][1])]
    with open(os.path.join(OUT, "shapes.json"), "w") as fh:
        json.dump(data, fh, separators=(",", ":"))
    print(f"[logo4] shapes.json n={n} forms={F}")
    return data


# ----------------------------------------------------------------- renders ----
def srgb_lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def cube_mesh():
    e = FILL
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=e)
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=e * BEVEL, segments=4, affect='EDGES', profile=0.5)
    me = bpy.data.meshes.new("rcube"); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    m = bpy.data.materials.new("satin"); m.use_nodes = True
    nt = m.node_tree; bsdf = nt.nodes.get("Principled BSDF")
    info = nt.nodes.new("ShaderNodeObjectInfo")
    nt.links.new(info.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.46
    for k, v in (("Coat Weight", 0.2), ("Coat Roughness", 0.3), ("Sheen Weight", 0.35), ("Sheen Roughness", 0.55)):
        if k in bsdf.inputs:
            bsdf.inputs[k].default_value = v
    me.materials.append(m)
    return me


def setup_scene():
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    try:
        sc.view_settings.view_transform = "Standard"
    except Exception:
        pass
    ee = sc.eevee
    ee.taa_render_samples = SAMPLES
    for k, v in (("use_raytracing", True), ("use_shadows", True), ("fast_gi_method", "GLOBAL_ILLUMINATION")):
        if hasattr(ee, k):
            try:
                setattr(ee, k, v)
            except Exception:
                pass
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.92, 0.93, 0.95, 1); bg.inputs[1].default_value = 0.35
    return sc


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)


def render_form(data, form, path, px, yaw=16, pitch=9, margin=1.06):
    sc = bpy.context.scene
    clear()
    mesh = bpy.data.meshes.get("rcube") or cube_mesh()
    P = np.array(data["forms"][form]).reshape(-1, 3); C = data["colors"][form]
    for i, (x, y, z) in enumerate(P):          # three (x, y up, z front) -> blender (x, -z, y)
        ob = bpy.data.objects.new(f"c{i}", mesh)
        ob.location = (x, -z, y)
        c = C[i]
        ob.color = (srgb_lin(((c >> 16) & 255) / 255), srgb_lin(((c >> 8) & 255) / 255), srgb_lin((c & 255) / 255), 1)
        sc.collection.objects.link(ob)
    mn = P.min(0) - 0.5; mx = P.max(0) + 0.5
    ctr = Vector(((mn[0] + mx[0]) / 2, -(mn[2] + mx[2]) / 2, (mn[1] + mx[1]) / 2))
    cam_d = bpy.data.cameras.new("cam"); cam_d.lens = 120
    cam = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(cam); sc.camera = cam
    yw, pt = math.radians(yaw), math.radians(pitch)
    dirv = Vector((math.sin(yw) * math.cos(pt), -math.cos(yw) * math.cos(pt), math.sin(pt)))
    cam.location = ctr + dirv * 300
    cam.rotation_euler = (-dirv).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.view_layer.update()
    corners = []
    for cx in (mn[0], mx[0]):
        for cy in (mn[1], mx[1]):
            for cz in (mn[2], mx[2]):
                corners += [cx, -cz, cy]
    loc, _ = cam.camera_fit_coords(bpy.context.evaluated_depsgraph_get(), corners)
    loc = Vector(loc)
    cam.location = ctr + (loc - ctr) * margin
    R = max(mx - mn) * 0.5
    def area(name, off, energy, size_, color):
        L = bpy.data.lights.new(name, "AREA"); L.energy = energy; L.size = size_; L.color = color
        o = bpy.data.objects.new(name, L); sc.collection.objects.link(o)
        o.location = ctr + Vector(off)
        o.rotation_euler = (ctr - o.location).to_track_quat('-Z', 'Y').to_euler()
    k = R * R
    area("key", (-1.8 * R, -3.0 * R, 2.6 * R), 80 * k, 2.4 * R, (1.0, 0.97, 0.93))
    area("top", (0.2 * R, -0.8 * R, 3.6 * R), 50 * k, 3.0 * R, (1.0, 0.99, 0.97))
    area("rim", (2.6 * R, 2.6 * R, 1.6 * R), 150 * k, 1.2 * R, (1.0, 0.86, 0.72))
    area("fill", (3.2 * R, -2.0 * R, 0.4 * R), 25 * k, 2.4 * R, (0.86, 0.9, 1.0))
    sc.render.resolution_x = sc.render.resolution_y = px
    sc.render.resolution_percentage = 100
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print(f"[logo4] rendered {os.path.basename(path)}")


def downsample(src, dst, size, pad=0.04, bg=None):
    """Crop to the cubes' alpha box (square, small pad), then scale: the mark fills its slot."""
    img = bpy.data.images.load(src)
    w, h = img.size
    px = np.array(img.pixels[:], np.float32).reshape(h, w, 4)
    ys, xs = np.nonzero(px[..., 3] > 0.02)
    cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
    half = int(max(xs.max() - xs.min(), ys.max() - ys.min()) * (0.5 + pad)) + 1
    out = np.zeros((2 * half, 2 * half, 4), np.float32)
    x0, y0 = int(cx) - half, int(cy) - half
    sx0, sy0 = max(0, x0), max(0, y0)
    sx1, sy1 = min(w, x0 + 2 * half), min(h, y0 + 2 * half)
    out[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = px[sy0:sy1, sx0:sx1]
    if bg is not None:                         # opaque tile (iOS home screen would show black)
        a = out[..., 3:4]
        out[..., :3] = out[..., :3] + np.array(bg, np.float32) * (1 - a)
        out[..., 3] = 1
    img = bpy.data.images.new("crop", 2 * half, 2 * half, alpha=True)
    img.pixels.foreach_set(out.reshape(-1))
    img.scale(size, size)
    img.filepath_raw = dst; img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    print(f"[logo4] wrote {os.path.basename(dst)}")


def render_brand(data):  # legacy header/favicons (logo4); not run by default any more
    setup_scene()
    big = os.path.join(OUT, "logo.png")
    render_form(data, "logo", big, 512, yaw=12, pitch=6, margin=1.0)
    rev = os.path.join(OUT, "logo-rev.png")
    render_form(data, "logo_rev", rev, 256, yaw=12, pitch=6, margin=1.0)
    # favicons read best straight on and tight
    fav = os.path.join(OUT, "_fav.png")
    render_form(data, "logo", fav, 360, yaw=0, pitch=0, margin=1.0)
    downsample(big, os.path.join(OUT, "logo-88.png"), 88)
    downsample(rev, os.path.join(OUT, "logo-rev-88.png"), 88)
    downsample(fav, os.path.join(OUT, "apple-touch-icon.png"), 180, pad=0.16, bg=(1.0, 1.0, 1.0))
    downsample(fav, os.path.join(OUT, "favicon-32.png"), 32)
    downsample(fav, os.path.join(OUT, "favicon-16.png"), 16)
    os.remove(fav)
    for f in glyphs.FORMS:                      # contact sheet stills for review
        render_form(data, f, os.path.join(ROOT, ".visual", "logo-piece", f"blender-{f}.png"), 320)


def render_stills(data):
    """Reduced motion / no WebGL: one still per form, light and dark, 360px (docks are at most 180 CSS px)."""
    setup_scene()
    for f in glyphs.FORMS:
        render_form(data, f, os.path.join(OUT, f"still-{f}.png"), 360, yaw=14, pitch=8, margin=1.02)
        dk = dict(data); dk["colors"] = dict(data["colors"])
        dk["colors"][f] = [DARK.get(c, c) for c in data["colors"][f]]
        render_form(dk, f, os.path.join(OUT, f"still-{f}-dark.png"), 360, yaw=14, pitch=8, margin=1.02)
    for f in glyphs.FORMS:
        render_form(data, f, os.path.join(ROOT, ".visual", "piece5", f"blender-{f}.png"), 320)


if __name__ == "__main__":
    bpy.ops.wm.read_factory_settings(use_empty=True)
    data = build_shapes() if STAGE in ("all", "shapes") else json.load(open(os.path.join(OUT, "shapes.json")))
    if STAGE in ("all", "renders"):
        render_stills(data)
    if STAGE == "brand":
        render_brand(data)
