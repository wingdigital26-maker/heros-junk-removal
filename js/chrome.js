/* Progressive enhancement only. The mobile layout fix is pure CSS: the
   header is no longer pinned on phones. This adds one nicety on top of
   that, sliding the estimate bar out of the way while you scroll down
   and bringing it straight back when you scroll up or reach the footer.
   If this file never loads, nothing breaks. */
(function () {
  var callBar = document.querySelector('.call-bar');
  var header = document.querySelector('header.site');
  if (!callBar && !header) return;

  var lastY = window.scrollY || 0;
  var HIDE_AFTER = 90;  /* stay put near the top of the page */
  var DELTA = 6;        /* ignore scroll jitter */
  var BOTTOM_PAD = 140; /* always visible once the footer is in reach */

  var mq = window.matchMedia('(max-width: 768px)');

  function apply() {
    var y = window.scrollY || 0;

    if (header) header.classList.toggle('scrolled', y > 40);

    if (!callBar) { lastY = y; return; }

    if (!mq.matches) {
      callBar.classList.remove('chrome-away');
      lastY = y;
      return;
    }

    var diff = y - lastY;
    if (Math.abs(diff) < DELTA) return;

    var docH = document.documentElement.scrollHeight;
    var atBottom = (y + window.innerHeight) >= (docH - BOTTOM_PAD);

    callBar.classList.toggle('chrome-away', diff > 0 && y > HIDE_AFTER && !atBottom);
    lastY = y;
  }

  window.addEventListener('scroll', apply, { passive: true });
  window.addEventListener('resize', apply, { passive: true });
  apply();
})();
