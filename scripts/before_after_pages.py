#!/usr/bin/env python3
"""Put the BEFORE / AFTER blocks on the pages (assets/before-after.css + .js, photos from
scripts/before_after_images.py).

  timeout 150 python scripts/before_after_pages.py

Homepage: the garage slider replaces the first card of "The work" (same grid cell, no extra length).
work.html: a "Before and after" section with all four jobs above the gallery.
services/garage-cleanouts.html: the garage slider after the intro. services/estate-cleanouts.html: living room,
kitchen and pantry tiles after the intro. Idempotent: a page that already carries a block is left alone.
"""
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARK = '<!-- before-after -->'

ARROWS = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
          'stroke-linejoin="round" aria-hidden="true"><path d="M9 6l-5 6 5 6"/><path d="M15 6l5 6-5 6"/></svg>')

# photo -> (alt, w, h)
PHOTOS = {
    'garage-before-1':  ('A two-car garage floor covered in moving boxes, bins and chairs', 1100, 825),
    'garage-after-1':   ('The same garage with an empty, swept concrete floor', 1100, 825),
    'living-before-1':  ('A living room with a wire shelf stacked with pillows, boxes and suitcases', 1100, 1467),
    'living-before-2':  ('Shoe racks and clear storage bins along the living room wall', 1100, 1467),
    'living-before-3':  ('A wire shelf of scarves, canvases and a dolly in the living room', 1100, 1467),
    'living-after-1':   ('The same living room cleared to the carpet', 1100, 1467),
    'living-after-2':   ('The fireplace wall of the same living room, empty', 1100, 1467),
    'kitchen-before-1': ('Kitchen cabinets open and full of glassware, counters covered', 1100, 1467),
    'kitchen-before-2': ('The farmhouse sink area of the kitchen, cluttered', 1100, 1467),
    'kitchen-before-3': ('A butcher-block counter covered in glass bakeware', 1100, 1467),
    'kitchen-after-1':  ('The same kitchen cleared, counters clean', 1100, 1467),
    'pantry-before-1':  ('A buffet counter covered in serving pieces and glass trays', 1100, 1467),
    'pantry-after-1':   ('The same counter and glass-front cabinets, empty', 1100, 1467),
}


def img(name, rel, sizes, cls=''):
    alt, w, h = PHOTOS[name]
    c = f' class="{cls}"' if cls else ''
    return (f'<img{c} src="{rel}img/before-after/{name}-640.webp" srcset="{rel}img/before-after/{name}-640.webp 640w, '
            f'{rel}img/before-after/{name}-1100.webp 1100w" sizes="{sizes}" width="{w}" height="{h}" alt="{alt}" loading="lazy">')


def slider(before, after, rel, sizes):
    return f'''<figure class="ba-slider" data-ba-slider style="--ba-pos:50%">
  {img(after, rel, sizes, 'ba-after-img')}
  {img(before, rel, sizes, 'ba-before-img')}
  <span class="ba-chip ba-chip--before">Before</span><span class="ba-chip ba-chip--after">After</span>
  <input class="ba-range" type="range" min="0" max="100" step="1" value="50" aria-label="Drag to compare before and after">
  <span class="ba-line" aria-hidden="true"></span><span class="ba-knob" aria-hidden="true">{ARROWS}</span>
</figure>'''


def tile(name, rel, sizes):
    kind = 'before' if '-before-' in name else 'after'
    label = 'Before' if kind == 'before' else 'After'
    return f'<figure class="ba-tile">{img(name, rel, sizes)}<span class="ba-chip ba-chip--{kind}">{label}</span></figure>'


def row(names, rel, sizes):
    return f'<div class="ba-row ba-row--{len(names)}">' + ''.join(tile(n, rel, sizes) for n in names) + '</div>'


def job(title, cap, body, rise=False):
    r = ' rise' if rise else ''
    return f'<div class="ba-job{r}"><h3 class="ba-title">{title}</h3><p class="ba-cap">{cap}</p>{body}</div>'


def living(rel, s3, s2):
    return row(['living-before-1', 'living-before-2', 'living-before-3'], rel, s3) + row(['living-after-1', 'living-after-2'], rel, s2)


def kitchen(rel, s3, s2):
    return row(['kitchen-before-1', 'kitchen-before-2', 'kitchen-before-3'], rel, s3) + row(['kitchen-after-1'], rel, s2)


def pantry(rel, s2):
    return row(['pantry-before-1', 'pantry-after-1'], rel, s2)


CAPS = {
    'garage':  'A two-car garage full of moving boxes, bins and chairs, then the same floor empty and swept.',
    'living':  'Wire shelving, shoe racks, bins and suitcases out of a paneled living room, down to the carpet.',
    'kitchen': 'Cabinets and counters full of glassware and bakeware, then the same kitchen cleared.',
    'pantry':  'Serving pieces and glass trays off a butcher-block buffet, and the glass-front cabinets emptied.',
}


def head_links(html, rel):
    css = f'<link rel="stylesheet" href="{rel}assets/before-after.css?v=1">'
    js = f'<script src="{rel}assets/before-after.js?v=1" defer></script>'
    if 'before-after.css' not in html:
        html = html.replace(f'<link rel="stylesheet" href="{rel}assets/logo-piece/logo-piece.css?v=1">',
                            f'<link rel="stylesheet" href="{rel}assets/logo-piece/logo-piece.css?v=1">\n{css}', 1)
    if 'before-after.js' not in html:
        html = html.replace(f'<script src="{rel}assets/trinity.js?v=12" defer></script>',
                            f'<script src="{rel}assets/trinity.js?v=12" defer></script>\n{js}', 1)
    assert 'before-after.css' in html and 'before-after.js' in html
    return html


def edit(path, fn):
    p = os.path.join(ROOT, path)
    html = open(p, encoding='utf-8').read()
    if MARK in html:
        print('skip (already there)', path); return
    new = fn(html)
    assert new != html, path
    open(p, 'w', encoding='utf-8', newline='\n').write(new)
    print('edited', path)


def home(html):
    rel = ''
    sizes = '(max-width:1000px) calc(100vw - 32px), 56vw'
    block = f'''<figure class="t-work-fig t-work-f1 ba ba-home">{MARK}
        <div class="rise">
        {slider('garage-before-1', 'garage-after-1', rel, sizes)}
        </div>
        <figcaption class="t-work-cap"><span>Garage cleanout, before and after</span><span class="t-num">(01)</span></figcaption>
        <a class="t-seeall rise" href="work.html#before-after" style="margin-top:18px">See every before and after<i aria-hidden="true"></i></a>
      </figure>'''
    old = re.search(r'      <figure class="t-work-fig t-work-f1">.*?</figure>', html, re.S)
    assert old
    html = html[:old.start()] + '      ' + block + html[old.end():]
    return head_links(html, rel)


def work(html):
    rel = ''
    s3 = '(max-width:760px) 74vw, (max-width:1000px) 30vw, 15vw'
    s2 = '(max-width:760px) 50vw, (max-width:1000px) 46vw, 23vw'
    sl = '(max-width:1000px) calc(100vw - 32px), 46vw'
    section = f'''<section class="s7-gal ba ba-work" id="before-after">{MARK}
  <div class="t-wrap">
    <div class="ba-intro">
      <div class="t-sec-head rise"><span class="t-sec-n">Before and after</span><span class="t-sec-rule"></span></div>
      <h2 class="rise">Before and after.</h2>
      <p class="rise">Four jobs, shot on the day. Drag the garage, and read the rest side by side.</p>
    </div>
    <div class="ba-work-grid">
      {job('Garage cleanout', CAPS['garage'], slider('garage-before-1', 'garage-after-1', rel, sl))}
      {job('Pantry counter', CAPS['pantry'], pantry(rel, s2))}
      {job('Move-out living room', CAPS['living'], living(rel, s3, s2))}
      {job('Kitchen cleared', CAPS['kitchen'], kitchen(rel, s3, s2))}
    </div>
  </div>
</section>

'''
    html = html.replace('<section class="s7-gal" id="garage">', section + '<section class="s7-gal" id="garage">', 1)
    return head_links(html, rel)


def svc(html, body_fn):
    rel = '../'
    # after the intro: the first <h2> + <p> inside .svc-content
    m = re.search(r'(<div class="svc-content">\s*<div class="t-sec-head rise">.*?</div>\s*<h2>.*?</h2>\s*<p>.*?</p>)', html, re.S)
    assert m
    html = html[:m.end()] + '\n' + body_fn(rel) + html[m.end():]
    return head_links(html, rel)


def garage_svc(rel):
    sizes = '(max-width:1000px) calc(100vw - 32px), 60vw'
    return (f'<div class="ba ba-svc">{MARK}' +
            job('Garage cleanout, before and after', CAPS['garage'], slider('garage-before-1', 'garage-after-1', rel, sizes), rise=False) +
            f'<a class="ba-more" href="{rel}work.html#before-after">See every before and after</a></div>')


def estate_svc(rel):
    s3 = '(max-width:760px) 74vw, (max-width:1000px) 30vw, 20vw'
    s2 = '(max-width:760px) 50vw, (max-width:1000px) 46vw, 30vw'
    return (f'<div class="ba ba-svc">{MARK}' +
            job('Move-out living room', CAPS['living'], living(rel, s3, s2), rise=False) +
            job('Kitchen cleared', CAPS['kitchen'], kitchen(rel, s3, s2), rise=False) +
            job('Pantry counter', CAPS['pantry'], pantry(rel, s2), rise=False) +
            f'<a class="ba-more" href="{rel}work.html#before-after">See every before and after</a></div>')


def main():
    edit('index.html', home)
    edit('work.html', work)
    edit('services/garage-cleanouts.html', lambda h: svc(h, garage_svc))
    edit('services/estate-cleanouts.html', lambda h: svc(h, estate_svc))


if __name__ == '__main__':
    main()
