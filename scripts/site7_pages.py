#!/usr/bin/env python
"""Site7: build reviews.html and faq.html from the site's own data, so the pages can never drift.

  reviews.html  every review in brand/reviews.json, quoted as written (stars drawn per review, the count
                never printed), the homepage's "job crew" treatment, filters by tag, 4.9 on Google + the profile link.
  faq.html      the homepage FAQ plus every FAQ entry on the service, city and about pages, deduped by question,
                answers word for word, grouped by topic, plus FAQPage JSON-LD built from the same Q&As.

Both pages are written with a placeholder header/footer; run scripts/trinity_chrome.py --apply afterwards to
stamp the homepage chrome on them (it also adds the Trinity stylesheets and favicons).

Usage: python scripts/site7_pages.py
"""
import html as H, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SMS = 'sms:+12142779069?&amp;body=Hi%2C%20here%20is%20a%20photo%20of%20what%20I%20need%20gone.'
GOOGLE = 'https://www.google.com/maps?cid=276680836995827442'
TODD = '<span class="t-av"><img src="img/p/face-todd.webp" alt=""></span>'
NASH = '<span class="t-av"><img src="img/p/face-nash.webp" alt=""></span>'

# the photo each review sits beside on the homepage (kept identical here)
PHOTOS = {
    'Sophia Yang': ('img/p/job-curbside-pickup-820.webp', 'Two toilets at the curb, one burned, picked up same day'),
    'Caden Boyd': ('img/p/garage-820.webp', 'Garage full of items ready for pickup'),
    'Calvin Mullinax Jr.': ('img/truck-bed.jpg', 'Truck bed loaded with items'),
    'Dex. Camerón': ('img/p/appliance-820.webp', 'Appliances ready for pickup'),
    'Evan Wright': ('img/p/card-sameday-820.webp', 'Same-day junk removal'),
    'p1xylz': ('img/crew-loading.jpg', 'Crew loading the truck'),
}
FILTERS = [('all', 'All'), ('same-day', 'Same day'), ('price', 'Price'), ('fast', 'Fast'), ('nash', 'Nash')]
TAG_KEY = {'same day': 'same-day', 'fair price': 'price', 'price': 'price', 'free quote': 'price', 'photo quote': 'price',
           'fast': 'fast', 'on time': 'fast', 'Nash': 'nash'}


def head(title, desc, path, og_image='assets/logo5/og.png', extra=''):
    url = 'https://herosjunkremovaltx.com/' + path
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#14284B">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Hero&rsquo;s Junk Removal">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="https://herosjunkremovaltx.com/{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="https://herosjunkremovaltx.com/{og_image}">
<link rel="icon" href="assets/logo5/mark.svg" type="image/svg+xml">
<link rel="icon" href="assets/logo5/favicon-32.png" sizes="32x32" type="image/png">
<link rel="icon" href="assets/logo5/favicon-16.png" sizes="16x16" type="image/png">
<link rel="apple-touch-icon" href="assets/logo5/apple-touch-icon.png">
{extra}</head>
<body>
<a class="skip" href="#main">Skip to main content</a>
<header class="t-header"></header>

<main id="main" tabindex="-1">
'''


def close_band(n, photo, alt):
    return f'''
<section class="contact-band" id="contact">
  <div class="wrap">
    <div class="cb-copy">
    <div class="t-sec-head rise"><span class="t-sec-n">({n})</span><span class="t-sec-rule"></span></div>
    <h2 class="reveal">Send the photo now.</h2>
    <p class="reveal">Open 7am to 8pm, every day. Text, call or email, whichever is easier.</p>
    <div class="cta-row reveal">
      <a class="btn-primary" href="{SMS}">Text a photo</a>
      <a class="call-quiet" href="tel:+12142779069">Call (214) 277-9069</a>
      <span class="dock" data-form="camera" data-size="M" data-phone aria-hidden="true"></span>
    </div>
    <p class="cities">Frisco, Plano, McKinney, Prosper, Allen, Little Elm &middot; <a href="contact.html">Or use the contact page</a></p>
  </div>
    <div class="cb-photo reveal"><img src="{photo}" alt="{alt}" loading="lazy"></div>
  </div>
</section>
</main>

<footer class="t-footer"></footer>
'''


def breadcrumb_ld(name, path):
    return json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://herosjunkremovaltx.com/"},
        {"@type": "ListItem", "position": 2, "name": name, "item": "https://herosjunkremovaltx.com/" + path}]}, ensure_ascii=False)


def stars(n):
    return '<span class="s7-stars" aria-label="%d out of 5 stars">%s</span>' % (n, ''.join('<i class="on"></i>' if i < n else '<i></i>' for i in range(5)))


def crew(tags):
    nash_only = 'Nash' in tags
    avs = NASH if nash_only else TODD + NASH
    return '<div class="t-rv-crew"><span class="t-avs">%s</span><span>Job crew: %s</span></div>' % (avs, 'Nash' if nash_only else 'Todd and Nash')


def who(r):
    return '<div class="t-rv-who"><span class="t-rv-name">%s</span><span class="t-rv-when">%s</span></div>' % (H.escape(r['name']), H.escape(r['when']))


def build_reviews():
    data = json.loads((ROOT / 'brand/reviews.json').read_text(encoding='utf-8'))
    reviews = data['reviews']
    feature = reviews[0]
    rest = reviews[1:]
    cards = []
    for r in rest:
        keys = sorted({TAG_KEY[t] for t in r['tags'] if t in TAG_KEY})
        q = H.escape(r['text'])
        foot = '<div class="t-rv-foot">%s%s</div>' % (who(r), crew(r['tags']))
        if r['name'] in PHOTOS:
            src, alt = PHOTOS[r['name']]
            cards.append(f'''      <article class="t-rv-card rise" data-tags="{' '.join(keys)}">
        <div class="t-rv-photo"><img src="{src}" alt="{H.escape(alt)}" loading="lazy"></div>
        {stars(r['stars'])}
        <p class="t-rv-quote">&ldquo;{q}&rdquo;</p>
        {foot}
      </article>''')
        else:
            cards.append(f'''      <article class="t-rv-card t-rv-tile rise" data-tags="{' '.join(keys)}">
        {stars(r['stars'])}
        <p class="t-rv-quote">&ldquo;{q}&rdquo;</p>
        {foot}
      </article>''')
    filters = ''.join('<li><button type="button" data-filter="%s"%s>%s</button></li>' % (k, ' aria-pressed="true"' if k == 'all' else ' aria-pressed="false"', l) for k, l in FILTERS)
    title = 'Reviews | Hero&rsquo;s Junk Removal, Frisco, Plano, McKinney'
    desc = 'Google reviews of Hero&rsquo;s Junk Removal, quoted as written. Same-day pickups, a price by text, Todd and Nash on every job in Frisco, Plano, McKinney, Prosper, Allen and Little Elm.'
    extra = '<script type="application/ld+json">\n%s\n</script>\n' % breadcrumb_ld('Reviews', 'reviews')
    body = f'''
<section class="s7-hero s7-warm">
  <div class="t-wrap">
    <div class="s7-hero-grid">
      <div>
        <p class="s7-crumb"><a href="./">Home</a> / Reviews</p>
        <div class="t-sec-head rise"><span class="t-sec-n">Reviews</span><span class="t-sec-rule"></span></div>
        <h1 class="s7-h1 rise">What people say after the truck leaves.</h1>
        <p class="s7-lead rise">Every word below is from Google, quoted as written. Read them there, or text a photo and find out for yourself.</p>
        <div class="t-pill-row rise">
          <a class="t-pill t-primary t-pill-lg" href="{SMS}">Text a photo</a>
          <a class="t-pill t-pill-lg" href="tel:+12142779069">Call (214) 277-9069</a>
        </div>
      </div>
      <div class="s7-hero-side">
        <span class="dock" data-form="star" data-size="M" data-phone aria-hidden="true"></span>
        <a class="s7-google rise" href="{GOOGLE}" rel="noopener"><span class="t-stars" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></span><strong>4.9</strong> on Google &middot; read them on the profile</a>
      </div>
    </div>
  </div>
</section>

<section class="s7-feature s7-navy">
  <div class="t-wrap">
    <article class="t-rv-feature">
      <div class="t-rv-feature-photo rise"><img src="img/p/job-garage-clearout-1100.webp" alt="Garage clearout in progress" loading="lazy"></div>
      <div class="t-rv-feature-body rise">
        <span class="t-quote-mark" aria-hidden="true">&ldquo;</span>
        <p class="t-rv-feature-quote">{H.escape(feature['text'])}</p>
        {stars(feature['stars'])}
        <div class="t-rv-foot" style="margin-top:20px">{who(feature)}{crew(feature['tags'])}</div>
      </div>
    </article>
  </div>
</section>

<section class="s7-svc s7-warm" id="all">
  <div class="t-wrap">
    <div class="s7-rv-head">
      <div>
        <div class="t-sec-head rise"><span class="t-sec-n">(01)</span><span class="t-sec-rule"></span></div>
        <h2 class="rise">Every review, as written.</h2>
      </div>
      <ul class="s7-filters rise" aria-label="Filter reviews">{filters}</ul>
    </div>
    <div class="t-rv-grid s7-rv-grid" id="rv-grid">
{chr(10).join(cards)}
    </div>
    <p class="s7-rv-empty" id="rv-empty">No review carries that tag yet. Pick another one, or read them all on <a href="{GOOGLE}" rel="noopener">Google</a>.</p>
  </div>
</section>

<figure class="s7-band s7-band--tall">
  <img src="img/p/rig-loaded-1400.webp" alt="Trailer loaded with junk ready to haul" loading="lazy">
  <figcaption><span>Trailer loaded with junk ready to haul</span><span class="t-num">(02)</span></figcaption>
</figure>
'''
    script = '''
<script>
(function(){var g=document.getElementById('rv-grid');if(!g)return;var bs=document.querySelectorAll('.s7-filters button');var empty=document.getElementById('rv-empty');
bs.forEach(function(b){b.addEventListener('click',function(){var k=b.dataset.filter;bs.forEach(function(x){x.setAttribute('aria-pressed',String(x===b))});var n=0;
g.querySelectorAll('article').forEach(function(a){var on=k==='all'||(' '+a.dataset.tags+' ').indexOf(' '+k+' ')>=0;a.hidden=!on;if(on)n++;});empty.classList.toggle('show',n===0);});});})();
</script>
'''
    out = head(title, desc, 'reviews', extra=extra) + body + close_band('03', 'img/p/real-rig-960.webp', 'Todd loading the trailer in a driveway') + script + '<script type="module" src="assets/logo-piece/logo-piece.js?v=1"></script>\n</body>\n</html>\n'
    (ROOT / 'reviews.html').write_text(out, encoding='utf-8', newline='')
    print('reviews.html: %d reviews' % len(reviews))


# ---------------- FAQ ----------------
TOPICS = [
    ('basics', 'The basics', 'Price, timing, what goes and where it ends up.'),
    ('same-day', 'Same-day pickups', 'What typical means and when it does not apply.'),
    ('furniture', 'Furniture, couches and mattresses', 'Upstairs, inside, donated first.'),
    ('appliances', 'Appliances', 'Fridges, washers, dryers, water heaters.'),
    ('garage', 'Garage cleanouts', 'Sorting, timing, what stays behind.'),
    ('estate', 'Estate cleanouts', 'Whole houses, handled with care.'),
    ('hot-tub', 'Hot tubs, sheds and playsets', 'Draining, power, the pad.'),
    ('yard', 'Yard debris', 'Limbs, brush, fence, storm leftovers.'),
    ('construction', 'Construction debris', 'After the remodel.'),
    ('frisco', 'Frisco', 'Questions from Frisco jobs.'),
    ('plano', 'Plano', 'Questions from Plano jobs.'),
    ('mckinney', 'McKinney', 'Questions from McKinney jobs.'),
    ('prosper', 'Prosper', 'Questions from Prosper jobs.'),
    ('allen', 'Allen', 'Questions from Allen jobs.'),
    ('little-elm', 'Little Elm', 'Questions from Little Elm jobs.'),
]


def topic_for(rel):
    n = pathlib.Path(rel).stem
    if rel in ('index.html', 'about.html'):
        return 'basics'
    for city in ('frisco', 'plano', 'mckinney', 'prosper', 'allen', 'little-elm'):
        if n.endswith('-' + city):
            return city
    if 'same-day' in n: return 'same-day'
    if 'furniture' in n or 'couch' in n or 'mattress' in n: return 'furniture'
    if 'appliance' in n: return 'appliances'
    if 'garage' in n: return 'garage'
    if 'estate' in n: return 'estate'
    if 'hot-tub' in n: return 'hot-tub'
    if 'yard' in n: return 'yard'
    if 'construction' in n: return 'construction'
    return 'basics'


def norm(q):
    return re.sub(r'[^a-z0-9 ]', '', H.unescape(re.sub(r'<[^>]+>', '', q)).lower()).strip()


def relink(ans, rel):
    """answers written on services/*.html link to siblings: point them at services/ from the site root."""
    def fix(m):
        url = m.group(1)
        if url.startswith(('http', 'tel:', 'sms:', 'mailto:', '#', '/')):
            return m.group(0)
        if url.startswith('../'):
            return 'href="%s"' % url[3:]
        if rel.startswith('services/'):
            return 'href="services/%s"' % url
        return m.group(0)
    return re.sub(r'href="([^"]*)"', fix, ans)


def plain(s):
    return re.sub(r'\s+', ' ', H.unescape(re.sub(r'<[^>]+>', '', s))).strip()


def collect():
    items = []  # (topic, question_html, answer_html, source)
    seen = set()
    home = (ROOT / 'index.html').read_text(encoding='utf-8')
    for q, a in re.findall(r'<span class="t-faq-q">(.*?)</span>.*?<div class="t-faq-a">(.*?)</div>', home, re.S):
        k = norm(q)
        if k in seen: continue
        seen.add(k); items.append(('basics', q.strip(), '<p>%s</p>' % a.strip(), 'index.html'))
    files = [ROOT / 'about.html'] + [p for p in sorted((ROOT / 'services').glob('*.html')) if p.name != 'index.html']
    for p in files:
        rel = p.relative_to(ROOT).as_posix()
        s = p.read_text(encoding='utf-8')
        for q, a in re.findall(r'<details>\s*<summary>(.*?)</summary>\s*<div class="faq-body">(.*?)</div>\s*</details>', s, re.S):
            k = norm(q)
            if k in seen: continue
            seen.add(k); items.append((topic_for(rel), q.strip(), relink(a.strip(), rel), rel))
    return items


def build_faq():
    items = collect()
    by = {}
    for t, q, a, src in items:
        by.setdefault(t, []).append((q, a, src))
    topics_html, index_html, ld = [], [], []
    n = 0
    for key, title, lead in TOPICS:
        rows = by.get(key)
        if not rows: continue
        n += 1
        index_html.append('<li><a href="#%s"><b>(%02d)</b>%s</a></li>' % (key, n, title))
        qs = []
        for i, (q, a, src) in enumerate(rows):
            qs.append(f'''      <details class="t-faq-item"{' open' if (n == 1 and i == 0) else ''}>
        <summary><span class="t-faq-q">{q}</span><span class="t-plus" aria-hidden="true"></span></summary>
        <div class="t-faq-a">{a}</div>
      </details>''')
            ld.append({"@type": "Question", "name": plain(q), "acceptedAnswer": {"@type": "Answer", "text": plain(a)}})
        topics_html.append(f'''    <section class="s7-topic" id="{key}" data-topic="{key}">
      <div class="t-sec-head rise"><span class="t-sec-n">({n:02d})</span><span class="t-sec-rule"></span></div>
      <h2 class="rise">{title}</h2>
      <p class="s7-topic-lead rise">{lead}</p>
      <div class="t-faq-list">
{chr(10).join(qs)}
      </div>
    </section>''')
    title = 'FAQ | Hero&rsquo;s Junk Removal, questions answered'
    desc = 'Every question people ask Hero&rsquo;s Junk Removal before they send the photo: pricing by text, same-day pickups, what we take, where it ends up, and city by city notes for Frisco, Plano, McKinney, Prosper, Allen and Little Elm.'
    faq_ld = json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": ld}, ensure_ascii=False)
    extra = '<script type="application/ld+json">\n%s\n</script>\n<script type="application/ld+json">\n%s\n</script>\n' % (breadcrumb_ld('FAQ', 'faq'), faq_ld)
    body = f'''
<section class="s7-hero s7-navy">
  <div class="t-wrap">
    <div class="s7-hero-grid">
      <div>
        <p class="s7-crumb"><a href="./">Home</a> / FAQ</p>
        <div class="t-sec-head rise"><span class="t-sec-n">FAQ</span><span class="t-sec-rule"></span></div>
        <h1 class="s7-h1 rise">Questions, answered.</h1>
        <p class="s7-lead rise">Everything people ask before they send the photo, gathered from every page on the site. Anything else, call <a href="tel:+12142779069">(214) 277-9069</a>. Todd or Nash picks up.</p>
        <div class="t-pill-row rise">
          <a class="t-pill t-primary t-pill-lg" href="{SMS}">Text a photo</a>
          <a class="t-pill t-pill-lg" href="tel:+12142779069">Call (214) 277-9069</a>
        </div>
      </div>
      <div class="s7-hero-side">
        <span class="dock" data-form="h" data-size="M" data-phone aria-hidden="true"></span>
      </div>
    </div>
  </div>
</section>

<section class="s7-faq s7-warm">
  <div class="t-wrap s7-faq-layout">
    <aside class="s7-faq-side">
      <label class="s7-search"><span class="t-sec-n" aria-hidden="true">Find</span><input type="search" id="faq-q" placeholder="Search the questions" aria-label="Search the questions" autocomplete="off"></label>
      <ul class="s7-topics" id="faq-topics">
        {chr(10).join(index_html)}
      </ul>
    </aside>
    <div class="s7-faq-main" id="faq-main">
{chr(10).join(topics_html)}
      <p class="s7-faq-empty" id="faq-empty">Nothing matches that. Call <a href="tel:+12142779069">(214) 277-9069</a> and ask; Todd or Nash picks up.</p>
    </div>
  </div>
</section>

<div class="t-rv-pull-band">
  <figure class="t-rv-pull rise">
    <blockquote>&ldquo;Nash was very professional. I had a bunch of stuff I needed gone in my garage. He came same day and gave me a free reasonable quote. Great business man. Would recommend to everyone.&rdquo;</blockquote>
    <figcaption><div class="t-rv-who"><span class="t-rv-name">Caden Boyd</span><span class="t-rv-when">a month ago</span></div><div class="t-rv-crew"><span class="t-avs">{NASH}</span><span>Job crew: Nash</span></div></figcaption>
  </figure>
</div>
'''
    script = '''
<script>
(function(){var q=document.getElementById('faq-q');if(!q)return;var topics=[].slice.call(document.querySelectorAll('.s7-topic'));var empty=document.getElementById('faq-empty');
function run(){var v=q.value.trim().toLowerCase();var any=false;topics.forEach(function(t){var n=0;t.querySelectorAll('.t-faq-item').forEach(function(d){var on=!v||d.textContent.toLowerCase().indexOf(v)>=0;d.hidden=!on;if(on){n++;if(v)d.open=true;}});t.hidden=n===0;if(n)any=true;});empty.classList.toggle('show',!any);}
q.addEventListener('input',run);
var links=[].slice.call(document.querySelectorAll('#faq-topics a'));
if('IntersectionObserver' in window){var cur=null;var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){links.forEach(function(a){a.classList.toggle('cur',a.getAttribute('href')==='#'+e.target.id);});}});},{rootMargin:'-20% 0px -70% 0px'});topics.forEach(function(t){io.observe(t);});}
})();
</script>
'''
    out = head(title, desc, 'faq', extra=extra) + body + close_band('%02d' % (n + 1), 'img/p/job-garage-clearout-900.webp', 'Garage clearout in progress') + script + '<script type="module" src="assets/logo-piece/logo-piece.js?v=1"></script>\n</body>\n</html>\n'
    (ROOT / 'faq.html').write_text(out, encoding='utf-8', newline='')
    print('faq.html: %d questions in %d topics' % (len(items), n))


if __name__ == '__main__':
    build_reviews()
    build_faq()
