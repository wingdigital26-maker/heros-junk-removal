#!/usr/bin/env python3
"""Overlap / clipping audit for every page at 1440, 1024, 768 and 390.

  timeout 150 python scripts/overlap_check.py [--json out.json] [page ...]

Pages default to every top-level page plus services/* and blog/*. For each page and viewport it scrolls the
whole page (so every reveal has fired), scrolls back to the top, then compares the document-space bounding
rects of images, figures, captions, headings, paragraphs, buttons/pills and docks. A pair is a hit when the
rects intersect by more than TOL px in both axes and the two are neither parent/child nor siblings inside the
same figure (a photo-in-photo inset over its own main photo, a caption chip on its own band photo). It also
reports text that overflows its own box, anything cut by an overflow:hidden ancestor, and horizontal page
overflow. Exit code 1 when any page you pass has a hit.
"""
import sys, os, json, glob
from playwright.sync_api import sync_playwright

TOL = 4
VIEWPORTS = [(1440, 900), (1024, 768), (768, 1024), (390, 844)]
if os.environ.get("VPS"):  # e.g. VPS=1440,390 for a quick pass
    VIEWPORTS = [v for v in VIEWPORTS if str(v[0]) in os.environ["VPS"].split(",")]

JS = r"""
(tol) => {
  const SEL = 'img,figure,figcaption,h1,h2,h3,h4,h5,h6,p,button,.t-pill,.dock,.lp-dock,summary,label,dt,dd,li';
  const sy = window.scrollY, sx = window.scrollX;
  const vis = (el) => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || +cs.opacity === 0) return false;
    for (let n = el.parentElement; n; n = n.parentElement) {
      const c = getComputedStyle(n);
      if (c.display === 'none' || c.visibility === 'hidden' || +c.opacity === 0) return false;
    }
    return true;
  };
  const hidden = (el) => el.closest('.t-menu,.t-mobile-menu,.t-mega,nav .t-drop,[hidden],template,marquee,.t-marquee,.t-ticker');
  const inDock = (el) => el.closest('.dock,.lp-dock') && !el.matches('.dock,.lp-dock');
  // fully hidden by a closed accordion or an overflow:hidden ancestor collapsed around it (FAQ bodies): not on screen
  const folded = (el) => {
    const d = el.closest('details:not([open])'); if (d && !el.matches('summary') && !el.closest('summary')) return true;
    const r = el.getBoundingClientRect();
    for (let n = el.parentElement; n && n !== document.body; n = n.parentElement) {
      const c = getComputedStyle(n);
      if (!/hidden|clip/.test(c.overflowX) && !/hidden|clip/.test(c.overflowY)) continue;
      const q = n.getBoundingClientRect();
      if (r.bottom <= q.top + 1 || r.top >= q.bottom - 1 || r.right <= q.left + 1 || r.left >= q.right - 1) return true;
    }
    return false;
  };
  const els = [...document.querySelectorAll(SEL)].filter(el => !hidden(el) && !inDock(el) && vis(el) && !folded(el));
  const label = (el) => {
    let s = el.tagName.toLowerCase();
    if (el.id) s += '#' + el.id;
    if (el.classList.length) s += '.' + [...el.classList].filter(c => c !== 'rise' && c !== 'in').slice(0, 3).join('.');
    if (el.tagName === 'IMG') s += '[' + (el.getAttribute('src') || '').split('/').pop() + ']';
    else { const t = (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 40); if (t) s += ' "' + t + '"'; }
    return s;
  };
  const kind = (el) => el.matches('.dock,.lp-dock') ? 'dock' : el.tagName === 'IMG' ? 'img' : el.tagName === 'FIGURE' ? 'figure' : el.tagName === 'FIGCAPTION' ? 'caption' : (el.matches('button,.t-pill') ? 'button' : 'text');
  const items = els.map(el => {
    const r = el.getBoundingClientRect();
    return { el, k: kind(el), x: r.left + sx, y: r.top + sy, r: r.right + sx, b: r.bottom + sy, w: r.width, h: r.height };
  }).filter(i => i.w > 2 && i.h > 2);
  // text-only elements only count when they hold direct text (skip pure wrappers like <li><a>..</a></li>)
  const hasOwnText = (el) => [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
  const textish = new Set(['text', 'caption', 'button']);
  const fig = (el) => el.closest('figure,.t-work-card,.s7-fig-card,.t-hero-photo,.s7-band,.t-rv-photo,picture');
  const hits = [];
  for (let i = 0; i < items.length; i++) for (let j = i + 1; j < items.length; j++) {
    const a = items[i], b = items[j];
    if (a.k === 'figure' && b.k === 'figure') continue; // figure boxes may share margins; their images and captions are compared instead
    const ox = Math.min(a.r, b.r) - Math.max(a.x, b.x), oy = Math.min(a.b, b.b) - Math.max(a.y, b.y);
    if (ox <= tol || oy <= tol) continue;
    if (a.el.contains(b.el) || b.el.contains(a.el)) continue;
    // text wrappers: a <p> holding an <a class=t-pill> is parent/child (skipped); a <li> next to a <li> of the same list
    if (a.k === 'text' && b.k === 'text' && (!hasOwnText(a.el) || !hasOwnText(b.el))) {
      // wrapper vs its neighbour's child: only flag when both carry their own text
      if (!(hasOwnText(a.el) && hasOwnText(b.el))) continue;
    }
    if (a.k === 'figure' && (b.k === 'img' || b.k === 'caption') && fig(b.el) === a.el) continue;
    if (b.k === 'figure' && (a.k === 'img' || a.k === 'caption') && fig(a.el) === b.el) continue;
    const fa = fig(a.el), fb = fig(b.el);
    if (fa && fa === fb && a.k !== 'dock' && b.k !== 'dock') continue; // inset over its own photo, caption chip on its own band
    if (a.k === 'figure' || b.k === 'figure') {
      // a figure's box vs a foreign element: only count if the foreign element also hits the figure's own image
      const f = a.k === 'figure' ? a : b, o = a.k === 'figure' ? b : a;
      const img = [...f.el.querySelectorAll('img')].map(im => items.find(it => it.el === im)).filter(Boolean);
      const hitsImg = img.some(im => Math.min(im.r, o.r) - Math.max(im.x, o.x) > tol && Math.min(im.b, o.b) - Math.max(im.y, o.y) > tol);
      if (!hitsImg) continue;
      continue; // the img pair itself is reported
    }
    hits.push({ type: 'overlap', a: label(a.el), ak: a.k, b: label(b.el), bk: b.k, ox: Math.round(ox), oy: Math.round(oy), y: Math.round(Math.max(a.y, b.y)) });
  }
  // text overflowing its own box (ellipsis or cut), and anything cut by an overflow:hidden ancestor
  const clips = [];
  for (const it of items) {
    const el = it.el;
    if (textish.has(it.k) && hasOwnText(el)) {
      const cs = getComputedStyle(el);
      if (cs.overflowX !== 'visible' && el.scrollWidth > el.clientWidth + 2) clips.push({ type: 'text-overflow-x', a: label(el), by: el.scrollWidth - el.clientWidth, y: Math.round(it.y) });
      if (cs.overflowY !== 'visible' && el.scrollHeight > el.clientHeight + 2 && cs.webkitLineClamp === 'none') clips.push({ type: 'text-overflow-y', a: label(el), by: el.scrollHeight - el.clientHeight, y: Math.round(it.y) });
    }
    if (it.k === 'dock') continue;
    for (let n = el.parentElement; n && n !== document.body; n = n.parentElement) {
      const c = getComputedStyle(n);
      const hx = /hidden|clip|scroll|auto/.test(c.overflowX), hy = /hidden|clip|scroll|auto/.test(c.overflowY);
      if (!hx && !hy) continue;
      if (c.overflowX === 'auto' || c.overflowX === 'scroll') break; // a real scroller (phone rails) is fine
      const r = n.getBoundingClientRect();
      const nx = r.left + sx, nr = r.right + sx, ny = r.top + sy, nb = r.bottom + sy;
      const cutx = hx && (it.x < nx - 3 || it.r > nr + 3), cuty = hy && (it.y < ny - 3 || it.b > nb + 3);
      if ((cutx || cuty) && !(it.k === 'img' && n.matches('figure,.t-hero-photo,.s7-band,.t-rv-photo,a'))) {
        // an img cover-cropped by its own frame is the design; text / captions cut by a frame are not
        if (it.k === 'img' && el.matches('.t-inset,.s7-inset') ) { clips.push({ type: 'inset-clipped', a: label(el), by: label(n), y: Math.round(it.y) }); break; }
        if (it.k !== 'img') { clips.push({ type: 'clipped', a: label(el), by: label(n), y: Math.round(it.y) }); break; }
      }
      break;
    }
  }
  return { hits, clips, docW: document.documentElement.scrollWidth, docH: document.documentElement.scrollHeight };
}
"""

def all_pages(root):
    tops = sorted(p[:-5] for p in os.listdir(root) if p.endswith('.html') and not p.startswith(('type-', 'index-trinity', 'piece-demo')))
    svc = sorted('services/' + os.path.basename(p)[:-5] for p in glob.glob(os.path.join(root, 'services', '*.html')))
    blog = sorted('blog/' + os.path.basename(p)[:-5] for p in glob.glob(os.path.join(root, 'blog', '*.html')))
    return tops + svc + blog

def main():
    args = sys.argv[1:]
    out_json = None
    if '--json' in args:
        i = args.index('--json'); out_json = args[i + 1]; del args[i:i + 2]
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pages = args or all_pages(root)
    report = []
    with sync_playwright() as p:
        b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader'])
        def new_page(vw, vh, errs):
            pg = b.new_page(viewport={"width": vw, "height": vh})
            pg.set_default_timeout(25000)
            pg.route("**/formsubmit.co/**", lambda r: r.abort())
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            return pg

        def audit(pg, page, vw):
            pg.goto(f"http://localhost:{os.environ.get('PORT', '4820')}/{page}.html", wait_until="domcontentloaded")
            pg.wait_for_timeout(900)
            h = pg.evaluate("document.body.scrollHeight")
            for y in range(0, h + 600, 500):
                pg.evaluate(f"window.scrollTo(0,{y})"); pg.wait_for_timeout(60)
            pg.evaluate("window.scrollTo(0,0)")
            pg.wait_for_timeout(1500)
            return pg.evaluate(JS, TOL)

        for vw, vh in VIEWPORTS:
            errs = []
            pg = new_page(vw, vh, errs)
            for page in pages:
                errs.clear()
                res = None
                for attempt in range(2):
                    try:
                        res = audit(pg, page, vw); break
                    except Exception as e:
                        err = str(e).splitlines()[0][:120]
                        try: pg.close()
                        except Exception: pass
                        pg = new_page(vw, vh, errs)  # renderer crashed (swiftshader + WebGL): fresh page, one retry
                if res is None:
                    report.append({"page": page, "vw": vw, "error": err}); print(f"!! {page:42s} {vw:5d}  ERROR {err}"); continue
                row = {"page": page, "vw": vw, "overflow": res["docW"] > vw, "hits": res["hits"], "clips": res["clips"], "errors": errs[:3]}
                report.append(row)
                n = len(row["hits"]) + len(row["clips"]) + (1 if row["overflow"] else 0)
                flag = "  " if n == 0 else "!!"
                print(f"{flag} {page:42s} {vw:5d}  overlaps={len(row['hits']):2d} clips={len(row['clips']):2d} overflow={row['overflow']} errs={len(errs)}")
                for hit in row["hits"]:
                    print(f"      overlap {hit['ox']}x{hit['oy']} @y{hit['y']}: [{hit['ak']}] {hit['a']}  <->  [{hit['bk']}] {hit['b']}")
                for c in row["clips"]:
                    print(f"      {c['type']} @y{c['y']}: {c['a']}  by {c['by']}")
            pg.close()
        try: b.close()
        except Exception: pass
    if out_json:
        with open(out_json, "w", encoding="utf-8") as f: json.dump(report, f, indent=1)
    bad = [r for r in report if r.get("hits") or r.get("clips") or r.get("overflow") or r.get("error")]
    print(f"\n{len(bad)} page/viewport combos with findings out of {len(report)}")
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
