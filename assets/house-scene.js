/* The live house. Loaded by house.js only when it is worth it (see the gate there).
   Camera, lens and target are the Blender ones from brand/house.py, converted to glTF axes (Blender Y -> -Z,
   Blender Z -> Y), so the first live frame sits exactly where the poster sat.

   v2 (2026-09-22): rebuilt for the closed house with the door on the right face.
   - blocks are MeshPhysicalMaterial with a light clearcoat, so the edges catch a real highlight
   - a soft contact shadow under the plinth, the same one poster.py bakes into the poster
   - a deliberate cycle: each block dwells in the doorway, then lifts with ease-out and fades near the top
   - an idle sway of the whole object, the pointer leans it and pulls the blocks a little, and both settle back
   - a click on the hero is a "clear-out" beat: the stream runs fast for a moment, then returns to its pace */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const LIFTS = ['lift0', 'lift1', 'lift2', 'lift3'];
const CYCLE = 24;             // seconds for one block to travel the whole arc: a new one clears the door every 6s
const POINTER_YAW = 0.16;     // radians of lean toward the pointer, either way
const POINTER_PITCH = 0.06;
const SWAY = 0.035;           // idle yaw sway, radians
const PULL = 0.28;            // how far (world units) a block drifts toward the pointer when it is over the hero

// house.py stage(): camera (9.8,-11.6,4.7) lens 105 on a 36mm sensor, target (1.05,-0.40,1.50), render 1500x1150
const CAM_POS = new THREE.Vector3(9.8, 4.7, 11.6);
const CAM_TGT = new THREE.Vector3(1.05, 1.50, 0.40);
const HFOV = 2 * Math.atan(18 / 105);
// poster.py prints this: the alpha crop of the full frame, padded to the page's 1400:1309 box
const CROP = { x: 21, y: -145, w: 1376, h: 1287 };

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

export async function init(piece) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.NeutralToneMapping;
  renderer.toneMappingExposure = 1.35;
  renderer.setClearColor(0x000000, 0);

  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 0.9;
  pmrem.dispose();

  const VFOV = THREE.MathUtils.radToDeg(2 * Math.atan(Math.tan(HFOV / 2) * 1150 / 1500));
  const camera = new THREE.PerspectiveCamera(VFOV, 1500 / 1150, 1, 60);
  camera.position.copy(CAM_POS);
  camera.lookAt(CAM_TGT);
  camera.setViewOffset(1500, 1150, CROP.x, CROP.y, CROP.w, CROP.h);

  // the Blender lamps, same places: key front-right-high (door side), rim back-left, soft fill front-left
  const key = new THREE.DirectionalLight(0xffffff, 2.4); key.position.set(4.6, 6.2, 5.6); key.target.position.copy(CAM_TGT); scene.add(key, key.target);
  const rim = new THREE.DirectionalLight(0xffffff, 2.2); rim.position.set(-5.2, 3.8, -4.8); rim.target.position.copy(CAM_TGT); scene.add(rim, rim.target);
  const fill = new THREE.DirectionalLight(0xffffff, 0.55); fill.position.set(-4.8, 2.2, 5.4); fill.target.position.copy(CAM_TGT); scene.add(fill, fill.target);

  const draco = new DRACOLoader();
  draco.setDecoderPath('https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/libs/draco/');
  const loader = new GLTFLoader();
  loader.setDRACOLoader(draco);
  const gltf = await loader.loadAsync('assets/house.glb?v=4');
  const house = gltf.scene;
  const rig = new THREE.Group();          // the pivot the pointer lean and sway act on
  rig.position.set(0.9, 0.9, 0);          // roughly the object's visual centre, so a lean turns it rather than swinging it
  house.position.set(-0.9, -0.9, 0);
  rig.add(house);
  scene.add(rig);
  house.updateMatrixWorld(true);

  // contact shadow under the plinth, drawn before everything so the base sits on it
  const shadow = new THREE.Mesh(new THREE.PlaneGeometry(1, 1),
    new THREE.MeshBasicMaterial({ map: shadowTexture(), transparent: true, depthWrite: false, toneMapped: false }));
  shadow.rotation.x = -Math.PI / 2;
  shadow.position.set(0.09, 0.002, 0);
  shadow.scale.set(3.0, 1.25, 1);
  shadow.renderOrder = -1;
  house.add(shadow);

  // ---- materials: the shell stays matte, the blocks get a light clearcoat so their edges pick up the key ----
  house.traverse((m) => {
    if (!m.isMesh) return;
    const src = m.material;
    if (/^(lift|inside)/.test(m.name)) {
      const p = new THREE.MeshPhysicalMaterial({ color: src.color, metalness: src.metalness, roughness: src.roughness, clearcoat: 0.55, clearcoatRoughness: 0.28 });
      m.material = p;
    } else {
      src.envMapIntensity = 0.55;   // the walls take a little of the room, not a mirror of it
    }
  });

  // ---- the four travelling blocks ----
  const lifts = [];
  const box = new THREE.Box3();
  const size = new THREE.Vector3();
  for (const name of LIFTS) {
    const m = house.getObjectByName(name);
    if (!m || !m.isMesh) continue;
    m.updateMatrixWorld(true);
    box.setFromObject(m);
    const homeW = box.getCenter(new THREE.Vector3());
    const home = house.worldToLocal(homeW.clone());
    box.getSize(size);
    // the exporter may have baked the offset into the geometry: put the pivot at the block's centre either way
    const local = m.worldToLocal(homeW.clone());
    if (local.length() > 1e-4) { m.geometry.translate(-local.x, -local.y, -local.z); m.position.add(local.applyQuaternion(m.quaternion).multiply(m.scale)); }
    m.material = m.material.clone();
    m.material.transparent = true;
    lifts.push({ mesh: m, home, quat: m.quaternion.clone(), baseScale: m.scale.clone(), extent: Math.max(size.x, size.y, size.z), pull: new THREE.Vector3() });
  }
  lifts.sort((a, b) => LIFTS.indexOf(a.mesh.name) - LIFTS.indexOf(b.mesh.name));

  let path = null, homeU = [], sizeAt = () => 1;
  if (lifts.length === 4) {
    // house.py: inside block (0.72,-0.02,0.37) and the doorway on the right face at x = W/2 (glTF: y up, z = -Blender y)
    const inside = new THREE.Vector3(0.72, 0.40, 0.02);
    const door = new THREE.Vector3(1.32, 0.62, 0.02);
    const l = lifts.map((o) => o.home);
    const end = l[3].clone().add(l[3].clone().sub(l[2]).multiplyScalar(1.3));
    const pts = [inside, door, l[0], l[1], l[2], l[3], end];
    path = new THREE.CatmullRomCurve3(pts, false, 'catmullrom', 0.5);
    const n = pts.length - 1;
    homeU = [2 / n, 3 / n, 4 / n, 5 / n];
    const e0 = lifts[0].extent, e3 = lifts[3].extent;
    sizeAt = (u) => THREE.MathUtils.clamp(e0 + (u - homeU[0]) * (e3 - e0) / (homeU[3] - homeU[0]), e3 * 0.55, e0 * 1.2);
  }
  // time -> path parameter with a dwell in the doorway (u about 0.12 to 0.2) and ease-out on the lift.
  // A block is "inside" for the first 12 percent, waits, then goes. Monotonic, so the order never changes.
  const warp = (u) => {
    if (u < 0.10) return u * 0.6;                                 // still inside, barely moving
    if (u < 0.22) return 0.06 + (u - 0.10) * 0.5;                  // creeping into the doorway
    const v = (u - 0.22) / 0.78;                                   // the lift: ease-out so it leaves quick and drifts
    return 0.12 + 0.88 * (1 - Math.pow(1 - v, 1.6));
  };

  // ---- canvas in the piece, sized to the poster's aspect ----
  const canvas = renderer.domElement;
  piece.appendChild(canvas);
  function resize() {
    const w = piece.clientWidth, h = piece.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
  }
  resize();
  addEventListener('resize', resize);

  // ---- pointer: lean over the whole window, pull only while the hand is over the hero ----
  let px = 0, py = 0, yaw = 0, pitch = 0, over = 0, overT = 0, wantOver = 0;
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
      // the blocks travel roughly in the plane z = -0.7 (Blender y 0.7 toward the camera): intersect that
      plane.constant = 0.7;
      hitOk = !!ray.ray.intersectPlane(plane, hit);
      if (hitOk) house.worldToLocal(hitL.copy(hit));
    }
  }, { passive: true });
  document.documentElement.addEventListener('pointerleave', () => { px = 0; py = 0; wantOver = 0; });
  // a click on the hero: a clear-out beat, the stream runs fast for a moment then settles to its pace
  let beat = 0;
  piece.addEventListener('pointerdown', () => { beat = 1; }, { passive: true });

  // ---- run only while on screen and the tab is visible ----
  let visible = true, hidden = document.hidden, raf = 0, last = performance.now(), t = 0, shown = false;
  new IntersectionObserver((es) => { visible = es[0].isIntersecting; kick(); }, { threshold: 0.05 }).observe(piece);
  document.addEventListener('visibilitychange', () => { hidden = document.hidden; kick(); });
  function kick() { if (visible && !hidden && !raf) { last = performance.now(); raf = requestAnimationFrame(frame); } }

  const q = new THREE.Quaternion(), axis = new THREE.Vector3(), toP = new THREE.Vector3(), tmp = new THREE.Vector3();
  function frame(now) {
    raf = 0;
    if (!visible || hidden) return;
    const dt = Math.min(0.05, (now - last) / 1000); last = now;
    beat = THREE.MathUtils.damp(beat, 0, 1.1, dt);
    t += dt * (1 + beat * 5);
    over = THREE.MathUtils.damp(over, wantOver, 3, dt);
    overT += dt;

    // orientation: idle sway + pointer lean, both damped so the object settles rather than stops
    const sway = Math.sin(t * (2 * Math.PI / 11)) * SWAY;
    yaw = THREE.MathUtils.damp(yaw, px * POINTER_YAW + sway, 3.2, dt);
    pitch = THREE.MathUtils.damp(pitch, py * POINTER_PITCH + Math.sin(t * (2 * Math.PI / 13)) * 0.008, 3.2, dt);
    rig.rotation.set(pitch, yaw, 0);

    if (path) {
      for (let i = 0; i < 4; i++) {
        const o = lifts[i];
        const u = warp((homeU[i] + t / CYCLE) % 1);
        path.getPointAt(u, o.mesh.position);
        // pointer pull: only once the block is out of the door, stronger for the nearer blocks, settles back when the hand goes
        let want = 0;
        if (hitOk && over > 0.01 && u > 0.26 && u < 0.85) {
          toP.copy(hitL).sub(o.mesh.position);
          const d = toP.length();
          want = over * PULL * Math.exp(-d * d / 4.5) * (1 - i * 0.12);
          toP.normalize().multiplyScalar(want);
        } else toP.set(0, 0, 0);
        o.pull.x = THREE.MathUtils.damp(o.pull.x, toP.x, 2.4, dt);
        o.pull.y = THREE.MathUtils.damp(o.pull.y, toP.y, 2.4, dt);
        o.pull.z = THREE.MathUtils.damp(o.pull.z, toP.z, 2.4, dt);
        o.mesh.position.add(o.pull);
        const s = sizeAt(u) / o.extent;
        o.mesh.scale.copy(o.baseScale).multiplyScalar(s);
        // a slow tumble on top of the block's own resting angle, each on its own axis; faster during a beat
        axis.set(0.6 + i * 0.1, 1, 0.3 - i * 0.15).normalize();
        q.setFromAxisAngle(axis, t * (0.16 + i * 0.03));
        o.mesh.quaternion.copy(o.quat).multiply(q);
        // hidden inside, in through the doorway, out before the top of the crop
        o.mesh.material.opacity = THREE.MathUtils.smoothstep(u, 0.09, 0.20) * (1 - THREE.MathUtils.smoothstep(u, 0.84, 0.94));
        o.mesh.visible = o.mesh.material.opacity > 0.01;
      }
    }

    renderer.render(scene, camera);
    if (!shown) { shown = true; piece.classList.add('live'); }
    raf = requestAnimationFrame(frame);
  }
  kick();
  return { renderer, scene, camera, house, rig, lifts };
}
