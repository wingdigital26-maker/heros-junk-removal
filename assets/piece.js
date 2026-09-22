/* Hero's Junk Removal v3: the house mark on the inner pages. Tiny and lazy: no WebGL, no library.
   1. the house mark in the page hero leans toward the pointer and its blocks lift while the hand is near,
      then everything settles back when the hand leaves
   2. content rises into place once as it scrolls into view, never again
   Both are off under prefers-reduced-motion (piece.css makes everything static). */
(function () {
  'use strict';
  var doc = document.documentElement;
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  doc.classList.add('hp-js');

  // ---- the mark ----
  var mark = document.querySelector('.hm');
  if (mark && !reduce && matchMedia('(hover: hover) and (pointer: fine)').matches) {
    var hero = mark.closest('.page-hero') || mark.parentElement;
    var raf = 0, tx = 0, ty = 0, awake = false, timer = 0;
    function apply() {
      raf = 0;
      mark.style.setProperty('--tx', tx.toFixed(3));
      mark.style.setProperty('--ty', ty.toFixed(3));
    }
    hero.addEventListener('pointermove', function (e) {
      var r = mark.getBoundingClientRect();
      var cx = r.left + r.width / 2, cy = r.top + r.height / 2;
      // measured over the whole hero so the mark answers the hand anywhere on it, clamped to one mark-width either way
      tx = Math.max(-1, Math.min(1, (e.clientX - cx) / (r.width * 2.2)));
      ty = Math.max(-1, Math.min(1, (e.clientY - cy) / (r.height * 2.2)));
      var near = Math.abs(e.clientX - cx) < r.width * 1.6 && Math.abs(e.clientY - cy) < r.height * 1.6;
      if (near !== awake) { awake = near; mark.classList.toggle('awake', awake); }
      if (!raf) raf = requestAnimationFrame(apply);
      clearTimeout(timer);
      timer = setTimeout(settle, 1800);   // the hand stopped: settle back even if it never left
    }, { passive: true });
    hero.addEventListener('pointerleave', settle);
    function settle() { tx = 0; ty = 0; awake = false; mark.classList.remove('awake'); if (!raf) raf = requestAnimationFrame(apply); }
  }

  // ---- rise once ----
  var items = document.querySelectorAll('main section > .wrap > *, main .card, main article.post > *, .cta-band .wrap > *');
  if (!items.length) return;
  if (reduce || !('IntersectionObserver' in window)) return;
  var io = new IntersectionObserver(function (es) {
    es.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } });
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.05 });
  items.forEach(function (el) {
    var r = el.getBoundingClientRect();
    if (r.top < innerHeight * 0.9) return;        // already on screen at load: never hide what the visitor can see
    el.classList.add('rise');
    io.observe(el);
  });
})();
