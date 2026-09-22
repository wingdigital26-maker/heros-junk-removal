/* Hero's Junk Removal v2, real 3D hero.
   Poster shows first (never the LCP-blocking canvas). Once the page is idle this loads
   three.js r170 from the importmap (jsdelivr, no build step) and a GLTFLoader for
   assets/room.glb, then fades the canvas in over the poster.
   prefers-reduced-motion and narrow viewports (<820px) stay on the poster, honestly: a
   loaded, orbit-controlled render is not worth the payload or the jank on a phone hero. */
(function(){
  var stage = document.getElementById('heroStage');
  var canvas = document.getElementById('heroCanvas');
  var poster = document.getElementById('stagePoster');
  if(!stage || !canvas || !poster) return;

  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var narrow = window.matchMedia('(max-width: 820px)').matches;

  // ---- poster idle float + pointer tilt (CSS custom properties), works with or without 3D ----
  var tiltX = 0, tiltY = 0, curX = 0, curY = 0, raf = null;
  function tiltLoop(){
    curX += (tiltX - curX) * 0.08;
    curY += (tiltY - curY) * 0.08;
    poster.style.setProperty('--tx', curX.toFixed(2) + 'deg');
    poster.style.setProperty('--ty', curY.toFixed(2) + 'deg');
    if(Math.abs(tiltX - curX) > 0.01 || Math.abs(tiltY - curY) > 0.01){
      raf = requestAnimationFrame(tiltLoop);
    } else {
      raf = null;
    }
  }
  function onPosterMove(e){
    var r = stage.getBoundingClientRect();
    var cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    var dx = (e.clientX - cx) / (r.width / 2 || 1);
    var dy = (e.clientY - cy) / (r.height / 2 || 1);
    tiltY = Math.max(-1, Math.min(1, dx)) * 5;
    tiltX = Math.max(-1, Math.min(1, -dy)) * 4;
    if(!raf) raf = requestAnimationFrame(tiltLoop);
  }
  function onPosterLeave(){
    tiltX = 0; tiltY = 0;
    if(!raf) raf = requestAnimationFrame(tiltLoop);
  }
  if(!reduce && window.matchMedia('(hover:hover)').matches){
    window.addEventListener('mousemove', onPosterMove, {passive:true});
    window.addEventListener('mouseleave', onPosterLeave, {passive:true});
  }

  // reduced motion or small screens: poster only, never start WebGL.
  if(reduce || narrow) return;

  function hasWebGL(){
    try{
      var c = document.createElement('canvas');
      return !!(c.getContext('webgl2') || c.getContext('webgl'));
    }catch(_){ return false; }
  }
  if(!hasWebGL()) return;

  // module scripts never set document.currentScript, so idle scheduling can't depend on it.
  // A fixed short delay after the poster paints is a safer "after idle" signal than
  // requestIdleCallback, which can sit unfired for a long time on a background/hidden tab.
  function idle(cb){
    if(document.readyState === 'complete') setTimeout(cb, 400);
    else window.addEventListener('load', function(){ setTimeout(cb, 400); }, {once: true});
  }

  idle(function(){ boot().catch(function(err){ /* stay on the poster, no error surfaced to the visitor */ if(window.__heroDebug) console.error(err); }); });

  async function boot(){
    var THREE = await import('three');
    var GLTFLoader = (await import('three/addons/loaders/GLTFLoader.js')).GLTFLoader;
    var DRACOLoader = (await import('three/addons/loaders/DRACOLoader.js')).DRACOLoader;

    var draco = new DRACOLoader();
    draco.setDecoderPath('https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/libs/draco/');
    var loader = new GLTFLoader();
    loader.setDRACOLoader(draco);

    var gltf = await new Promise(function(res, rej){
      loader.load('assets/room.glb', res, undefined, rej);
    });

    function getW(){ return stage.clientWidth || 1; }
    function getH(){ return stage.clientHeight || 1; }

    var scene = new THREE.Scene();
    var camera = new THREE.PerspectiveCamera(26, getW() / getH(), 0.1, 200);
    camera.position.set(0, 1.1, 24);

    var renderer = new THREE.WebGLRenderer({canvas: canvas, antialias: true, alpha: true});
    renderer.setSize(getW(), getH());
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.NeutralToneMapping;
    renderer.toneMappingExposure = 1.05;
    renderer.setClearColor(0x000000, 0);

    // cool studio environment so the navy metal never reads flat or black, matched to the
    // silver backdrop rather than any warm/orange source
    var envScene = new THREE.Scene();
    (function(){
      var g = new THREE.SphereGeometry(30, 24, 16);
      var cBot = new THREE.Color('#0b1420'), cTop = new THREE.Color('#c7d0dd');
      var colors = new Float32Array(g.attributes.position.count * 3), c = new THREE.Color();
      for(var i = 0; i < g.attributes.position.count; i++){
        var t = (g.attributes.position.getY(i) / 30 + 1) / 2;
        c.copy(cBot).lerp(cTop, t);
        colors.set([c.r, c.g, c.b], i * 3);
      }
      g.setAttribute('color', new THREE.BufferAttribute(colors, 3));
      var m = new THREE.MeshBasicMaterial({vertexColors: true, side: THREE.BackSide, toneMapped: false});
      envScene.add(new THREE.Mesh(g, m));
    })();
    var pmrem = new THREE.PMREMGenerator(renderer);
    scene.environment = pmrem.fromScene(envScene, 0.04).texture;

    var key = new THREE.DirectionalLight(0xf4f7ff, 2.0); key.position.set(-5, 7, 9); scene.add(key);
    var rim = new THREE.DirectionalLight(0xffffff, 2.6); rim.position.set(7, 3, -6); scene.add(rim);
    var fill = new THREE.AmbientLight(0x9aa8c4, 0.42); scene.add(fill);
    // a low, cool bounce under the room so the pale walls separate from the silver backdrop
    // instead of washing into it
    var bounce = new THREE.DirectionalLight(0xdfe6f2, 0.7); bounce.position.set(-2, -4, 5); scene.add(bounce);

    // the model's own "clay" material is the old orange rail/load-strap accent; retint it to the
    // new signal-red so the piece matches the page theme instead of carrying the retired colour
    gltf.scene.traverse(function(o){
      if(o.isMesh && o.material && o.material.name === 'clay'){
        o.material = o.material.clone();
        o.material.color.set(0xC2362F);
      }
    });

    var group = new THREE.Group();
    group.add(gltf.scene);
    // frame the room: centre it and fit it to a consistent visual height regardless of source scale.
    // Bigger than the original pass so the piece reads as the dominant object, not a small prop
    // floating in the gradient.
    var box = new THREE.Box3().setFromObject(gltf.scene);
    var size = new THREE.Vector3(); box.getSize(size);
    var center = new THREE.Vector3(); box.getCenter(center);
    gltf.scene.position.sub(center);
    var targetH = 4.35;
    var scale = targetH / (size.y || 1);
    group.scale.setScalar(scale);
    group.rotation.y = THREE.MathUtils.degToRad(-28);
    // sit the room lower in frame, grounded against the shadow rather than centred and floating
    group.position.y = -targetH * 0.10;
    scene.add(group);

    // grab the three lifting blocks and the settled one by name so only they animate;
    // the room shell (floor/wallB/wallL*/lintel) stays put and reads as the building.
    var liftBlocks = [];
    gltf.scene.traverse(function(o){
      if(o.isMesh && /^up\d/.test(o.name)){
        liftBlocks.push({ mesh: o, baseY: o.position.y, baseX: o.position.x });
      }
    });

    // soft contact shadow under the truck, staged like the reference
    var shadowTex = (function(){
      var c = document.createElement('canvas'); c.width = c.height = 256;
      var x = c.getContext('2d'); var g = x.createRadialGradient(128, 128, 0, 128, 128, 128);
      g.addColorStop(0, 'rgba(14,22,33,0.55)'); g.addColorStop(0.55, 'rgba(14,22,33,0.22)'); g.addColorStop(1, 'rgba(14,22,33,0)');
      x.fillStyle = g; x.fillRect(0, 0, 256, 256);
      var t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
    })();
    var shadowMat = new THREE.SpriteMaterial({map: shadowTex, transparent: true, opacity: 0.9, depthWrite: false});
    var shadowSprite = new THREE.Sprite(shadowMat);
    shadowSprite.scale.set(6.4, 2.5, 1);
    shadowSprite.position.set(0, group.position.y - targetH * 0.54, 0);
    scene.add(shadowSprite);

    // idle drift, matching the reference: it performs on its own, reacts to the pointer,
    // and settles back to rest when left alone.
    var t0 = performance.now();
    var pTiltX = 0, pTiltY = 0, curTiltX = 0, curTiltY = 0;
    var pointerActive = false, settleTimer = null;

    function onMove(e){
      var r = stage.getBoundingClientRect();
      var cx = r.left + r.width / 2, cy = r.top + r.height / 2;
      var dx = Math.max(-1, Math.min(1, (e.clientX - cx) / (r.width / 2 || 1)));
      var dy = Math.max(-1, Math.min(1, (e.clientY - cy) / (r.height / 2 || 1)));
      pTiltY = dx * 0.5;
      pTiltX = -dy * 0.3;
      pointerActive = true;
      clearTimeout(settleTimer);
      settleTimer = setTimeout(function(){ pointerActive = false; pTiltX = 0; pTiltY = 0; }, 1600);
    }
    window.addEventListener('mousemove', onMove, {passive: true});

    var visible = true;
    var io = new IntersectionObserver(function(entries){
      entries.forEach(function(en){ visible = en.isIntersecting; });
    }, {threshold: 0});
    io.observe(stage);

    function resize(){
      var w = getW(), h = getH();
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    }
    window.addEventListener('resize', resize, {passive: true});

    function animate(){
      requestAnimationFrame(animate);
      if(!visible) return;
      var t = (performance.now() - t0) / 1000;
      curTiltX += (pTiltX - curTiltX) * 0.06;
      curTiltY += (pTiltY - curTiltY) * 0.06;
      var driftY = pointerActive ? 0 : t * 0.12;              // slow rotation when left alone
      group.rotation.y = THREE.MathUtils.degToRad(-28) + driftY * 0.3 + curTiltY;
      group.rotation.x = curTiltX + Math.sin(t * 0.55) * 0.015;

      // the idea, not just the object: the three blocks lift out of the room and settle back,
      // each slightly out of phase so they read as separate pieces leaving one at a time, and
      // drift a touch further from the pointer before re-gathering when it is left alone.
      var period = 5.2;
      liftBlocks.forEach(function(b, i){
        var phase = t / period * Math.PI * 2 + i * 2.1;
        var lift = (Math.sin(phase) * 0.5 + 0.5);              // 0..1, eased rise and settle
        b.mesh.position.y = b.baseY + lift * 0.34;
        var drift = pointerActive ? curTiltY * (0.5 + i * 0.25) : 0;
        b.mesh.position.x = b.baseX + drift;
      });

      renderer.render(scene, camera);
    }
    animate();

    canvas.classList.add('is-live');
    poster.classList.add('is-hidden');
  }
})();
