"""Remove Todd from the site and make Nash the owner in every sentence. Reviews are never touched.
Run from the repo root: python scripts/nash_sweep.py
"""
import glob, pathlib, re
from PIL import Image

# Nash-only crop from the team photo (Nash is the left figure, Dallas jersey)
im = Image.open('img/p/team-todd-nash-1050.webp').convert('RGB')
im.crop((150, 40, 610, 615)).save('img/p/nash-460.webp', quality=86, method=6)
print('nash-460', Image.open('img/p/nash-460.webp').size)

R = [
 ('Talk to Todd or Nash', 'Talk to Nash'),
 ('Meet Todd and Nash and how Hero&#39;s got started', 'Meet Nash and how Hero&#39;s got started'),
 ("Meet Todd and Nash and how Hero's got started", "Meet Nash and how Hero's got started"),
 ('Todd started this company himself and his son Nash runs it with him, which is why we are comfortable sending a crew inside a house rather than only working a driveway.',
  'Nash owns the company and works every job himself, which is why we are comfortable sending a crew inside a house rather than only working a driveway.'),
 ('Todd started this company himself and his son Nash runs it with him, so there is no franchise ad budget buried in your invoice.',
  'Nash owns the company and works every job himself, so there is no franchise ad budget buried in your invoice.'),
 ('owned by Todd and run with his son Nash', 'owned and run by Nash'),
 ('<h2>Meet Todd and Nash</h2>', '<h2>Meet Nash</h2>'),
 ('<p>Hero&rsquo;s is Todd&rsquo;s company. He learned early, on every job he has ever had, that how you treat people is the whole job. He started Hero&rsquo;s Junk Removal with a pickup truck and a borrowed trailer, helping neighbors clear out garages after storms and moves, and he built it on one idea: treat every house like it belongs to your own family.</p>',
  '<p>Hero&rsquo;s is Nash&rsquo;s company. He reads the photo you send, sends the price, and is on the truck when it pulls up. Hero&rsquo;s Junk Removal started with a pickup truck and a borrowed trailer, helping neighbors clear out garages after storms and moves, and it was built on one idea: treat every house like it belongs to your own family.</p>'),
 ('So Hero&rsquo;s runs on the promise Todd made on those first jobs:', 'So Hero&rsquo;s runs on the promise made on those first jobs:'),
 ('<p>Today Todd runs Hero&rsquo;s with Nash beside him. What started as weekend favors', '<p>Today Nash runs Hero&rsquo;s himself. What started as weekend favors'),
 ('<strong>Owner run.</strong> Todd and Nash review every job personally. If there is a scuff or a surprise on the invoice, they want to know why, and they make it right.',
  '<strong>Owner run.</strong> Nash reviews every job personally. If there is a scuff or a surprise on the invoice, he wants to know why, and he makes it right.'),
 ('<h3>Same two guys, every time.</h3><p>Todd and Nash show up together, 7am to 8pm, every day of the week. You are not getting a rotating crew or a name you have never heard before.</p>',
  '<h3>Same guy, every time.</h3><p>Nash shows up himself, 7am to 8pm, every day of the week. You are not getting a rotating crew or a name you have never heard before.</p>'),
 ('Hero&rsquo;s is owner run. Todd sets the standard and runs the whole operation:', 'Hero&rsquo;s is owner run. Nash sets the standard and runs the whole operation:'),
 ('worked by the same two owners, Todd and Nash, open 7am to 8pm every day.', 'worked by the same owner, Nash, open 7am to 8pm every day.'),
 ('<strong>Same two owners, every city.</strong> Todd and Nash are the crew that shows up, not a rotating hire off an app.',
  '<strong>Same owner, every city.</strong> Nash is the one who shows up, not a rotating hire off an app.'),
 ('<p>Same two owners, every city. Open 7am to 8pm, every day.', '<p>Same owner, every city. Open 7am to 8pm, every day.'),
 ('Who shows up: Todd and Nash, on every job.', 'Who shows up: Nash, on every job.'),
 ("<p>Todd started Hero's helping neighbors clear out garages, and his son Nash runs it with him now.",
  "<p>Hero's started out helping neighbors clear out garages, and Nash runs it himself now."),
 ('"text": "Our own people. Todd owns the company and works the jobs, his son Nash runs it with him, and the crew is hired and kept rather than dispatched off an app."',
  '"text": "Our own people. Nash owns the company and works the jobs, and the crew is hired and kept rather than dispatched off an app."'),
 ('<p class="lead">The people who show up on a Hero\'s job are Todd\'s own crew. Todd owns the company, he is a military veteran, and he still works the jobs. His son Nash runs it with him. The rest are people they hired and kept. Nobody gets dispatched to your house off an app that morning.</p>',
  '<p class="lead">The people who show up on a Hero\'s job are Nash\'s own crew. Nash owns the company and he still works the jobs. The rest are people he hired and kept. Nobody gets dispatched to your house off an app that morning.</p>'),
 ('and because the people who own the company are on the jobs. Todd started this with one trailer. He is not sitting in an office watching a dispatch board.',
  'and because the owner is on the jobs. Hero\'s started with one trailer, and Nash is not sitting in an office watching a dispatch board.'),
 ("<p>What is true: it is Todd's crew, they work for Hero's, the owner is on the jobs,", "<p>What is true: it is Nash's crew, they work for Hero's, the owner is on the jobs,"),
 ('<p>Our own people. Todd owns the company and works the jobs, his son Nash runs it with him, and the crew is hired and kept rather than dispatched off an app.</p>',
  '<p>Our own people. Nash owns the company and works the jobs, and the crew is hired and kept rather than dispatched off an app.</p>'),
 ('Todd or Nash picks up.', 'Nash picks up.'),
 ('Text a photo of the pile. Todd and Nash send a price back, and it does not change in the driveway.', 'Text a photo of the pile. Nash sends a price back, and it does not change in the driveway.'),
 ('a price by text, Todd and Nash on every job in', 'a price by text, Nash on every job in'),
 ('<strong>Same two guys, every time.</strong> Todd and Nash run every job themselves, 7am to 8pm, every day.', '<strong>Same guy, every time.</strong> Nash runs every job himself, 7am to 8pm, every day.'),
 ('About Todd and Nash<i aria-hidden="true"></i>', 'About Nash<i aria-hidden="true"></i>'),
 # crew rows and avatars
 ('<span class="t-av"><img src="img/p/face-todd.webp" alt=""></span>', ''),
 ('Job crew: Todd and Nash', 'Job crew: Nash'),
 ('<div class="t-crew-member"><span class="t-avatar"><img src="img/p/face-todd.webp" alt="Todd"></span><div><div class="t-crew-name">Todd</div><div class="t-crew-role">Owner</div></div></div>', ''),
 # photos: the team shot becomes the Nash crop; the trailer shot with Todd in it becomes the loaded trailer or a job photo
 ('<img src="../img/p/team-todd-nash-900.webp" alt="Todd and Nash with the truck and trailer" width="900" height="1125"', '<img src="../img/p/nash-460.webp" alt="Nash with the truck and trailer" width="460" height="575"'),
 ('<img src="img/p/team-todd-nash-900.webp" srcset="img/p/team-todd-nash-480.webp 480w, img/p/team-todd-nash-900.webp 900w" sizes="(max-width:900px) 70vw, 380px" width="900" height="1125" alt="Todd and Nash of Hero\'s Junk Removal standing in a driveway in front of their black pickup and trailer"',
  '<img src="img/p/nash-460.webp" sizes="(max-width:900px) 70vw, 380px" width="460" height="575" alt="Nash of Hero\'s Junk Removal standing in a driveway in front of the black pickup and trailer"'),
 ('<img src="img/p/team-todd-nash-1050.webp" alt="Todd and Nash of Hero\'s Junk Removal standing with their truck and trailer" width="1050" height="1400" fetchpriority="high">',
  '<img src="img/p/rig-loaded-1400.webp" alt="Hero\'s trailer loaded with junk in a North Texas driveway, ready to haul" width="1400" height="788" fetchpriority="high">'),
 ('<img class="s7-main" src="img/p/team-todd-nash-900.webp" alt="Todd and Nash with the truck and trailer" width="900" height="1125" loading="lazy">', '<img class="s7-main" src="img/p/nash-460.webp" alt="Nash with the truck and trailer" width="460" height="575" loading="lazy">'),
 ('<span>Todd and Nash with the truck and trailer</span>', '<span>Nash with the truck and trailer</span>'),
 ('<img src="../img/p/real-rig-960.webp" srcset="../img/p/real-rig-480.webp 480w, ../img/p/real-rig-960.webp 820w" sizes="(max-width:900px) 88vw, 40vw" width="960" height="640" alt="Todd loading the trailer on a North Texas driveway"',
  '<img src="../img/p/job-garage-cleanout-960.webp" sizes="(max-width:900px) 88vw, 40vw" width="960" height="640" alt="A garage stacked with items waiting for pickup"'),
 ('<img src="../img/p/real-rig-960.webp" alt="Todd loading the trailer in a driveway" width="960" height="640"', '<img src="../img/p/rig-loaded-1100.webp" alt="Trailer loaded with junk, ready to haul" width="1100" height="733"'),
 ('<figure><img src="img/p/real-rig-960.webp" width="960" height="640" alt="Todd loading the trailer in a driveway" loading="lazy"></figure>', '<figure><img src="img/p/job-garage-cleanout-960.webp" width="960" height="640" alt="A garage stacked with items waiting for pickup" loading="lazy"></figure>'),
 ('<img class="t-inset" src="img/p/real-rig-960.webp" alt="Todd loading the trailer">', '<img class="t-inset" src="img/p/estate-820.webp" alt="Furniture covered and boxed for an estate pickup">'),
 ('<div class="t-close-photo rise"><img src="img/p/real-rig-960.webp" alt="Todd loading the trailer in a driveway" loading="lazy"></div>', '<div class="t-close-photo rise"><img src="img/p/job-garage-cleanout-960.webp" alt="A garage stacked with items waiting for pickup" loading="lazy"></div>'),
 ('<div class="cb-photo reveal"><img src="img/p/real-rig-960.webp" alt="Todd loading the trailer in a driveway" loading="lazy"></div>', '<div class="cb-photo reveal"><img src="img/p/rig-loaded-1100.webp" alt="Trailer loaded with junk, ready to haul" loading="lazy"></div>'),
 ('<figure class="s7-hero-photo rise"><img src="img/p/real-rig-960.webp" alt="Todd loading the trailer in a driveway" width="960" height="640"', '<figure class="s7-hero-photo rise"><img src="img/p/rig-loaded-1400.webp" alt="Trailer loaded with junk, ready to haul" width="1400" height="788"'),
 ('<img class="s7-main" src="img/p/real-rig-960.webp" alt="Todd loading the trailer in a driveway" width="960" height="640" loading="lazy">', '<img class="s7-main" src="img/p/rig-loaded-1100.webp" alt="Trailer loaded with junk, ready to haul" width="1100" height="733" loading="lazy">'),
 ('<span>Todd loading the trailer in a driveway</span>', '<span>The trailer loaded, ready to haul</span>'),
]
files = [f for f in glob.glob('**/*.html', recursive=True) if not f.startswith(('type-', 'index-trinity', 'piece-demo'))]
used = {i: 0 for i in range(len(R))}; touched = 0
for f in files:
    p = pathlib.Path(f); s = p.read_text(encoding='utf-8'); o = s
    for i, (a, b) in enumerate(R):
        n = s.count(a)
        if n: s = s.replace(a, b); used[i] += n
    if f == 'work.html':   # the trailer now sits in the hero and (08): the repeated band goes
        s, n = re.subn(r'<figure class="s7-band s7-band--tall">.*?</figure>\n', '', s, flags=re.S); print('work band removed', n)
    if s != o: p.write_text(s, encoding='utf-8'); touched += 1
print('files touched', touched)
print('unused rules', [R[i][0][:70] for i, n in used.items() if n == 0])
