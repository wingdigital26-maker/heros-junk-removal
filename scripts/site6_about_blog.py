"""Site6 round 3: about + blog at the homepage's level. Idempotent. Run: python scripts/site6_about_blog.py
  about.html : (01)-(06) story index, "What we believe" as a sticky-head split, the lone "Local, owner run" section
               becomes a navy band with the crew and the phone (words unchanged)
  blog/*.html: warm editorial header with the photo pulled up over the edge, (01)-(03) index on reviews / keep
               reading / close; the index gets a navy review band after the first nine posts
"""
import re, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent

def sec_head(n, ind=''):
    return f'<div class="t-sec-head rise"><span class="t-sec-n">({n:02d})</span><span class="t-sec-rule"></span></div>\n{ind}'

CREW = '''<div class="about-crew reveal">
      <div class="t-crew-row">
        <div class="t-crew-member"><span class="t-avatar"><img src="img/p/face-todd.webp" alt="Todd"></span><div><div class="t-crew-name">Todd</div><div class="t-crew-role">Owner</div></div></div>
        <div class="t-crew-member"><span class="t-avatar"><img src="img/p/face-nash.webp" alt="Nash"></span><div><div class="t-crew-name">Nash</div><div class="t-crew-role">Owner's son, on every job</div></div></div>
      </div>
      <a class="about-band-phone" href="tel:+12142779069">(214) 277-9069</a>
      <span class="about-band-hours">7am to 8pm, every day</span>
    </div>'''

def about():
    p = ROOT / 'about.html'; s = p.read_text(encoding='utf-8'); o = s
    if 'about-page' not in s: s = s.replace('<body>', '<body class="about-page">', 1)
    if 't-sec-head' not in s:
        n = [0]
        def nxt(ind=''): n[0] += 1; return sec_head(n[0], ind)
        s = s.replace('<div class="prose reveal">\n      <h2>Meet Todd and Nash</h2>', '<div class="prose reveal">\n      ' + nxt('      ') + '<h2>Meet Todd and Nash</h2>', 1)
        s = s.replace('<div class="mini-head reveal">\n      <h2>What we believe</h2>', '<div class="mini-head reveal">\n      ' + nxt('      ') + '<h2>What we believe</h2>', 1)
        s = s.replace('<div class="prose reveal">\n      <h2>Local, owner run, easy to reach</h2>', '<div class="prose reveal">\n      ' + nxt('      ') + '<h2>Local, owner run, easy to reach</h2>', 1)
        s = s.replace('<div class="mini-head reveal">\n      <h2>Nash, in their own words</h2>', '<div class="mini-head reveal">\n      ' + nxt('      ') + '<h2>Nash, in their own words</h2>', 1)
        s = re.sub(r'(<div class="faq-grid">\s*<div class="reveal">\s*)(<h2)', lambda m: m.group(1) + nxt('        ') + m.group(2), s, count=1)
        s = re.sub(r'(<div class="cb-copy">\s*)(<h2 class="reveal">)', lambda m: m.group(1) + nxt('    ') + m.group(2), s, count=1)
    if 'about-band' not in s:
        m = re.search(r'<section class="inner-section">\s*<div class="wrap">\s*(<div class="prose reveal">\s*(?:<div class="t-sec-head[^\n]*\n\s*)?<h2>Local, owner run, easy to reach</h2>.*?</div>)\s*</div>\s*</section>', s, re.S)
        if m:
            new = '<section class="inner-section about-band">\n  <div class="wrap about-band-grid">\n    ' + m.group(1) + '\n    ' + CREW + '\n  </div>\n</section>'
            s = s[:m.start()] + new + s[m.end():]
    if 'about-split' not in s:
        m = re.search(r'(<div class="mini-head reveal">\s*<div class="t-sec-head.*?<h2>What we believe</h2>\s*</div>)(.*?)(</div>\s*</div>\s*</section>)', s, re.S)
        if m:
            s = s[:m.start()] + '<div class="about-split">\n    ' + m.group(1) + m.group(2) + '</div>\n    ' + m.group(3) + s[m.end():]
    if s != o: p.write_text(s, encoding='utf-8'); return 1
    return 0

BAND = '''      <div class="blog-band reveal">
        <div>
          <blockquote>&ldquo;Called Hero's and they came later the same day. Very reasonable pricing and a great father and son team. Very friendly and professional. Would definitely recommend them to others!&rdquo;</blockquote>
          <p class="who">Hayden Hudnall, on Google</p>
        </div>
        <a class="btn-primary" href="sms:+12142779069?&amp;body=Hi%2C%20here%20is%20a%20photo%20of%20what%20I%20need%20gone.">Text a photo</a>
      </div>
'''

def blog(p):
    s = p.read_text(encoding='utf-8'); o = s
    if p.name == 'index.html':
        if 'blog-index' not in s: s = s.replace('<body>', '<body class="blog-index">', 1)
        if 'blog-band' not in s:
            parts = s.split('      <div class="card post-card">')
            if len(parts) > 10:
                s = '      <div class="card post-card">'.join(parts[:10]) + BAND + '      <div class="card post-card">' + '      <div class="card post-card">'.join(parts[10:])
    if 't-sec-head' not in s:
        n = [0]
        def nxt(ind=''): n[0] += 1; return sec_head(n[0], ind)
        s = re.sub(r'(<div class="section-head reveal">\s*)(<h2>)', lambda m: m.group(1) + nxt('      ') + m.group(2), s)
        s = re.sub(r'(<div class="cb-copy">\s*)(<h2 class="reveal">)', lambda m: m.group(1) + nxt('    ') + m.group(2), s, count=1)
    if s != o: p.write_text(s, encoding='utf-8'); return 1
    return 0

c = about()
for p in sorted((ROOT / 'blog').glob('*.html')): c += blog(p)
print('changed', c)
