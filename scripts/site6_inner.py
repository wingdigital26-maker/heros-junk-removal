"""Site6 round 2/3: bring the inner pages up to the homepage's level without touching their words or SEO heads.
Idempotent. Run: python scripts/site6_inner.py
  services/*.html : navy marquee strip under the hero, (01).. story index above the section heads,
                    a dock in the sticky aside, composed close (photo + camera dock)
  about/areas/blog : composed close (photo + camera dock); about + blog get their own passes in round 3
"""
import re, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent

MARQUEE = ('<div class="t-strip" aria-hidden="true"><div class="t-marquee"><div class="t-marquee-track">'
           '<span>Furniture removal</span><span>Appliance removal</span><span>Garage cleanouts</span><span>Estate cleanouts</span>'
           '<span>Hot tub removal</span><span>Yard debris</span><span>Construction debris</span><span>Mattresses</span>'
           '<span>Frisco</span><span>Plano</span><span>McKinney</span><span>Prosper</span><span>Allen</span><span>Little Elm</span>'
           '</div></div></div>')

def sec_head(n):
    return f'<div class="t-sec-head rise"><span class="t-sec-n">({n:02d})</span><span class="t-sec-rule"></span></div>\n'

def form_for(name):
    n = name.lower()
    if n.startswith('junk-removal-'): return 'pin'
    if 'couch' in n or 'furniture' in n or 'mattress' in n: return 'couch'
    if 'appliance' in n or 'hot-tub' in n: return 'box'
    if 'garage' in n or 'estate' in n or n == 'index': return 'house'
    if 'yard' in n or 'debris' in n or 'same-day' in n: return 'truck'
    return 'house'

def close_photo(prefix):
    return (f'<div class="cb-photo reveal"><img src="{prefix}img/p/rig-loaded-1100.webp" '
            f'srcset="{prefix}img/p/rig-loaded-480.webp 480w, {prefix}img/p/rig-loaded-1100.webp 1100w" sizes="(max-width:1000px) 100vw, 40vw" '
            'width="1100" height="619" alt="Trailer loaded with junk ready to haul" loading="lazy"></div>')

def compose_close(s, prefix):
    if 'cb-copy' in s: return s
    m = re.search(r'(<section class="contact-band" id="contact">\s*<div class="wrap">)(.*?)(</div>\s*</section>)', s, re.S)
    if not m: return s
    body = m.group(2)
    body = body.replace('<div class="cta-row reveal">', '<div class="cta-row reveal">', 1)
    # camera dock at the end of the action row
    body = re.sub(r'(<div class="cta-row reveal">.*?)(\n\s*</div>)', r'\1\n      <span class="dock" data-form="camera" data-size="M" data-phone aria-hidden="true"></span>\2', body, count=1, flags=re.S)
    new = m.group(1) + '\n    <div class="cb-copy">' + body + '</div>\n    ' + close_photo(prefix) + '\n  ' + m.group(3)
    return s[:m.start()] + new + s[m.end():]

def service_page(p):
    s = p.read_text(encoding='utf-8'); o = s
    prefix = '../'
    # 1. navy strip under the hero
    if 't-strip' not in s:
        s = re.sub(r'(<section class="svc-hero">.*?</section>)', lambda m: m.group(1) + '\n' + MARQUEE, s, count=1, flags=re.S)
    # 2. dock in the sticky aside
    if 'svc-aside-card">\n        <span class="dock"' not in s and '<aside class="svc-aside-card">' in s:
        s = s.replace('<aside class="svc-aside-card">', f'<aside class="svc-aside-card">\n        <span class="dock" data-form="{form_for(p.stem)}" data-size="M" data-phone aria-hidden="true"></span>', 1)
    # 3. story index: first body h2, then each section head, the faq head, the close
    if 't-sec-head' not in s:
        n = [0]
        def nxt(): n[0] += 1; return sec_head(n[0])
        s = re.sub(r'(<div class="svc-content">\s*)(<h2>)', lambda m: m.group(1) + nxt() + '    ' + m.group(2), s, count=1)
        s = re.sub(r'(<div class="section-head reveal">\s*)(<h2>)', lambda m: m.group(1) + nxt() + '      ' + m.group(2), s)
        s = re.sub(r'(<div class="faq-grid">\s*<div class="reveal">\s*)(<h2)', lambda m: m.group(1) + nxt() + '        ' + m.group(2), s, count=1)
        s = re.sub(r'(<section class="contact-band" id="contact">\s*<div class="wrap">\s*)(<h2 class="reveal">)', lambda m: m.group(1) + nxt() + '    ' + m.group(2), s, count=1)
    # 4. composed close
    s = compose_close(s, prefix)
    if s != o: p.write_text(s, encoding='utf-8'); return True
    return False

def other_page(p, prefix):
    s = p.read_text(encoding='utf-8'); o = compose_close(s, prefix)
    if o != s: p.write_text(o, encoding='utf-8'); return True
    return False

changed = 0
for p in sorted((ROOT / 'services').glob('*.html')): changed += service_page(p)
for p in [ROOT / 'about.html', ROOT / 'areas.html']: changed += other_page(p, '')
for p in sorted((ROOT / 'blog').glob('*.html')): changed += other_page(p, '../')
print('changed', changed)
