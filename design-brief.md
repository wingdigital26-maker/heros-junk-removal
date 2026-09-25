# design-brief.md - heros / site
opened: 2026-09-22
route: kit          # kit = house system + this brand | diverge = 3 tiles, one decider
judge_model: fable-5.1 (fallback: opus)   # one judge model for the whole build
builder_model: fable-5.1                  # Jack's call this build (seat table default is sonnet-5)
budget_cap: 4 rounds; vision judges only after a clean mechanical round

## THE ONE CONVERSION  (fill this before any code)
A DFW homeowner texts a photo of their pile to (214) 277-9069 and gets a price
back before anyone drives out. Every page is graded on how fast it gets a
stranger to that text. Calling is the fallback, not the ask.

## Brand block (the only part of tokens.css that changes)
accent:            #B32A25   (white on it 6.4:1)
accent-press:      #9E241F   (white on it 7.5:1)
on-accent:         #FFFFFF
ink / ink-muted:   #1C1917 / #57534E
bg / bar / surface: #FFFFFF / #F7F5F1 / #F7F5F1
hairlines:         #E7E5E4 / #D6D3D1 / #78716C (edge)
display font:      Fraunces (opsz 9..144, 600, SOFT 0..100)
text font:         Source Sans 3 (400/600/700)
mono font:         none - this site has no numeric UI
licence checked:   yes - both SIL Open Font License 1.1, free for commercial use

## The three things that make this not the template  (HARD-RULES A5)
1. The hero object is a scroll-driven WebGL piece: a house built from 1,074
   instanced blocks in ONE draw call that re-forms into couch, fridge, map,
   message and truck as you scroll. Nothing in the house kit has a 3D piece.
2. The H1 is split around that object - "Junk [piece] gone." - instead of the
   kit's stacked hero block. The object is a word in the sentence.
3. The primary action is an SMS deep link with a prefilled body, not a form.
   Every primary button opens the visitor's own messaging app with the photo
   ask already written.

## References - at least two, crossed with the brand
- The client's own photography: Todd and Nash in the driveway, the black pickup
  and trailer, real job shots (garage clearout, curbside pickup). This sets the
  imagery cast and the copy voice - plain, first-person, no stock crews.
- Junk King and College Hunks (the category's best-funded sites) for structure
  only: what a homeowner expects to find and in what order. Crossed with the
  brand, not copied - both lean on stock photography and loud price badges,
  which this build refuses.

## Diverge (route: diverge only) - three tiles in .visual/tiles/{a,b,c}.html
decider: Jack (route kit - no tiles; the v3 look is the direction he already
approved on 2026-09-22 and it is option zero)

## Pinned tokens - the exact values this build is locked to
- accent #B32A25 / accent-down #9E241F on #FFFFFF, one warm band #F7F5F1
- Fraunces display + Source Sans 3 text, scale 1.25 phone opening to 1.333 desktop
- --step-hero clamp(3.5rem, 1.6rem + 8.2vw, 7.75rem), used once, on the homepage only
- radius scale 4 / 10 / 16 / pill; spacing 4px base; --target 44px
- --col-text 44rem, --col-wide 76rem, --measure 62ch

## Surface prerequisites
static folder; gate serves it locally

## Measured state at round 1 (baseline, 2026-09-22)
index.html alone is on the new style.css. The other 84 pages still load the old
styles.css + piece.css and carry a different nav, a different CTA label and an
announcement bar the homepage does not have. Unifying them is this build's job.

## The pick
- b.png  (Jack 2026-09-25: B in general looks best (Wing-style split name around centered video window, dark ink header bar))
