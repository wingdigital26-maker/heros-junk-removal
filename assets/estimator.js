/* Heros v2 load estimator.
   Outputs LOAD SIZE only. It never shows a dollar figure, because Heros has not
   supplied real pricing and inventing one would be dishonest and unkeepable.
   When real prices exist, add them to PRICE_BANDS below and switch SHOW_PRICE on. */
(function () {
  "use strict";

  // CONFIRM WITH TODD: cubic yard capacity of a full load on the actual trailer.
  // 12 is the common size for a junk removal dump trailer and is used as a
  // placeholder for the load-fraction display only. It affects no price.
  var FULL_LOAD_CY = 12;
  var SHOW_PRICE = false;   // stays false until Heros supplies real numbers
  var PRICE_BANDS = [];     // e.g. [{maxFraction:0.25, low:0, high:0, label:""}]

  var items = document.getElementById("items");
  if (!items) return;
  var result = document.getElementById("est-result");
  var sub = document.getElementById("est-sub");
  var bar = document.getElementById("loadbar");
  var textBtn = document.getElementById("est-text");
  var dots = document.querySelectorAll(".est-dot");
  var SEGMENTS = 8; // the trade prices in eighths of a load
  var started = false;

  for (var i = 0; i < SEGMENTS; i++) {
    var s = document.createElement("span");
    s.className = "loadseg";
    bar.appendChild(s);
  }
  var segs = bar.querySelectorAll(".loadseg");

  function chosen() {
    return Array.prototype.filter.call(items.querySelectorAll(".item"), function (b) {
      return b.getAttribute("aria-pressed") === "true";
    });
  }

  function describe(f) {
    if (f <= 0) return "Nothing picked yet.";
    if (f < 0.16) return "About an eighth of a load.";
    if (f < 0.3) return "About a quarter load.";
    if (f < 0.42) return "Between a quarter and a half load.";
    if (f < 0.56) return "About a half load.";
    if (f < 0.68) return "A bit over a half load.";
    if (f < 0.8) return "About three quarters of a load.";
    if (f < 1) return "Close to a full load.";
    return "A full load or more. We may come back for a second run.";
  }

  function step(n) {
    dots.forEach(function (d, idx) {
      d.setAttribute("aria-current", idx === n ? "true" : "false");
    });
  }

  function update() {
    var picked = chosen();
    var cy = picked.reduce(function (t, b) { return t + parseFloat(b.dataset.cy || 0); }, 0);
    var frac = cy / FULL_LOAD_CY;
    var filled = Math.min(SEGMENTS, Math.ceil(frac * SEGMENTS));

    segs.forEach(function (s, idx) { s.classList.toggle("on", idx < filled); });

    if (!picked.length) {
      result.textContent = "Nothing picked yet.";
      sub.textContent = "A cubic yard is roughly one washer or dryer. We price by how much of the truck you fill, so the list below is what decides it.";
      textBtn.setAttribute("href", "sms:+12142779069");
      step(0);
      return;
    }

    var labels = picked.map(function (b) { return b.dataset.label; });
    result.textContent = describe(frac);

    if (SHOW_PRICE && PRICE_BANDS.length) {
      var band = PRICE_BANDS.find(function (p) { return frac <= p.maxFraction; });
      if (band) sub.textContent = band.label;
    } else {
      sub.textContent = "Roughly " + (Math.round(cy * 10) / 10) + " cubic yards, which is about " +
        Math.max(1, Math.round(cy)) + " washing machines worth of space. Send this list with a photo and Todd will come back with a firm price.";
    }

    var body = "Hi Hero's, I need this hauled: " + labels.join(", ") +
      ". Your site said that is " + describe(frac).toLowerCase().replace(/\.$/, "") +
      ". Photo attached. What would that cost?";
    textBtn.setAttribute("href", "sms:+12142779069?&body=" + encodeURIComponent(body));
    step(1);

    if (!started) {
      started = true;
      if (window.hjrTrack) window.hjrTrack("estimator_start", {});
    }
    if (window.hjrTrack) {
      window.hjrTrack("estimator_update", { items: labels.length, cubic_yards: cy });
    }
  }

  items.addEventListener("click", function (e) {
    var b = e.target.closest(".item");
    if (!b) return;
    b.setAttribute("aria-pressed", b.getAttribute("aria-pressed") === "true" ? "false" : "true");
    update();
  });

  textBtn.addEventListener("click", function () {
    var picked = chosen();
    if (window.hjrTrack) {
      window.hjrTrack("estimator_complete", {
        items: picked.length,
        list: picked.map(function (b) { return b.dataset.label; }).join(", ")
      });
    }
    step(2);
  });
})();
