#!/usr/bin/env python3
"""Before/after QA: slider drag (mouse, keyboard, touch), console errors, horizontal overflow, block shots.
  timeout 150 python scripts/before_after_check.py [port]
Writes .visual/beforeafter/<page>-<vw>.png of each block."""
import os, sys, json
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, '.visual', 'beforeafter'); os.makedirs(OUT, exist_ok=True)
PORT = sys.argv[1] if len(sys.argv) > 1 else '4822'
VPS = [v for v in ((1440, 900, False), (390, 844, True)) if len(sys.argv) < 3 or str(v[0]) == sys.argv[2]]
PAGES = [('index', '.ba-home'), ('work', '#before-after'), ('services/garage-cleanouts', '.ba-svc'), ('services/estate-cleanouts', '.ba-svc')]
res = {}
with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader'])
    for vw, vh, touch in VPS:
        ctx = b.new_context(viewport={'width': vw, 'height': vh}, has_touch=touch, is_mobile=touch, device_scale_factor=1)
        for page, sel in PAGES:
            errs = []
            pg = ctx.new_page(); pg.set_default_timeout(25000)
            pg.route('**/formsubmit.co/**', lambda r: r.abort())
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
            pg.goto(f'http://localhost:{PORT}/{page}.html', wait_until='domcontentloaded'); pg.wait_for_timeout(1200)
            pg.locator(sel).first.scroll_into_view_if_needed(); pg.wait_for_timeout(1400)
            row = {'errors': errs[:5], 'overflow': pg.evaluate('document.documentElement.scrollWidth') > vw}
            sl = pg.locator(f'{sel} [data-ba-slider]').first
            if sl.count():
                sl.scroll_into_view_if_needed(); pg.wait_for_timeout(600); box = sl.bounding_box()
                get = lambda: pg.evaluate('(s)=>getComputedStyle(s).getPropertyValue("--ba-pos").trim()', sl.element_handle())
                row['start'] = get()
                x0, y0 = box['x'] + box['width'] * 0.5, box['y'] + box['height'] * 0.5
                if touch:
                    cdp = ctx.new_cdp_session(pg)
                    cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x0, 'y': y0}]})
                    for i in range(1, 11):
                        cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x0 - box['width'] * 0.03 * i, 'y': y0}]})
                    cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
                    pg.wait_for_timeout(200); row['after_touch'] = get()
                else:
                    pg.mouse.move(x0, y0); pg.mouse.down()
                    for i in range(1, 11): pg.mouse.move(x0 + box['width'] * 0.03 * i, y0)
                    pg.mouse.up(); pg.wait_for_timeout(200); row['after_mouse'] = get()
                    sl.locator('.ba-range').focus(); pg.keyboard.press('ArrowLeft'); pg.keyboard.press('ArrowLeft'); pg.wait_for_timeout(100)
                    row['after_keys'] = get()
                knob = sl.locator('.ba-knob').bounding_box(); row['knob'] = (round(knob['width']), round(knob['height']))
                sl.locator('.ba-range').evaluate('r=>{r.value=35;r.dispatchEvent(new Event("input"))}'); pg.wait_for_timeout(150)
            pg.locator(sel).first.screenshot(path=os.path.join(OUT, f"{page.replace('/', '-')}-{vw}.png"))
            res[f'{page}@{vw}'] = row; print(page, vw, row, flush=True)
            pg.close()
        ctx.close()
    b.close()
print(json.dumps(res, indent=1))
