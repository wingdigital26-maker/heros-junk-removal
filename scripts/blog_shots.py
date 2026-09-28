#!/usr/bin/env python3
"""Viewport screenshots + checks for blog pages. Usage:
  python scripts/blog_shots.py <outdir> [page ...]
Pages default to blog/index + 6 posts. Prints console errors, overflow, tap targets.
"""
import sys, os, json
from playwright.sync_api import sync_playwright

out = sys.argv[1] if len(sys.argv) > 1 else ".visual/site11/shots"
pages = sys.argv[2:] or [
    "blog/index", "blog/how-junk-removal-works", "blog/estate-cleanout-checklist",
    "blog/dumpster-rental-vs-junk-removal", "blog/workshop-hobby-room-cleanout",
    "blog/mattress-disposal-dfw", "blog/hoarder-house-junk-removal",
]
os.makedirs(out, exist_ok=True)
SCROLLS = [0, 900, 1800, 2700, 3600]

with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader'])
    for vw, vh, suf in [(1440, 900, "d"), (390, 844, "m")]:
        pg = b.new_page(viewport={"width": vw, "height": vh})
        pg.set_default_timeout(25000)
        pg.route("**/formsubmit.co/**", lambda r: r.abort())
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        for page in pages:
            errs.clear()
            pg.goto(f"http://localhost:4820/{page}.html", wait_until="domcontentloaded")
            pg.wait_for_timeout(1200)
            name = page.replace("/", "-")
            # reveals-only-on-scroll check: how many .reveal are in-view before scroll vs below fold
            pre = pg.evaluate("""() => {
              const els=[...document.querySelectorAll('.reveal,.reveal-group')];
              const below=els.filter(e=>e.getBoundingClientRect().top>innerHeight);
              return {total:els.length, belowFold:below.length, belowFoldInView:below.filter(e=>e.classList.contains('in-view')).length};
            }""")
            for i, y in enumerate(SCROLLS):
                pg.evaluate(f"window.scrollTo(0,{y})")
                pg.wait_for_timeout(700)
                pg.screenshot(path=f"{out}/{name}-{suf}{i}.png")
            h = pg.evaluate("document.body.scrollHeight")
            for y in range(0, h, 700):
                pg.evaluate(f"window.scrollTo(0,{y})"); pg.wait_for_timeout(50)
            pg.wait_for_timeout(300)
            ow = pg.evaluate("document.documentElement.scrollWidth")
            small = pg.evaluate("""() => {
              const r=[];for(const a of document.querySelectorAll('a,button,summary')){
                const b=a.getBoundingClientRect(); if(b.width===0||b.height===0) continue;
                const cs=getComputedStyle(a); if(cs.visibility==='hidden'||cs.opacity==='0') continue;
                if(a.closest('.t-menu,.t-mobile-menu')) continue;
                if(b.height<44) r.push((a.textContent||a.getAttribute('aria-label')||'').trim().slice(0,30)+' h='+Math.round(b.height));
              } return r.slice(0,12);}""")
            ld_ok = pg.evaluate("""() => {let ok=true;for(const s of document.querySelectorAll('script[type="application/ld+json"]')){try{JSON.parse(s.textContent)}catch(e){ok=false}}return ok}""")
            print(json.dumps({"page": page, "vp": suf, "height": h, "overflow": ow > vw, "errors": errs[:5],
                              "reveal": pre, "small_taps": small if vw < 500 else [], "jsonld_ok": ld_ok}))
        pg.close()
    b.close()
