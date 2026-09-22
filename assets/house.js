/* Hero's Junk Removal v3: the house that empties itself.
   Poster first (img/house-hero.webp is the LCP). This module only boots the live scene on a desktop with a
   real pointer, no reduced-motion preference and no data-saver, then crossfades the canvas over the poster
   from the exact same camera, so nothing jumps. Phones keep the poster: the gesture reads at a glance there,
   and a megabyte of WebGL for a slow drift is not a fair trade on a phone.
   Animates ONLY lift0..lift3: blocks travel out through the door on a fixed arc, shrinking as they go,
   then the next one follows. The shell (base, walls, piers, lintel, reveal, windows, roof, inside) never moves. */

const piece = document.getElementById('piece');
if (piece) boot();

function ok() {
  const mq = (q) => matchMedia(q).matches;
  if (mq('(prefers-reduced-motion: reduce)')) return false;
  if (!mq('(min-width: 821px)') || !mq('(hover: hover) and (pointer: fine)')) return false;
  const c = navigator.connection;
  if (c && (c.saveData || /2g/.test(c.effectiveType || ''))) return false;
  try {
    const t = document.createElement('canvas');
    return !!(t.getContext('webgl2') || t.getContext('webgl'));
  } catch (_) { return false; }
}

function boot() {
  if (!ok()) return;
  // never race the poster: wait for the page to be quiet, then load three
  const start = () => import('./house-scene.js?v=5').then((m) => m.init(piece)).catch((e) => console.warn('house: live scene skipped', e));
  if ('requestIdleCallback' in window) requestIdleCallback(start, { timeout: 2500 });
  else setTimeout(start, 600);
}
