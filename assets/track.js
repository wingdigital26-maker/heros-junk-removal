/* Heros v2 conversion tracking.
   v1 had ZERO analytics across 79 pages, which is why "3 calls" meant nothing.
   This fires an event for every contact action, and queues them if no analytics
   provider is installed yet, so nothing is lost before the tag goes in. */
(function () {
  "use strict";
  window.dataLayer = window.dataLayer || [];
  var QUEUE_KEY = "hjr_events";

  function push(name, params) {
    var payload = Object.assign({ event: name, ts: Date.now(), page: location.pathname }, params || {});
    window.dataLayer.push(payload);
    if (typeof window.gtag === "function") window.gtag("event", name, payload);
    if (typeof window.plausible === "function") window.plausible(name, { props: payload });
    // Keep a local copy so early conversions are recoverable before a tag is installed.
    try {
      var q = JSON.parse(sessionStorage.getItem(QUEUE_KEY) || "[]");
      q.push(payload);
      sessionStorage.setItem(QUEUE_KEY, JSON.stringify(q.slice(-50)));
    } catch (e) { /* private mode, ignore */ }
  }
  window.hjrTrack = push;

  document.addEventListener("click", function (e) {
    var el = e.target.closest("[data-track]");
    if (!el) return;
    push("contact_" + el.getAttribute("data-track"), {
      location: el.getAttribute("data-loc") || "unknown",
      href: el.getAttribute("href") || ""
    });
  });

  // Catch any tel: or sms: link that was not tagged, so a missed attribute
  // can never silently cost us a tracked conversion.
  document.addEventListener("click", function (e) {
    var a = e.target.closest('a[href^="tel:"], a[href^="sms:"]');
    if (!a || a.hasAttribute("data-track")) return;
    push(a.getAttribute("href").indexOf("tel:") === 0 ? "contact_call" : "contact_text",
         { location: "untagged", href: a.getAttribute("href") });
  });
})();
