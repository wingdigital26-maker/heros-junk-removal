/* The live house. Loaded by house.js only when it is worth it (see the gate there).
   Camera, lens and target are the Blender ones from brand/house.py, converted to glTF axes (Blender Y -> -Z,
   Blender Z -> Y), so the first live frame sits exactly where the poster sat.

   v3 (2026-09-22): ONE SET OF FRAGMENTS that travels between formations, driven by scroll.
   - assets/house.glb holds the 66 fragments in their house pose (real bevelled geometry, named frag0.., lift0..3).
   - assets/house-shapes.json (written by brand/house.py) holds every fragment's position, rotation, scale ratio and
     colour for each formation: house, couch, fridge, map, message, truck. Nothing is added or removed between
     forms, they only move, so it reads as one object transforming.
   - PROGRAM: each homepage section names the formation it resolves to. Scroll position is turned into one
     continuous value per fragment (a stagger over the transition), so it scrubs both ways and settles when the
     reader stops. In the hero the house sits in the page; as the hero scrolls away the canvas docks to the bottom
     right corner as a small companion (pointer-events none, never over the text column) and re-forms per section.
   - the studio environment is the same hand-built HDRI as the Blender one (gradient dome + softboxes), so metal
     faces carry the same gradient live as in the poster.
   - prefers-reduced-motion never reaches this file: house.js keeps the poster.
   v3.1 (2026-09-22, variant A shipped): 68 fragments (3 x 2 roof panels, three gable steps, rounded bevels).
   - the program is authored against the homepage sections: 01 how a price happens = message, 02 what we take = couch,
     03 where = map, 04 on Google = truck (the loads that earned the rating), 05 questions = fridge, 06 contact = the
     house again, so the story is house on the way in, apart in the middle, house where the reader arrives
   - jitter is a house thing: in the other formations it is scaled by JIT_FORM (same number as brand/house.py)
   - the companion docks beside the text column, never over it: it lands just right of the widest column, clamped
     inside the window, shrinks when the gap is tight, hides when there is no room, and fades out under the footer */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';

const CYCLE = 24;             // seconds for one block to travel the whole arc in the house state
const POINTER_YAW = 0.16;     // radians of lean toward the pointer, either way
const POINTER_PITCH = 0.06;
const SWAY = 0.035;           // idle yaw sway, radians
const PULL = 0.28;            // how far (world units) a block drifts toward the pointer when it is over the hero
const JIT_FORM = 0.25;        // brand/house.py JIT_FORM: jitter outside the house formation
const FLOOR = 0.58;           // brand/house.py FLOOR: studio dome brightness straight down
const RED_ROUGH = 0.08;       // live-only: the lacquer's highlight under NeutralToneMapping peaks hotter than AgX's, so it is a touch rougher
const RED_ENV = 0.28;         // how much studio the lacquer red reflects live (0.45 ran hotter than the poster's deep red)

// house.py stage(): camera (9.8,-11.6,4.7) lens 105 on a 36mm sensor, target (1.05,-0.40,1.50), render 1500x1150
const CAM_POS = new THREE.Vector3(9.8, 4.7, 11.6);
const CAM_TGT = new THREE.Vector3(1.05, 1.50, 0.40);
const HFOV = 2 * Math.atan(18 / 105);
// poster.py prints this: the alpha crop of the full frame, padded to the page's 1400:1309 box
const CROP = { x: -5, y: -172, w: 1402, h: 1311 };

// brand/house.py COLORS (linear) and SURF (metalness, roughness), kept in step by hand
const COLORS = [[0.062, 0.074, 0.094], [0.030, 0.037, 0.050], [0.014, 0.020, 0.036], [0.34, 0.038, 0.040]];   // red opened a touch: AgX in the poster desaturates it, Neutral here does not
const SURF = [[0.78, 0.34], [0.80, 0.36], [0.85, 0.28], [0.40, 0.30]];
// brand/house.py SOFTBOXES: (blender direction, half-width deg, half-height deg, intensity, tint)
const SOFTBOXES = [
  [[4.6, -5.6, 6.2], 30, 20, 3.5, [1, 1, 1]],
  [[7.0, -3.0, 1.2], 5, 42, 9.0, [0.98, 0.99, 1]],
  [[-5.2, 4.8, 3.8], 5, 34, 6.5, [0.92, 0.95, 1]],
  [[0, 0, 1], 48, 7, 3.2, [1, 1, 1]],
  [[3.5, -6.5, -0.7], 46, 6, 2.4, [0.96, 0.97, 1]],
  [[-5, -5, 1.6], 24, 16, 1.8, [0.95, 0.96, 1]],
];

// the homepage program: which formation each section resolves to. A section not listed keeps the previous form.
// Companion mode docks the canvas bottom-right once the hero has scrolled away (set to false to keep it in the hero only).
const PROGRAM = [
  { sel: '#how', form: 'message' },      // 01 text a photo, get a price back
  { sel: '#services', form: 'couch' },   // 02 what we take
  { sel: '#areas', form: 'map' },        // 03 six cities
  { sel: '#proof', form: 'truck' },      // 04 the loads behind the rating
  { sel: '#faq', form: 'fridge' },       // 05 what do you take, can it go today
  { sel: '#contact', form: 'house' },    // 06 the house again, where the reader arrives
];
// size is the largest the companion gets; min is where it hides instead; gap is the clearance from the text column
const COMPANION = { size: 240, min: 108, right: 32, bottom: 28, gap: 28 };

const b2t = (v) => new THREE.Vector3(v[0], v[2], -v[1]);                       // blender -> three axes
const q2t = (q) => new THREE.Quaternion(q[0], q[2], -q[1], q[3]);              // same, for quaternions (x,y,z,w)
const s2t = (s) => new THREE.Vector3(s[0], s[2], s[1]);                        // scale ratios: axes swap only
const smooth = (a, b, x) => { const t = THREE.MathUtils.clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
const hash = (i, k) => { let h = (i * 374761393 + k * 668265263) | 0; h = ((h ^ (h >>> 13)) * 1274126177) | 0; return ((h ^ (h >>> 16)) >>> 0) / 4294967296; };

function studioTexture() {
  // the same procedural HDRI as brand/house.py write_studio(): three.js equirect, +Y up
  const W = 512, H = 256, data = new Float32Array(W * H * 4);
  const boxes = SOFTBOXES.map(([d, hw, hh, i, tint]) => {
    const c = b2t(d).normalize();
    const up = Math.abs(c.y) < 0.95 ? new THREE.Vector3(0, 1, 0) : new THREE.Vector3(1, 0, 0);
    const t1 = new THREE.Vector3().crossVectors(up, c).normalize();
    const t2 = new THREE.Vector3().crossVectors(c, t1);
    return { c, t1, t2, hw, hh, i, tint };
  });
  const dir = new THREE.Vector3();
  for (let y = 0; y < H; y++) {
    const el = ((y + 0.5) / H - 0.5) * Math.PI;                 // row 0 = straight down
    for (let x = 0; x < W; x++) {
      const az = ((x + 0.5) / W - 0.5) * 2 * Math.PI;           // three: u = atan2(z, x) / 2pi + 0.5
      dir.set(Math.cos(el) * Math.cos(az), Math.sin(el), Math.cos(el) * Math.sin(az));
      const t = dir.y;
      const sky = t < 0 ? 0.42 + (FLOOR - 0.42) * Math.pow(-t, 0.7) : 0.42 + (0.20 - 0.42) * Math.pow(t, 0.8);
      let r = sky * 0.96, g = sky * 0.975, b = sky;
      for (const bx of boxes) {
        const dot = dir.dot(bx.c);
        if (dot <= 0) continue;
        const a1 = THREE.MathUtils.radToDeg(Math.atan2(dir.dot(bx.t1), Math.max(dot, 1e-3)));
        const a2 = THREE.MathUtils.radToDeg(Math.atan2(dir.dot(bx.t2), Math.max(dot, 1e-3)));
        const m1 = THREE.MathUtils.clamp((bx.hw - Math.abs(a1)) / (bx.hw * 0.35), 0, 1);
        const m2 = THREE.MathUtils.clamp((bx.hh - Math.abs(a2)) / (bx.hh * 0.35), 0, 1);
        let m = (m1 * m1 * (3 - 2 * m1)) * (m2 * m2 * (3 - 2 * m2));
        m *= 1 - 0.35 * THREE.MathUtils.clamp((a2 / Math.max(bx.hh, 1e-3)) * 0.5 + 0.5, 0, 1);
        r += m * bx.i * bx.tint[0]; g += m * bx.i * bx.tint[1]; b += m * bx.i * bx.tint[2];
      }
      const o = (y * W + x) * 4;
      data[o] = r; data[o + 1] = g; data[o + 2] = b; data[o + 3] = 1;
    }
  }
  const tex = new THREE.DataTexture(data, W, H, THREE.RGBAFormat, THREE.FloatType);
  tex.mapping = THREE.EquirectangularReflectionMapping;
  tex.colorSpace = THREE.LinearSRGBColorSpace;
  tex.needsUpdate = true;
  return tex;
}

function shadowTexture() {
  const c = document.createElement('canvas'); c.width = c.height = 256;
  const g = c.getContext('2d');
  const grd = g.createRadialGradient(128, 128, 0, 128, 128, 128);
  grd.addColorStop(0, 'rgba(14,20,32,0.55)');
  grd.addColorStop(0.45, 'rgba(14,20,32,0.22)');
  grd.addColorStop(0.8, 'rgba(14,20,32,0.05)');
  grd.addColorStop(1, 'rgba(14,20,32,0)');
  g.fillStyle = grd; g.fillRect(0, 0, 256, 256);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}

export async function init(piece, opts = {}) {
  const program = opts.program || PROGRAM;
  const companion = opts.companion === undefined ? COMPANION : opts.companion;

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.NeutralToneMapping;
  renderer.toneMappingExposure = 1.3;
  renderer.setClearColor(0x000000, 0);

  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromEquirectangular(studioTexture()).texture;
  scene.environmentIntensity = 2.0;
  pmrem.dispose();

  const VFOV = THREE.MathUtils.radToDeg(2 * Math.atan(Math.tan(HFOV / 2) * 1150 / 1500));
  const camera = new THREE.PerspectiveCamera(VFOV, 1500 / 1150, 1, 60);
  camera.position.copy(CAM_POS);
  camera.lookAt(CAM_TGT);
  camera.setViewOffset(1500, 1150, CROP.x, CROP.y, CROP.w, CROP.h);

  // the Blender area lamps, same places: they carry the diffuse, the studio carries the reflections
  const key = new THREE.DirectionalLight(0xffffff, 1.7); key.position.set(4.6, 6.2, 5.6); key.target.position.copy(CAM_TGT); scene.add(key, key.target);
  const rim = new THREE.DirectionalLight(0xffffff, 1.6); rim.position.set(-5.2, 3.8, -4.8); rim.target.position.copy(CAM_TGT); scene.add(rim, rim.target);
  const fill = new THREE.DirectionalLight(0xffffff, 0.4); fill.position.set(-4.8, 2.2, 5.4); fill.target.position.copy(CAM_TGT); scene.add(fill, fill.target);

  const draco = new DRACOLoader();
  draco.setDecoderPath('https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/libs/draco/');
  const loader = new GLTFLoader();
  loader.setDRACOLoader(draco);
  const [gltf, shapes] = await Promise.all([
    loader.loadAsync('assets/house.glb?v=6'),
    fetch('assets/house-shapes.json?v=6').then((r) => r.json()),
  ]);
  const house = gltf.scene;
  const rig = new THREE.Group();          // the pivot the pointer lean and sway act on
  rig.position.set(0.9, 0.9, 0);
  house.position.set(-0.9, -0.9, 0);
  rig.add(house);
  scene.add(rig);
  house.updateMatrixWorld(true);

  // contact shadow under the plinth, drawn before everything so the base sits on it; fades as the house comes apart
  const shadow = new THREE.Mesh(new THREE.PlaneGeometry(1, 1),
    new THREE.MeshBasicMaterial({ map: shadowTexture(), transparent: true, depthWrite: false, toneMapped: false }));
  shadow.rotation.x = -Math.PI / 2;
  shadow.position.set(0.09, 0.002, 0);
  shadow.scale.set(3.0, 1.25, 1);
  shadow.renderOrder = -1;
  house.add(shadow);

  // ---- fragments: one mesh each, its own material, targets from shapes.json ----
  const FORMS = Object.keys(shapes.targets);
  const N = shapes.n;
  const frags = [];
  const colorOf = (c) => new THREE.Color().setRGB(COLORS[c][0], COLORS[c][1], COLORS[c][2], THREE.LinearSRGBColorSpace);
  for (let i = 0; i < N; i++) {
    const f = shapes.frags[i];
    const m = house.getObjectByName(f.name);
    if (!m || !m.isMesh) { console.warn('house: missing fragment', f.name); continue; }
    const c0 = shapes.targets.house[i].c;
    m.material = new THREE.MeshPhysicalMaterial({
      color: colorOf(c0).multiplyScalar(1 + f.v[0] * 2.2), metalness: SURF[c0][0], roughness: Math.max(0.06, SURF[c0][1] + f.v[1] + (c0 === 3 ? RED_ROUGH : 0)),
      clearcoat: SURF[c0][0] < 0.6 ? 0.22 : 0.18, clearcoatRoughness: 0.16, transparent: true,
    });
    m.material.envMapIntensity = c0 === 3 ? RED_ENV : 1;   // the lacquer red takes less of the studio, or it runs pink
    const targets = {};
    for (const k of FORMS) {
      const t = shapes.targets[k][i];
      const jit = k === 'house' ? 1 : JIT_FORM;
      targets[k] = { p: b2t(t.p), r: q2t(t.r), k: s2t(t.k), c: t.c, col: colorOf(t.c).multiplyScalar(1 + f.v[0] * 2.2 * jit),
        rough: Math.max(0.06, SURF[t.c][1] + f.v[1] * jit + (t.c === 3 ? RED_ROUGH : 0)) };
    }
    // stagger: blocks go first, then the roof, walls, gables, and the base last; a hash spreads each group
    const order = { lift: 0.0, inside: 0.12, roof: 0.2, wall: 0.45, gable: 0.55, base: 0.75 }[f.role] ?? 0.5;
    const d = THREE.MathUtils.clamp(order + hash(i, 1) * 0.22, 0, 0.95);
    const fly = new THREE.Vector3(hash(i, 2) - 0.5, 0.35 + hash(i, 3) * 0.5, hash(i, 4) - 0.5).normalize().multiplyScalar(0.5 + hash(i, 5) * 0.7);
    const spin = new THREE.Vector3(hash(i, 6) - 0.5, hash(i, 7) - 0.5, hash(i, 8) - 0.5).normalize();
    frags.push({ mesh: m, role: f.role, name: f.name, targets, d, fly, spin, spinAmt: (0.6 + hash(i, 9)) * (f.role === 'lift' ? 0.6 : 1), pull: new THREE.Vector3() });
  }

  // ---- the four travelling blocks: same arc as before, animated only in the house state ----
  const lifts = ['lift0', 'lift1', 'lift2', 'lift3'].map((n) => frags.find((f) => f.name === n)).filter(Boolean);
  let path = null, homeU = [], sizeAt = () => 1;
  if (lifts.length === 4) {
    const inside = new THREE.Vector3(0.72, 0.40, 0.02);
    const door = new THREE.Vector3(1.32, 0.62, 0.02);
    const l = lifts.map((o) => o.targets.house.p);
    const end = l[3].clone().add(l[3].clone().sub(l[2]).multiplyScalar(1.3));
    const pts = [inside, door, l[0], l[1], l[2], l[3], end];
    path = new THREE.CatmullRomCurve3(pts, false, 'catmullrom', 0.5);
    const n = pts.length - 1;
    homeU = [2 / n, 3 / n, 4 / n, 5 / n];
    const ext = (o) => { const s = shapes.frags[frags.indexOf(o)].s; return Math.max(s[0], s[1], s[2]); };
    const e0 = ext(lifts[0]), e3 = ext(lifts[3]);
    lifts.forEach((o) => { o.extent = ext(o); });
    sizeAt = (u) => THREE.MathUtils.clamp(e0 + (u - homeU[0]) * (e3 - e0) / (homeU[3] - homeU[0]), e3 * 0.55, e0 * 1.2);
  }
  const warp = (u) => {
    if (u < 0.10) return u * 0.6;
    if (u < 0.22) return 0.06 + (u - 0.10) * 0.5;
    const v = (u - 0.22) / 0.78;
    return 0.12 + 0.88 * (1 - Math.pow(1 - v, 1.6));
  };

  // ---- canvas in the piece, sized to the poster's aspect ----
  const canvas = renderer.domElement;
  piece.appendChild(canvas);
  let docked = 0;   // 0 = in the hero, 1 = companion in the corner
  function resize() {
    const w = piece.clientWidth, h = piece.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
    if (docked) applyDock(docked, true);
  }
  resize();
  addEventListener('resize', resize);

  // docking: the canvas leaves the hero box and settles beside the text column as a small companion, scrubbed by scroll.
  // Where it lands: just right of the widest text column (so on a wide screen the travel is short and it stays by
  // the reading line), clamped inside the window. If the column leaves no room it shrinks, and below companion.min
  // it hides. Under the footer it fades, so it never covers a footer link. It never takes pointer events.
  let pr = null;
  const columns = Array.from(document.querySelectorAll('main .column'));
  const footer = document.querySelector('footer');
  function dockRect() {
    const s = companion.size, r = piece.getBoundingClientRect(), ar = r.width / r.height;
    let colRight = 0;
    for (const c of columns) { const cr = c.getBoundingClientRect(); if (cr.width && cr.right > colRight) colRight = cr.right; }
    const room = innerWidth - companion.right - (colRight + companion.gap);
    const w1 = Math.max(1, Math.min(s, room));
    const h1 = w1 / ar;
    const x1 = Math.min(colRight + companion.gap, innerWidth - companion.right - w1);
    return { w1, h1, x1, y1: innerHeight - companion.bottom - h1, ok: w1 >= companion.min };
  }
  function applyDock(k, force) {
    if (!companion) return;
    const r = piece.getBoundingClientRect();
    if (k <= 0.001) {
      if (docked > 0.001 || force) { canvas.style.cssText = ''; }
      docked = 0; return;
    }
    const d = dockRect();
    const e = k * k * (3 - 2 * k);
    const w = r.width + (d.w1 - r.width) * e, h = r.height + (d.h1 - r.height) * e;
    const x = r.left + (d.x1 - r.left) * e, y = r.top + (d.y1 - r.top) * e;
    // fade: no room beside the column, or the footer has risen under the companion
    let op = d.ok ? 1 : 1 - e;
    if (footer) { const ft = footer.getBoundingClientRect().top; op *= 1 - smooth(innerHeight, innerHeight - d.h1 - companion.bottom, ft); }
    canvas.style.cssText = `position:fixed;inset:auto;left:${x}px;top:${y}px;width:${w}px !important;height:${h}px !important;z-index:2;pointer-events:none;opacity:${op.toFixed(3)}`;
    if (Math.abs(w - pr) > 1) { renderer.setSize(Math.round(w), Math.round(h), false); pr = w; }
    docked = k;
  }

  // ---- the program: scroll -> which two formations, and how far between them ----
  const stops = program.map((s) => ({ el: document.querySelector(s.sel), form: s.form })).filter((s) => s.el && shapes.targets[s.form]);
  let fromForm = 'house', toForm = 'house', mix = 0, dockWant = 0, heroGone = 0;
  function readScroll() {
    const r = piece.getBoundingClientRect();
    // the hero leaving: the piece's bottom crossing up through the viewport. 0 in place, 1 fully gone.
    heroGone = smooth(innerHeight * 0.55, -r.height * 0.2, r.bottom);
    dockWant = companion ? heroGone : 0;
    // formation: walk the stops; a stop takes over as its top rises from 85% to 35% of the viewport
    let a = 'house', b = 'house', m = 0;
    for (const s of stops) {
      const t = s.el.getBoundingClientRect().top;
      const k = smooth(innerHeight * 0.85, innerHeight * 0.35, t);
      if (k <= 0) break;
      a = b; b = s.form; m = k;
      if (k < 1) break;
    }
    if (m >= 1) { a = b; m = 0; }
    fromForm = a; toForm = b; mix = m;
  }
  addEventListener('scroll', readScroll, { passive: true });
  readScroll();

  // ---- pointer: lean over the whole window, pull only while the hand is over the hero ----
  let px = 0, py = 0, yaw = 0, pitch = 0, over = 0, wantOver = 0;
  const ray = new THREE.Raycaster(), ndc = new THREE.Vector2(), plane = new THREE.Plane(new THREE.Vector3(0, 0, 1), 0), hit = new THREE.Vector3(), hitL = new THREE.Vector3();
  let hitOk = false;
  addEventListener('pointermove', (e) => {
    const r = piece.getBoundingClientRect();
    px = THREE.MathUtils.clamp((e.clientX - (r.left + r.width / 2)) / innerWidth * 2, -1, 1);
    py = THREE.MathUtils.clamp((e.clientY - (r.top + r.height / 2)) / innerHeight * 2, -1, 1);
    const inside = e.clientX >= r.left - 40 && e.clientX <= r.right + 40 && e.clientY >= r.top - 40 && e.clientY <= r.bottom + 40;
    wantOver = inside ? 1 : 0;
    if (inside) {
      ndc.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
      ray.setFromCamera(ndc, camera);
      plane.constant = 0.7;
      hitOk = !!ray.ray.intersectPlane(plane, hit);
      if (hitOk) house.worldToLocal(hitL.copy(hit));
    }
  }, { passive: true });
  document.documentElement.addEventListener('pointerleave', () => { px = 0; py = 0; wantOver = 0; });
  let beat = 0;
  piece.addEventListener('pointerdown', () => { beat = 1; }, { passive: true });

  // ---- run only while something of it is on screen and the tab is visible ----
  let visible = true, hidden = document.hidden, raf = 0, last = performance.now(), t = 0, shown = false;
  new IntersectionObserver((es) => { visible = es[0].isIntersecting || dockWant > 0; kick(); }, { threshold: 0.02 }).observe(piece);
  document.addEventListener('visibilitychange', () => { hidden = document.hidden; kick(); });
  addEventListener('scroll', kick, { passive: true });
  function kick() { if (!hidden && !raf) { last = performance.now(); raf = requestAnimationFrame(frame); } }

  const q = new THREE.Quaternion(), qa = new THREE.Quaternion(), qb = new THREE.Quaternion(), axis = new THREE.Vector3(), toP = new THREE.Vector3();
  const pa = new THREE.Vector3(), pb = new THREE.Vector3(), sa = new THREE.Vector3(), sb = new THREE.Vector3(), ca = new THREE.Color();
  let mixS = 0, dockS = 0, showFrom = 'house', showTo = 'house';
  const K = 0.5;   // each fragment's own transition takes this share of the whole, staggered by d

  function frame(now) {
    raf = 0;
    if (hidden) return;
    if (!visible && dockS < 0.001 && mixS < 0.001) return;
    const dt = Math.min(0.05, (now - last) / 1000); last = now;
    beat = THREE.MathUtils.damp(beat, 0, 1.1, dt);
    t += dt * (1 + beat * 5);
    over = THREE.MathUtils.damp(over, wantOver, 3, dt);

    // settle toward the scroll targets rather than snapping, so the object responds and then comes to rest
    if (showTo !== toForm || showFrom !== fromForm) {
      // the pair changed: continue from where the fragments are by re-basing the mix
      if (showTo === fromForm) { showFrom = showTo; showTo = toForm; mixS = 0; }
      else { showFrom = fromForm; showTo = toForm; mixS = Math.min(mixS, mix); }
    }
    mixS = THREE.MathUtils.damp(mixS, mix, 6, dt);
    dockS = THREE.MathUtils.damp(dockS, dockWant, 5, dt);
    applyDock(dockS);

    // orientation: idle sway + pointer lean; the companion turns a little more so the form shows its face
    const sway = Math.sin(t * (2 * Math.PI / 11)) * SWAY;
    yaw = THREE.MathUtils.damp(yaw, px * POINTER_YAW * (1 - dockS) + sway, 3.2, dt);
    pitch = THREE.MathUtils.damp(pitch, py * POINTER_PITCH * (1 - dockS) + Math.sin(t * (2 * Math.PI / 13)) * 0.008, 3.2, dt);
    rig.rotation.set(pitch, yaw, 0);

    const inHouse = (showFrom === 'house' ? 1 - mixS : 0) + (showTo === 'house' ? mixS : 0);
    shadow.material.opacity = inHouse;
    shadow.visible = inHouse > 0.01;

    for (const o of frags) {
      const A = o.targets[showFrom], B = o.targets[showTo];
      pa.copy(A.p); qa.copy(A.r); sa.copy(A.k);
      pb.copy(B.p); qb.copy(B.r); sb.copy(B.k);
      let opA = 1, opB = 1;
      // in the house state the four blocks ride their arc
      if (path && o.extent) {
        const i = lifts.indexOf(o);
        const u = warp((homeU[i] + t / CYCLE) % 1);
        const s = sizeAt(u) / o.extent;
        const op = smooth(0.09, 0.20, u) * (1 - smooth(0.84, 0.94, u));
        axis.set(0.6 + i * 0.1, 1, 0.3 - i * 0.15).normalize();
        q.setFromAxisAngle(axis, t * (0.16 + i * 0.03));
        if (showFrom === 'house') { path.getPointAt(u, pa); sa.setScalar(s); qa.multiply(q); opA = op; }
        if (showTo === 'house') { path.getPointAt(u, pb); sb.setScalar(s); qb.multiply(q); opB = op; }
        // pointer pull, only in the house at rest
        let want = 0;
        if (hitOk && over > 0.01 && u > 0.26 && u < 0.85 && inHouse > 0.5) {
          toP.copy(hitL).sub(pa);
          const dd = toP.length();
          want = over * PULL * Math.exp(-dd * dd / 4.5) * (1 - i * 0.12) * inHouse;
          toP.normalize().multiplyScalar(want);
        } else toP.set(0, 0, 0);
        o.pull.x = THREE.MathUtils.damp(o.pull.x, toP.x, 2.4, dt);
        o.pull.y = THREE.MathUtils.damp(o.pull.y, toP.y, 2.4, dt);
        o.pull.z = THREE.MathUtils.damp(o.pull.z, toP.z, 2.4, dt);
        pa.add(o.pull);
      }
      // this fragment's own progress through the transition, staggered
      const lt = showFrom === showTo ? 0 : smooth(0, 1, (mixS - o.d * (1 - K)) / K);
      const arc = Math.sin(Math.PI * lt);
      o.mesh.position.lerpVectors(pa, pb, lt).addScaledVector(o.fly, arc);
      o.mesh.quaternion.slerpQuaternions(qa, qb, lt);
      if (arc > 0.001) { q.setFromAxisAngle(o.spin, arc * o.spinAmt); o.mesh.quaternion.multiply(q); }
      o.mesh.scale.lerpVectors(sa, sb, lt);
      ca.copy(A.col).lerp(B.col, lt);
      o.mesh.material.color.copy(ca);
      o.mesh.material.metalness = SURF[A.c][0] + (SURF[B.c][0] - SURF[A.c][0]) * lt;
      o.mesh.material.roughness = A.rough + (B.rough - A.rough) * lt;
      o.mesh.material.envMapIntensity = (A.c === 3 ? RED_ENV : 1) + ((B.c === 3 ? RED_ENV : 1) - (A.c === 3 ? RED_ENV : 1)) * lt;
      o.mesh.material.opacity = opA + (opB - opA) * lt;
      o.mesh.visible = o.mesh.material.opacity > 0.01;
    }

    renderer.render(scene, camera);
    if (!shown) { shown = true; piece.classList.add('live'); }
    raf = requestAnimationFrame(frame);
  }
  kick();
  return { renderer, scene, camera, house, rig, frags, forms: FORMS, readScroll };
}
