# The house piece: data contract (v2, instanced)

Written 2026-09-22 by the brand agent for whoever rewrites the runtime. The generator is `brand/house.py`
(Blender, `blender --background --python brand/house.py -- <outdir> glb json form=all`). It writes
`assets/house.glb` and `assets/house-shapes.json`. Everything the runtime needs is in the JSON; the GLB is only
the one fragment shape.

## The idea, in one line

ONE `THREE.InstancedMesh` of ONE bevelled unit cube, N instances. Every formation is a table of N transforms
(position, scale, rotation) plus a colour index per instance. Morphing = lerp the tables per instance, write the
matrix straight into `instanceMatrix.array`, set `needsUpdate`. No per-fragment objects, no per-fragment
materials, one draw call.

## Files

| file | what | size target |
|---|---|---|
| `assets/house.glb` | one mesh, one node, named `frag`: a 1 x 1 x 1 cube centred on the origin, bevelled edges, smooth normals, NO material worth reading (materials="NONE") | a few KB |
| `assets/house-shapes.json` | the whole piece as flat integer arrays, see below | tens of KB raw, well under 100KB gzipped |

The runtime may ignore the GLB entirely and build the same unit cube itself (a `RoundedBoxGeometry` or a
chamfered box of side 1). The GLB exists so the poster (Blender) and the live piece are provably the same shape.

## Coordinate convention

- All numbers in the JSON are in BLENDER world space: Z is up, Y points away from the camera side, X to the
  right. The house sits at the origin, its plinth on z = 0, door wall on +X.
- To three.js (Y up): `three = (x, z, -y)` for positions, `(qx, qz, -qy, qw)` for quaternions, `(sx, sz, sy)`
  for scales. Exactly what the v1 runtime did with `b2t / q2t / s2t`.
- Units: metres-ish. The house body is 2.30 x 1.80 x 1.45 with a 0.84 roof rise. The camera that matches the
  poster is unchanged from v1: Blender position (9.8, -11.6, 4.7), lens 105mm on a 36mm sensor, aimed at
  (1.05, -0.40, 1.50), frame 1500 x 1150. The crop for `setViewOffset` is in the Sizes section at the bottom.

## JSON layout (`assets/house-shapes.json`)

```
{
  "v": 2,
  "n": N,                         // fragment count, identical in every formation
  "pitch": 0.18,                  // the nominal cell size the house was voxelised at (info only)
  "forms": ["house","couch","fridge","map","message","truck"],   // formation names, THIS order
  "q": { "p": 1000, "s": 1000, "r": 32767, "j": 1000 },          // divisors that turn ints back into floats
  "colors": [[r,g,b] x 4],        // LINEAR rgb per colour index, same numbers as brand/house.py COLORS
  "surf":   [[metalness, roughness] x 4],
  "roles":  ["base","wall","window","reveal","lintel","roof","gable","inside","lift"],
  "role":   [N x uint8],          // index into roles, fixed per fragment (does not change between forms)
  "group":  [N x uint8],          // 0 = the shell, 1..4 = leaving block lift0..lift3, 5 = the block inside
  "jit":    [2N x int8],          // per fragment: [lightness, roughness] offsets, divide by q.j
  "f": {
    "<form>": {
      "p": [3N x int16],          // position xyz, divide by q.p
      "s": [3N x uint16],         // ABSOLUTE size xyz of the unit cube, divide by q.s (180 => a 0.18 wide cell)
      "r": [4N x int16],          // quaternion x y z w, divide by q.r, normalise after dequantising
      "c": [N x uint8]            // colour index 0..3 in THIS formation (a fragment may change colour between forms)
    }
  }
}
```

All arrays are plain JSON arrays of integers, fragment-major (`p[3i], p[3i+1], p[3i+2]` belong to fragment i).
Same index i is the same fragment in every formation. Nothing is added or removed between forms.

Reconstruct one instance of formation F for fragment i:

```js
const q = shapes.q, F = shapes.f[form];
pos.set(F.p[3*i] / q.p, F.p[3*i+2] / q.p, -F.p[3*i+1] / q.p);
scl.set(F.s[3*i] / q.s, F.s[3*i+2] / q.s, F.s[3*i+1] / q.s);
quat.set(F.r[4*i] / q.r, F.r[4*i+2] / q.r, -F.r[4*i+1] / q.r, F.r[4*i+3] / q.r).normalize();
mat4.compose(pos, quat, scl).toArray(mesh.instanceMatrix.array, i * 16);
```

Morphing between two forms: lerp position and scale, slerp the quaternion, per instance, with whatever stagger
the runtime wants. Colour: `setColorAt(i, color)` from `colors[c]` times `(1 + jit_light * 2.2 * jitScale)`
where jitScale is 1 in the house and 0.25 (JIT_FORM) elsewhere, same as v1. Blend colour across the transition
too, or switch it at the midpoint; both read fine.

Roughness per instance is optional. v1 did it per material; instanced, do it as a custom attribute
(`aRough`, from `jit[2i+1]`) patched into `roughnessFactor`, exactly like `wing-site-v4/assets/piece-engine.js`.
Metalness varies only by colour index (red is 0.40, everything else ~0.8); if one material is wanted, put
metalness in a second attribute or just use 0.8 and give red a lower `envMapIntensity` via the colour.

## Colour indices (palette unchanged)

| index | meaning | linear rgb |
|---|---|---|
| 0 | slate walls | 0.062, 0.074, 0.094 |
| 1 | darker slate: roof, plinth | 0.030, 0.037, 0.050 |
| 2 | ink, near-black navy: blocks, window, reveal | 0.014, 0.020, 0.036 |
| 3 | THE ONE red accent | 0.36, 0.024, 0.030 |

No green, no orange, no fifth colour.

## Roles and groups (for the gestures the runtime may keep)

- `role` says what part of the house a fragment builds. The old runtime used it to order the disassembly
  (lift first, then inside, roof, wall, gable, base). Same trick works: `order = {lift:0, inside:.12, roof:.2,
  wall:.45, window:.45, reveal:.45, lintel:.45, gable:.55, base:.75}`.
- `group` 1..4 are the four leaving blocks (lift0..lift3 in v1). They are now CLUSTERS of small fragments, so
  the "blocks travel out through the door" gesture moves a cluster: compute each cluster's centroid from the
  house table, move the centroid, keep each member's offset. The cluster's arc order is group 1 (nearest the
  door) to group 4 (highest, farthest).
- `group` 5 is the block still inside the house, seen through the door.

## Formation names, order, meaning

`house` (the logo, formation zero) then `couch`, `fridge`, `map`, `message`, `truck`. The homepage program in
the v1 runtime mapped sections to these names; that mapping is the runtime's business and is unchanged.

## What is NOT in the JSON

- Bevel width: baked into the GLB / geometry (unit cube, bevel 0.08 of the side, 2 segments). Because scale is
  per instance and the cells are near-cubic, the bevel reads the same size on every fragment.
- Camera, lights, studio HDRI: unchanged from v1 (`house.py` SOFTBOXES, FLOOR 0.58). Copy from the old runtime.
- Any per-frame animation state.

## Sizes and numbers (final export, 2026-09-22)

- N = 1074 fragments, house pitch 0.18. Per role: base 165, wall 318, window 9, reveal 24, lintel 21, roof 296,
  gable 44, inside 27, lift 170 (group 1: 80, group 2: 64, group 3: 18, group 4: 8; group 5 inside: 27; shell 877).
- `assets/house.glb`: 3,860 bytes raw, 1,471 gzipped. 108 triangles.
- `assets/house-shapes.json`: 298,856 bytes raw, 71,593 gzipped. Six formations x 1074 x (3+3+4+1) ints.
- Other formations are laid out as SURFACE SHELLS at their own pitch (couch 0.142, fridge 0.128, map 0.101,
  message 0.116, truck 0.172) so that every visible face is complete with the same N. Leftover fragments are
  parked at interior grid positions (hidden) and, for the map only, 78 are parked as 0.002-size duplicates
  inside random surface cells. The runtime needs no special handling: they are ordinary instances.
- Poster crop (poster.py output for the v2 hero render): `setViewOffset(1500, 1150, -7, -175, 1410, 1318)`.
  The v1 runtime had `{ x: -5, y: -172, w: 1402, h: 1311 }`; update it or the live canvas lands 2px off the poster.
- Roughness offsets and lightness offsets live in `jit` (int8 / 1000): lightness in [-35, 35], roughness in [-60, 60].
