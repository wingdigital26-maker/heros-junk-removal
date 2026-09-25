/*
 * Hero's piece2: ONE object of ~1,600 identical navy cubes that takes itself
 * apart and rebuilds as a house -> truck + trailer -> couch -> the Hero's H,
 * driven by scroll.
 *
 *   import { mount } from './assets/piece2/piece.js';
 *   mount(document.querySelector('#piece'));
 *
 * The host page needs an import map so the three.js example modules resolve
 * to the same pinned build:
 *   <script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.169.0/build/three.module.js"}}</script>
 *
 * Data: shapes.json (from brand/morph2/build.py). Fallback (reduced motion or
 * no WebGL): the four Blender posters, stacked.
 */
import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.169.0/build/three.module.js';
import { RoundedBoxGeometry } from 'https://cdn.jsdelivr.net/npm/three@0.169.0/examples/jsm/geometries/RoundedBoxGeometry.js';
import { RoomEnvironment } from 'https://cdn.jsdelivr.net/npm/three@0.169.0/examples/jsm/environments/RoomEnvironment.js';

const FORMS = ['house', 'truck', 'couch', 'h'];
const CAPTIONS = ['Your house', 'Our truck', 'The couch', "Hero's"];
const NAVY = 0x14284b;
const HERE = (p) => new URL(p, import.meta.url).href;

const CSS = `
.p2{position:relative;height:400vh;height:400svh}
.p2-stage{position:sticky;top:0;height:100vh;height:100svh;overflow:hidden}
.p2-stage canvas{position:absolute;inset:0;width:100%!important;height:100%!important;display:block;touch-action:pan-y}
.p2-cap{position:absolute;left:clamp(20px,4vw,56px);bottom:clamp(24px,6vh,64px);font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif;pointer-events:none}
.p2-cap span{position:absolute;left:0;bottom:0;white-space:nowrap;opacity:0;transition:none}
.p2-cap b{display:block;font-weight:600;font-size:clamp(22px,2.4vw,34px);letter-spacing:-.02em;color:#14284B;line-height:1.1}
.p2-cap i{display:block;font-style:normal;font-weight:500;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:#7A8394;margin-bottom:8px}
.p2-rail{position:absolute;right:clamp(20px,4vw,56px);bottom:clamp(30px,6vh,70px);display:flex;gap:6px;pointer-events:none}
.p2-rail u{display:block;width:22px;height:2px;background:#D5D9E0;text-decoration:none}
.p2-rail u>s{display:block;height:100%;width:0;background:#14284B}
.p2-still{display:grid;gap:clamp(16px,3vw,32px);padding:clamp(16px,3vw,40px) 0}
.p2-still figure{margin:0}
.p2-still img{width:100%;max-width:960px;height:auto;display:block;margin:0 auto}
.p2-still figcaption{font-family:Inter,system-ui,sans-serif;font-weight:600;color:#14284B;font-size:20px;text-align:center;margin-top:4px}
`;

function injectCSS() {
  if (document.getElementById('p2-css')) return;
  const s = document.createElement('style');
  s.id = 'p2-css';
  s.textContent = CSS;
  document.head.appendChild(s);
}

function webglOK() {
  try {
    const c = document.createElement('canvas');
    return !!(window.WebGLRenderingContext && (c.getContext('webgl2') || c.getContext('webgl')));
  } catch (e) { return false; }
}

function mountStill(el) {
  el.classList.add('p2-still');
  el.innerHTML = FORMS.map((f, i) =>
    `<figure><img src="${HERE(`poster-${f}.webp`)}" width="1600" height="1200" loading="lazy" alt="${CAPTIONS[i]}, built from navy cubes"><figcaption>${CAPTIONS[i]}</figcaption></figure>`
  ).join('');
}

const clamp01 = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);
const easeInOut = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const smooth = (t) => t * t * (3 - 2 * t);

// Scroll progress (0..1) -> continuous form index (0..3) with holds on every form.
function formAt(p) {
  const q = clamp01((p - 0.05) / 0.9) * 3;          // short hold at both ends
  const i = Math.min(2, Math.floor(q));
  const x = q - i;
  const HOLD = 0.2;                                 // each side of a transition
  return i + smooth(clamp01((x - HOLD) / (1 - 2 * HOLD)));
}

export async function mount(el) {
  injectCSS();
  const reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduced || !webglOK()) { mountStill(el); return; }

  let data;
  try {
    data = await (await fetch(HERE('shapes.json'))).json();
  } catch (e) { mountStill(el); return; }
  const N = data.n;

  el.classList.add('p2');
  el.innerHTML = '';
  const stage = document.createElement('div');
  stage.className = 'p2-stage';
  el.appendChild(stage);

  // ---- captions + progress rail
  const cap = document.createElement('div');
  cap.className = 'p2-cap';
  cap.setAttribute('aria-live', 'polite');
  const capSpans = CAPTIONS.map((t, i) => {
    const s = document.createElement('span');
    s.innerHTML = `<i>0${i + 1} / 04</i><b>${t}</b>`;
    cap.appendChild(s);
    return s;
  });
  const rail = document.createElement('div');
  rail.className = 'p2-rail';
  const railFill = [0, 1, 2].map(() => {
    const u = document.createElement('u'); const s = document.createElement('s');
    u.appendChild(s); rail.appendChild(u); return s;
  });
  stage.appendChild(cap);
  stage.appendChild(rail);

  // ---- renderer
  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
  } catch (e) {
    el.classList.remove('p2'); el.innerHTML = ''; mountStill(el); return;
  }
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
  renderer.setClearColor(0x000000, 0);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.0;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFShadowMap;
  renderer.shadowMap.autoUpdate = false;   // lights and ground are static: re-render shadows only while cubes move
  stage.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 0.32;

  const camera = new THREE.PerspectiveCamera(26, 1, 1, 1000);

  // ---- lights: soft hemisphere, key from upper-left front, warm rim from behind right
  scene.add(new THREE.HemisphereLight(0xf4f6fb, 0xb8ac98, 1.15));
  const key = new THREE.DirectionalLight(0xffffff, 3.2);
  key.position.set(-18, 56, 34);
  key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048);
  Object.assign(key.shadow.camera, { left: -34, right: 34, top: 34, bottom: -34, near: 1, far: 140 });
  key.shadow.bias = -0.0006;
  key.shadow.normalBias = 0.04;
  key.shadow.radius = 7;
  key.shadow.blurSamples = 16;
  scene.add(key);
  const rim = new THREE.DirectionalLight(0xffc48c, 1.9);
  rim.position.set(34, 22, -36);
  scene.add(rim);
  const fill = new THREE.DirectionalLight(0xcfdcff, 0.45);
  fill.position.set(40, 8, 24);
  scene.add(fill);

  // ---- the piece
  const pivot = new THREE.Group();
  scene.add(pivot);
  const fillK = data.fill || 0.92;
  const geo = new RoundedBoxGeometry(fillK, fillK, fillK, 2, 0.1);
  const mat = new THREE.MeshStandardMaterial({ color: NAVY, roughness: 0.45, metalness: 0.08, envMapIntensity: 0.9 });
  const mesh = new THREE.InstancedMesh(geo, mat, N);
  mesh.castShadow = false;
  mesh.receiveShadow = true;
  mesh.frustumCulled = false;
  pivot.add(mesh);
  // cheap shadow caster: plain 12-triangle boxes sharing the same instance matrices, invisible in the colour pass
  const proxyGeo = new THREE.BoxGeometry(fillK, fillK, fillK);
  const proxyMat = new THREE.MeshBasicMaterial({ colorWrite: false, depthWrite: false });
  const proxy = new THREE.InstancedMesh(proxyGeo, proxyMat, N);
  proxy.instanceMatrix = mesh.instanceMatrix;
  proxy.castShadow = true;
  proxy.frustumCulled = false;
  pivot.add(proxy);

  const ground = new THREE.Mesh(new THREE.PlaneGeometry(400, 400), new THREE.ShadowMaterial({ opacity: 0.09 }));
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  pivot.add(ground);

  // ---- per-form data
  const P = FORMS.map((f) => Float32Array.from(data.forms[f]));
  const info = P.map((a) => {
    let x0 = 1e9, x1 = -1e9, y1 = -1e9, z0 = 1e9, z1 = -1e9;
    for (let k = 0; k < N; k++) {
      const x = a[k * 3], y = a[k * 3 + 1], z = a[k * 3 + 2];
      if (x < x0) x0 = x; if (x > x1) x1 = x; if (y > y1) y1 = y;
      if (z < z0) z0 = z; if (z > z1) z1 = z;
    }
    const w = x1 - x0 + 1, h = y1 + 0.5, d = z1 - z0 + 1;
    return { cy: h / 2, rh: 0.5 * Math.hypot(w, d), rv: 0.5 * h, w, h };
  });

  // per-cube randoms (deterministic) and per-transition stagger delays
  let seed = 7;
  const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  const R1 = new Float32Array(N), R2 = new Float32Array(N), AX = new Float32Array(N * 3);
  for (let k = 0; k < N; k++) {
    R1[k] = rnd(); R2[k] = rnd();
    const a = rnd() * Math.PI * 2, b = Math.acos(2 * rnd() - 1);
    AX[k * 3] = Math.sin(b) * Math.cos(a); AX[k * 3 + 1] = Math.sin(b) * Math.sin(a); AX[k * 3 + 2] = Math.cos(b);
  }
  const SPAN = 0.45; // max delay; each cube then travels over (1 - SPAN)
  const DELAY = [0, 1, 2].map((i) => {
    const a = P[i], dl = new Float32Array(N);
    const inf = info[i];
    for (let k = 0; k < N; k++) {
      // sweep: top-left leaves first, a little noise so it never looks mechanical
      const nx = clamp01((a[k * 3] + inf.w / 2) / inf.w);
      const ny = clamp01(1 - a[k * 3 + 1] / inf.h);
      dl[k] = SPAN * clamp01(0.62 * nx + 0.23 * ny + 0.15 * R1[k]);
    }
    return dl;
  });

  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), v = new THREE.Vector3(), s3 = new THREE.Vector3(), ax = new THREE.Vector3();
  let lastF = -1;

  function layout(f) {
    const i = Math.min(2, Math.floor(f));
    const u = f - i;
    const A = P[i], B = P[i + 1], dl = DELAY[i];
    const ca = info[i], cb = info[i + 1];
    const cy = ca.cy + (cb.cy - ca.cy) * u;
    for (let k = 0; k < N; k++) {
      const j = k * 3;
      const t = clamp01((u - dl[k]) / (1 - SPAN));
      const e = easeInOut(t);
      const arc = Math.sin(Math.PI * t);
      let x = A[j] + (B[j] - A[j]) * e;
      let y = A[j + 1] + (B[j + 1] - A[j + 1]) * e;
      let z = A[j + 2] + (B[j + 2] - A[j + 2]) * e;
      if (arc > 0.0005) {
        // lift and spread away from the centre so the object visibly comes apart
        const dx = x, dy = y - cy, dz = z;
        const len = Math.hypot(dx, dy * 0.6, dz) + 1e-3;
        const spread = arc * (2.5 + 5.0 * R2[k]);
        x += (dx / len) * spread;
        y += (dy / len) * spread * 0.6 + arc * (2.0 + 3.0 * R1[k]);
        z += (dz / len) * spread + arc * 2.0;
        ax.set(AX[j], AX[j + 1], AX[j + 2]);
        q.setFromAxisAngle(ax, arc * (R2[k] > 0.5 ? 1 : -1) * (0.9 + 1.4 * R1[k]));
        const sc = 1 - 0.28 * arc;
        s3.set(sc, sc, sc);
      } else {
        q.identity();
        s3.set(1, 1, 1);
      }
      v.set(x, y, z);
      m4.compose(v, q, s3);
      mesh.setMatrixAt(k, m4);
    }
    mesh.instanceMatrix.needsUpdate = true;
    renderer.shadowMap.needsUpdate = true;
  }

  // ---- sizing
  let W = 1, H = 1;
  function resize() {
    W = stage.clientWidth || window.innerWidth;
    H = stage.clientHeight || window.innerHeight;
    renderer.setSize(W, H, false);
    camera.aspect = W / H;
    camera.updateProjectionMatrix();
  }
  resize();
  const ro = new ResizeObserver(resize);
  ro.observe(stage);

  // ---- input
  let targetP = 0, curP = 0, tiltX = 0, tiltY = 0, tX = 0, tY = 0;
  const readScroll = () => {
    const r = el.getBoundingClientRect();
    const total = r.height - window.innerHeight;
    targetP = total > 0 ? clamp01(-r.top / total) : 0;
  };
  readScroll();
  curP = targetP;
  window.addEventListener('scroll', readScroll, { passive: true });
  window.addEventListener('resize', readScroll, { passive: true });
  window.addEventListener('pointermove', (e) => {
    tX = (e.clientX / window.innerWidth - 0.5) * 2;
    tY = (e.clientY / window.innerHeight - 0.5) * 2;
  }, { passive: true });

  let visible = true;
  new IntersectionObserver((ents) => { visible = ents[0].isIntersecting; if (visible) loopStart(); }, { rootMargin: '100px' }).observe(el);

  // ---- camera: 3/4 view from front-right, distance fitted per form
  const YAWS = [0.5, 0.36, 0.42, 0.2], PITCH = 0.28, FOV = THREE.MathUtils.degToRad(26);
  function place(f, orbit, lift) {
    const i = Math.min(2, Math.floor(f)), u = f - i;
    const a = info[i], b = info[i + 1];
    const rh = a.rh + (b.rh - a.rh) * u, rv = a.rv + (b.rv - a.rv) * u;
    const cy = a.cy + (b.cy - a.cy) * u;
    const tv = Math.tan(FOV / 2), th = tv * camera.aspect;
    const phone = camera.aspect < 0.8;
    // fit width and height separately (plus depth slack) so wide forms are not tiny
    const fit = Math.max(rh / th * (phone ? 1.22 : 1.5), (rv + rh * Math.sin(PITCH) * 0.6) / tv * 1.3) + rh * 0.5;
    const YAW = YAWS[i] + (YAWS[i + 1] - YAWS[i]) * smooth(u) + orbit;
    const PIT = PITCH + lift;
    const dist = fit * (1 + 0.3 * Math.sin(Math.PI * u));
    camera.position.set(Math.sin(YAW) * Math.cos(PIT) * dist, cy + Math.sin(PIT) * dist, Math.cos(YAW) * Math.cos(PIT) * dist);
    camera.lookAt(0, cy * 0.92, 0);
  }

  // ---- loop
  let raf = 0, last = performance.now(), t0 = last;
  function frame(now) {
    raf = 0;
    if (!visible) return;
    const dt = Math.min(0.05, (now - last) / 1000);
    last = now;
    curP += (targetP - curP) * (1 - Math.exp(-dt * 7));
    const f = formAt(curP);
    if (Math.abs(f - lastF) > 1e-5) { layout(f); lastF = f; }

    tiltX += (tX - tiltX) * (1 - Math.exp(-dt * 3));
    tiltY += (tY - tiltY) * (1 - Math.exp(-dt * 3));
    const time = (now - t0) / 1000;
    // slow idle orbit + subtle pointer tilt (camera moves, so the static shadow map stays valid)
    place(f, Math.sin(time * 0.22) * 0.2 - tiltX * 0.14, tiltY * 0.05);

    for (let i = 0; i < 4; i++) {
      const o = clamp01(1 - Math.abs(f - i) * 3);
      capSpans[i].style.opacity = o.toFixed(3);
      capSpans[i].style.transform = `translateY(${((1 - o) * (f > i ? -10 : 10)).toFixed(1)}px)`;
    }
    for (let i = 0; i < 3; i++) railFill[i].style.width = `${(clamp01(f - i) * 100).toFixed(1)}%`;

    renderer.render(scene, camera);
    loopStart();
  }
  function loopStart() { if (!raf) raf = requestAnimationFrame(frame); }
  layout(formAt(curP));
  loopStart();

  return {
    destroy() {
      cancelAnimationFrame(raf); ro.disconnect();
      window.removeEventListener('scroll', readScroll);
      renderer.dispose(); geo.dispose(); mat.dispose(); proxyGeo.dispose(); proxyMat.dispose();
    },
  };
}
