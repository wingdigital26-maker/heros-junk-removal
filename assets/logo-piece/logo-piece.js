/*
 * Hero's travelling logo piece.
 *
 * ONE small WebGL canvas (fixed, pointer-events none) carrying ~365 bevelled cubes. It lives in the header
 * logo slot ([data-lp-home]) as the Hero's house-H mark and, as the page scrolls, flies to small dock
 * spots (<span class="lp-dock" data-form="truck">) placed in empty space in sections, taking itself
 * apart mid-flight and rebuilding as that spot's icon. When no dock is fully on screen it flies home.
 * It never stops moving: idle sway, breathing, per-cube shimmer, a ripple every few seconds, cursor
 * tilt, and hover makes the cubes spread and re-pop.
 *
 *   <script type="module" src="assets/logo-piece/logo-piece.js"></script>
 *
 * Data: shapes.json from brand/logo4/build.py (Blender). The header keeps a static Blender render of
 * the logo (logo-88.png) as the fallback for reduced motion / no WebGL, and while the piece is away.
 * three.js is imported only after the page has loaded, so it never competes with the first paint.
 */
const HERE = (p) => new URL(p, import.meta.url).href;
const THREE_URL = 'https://cdn.jsdelivr.net/npm/three@0.169.0/build/three.module.js';
const root = document.documentElement;

function webglOK() {
  try {
    const c = document.createElement('canvas');
    return !!(window.WebGLRenderingContext && (c.getContext('webgl2') || c.getContext('webgl')));
  } catch (e) { return false; }
}

const reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const home = document.querySelector('[data-lp-home]');
if (!home || reduced || !webglOK()) {
  root.classList.add('lp-off');
} else {
  const go = () => boot().catch((e) => { root.classList.add('lp-off'); root.classList.remove('lp-live', 'lp-home'); console.warn('[logo-piece]', e); });
  const idle = () => (window.requestIdleCallback ? requestIdleCallback(go, { timeout: 1500 }) : setTimeout(go, 200));
  if (document.readyState === 'complete') idle(); else window.addEventListener('load', idle, { once: true });
}

// ------------------------------------------------------------------ helpers
const clamp01 = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);
const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const easeOutBack = (t) => { const c = 1.5; const u = t - 1; return 1 + (c + 1) * u * u * u + c * u * u; };

function roundedCube(THREE, size, radius, seg) {
  // box subdivided, then every vertex pushed onto the rounded shell (what RoundedBoxGeometry does)
  const g = new THREE.BoxGeometry(size, size, size, seg, seg, seg);
  const pos = g.attributes.position, nor = g.attributes.normal;
  const h = size / 2 - radius, v = new THREE.Vector3(), c = new THREE.Vector3();
  for (let i = 0; i < pos.count; i++) {
    v.fromBufferAttribute(pos, i);
    c.set(Math.max(-h, Math.min(h, v.x)), Math.max(-h, Math.min(h, v.y)), Math.max(-h, Math.min(h, v.z)));
    v.sub(c);
    const len = v.length() || 1;
    v.multiplyScalar(1 / len);
    nor.setXYZ(i, v.x, v.y, v.z);
    pos.setXYZ(i, c.x + v.x * radius, c.y + v.y * radius, c.z + v.z * radius);
  }
  return g;
}

function studioEnv(THREE, renderer) {
  // small soft studio: grey room, one big soft top light, a warm side card, a cool fill card
  const s = new THREE.Scene();
  const room = new THREE.Mesh(new THREE.BoxGeometry(10, 10, 10), new THREE.MeshBasicMaterial({ color: 0x5b5f66, side: THREE.BackSide }));
  s.add(room);
  const card = (c, x, y, z, w, h, ry, rx) => {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ color: c, side: THREE.DoubleSide }));
    m.position.set(x, y, z); m.rotation.set(rx || 0, ry || 0, 0); s.add(m);
  };
  card(0xffffff, 0, 4.9, 0, 6, 6, 0, Math.PI / 2);
  card(0xfff1e0, -4.9, 1, 1, 3, 5, Math.PI / 2);
  card(0xdfe8ff, 4.9, 0, 2, 2, 4, -Math.PI / 2);
  card(0xffffff, 0, 1.5, 4.9, 5, 2, 0);
  const pm = new THREE.PMREMGenerator(renderer);
  const tex = pm.fromScene(s, 0.02).texture;
  pm.dispose();
  return tex;
}

// ------------------------------------------------------------------ boot
async function boot() {
  const [THREE, data] = await Promise.all([
    import(THREE_URL),
    fetch(HERE('shapes.json?v=1')).then((r) => r.json()),
  ]);
  const N = data.n;
  const FORMS = Object.keys(data.forms);

  // ---- per-form tables (built once)
  const P = {}, COL = {}, DIM = {};
  const tc = new THREE.Color();
  for (const f of FORMS) {
    P[f] = Float32Array.from(data.forms[f]);
    const a = new Float32Array(N * 3);
    for (let k = 0; k < N; k++) { tc.setHex(data.colors[f][k]); a[k * 3] = tc.r; a[k * 3 + 1] = tc.g; a[k * 3 + 2] = tc.b; }
    COL[f] = a;
    DIM[f] = data.dims[f];
  }

  // ---- canvas + renderer
  const canvas = document.createElement('canvas');
  canvas.className = 'lp-canvas';
  canvas.setAttribute('aria-hidden', 'true');
  document.body.appendChild(canvas);
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setClearColor(0x000000, 0);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.NeutralToneMapping;
  renderer.toneMappingExposure = 1.0;

  const scene = new THREE.Scene();
  scene.environment = studioEnv(THREE, renderer);
  scene.environmentIntensity = 0.8;
  scene.add(new THREE.HemisphereLight(0xffffff, 0x9aa3b5, 0.9));
  const key = new THREE.DirectionalLight(0xfff6ea, 2.1); key.position.set(-0.5, 0.9, 1); scene.add(key);
  const rim = new THREE.DirectionalLight(0xffd0a8, 1.1); rim.position.set(1, 0.4, -0.6); scene.add(rim);

  const camera = new THREE.PerspectiveCamera(16, 1, 1, 10000);
  const pivot = new THREE.Group();
  scene.add(pivot);

  const geo = roundedCube(THREE, data.fill || 0.92, (data.fill || 0.92) * (data.bevel || 0.14), 3);
  const mat = new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.36, metalness: 0, clearcoat: 0.45, clearcoatRoughness: 0.18 });
  const mesh = new THREE.InstancedMesh(geo, mat, N);
  mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  mesh.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(N * 3), 3);
  mesh.instanceColor.setUsage(THREE.DynamicDrawUsage);
  mesh.frustumCulled = false;
  pivot.add(mesh);

  // ---- sizing: the canvas is a fixed square that follows the piece; 1 world unit = 1 CSS px at the pivot
  let S = 0, phone = false;
  function resize() {
    phone = window.innerWidth < 760;
    const s = phone ? 300 : 440;
    if (s === S) return;
    S = s;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
    renderer.setSize(S, S, false);
    canvas.style.width = canvas.style.height = S + 'px';
    const D = (S / 2) / Math.tan(THREE.MathUtils.degToRad(8));
    camera.position.set(0, 0, D);
    camera.near = D - 800; camera.far = D + 800;
    camera.updateProjectionMatrix();
  }
  resize();

  // ---- docks: 0 = home (header slot), then the page docks in document order
  const docks = [{ el: home, form: 'logo' }];
  document.querySelectorAll('.lp-dock[data-form]').forEach((el) => {
    if (FORMS.includes(el.dataset.form)) docks.push({ el, form: el.dataset.form });
  });
  const header = home.closest('header');

  // cube size in px so the form fits the dock box
  function kFor(form, w, h) {
    const d = DIM[form];
    return Math.min(w / (d[0] + 1.2), h / (d[1] + 1.2));
  }

  // ---- per-cube randoms
  let seed = 11;
  const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  const R1 = new Float32Array(N), R2 = new Float32Array(N), PH = new Float32Array(N), AX = new Float32Array(N * 3);
  for (let k = 0; k < N; k++) {
    R1[k] = rnd(); R2[k] = rnd(); PH[k] = rnd() * Math.PI * 2;
    const a = rnd() * Math.PI * 2, b = Math.acos(2 * rnd() - 1);
    AX[k * 3] = Math.sin(b) * Math.cos(a); AX[k * 3 + 1] = Math.sin(b) * Math.sin(a); AX[k * 3 + 2] = Math.cos(b);
  }

  // ---- morph state: from SNAP (whatever the cubes were doing when the flight began) to the target form
  const SNAP = new Float32Array(N * 3), SNAPC = new Float32Array(N * 3), CUR = new Float32Array(N * 3), CURC = new Float32Array(N * 3);
  const DELAY = new Float32Array(N);
  let form = 'logo';
  CUR.set(P.logo); CURC.set(COL.logo);
  const SPAN = 0.4;

  // ---- flight state
  let cur = 0;                        // dock index the piece belongs to
  let flying = false, fT0 = 0, fDur = 1, fx = 0, fy = 0, fk = 1, fSpin = 1;
  let px = 0, py = 0, pk = 1;         // current screen centre + cube size
  let slow = 1;                      // test hook only: stretches flights so a verifier can catch mid-air frames

  function rectOf(i) {
    const r = docks[i].el.getBoundingClientRect();
    return r;
  }
  { const r = rectOf(0); px = r.left + r.width / 2; py = r.top + r.height / 2; pk = kFor('logo', r.width, r.height); }

  function headerBottom() { return header ? header.getBoundingClientRect().bottom : 0; }

  function pick() {
    const top = headerBottom() + 8, bot = window.innerHeight - 8, mid = (top + bot) / 2;
    let best = 0, bd = 1e9;
    for (let i = 1; i < docks.length; i++) {
      const r = rectOf(i);
      if (r.width < 4 || r.height < 4) continue;              // hidden at this breakpoint
      if (r.top < top || r.bottom > bot) continue;           // only docks fully on screen
      let d = Math.abs((r.top + r.bottom) / 2 - mid);
      if (i === cur) d -= window.innerHeight * 0.25;         // hysteresis: stay put unless clearly better
      if (d < bd) { bd = d; best = i; }
    }
    return best;
  }

  function launch(to, now) {
    const t = docks[to];
    // freeze where every cube is right now, then plan a staggered rebuild into the new icon
    SNAP.set(CUR); SNAPC.set(CURC);
    form = t.form;
    const A = P[form], d = DIM[form];
    const dir = Math.random() < 0.5 ? 1 : -1;
    for (let k = 0; k < N; k++) {
      const nx = clamp01((A[k * 3] * dir) / (d[0] + 1) + 0.5), ny = clamp01(0.5 - A[k * 3 + 1] / (d[1] + 1));
      DELAY[k] = SPAN * clamp01(0.55 * nx + 0.25 * ny + 0.2 * R1[k]);
    }
    fx = px; fy = py; fk = pk; fT0 = now;
    const r = rectOf(to);
    const dist = Math.hypot(r.left + r.width / 2 - px, r.top + r.height / 2 - py);
    fDur = (1.05 + Math.min(0.65, dist / 1600)) * slow;
    fSpin = dir;
    flying = true;
    cur = to;
    root.classList.toggle('lp-home', false);
  }

  // ---- input
  let mx = -1e4, my = -1e4, tiltX = 0, tiltY = 0, spread = 0, spreadV = 0, needPick = true;
  window.addEventListener('pointermove', (e) => { mx = e.clientX; my = e.clientY; }, { passive: true });
  document.addEventListener('pointerleave', () => { mx = my = -1e4; });
  window.addEventListener('scroll', () => { needPick = true; }, { passive: true });
  window.addEventListener('resize', () => { resize(); needPick = true; }, { passive: true });
  const menu = document.querySelector('.t-mobile-menu');

  // ---- scratch (no per-frame allocations)
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), v = new THREE.Vector3(), s3 = new THREE.Vector3(), ax = new THREE.Vector3();
  const colArr = mesh.instanceColor.array;

  let raf = 0, last = performance.now(), t0 = last;
  function frame(now) {
    raf = 0;
    const dt = Math.min(0.05, (now - last) / 1000);
    last = now;
    const time = (now - t0) / 1000;

    if (needPick) {
      needPick = false;
      const want = pick();
      if (want !== cur) launch(want, now);
    }

    // ---- where on screen
    const r = rectOf(cur);
    const tx = r.left + r.width / 2, ty = r.top + r.height / 2;
    const tk = kFor(docks[cur].form, r.width, r.height);
    let m = 1, spin = 0;
    if (flying) {
      const u = clamp01((now - fT0) / 1000 / fDur);
      const e = ease(u);
      const dx = tx - fx, dy = ty - fy, len = Math.hypot(dx, dy) || 1;
      // bow the path towards the middle of the screen, never up over the header
      const nx = -dy / len, ny = dx / len;
      const side = nx * (window.innerWidth / 2 - (fx + tx) / 2) + ny * (window.innerHeight / 2 - (fy + ty) / 2) >= 0 ? 1 : -1;
      const bow = Math.sin(Math.PI * e) * Math.min(170, len * 0.22) * side;
      px = fx + dx * e + nx * bow;
      py = fy + dy * e + ny * bow;
      pk = (fk + (tk - fk) * e) * (1 + 0.3 * Math.sin(Math.PI * e));
      m = u;
      spin = fSpin * Math.PI * 2 * ease(clamp01(u * 1.1));
      if (u >= 1) {
        flying = false;
        if (cur === 0) root.classList.add('lp-home');
      }
    } else {
      px = tx; py = ty; pk = tk;
    }

    // ---- hover spread (spring with overshoot so the cubes re-pop)
    const reach = Math.max(34, pk * 11);
    const over = !flying && Math.hypot(mx - px, my - py) < reach ? 1 : 0;
    spreadV += ((over - spread) * 90 - spreadV * 9) * dt;
    spread += spreadV * dt;

    // ---- whole-piece motion: sway, breathe, cursor tilt, ripple
    const calm = cur === 0 && !flying ? 0.55 : 1;
    tiltX += (clamp01((mx - px) / 900 + 0.5) * 2 - 1 - tiltX) * (1 - Math.exp(-dt * 3));
    tiltY += (clamp01((my - py) / 900 + 0.5) * 2 - 1 - tiltY) * (1 - Math.exp(-dt * 3));
    if (mx < -1e3) { tiltX *= 0.98; tiltY *= 0.98; }
    pivot.rotation.set(
      (-0.1 + 0.07 * Math.sin(time * 0.61) + tiltY * 0.22) * calm,
      (0.34 * Math.sin(time * 0.47) + 0.08 * Math.sin(time * 1.13) + tiltX * 0.35) * calm + spin,
      0.03 * Math.sin(time * 0.37) * calm
    );
    const breathe = 1 + 0.018 * Math.sin(time * 1.25);
    pivot.scale.setScalar(pk * breathe);
    const bob = cur === 0 && !flying ? 0 : 2.5 * Math.sin(time * 1.3);

    // ripple: a diagonal wave pops the cubes forward every ~5.5 s
    const cyc = time % 5.5, wv = cyc < 1.5 ? cyc / 1.5 : -1;
    const d = DIM[form], span = d[0] + d[1];

    // ---- cubes
    const A = P[form], CA = COL[form];
    for (let k = 0; k < N; k++) {
      const j = k * 3;
      let x, y, z, sc = 1, ang = 0;
      if (flying || m < 1) {
        const t = clamp01((m - DELAY[k]) / (1 - SPAN));
        const e = ease(t), arc = Math.sin(Math.PI * t);
        x = SNAP[j] + (A[j] - SNAP[j]) * e;
        y = SNAP[j + 1] + (A[j + 1] - SNAP[j + 1]) * e;
        z = SNAP[j + 2] + (A[j + 2] - SNAP[j + 2]) * e;
        if (arc > 0.001) {
          const l = Math.hypot(x, y) + 0.5, sp = arc * (2.2 + 4.5 * R2[k]);
          x += (x / l) * sp; y += (y / l) * sp; z += arc * (1.5 + 5 * R1[k]);
          ang = arc * (R2[k] > 0.5 ? 1.6 : -1.6) * (0.6 + R1[k]);
          sc = 1 - 0.3 * arc;
        }
        CURC[j] = SNAPC[j] + (CA[j] - SNAPC[j]) * e;
        CURC[j + 1] = SNAPC[j + 1] + (CA[j + 1] - SNAPC[j + 1]) * e;
        CURC[j + 2] = SNAPC[j + 2] + (CA[j + 2] - SNAPC[j + 2]) * e;
      } else {
        x = A[j]; y = A[j + 1]; z = A[j + 2];
        CURC[j] = CA[j]; CURC[j + 1] = CA[j + 1]; CURC[j + 2] = CA[j + 2];
      }
      CUR[j] = x; CUR[j + 1] = y; CUR[j + 2] = z;

      // idle life on top of the layout (not written back into CUR, so a morph starts from the clean form)
      z += 0.06 * Math.sin(time * 1.7 + PH[k]);
      if (wv >= 0) {
        const pos = (x - y) / span + 0.5;                    // 0..1 across the icon, top-left to bottom-right
        const b = Math.exp(-Math.pow((pos - (wv * 1.6 - 0.3)) * 7, 2));
        z += 0.85 * b; sc += 0.1 * b;
      }
      if (spread > 0.001 || spread < -0.001) {
        const l = Math.hypot(x, y) + 0.8, s = spread * (1.1 + 1.6 * R2[k]);
        x += (x / l) * s * 1.4; y += (y / l) * s * 1.4; z += s * (0.5 + 2.2 * R1[k]);
        ang += spread * (R1[k] - 0.5) * 1.8;
      }
      if (ang !== 0) { ax.set(AX[j], AX[j + 1], AX[j + 2]); q.setFromAxisAngle(ax, ang); } else q.identity();
      v.set(x, y, z); s3.set(sc, sc, sc);
      m4.compose(v, q, s3);
      m4.toArray(mesh.instanceMatrix.array, k * 16);
      colArr[j] = CURC[j]; colArr[j + 1] = CURC[j + 1]; colArr[j + 2] = CURC[j + 2];
    }
    mesh.instanceMatrix.needsUpdate = true;
    mesh.instanceColor.needsUpdate = true;

    canvas.style.transform = `translate3d(${(px - S / 2).toFixed(1)}px,${(py - S / 2 + bob).toFixed(1)}px,0)`;
    canvas.style.visibility = menu && menu.classList.contains('open') ? 'hidden' : '';
    renderer.render(scene, camera);
    loop();
  }
  function loop() { if (!raf && !document.hidden) raf = requestAnimationFrame(frame); }
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) { cancelAnimationFrame(raf); raf = 0; } else { last = performance.now(); needPick = true; loop(); }
  });

  root.classList.add('lp-live', 'lp-home');
  loop();

  // test / debug handle
  window.__logoPiece = {
    state: () => ({ dock: cur, form, flying, x: px, y: py, k: pk, docks: docks.map((d) => d.form) }),
    slow: (n) => { slow = Math.max(1, Math.min(20, +n || 1)); },
  };
}
