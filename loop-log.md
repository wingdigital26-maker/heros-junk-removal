# loop-log.md - heros / site

Written by scripts/visual_run.py, one row per round. Judge verdicts get
appended underneath by the orchestrator.

| round | date | kit | gate | conversion | overall | defects / note |
|---|---|---|---|---|---|---|
| 1 | 2026-09-22 | WARN | FAIL | 1/3 pass | **FAIL** | gate: receipt incomplete: design-brief.md pinned tokens section has no non-empty bullets; gate: receipts missing; lint: ? only 1 distinct border-radius value(s) (50%). Real design systems have a radius scale. (style.css); conv contact.ht... |
| 1 | 2026-09-22 | WARN | PASS | 1/3 pass | **FAIL** | conv contact.html: W12 fields with no visible label @phone: ['company']; conv contact.html: W20 first-viewport image contact-480.webp lazy=True has_dims=True @phone; conv contact.html: W12 fields with no visible label @desktop: ['company... |
| 2 | 2026-09-22 | WARN | PASS | 1/3 pass | **FAIL** | conv contact.html: W1 no primary CTA or input in the first viewport @phone; conv contact.html: W1 no primary CTA or input in the first viewport @desktop; conv about.html: W1 no primary CTA or input in the first viewport @phone; conv abou... |
| 3 | 2026-09-22 | WARN | PASS | 3/3 pass | **PASS** | clean |
| 4 | 2026-09-22 | WARN | PASS | 3/3 pass | **PASS** | clean |

## Round 4 - Judge A (fidelity)

Majority of 3 permuted runs (axis order and image order shuffled): 3/3 FAIL, scores identical across runs.

```json
{
  "seat": "A",
  "images_visible": {"candidate": true, "reference": true, "previous": true},
  "axes": {
    "utility":   {"score": 4, "evidence": "after-about/desktop.png first viewport: H1, one-line story, red 'Text a photo, get a price' pill and an outline call button tell a stranger what this is and what to press; same block sits at y 424-486 of 812 in after-about/mobile.png, so questions 1-3 all pass on every AFTER page."},
    "usability": {"score": 4, "evidence": "after-services-index/desktop.png reads cleanly at 1440 with nothing broken, but after-about/mobile.png opens with the house piece orphaned top-left over a blank right half before the breadcrumb, and every inner page closes on a second and third filled red button with different labels ('Get a Free Estimate', 'Contact Us') that pull toward calling, which the brief calls the fallback."},
    "craft":     {"score": 3, "evidence": "after-about/desktop.png FAQ block: four white cards each ~110px tall with a lone '+' and a hairline eyebrow, a boxed treatment the homepage never uses (round-4/desktop.png FAQ is a hairline list); after-services-index/desktop.png row three is one card and two empty grid cells."},
    "beauty":    {"score": 3, "evidence": "The hero band of every AFTER page (house piece beside a Fraunces H1) would get a senior sign-off, but from the mid-page down after-about/desktop.png and after-blog-garage-cleanout-checklist/desktop.png fall back to a black band, centered serif line, one red pill, which is the statistical average closer."}
  },
  "one_site": {
    "verdict": "Mostly, not fully. Header, footer, breadcrumb, type stack and hero action now match the homepage on all four pages. The lower half of every inner page still belongs to the old site.",
    "breaks": [
      "Closing band: after-about, after-services-index and after-blog all end on a near-black band with a centered white serif line and a red pill ('Contact Us' / 'Get a Free Estimate'); the homepage (round-4/desktop.png) ends on the warm #F7F5F1 band 'Send the photo now.' with 'Text a photo, get a price' plus a call button. Two different closers, two different asks.",
      "FAQ: inner pages use boxed white cards with '+' on the warm band; the homepage uses a hairline-separated list on white ('Before you text.').",
      "after-about/desktop.png mid-page still carries the old 'Get a Free Estimate' + 'See What We Haul' pair, a second red filled button with a label the homepage never uses."
    ]
  },
  "a5_not_template": {
    "pass": true,
    "seen": [
      "A block-built 3D house with blocks breaking away, used as the hero object on every page, and on the homepage set inside the sentence 'Junk [house] gone.' as if it were a word (round-4/desktop.png, after-about/desktop.png top right).",
      "The primary ask is a text, not a form or quote request: 'Text a photo, get a price' with a speech-bubble glyph on the homepage pill, and no form anywhere in five pages.",
      "The photography is the owners' own: two men at a black pickup in a driveway with the caption naming them, the open trailer on a driveway, and real pile shots (couch, chair, garage) on the service cards rather than stock crews in matching polos."
    ]
  },
  "conversion": {
    "q1_five_second": "yes on all four AFTER pages",
    "q2_one_dominant_action": "yes in the first viewport; red is used only on the primary pill (header pill is black)",
    "q3_in_first_viewport": "yes desktop and phone",
    "q4_competition": "no in the first viewport; yes further down (two more filled red buttons per page with different labels)",
    "q5_login_wall": "n/a, no app",
    "q6_status_without_colour": "n/a, no statuses shown",
    "q7_verb_plus_value": "hero yes ('Text a photo, get a price'); closer no ('Contact Us' on about is generic)",
    "q8_fabricated_proof": "FLAG: after-blog-garage-cleanout-checklist/desktop.png intro says the method is watched 'in hundreds of DFW garages', an unverifiable count for a two-man crew; after-services-index card says 'certified refrigerant recovery' with no certifier shown. Homepage '4.9 on Google' is linked to the reviews so it is checkable and not counted. The count claim is inherited copy (present in BEFORE too) but the rubric makes it an automatic FAIL."
  },
  "tells": ["blank-region"],
  "gaps": [
    "Inner pages still close on the old black band with a call/contact ask; swap for the homepage's warm 'Send the photo now.' closer so the ONE conversion holds to the last pixel.",
    "Blog and services copy carry an unverifiable count ('hundreds of DFW garages') and an unnamed certification; cut or make checkable.",
    "FAQ on inner pages is boxed cards; homepage is a hairline list. Pick the homepage treatment site-wide."
  ],
  "one_move": "Replace the black closing band on every inner page with the homepage's warm 'Send the photo now.' block (text pill + call outline) and drop the mid-page 'Get a Free Estimate' pair.",
  "better_than_previous_round": true,
  "overall": "FAIL"
}
```

## Round 4 - Judge C (slop)

Three independent runs with candidate and rubric order permuted (about/services/blog; blog/about/services; services/blog/about). All three returned FAIL. Five tells appeared in 3/3 runs, even-spacing in 2/3. Majority verdict below.

```json
{
  "seat": "C",
  "images_visible": {"candidate": true, "reference": false, "previous": true},
  "axes": {
    "utility":   {"score": 4, "evidence": "after-about/desktop.png: the first viewport says who this is and the red 'Text a photo, get a price' button says exactly what happens; the trailer and coffee-table photos are the company's own, not stock."},
    "usability": {"score": 3, "evidence": "after-services-index/desktop.png: the filled black 'Text a photo' pill in the header sits in the same viewport as the red primary button, a second filled button competing with the one action (conversion Q4 caps this at 3); the seventh service card sits alone beside two empty slots."},
    "craft":     {"score": 3, "evidence": "after-services-index/desktop.png: three different left edges on one page, the card grid starts at x=150, the 'By city' table at x=300 and the second callout box at x=340, so the column never settles."},
    "beauty":    {"score": 3, "evidence": "after-about/desktop.png: serif display, sans body, cream FAQ band, white hairline cards and a black CTA band is the statistical average of a clean editorial template; the voxel house is the only distinctive element and it repeats unchanged on every inner hero."}
  },
  "tells": [
    "eyebrow-microlabels: after-about/desktop.png 'OUR STORY' tracked caps above 'Meet Todd and Nash' and 'GOOD QUESTIONS' above the FAQ heading (also on after-about/mobile.png); after-blog-garage-cleanout-checklist/desktop.png meta string 'By the Hero's team · Updated July 2026 · 6 min read' with middle dots; after-services-index/desktop.png seven card links ending in an arrow 'Furniture removal details →'; SERVICES / CITIES / MORE tracked caps in every footer including round-4/desktop.png.",
    "rule-of-three: after-services-index/desktop.png, seven services forced into a three-column card grid, leaving Construction Debris orphaned on its own row.",
    "blank-region: after-services-index/desktop.png, the two empty card slots beside Construction Debris leave roughly 800 by 400 px of white doing nothing in the middle of the page.",
    "uniform-radius: after-services-index/desktop.png and after-about/desktop.png, service cards, FAQ cards, callout boxes, the trailer photo, the card thumbnails and every button share the same rounding; there is no radius scale between a 1200 px photo and a 40 px button.",
    "stacked-separation: after-about/desktop.png reads bottom-up as four flat colour bands stacked with nothing bridging them: white content, cream FAQ band, black CTA band, cream footer; after-blog-garage-cleanout-checklist/desktop.png is the same white / black / cream stack.",
    "even-spacing: after-about/desktop.png, every band carries the same roughly 90 to 100 px top and bottom padding and the four FAQ cards are identical 100 px boxes with identical 16 px gaps, so the page has no rhythm between a hero, a story and a footer."
  ],
  "gaps": [
    "The inner pages were unified onto the homepage but not onto the homepage's own FAQ: round-4/desktop.png runs 'Before you text.' as a plain hairline list, while after-about and after-blog use white SaaS-style cards with plus icons on a cream band. Two FAQ systems on one site.",
    "The services page has three left edges (cards, By-city table, callouts) and an orphan seventh card; it is the page a homeowner lands on from search and it is the least resolved.",
    "Every inner hero is the same block with the words swapped: same left title, same two buttons, same voxel house at the same spot on about and blog. That is what makes it read as a template with the logo dropped in rather than pages a real two-man crew would have."
  ],
  "one_move": "On after-services-index/desktop.png replace the seven-card three-column grid with the homepage's own 'If it is in the way, it goes' hairline list (round-4/desktop.png), one row per service with the real photo at the left, which removes the orphan card, the blank two-thirds row, the arrow links and the uniform card radius in one edit, then strip the OUR STORY / GOOD QUESTIONS eyebrows and the middle-dot blog meta string.",
  "better_than_previous_round": true,
  "overall": "FAIL"
}
```

Answers:
1. Real business or template: the photos argue for a real business (their own trailer, a real sectional, a real gutted garage, the coffee table on their concrete) and the copy names Todd and Nash. The chrome around those photos argues template: tracked-caps eyebrows, carded FAQs, arrow links, a three-column grid that the content does not fit, and the identical hero block on every inner page. Verdict: a real business wearing a template.
2. Single change: the services grid to the homepage hairline list, as in one_move.

Better than before: yes. The before-about and before-services renders had a stretched, low-resolution red-and-blue logo banner in the footer, a promo top bar, no CTA in the hero at all, and a 'Site by Wing Digital' credit; all gone.
| 5 | 2026-09-22 | WARN | PASS | 3/3 pass | **PASS** | clean |
| 6 | 2026-09-22 | WARN | PASS | 3/3 pass | **PASS** | clean |
| 7 | 2026-09-22 | WARN | PASS | 4/4 pass | **PASS** | clean |
| 8 | 2026-09-22 | WARN | PASS | 5/5 pass | **PASS** | clean |
| 9 | 2026-09-22 | WARN | PASS | 5/5 pass | **PASS** | clean |

### Round 9 judge pass (Fable 5.1, in-chat on the captures, no agents per Jack, 2026-09-22)
Utility 4 (kicker names job + place on the first screen; one red action, isolated; proof is three real Google reviews, attributed, no count). Usability 4 (header tel link, 44px targets, primary action above the fold at 900 and at 720 via the short-window rule). Craft 4 (one hairline system, two families, radius scale; the proof split leaves white under the rating column, same pattern as the other splits). Beauty 4 (the piece and its parked twin in the nav are the signature; real photos). Tells: none from the taxonomy. Gaps: the parked logo's leaving blocks can read as specks beside the wordmark at 32px; the flight's mid frame crosses the hero words for a beat; 1280x720 lands the button at the fold edge. Verdict PASS, better_than_previous true.
