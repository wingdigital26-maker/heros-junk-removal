/* Hero's v2 inner-page interaction. Shared by page.css/service.css/blog.css pages.
   Tiny, no libraries: rise-in on first view, hero parallax, pointer tilt on the hero mark.
   Fully static under prefers-reduced-motion. */
(function(){
'use strict';
var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/* rise-in: once, on first view */
var rv = document.querySelectorAll('.section .eyebrow, .section h2, .section h3, .section p, .section .card, .section .panel, .section .faq details, .post-row, .split > *');
if(reduced || !('IntersectionObserver' in window) || !rv.length){
  rv.forEach(function(el){ el.classList.add('iv'); });
} else {
  rv.forEach(function(el){ el.classList.add('rv'); });
  var io = new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      if(e.isIntersecting){ e.target.classList.add('iv'); io.unobserve(e.target); }
    });
  }, {threshold:0.12, rootMargin:'0px 0px -8% 0px'});
  rv.forEach(function(el){ io.observe(el); });
}

/* hero parallax: the band's own gradient layer drifts slower than scroll */
var band = document.querySelector('.inner-band, .blog-hero');
if(band && !reduced){
  var ticking = false;
  function onScroll(){
    if(ticking) return;
    ticking = true;
    requestAnimationFrame(function(){
      var y = Math.min(window.scrollY || window.pageYOffset || 0, band.offsetHeight);
      band.style.backgroundPosition = '50% ' + (y*0.18) + 'px, 0 0';
      ticking = false;
    });
  }
  window.addEventListener('scroll', onScroll, {passive:true});
}

/* pointer wake on the small mark in the hero */
var mark = document.querySelector('.hero-mark, .inner-band-mark');
if(mark && !reduced && window.matchMedia && window.matchMedia('(hover:hover) and (pointer:fine)').matches){
  var raf = null;
  document.addEventListener('pointermove', function(e){
    if(raf) return;
    raf = requestAnimationFrame(function(){
      raf = null;
      var r = mark.getBoundingClientRect();
      var cx = r.left + r.width/2, cy = r.top + r.height/2;
      var dx = Math.max(-1, Math.min(1, (e.clientX - cx)/140));
      var dy = Math.max(-1, Math.min(1, (e.clientY - cy)/140));
      mark.style.transform = 'rotate(' + (dx*6) + 'deg) translate(' + (dx*3) + 'px,' + (dy*3) + 'px)';
    });
  }, {passive:true});
}
})();
