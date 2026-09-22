/* The live house. Loaded by house.js only when it is worth it (see the gate there).
   Camera, lens and target are the Blender ones from brand/house.py, converted to glTF axes (Blender Y -> -Z,
   Blender Z -> Y), so the first live frame sits exactly where the poster sat. */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const LIFTS = ['lift0', 'lift1', 'lift2', 'lift3'];
const CYCLE = 22;            // seconds for one block to travel the whole arc; a new one clears the door every ~3.7s
const POINTER_YAW = 0.12;    // radians of lean toward the pointer, either way
const POINTER_PITCH = 0.05;

// house.py stage(): camera (-10.8,-12.8,6.4) lens 105 on a 36mm sensor, target (-0.85,-0.70,1.35), render 1500x1150
const CAM_POS = new THREE.Vector3(-10.8, 6.4, 12.8);
const CAM_TGT = new THREE.Vector3(-0.85, 1.35, 0.70);
const HFOV = 2 * Math.atan(18 / 105);

export async function init(piece) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.NeutralToneMapping;
  renderer.toneMappingExposure = 1.7;
  renderer.setClearColor(0x000000, 0);

  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 1.15;
  pmrem.dispose();

  // full Blender frame: 1500x1150, vertical fov from the 36mm sensor fit to width; the poster is the alpha
  // crop (394,198)-(1201,953) of that frame, so the live camera renders exactly that window of it
  const VFOV = THREE.MathUtils.radToDeg(2 * Math.atan(Math.tan(HFOV / 2) * 1150 / 1500));
  const camera = new THREE.PerspectiveCamera(VFOV, 1500 / 1150, 1, 60);
  camera.position.copy(CAM_POS);
  camera.lookAt(CAM_TGT);
  camera.setViewOffset(1500, 1150, 394, 198, 807, 755);

  // the Blender lamps, same places: key front-left-high, rim back-right, soft fill front-right
  const key = new THREE.DirectionalLight(0xffffff, 2.2); key.position.set(-4.0, 6.0, 5.4); key.target.position.copy(CAM_TGT); scene.add(key, key.target);
  const rim = new THREE.DirectionalLight(0xffffff, 2.6); rim.position.set(5.4, 3.6, -4.8); rim.target.position.copy(CAM_TGT); scene.add(rim, rim.target);
  const fill = new THREE.DirectionalLight(0xffffff, 0.6); fill.position.set(4.6, 2.4, 5.6); fill.target.position.copy(CAM_TGT); scene.add(fill, fill.target);

  const draco = new DRACOLoader();
  draco.setDecoderPath('https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/libs/draco/');
  const loader = new GLTFLoader();
  loader.setDRACOLoader(draco);
  const gltf = await loader.loadAsync('assets/house.glb');
  const house = gltf.scene;
  scene.add(house);
  house.updateMatrixWorld(true);

  // ---- the four travelling blocks ----
  const lifts = [];
  const box = new THREE.Box3();
  const size = new THREE.Vector3();
  for (const name of LIFTS) {
    const m = house.getObjectByName(name);
    if (!m || !m.isMesh) continue;
    m.updateMatrixWorld(true);
    box.setFromObject(m);
    const home = box.getCenter(new THREE.Vector3());
    box.getSize(size);
    // the exporter may have baked the offset into the geometry: put the pivot at the block's centre either way
    const local = m.worldToLocal(home.clone());
    if (local.length() > 1e-4) { m.geometry.translate(-local.x, -local.y, -local.z); m.position.add(local.applyQuaternion(m.quaternion).multiply(m.scale)); }
    m.material = m.material.clone();
    m.material.transparent = true;
    lifts.push({ mesh: m, home, quat: m.quaternion.clone(), baseScale: m.scale.clone(), extent: Math.max(size.x, size.y, size.z) });
  }
  lifts.sort((a, b) => LIFTS.indexOf(a.mesh.name) - LIFTS.indexOf(b.mesh.name));

  let path = null, homeU = [], sizeAt = () => 1;
  if (lifts.length === 4) {
    const inside = new THREE.Vector3(0.10, 0.48, -0.10);
    const door = new THREE.Vector3(-0.05, 0.56, 0.98);
    const l = lifts.map((o) => o.home);
    const end = l[3].clone().add(l[3].clone().sub(l[2]).multiplyScalar(1.25));
    const pts = [inside, door, l[0], l[1], l[2], l[3], end];
    path = new THREE.CatmullRomCurve3(pts, false, 'catmullrom', 0.5);
    const n = pts.length - 1;
    homeU = [2 / n, 3 / n, 4 / n, 5 / n];
    // size: the real extents at the four home params, linear through them, clamped
    const e0 = lifts[0].extent, e3 = lifts[3].extent;
    sizeAt = (u) => THREE.MathUtils.clamp(e0 + (u - homeU[0]) * (e3 - e0) / (homeU[3] - homeU[0]), e3 * 0.55, e0 * 1.25);
  }

  // ---- canvas in the piece, sized to the poster's aspect ----
  const canvas = renderer.domElement;
  piece.appendChild(canvas);
  function resize() {
    const w = piece.clientWidth, h = piece.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h, false);   // the crop's aspect is fixed by CSS (1400/1309); the view offset does the rest
  }
  resize();
  addEventListener('resize', resize);

  // ---- pointer lean, measured over the whole window so the house answers the hand anywhere on the hero ----
  let px = 0, py = 0, yaw = 0, pitch = 0;
  addEventListener('pointermove', (e) => {
    const r = piece.getBoundingClientRect();
    px = THREE.MathUtils.clamp((e.clientX - (r.left + r.width / 2)) / innerWidth * 2, -1, 1);
    py = THREE.MathUtils.clamp((e.clientY - (r.top + r.height / 2)) / innerHeight * 2, -1, 1);
  }, { passive: true });
  addEventListener('pointerleave', () => { px = 0; py = 0; });

  // ---- run only while on screen and the tab is visible ----
  let visible = true, hidden = document.hidden, raf = 0, last = performance.now(), t = 0, shown = false;
  new IntersectionObserver((es) => { visible = es[0].isIntersecting; kick(); }, { threshold: 0.05 }).observe(piece);
  document.addEventListener('visibilitychange', () => { hidden = document.hidden; kick(); });
  function kick() { if (visible && !hidden && !raf) { last = performance.now(); raf = requestAnimationFrame(frame); } }

  const tmp = new THREE.Vector3(), q = new THREE.Quaternion(), axis = new THREE.Vector3();
  function frame(now) {
    raf = 0;
    if (!visible || hidden) return;
    const dt = Math.min(0.05, (now - last) / 1000); last = now; t += dt;

    yaw = THREE.MathUtils.damp(yaw, px * POINTER_YAW, 4, dt);
    pitch = THREE.MathUtils.damp(pitch, py * POINTER_PITCH, 4, dt);
    house.rotation.set(pitch, yaw, 0);

    if (path) {
      for (let i = 0; i < 4; i++) {
        const o = lifts[i];
        const u = (homeU[i] + t / CYCLE) % 1;
        path.getPointAt(u, o.mesh.position);
        const s = sizeAt(u) / o.extent;
        o.mesh.scale.copy(o.baseScale).multiplyScalar(s);
        // a slow tumble on top of the block's own resting angle, each on its own axis
        axis.set(0.6 + i * 0.1, 1, 0.3 - i * 0.15).normalize();
        q.setFromAxisAngle(axis, t * (0.18 + i * 0.03));
        o.mesh.quaternion.copy(o.quat).multiply(q);
        // in through the doorway, out at the top of the arc
        o.mesh.material.opacity = THREE.MathUtils.smoothstep(u, 0.10, 0.24) * (1 - THREE.MathUtils.smoothstep(u, 0.80, 0.92));   // gone before the crop edge
        o.mesh.visible = o.mesh.material.opacity > 0.01;
      }
    }

    renderer.render(scene, camera);
    if (!shown) { shown = true; piece.classList.add('live'); }
    raf = requestAnimationFrame(frame);
  }
  kick();
  return { renderer, scene, camera, house, lifts };
}
