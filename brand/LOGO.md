# Hero's Junk Removal — logo rework, 2026-09-22

Reason for the rework: the client rejected the open-doorway arch mark outright ("logo is bad,
rework it") and killed the orange theme. This replaces both.

## Palette (orange retired)
- `--ink` #0E1621, primary
- `--steel` #6E7A8A, secondary
- `--accent` #C2362F, signal red, used sparingly (CTA buttons, one hairline)

## The six directions explored
Contact sheet: `brand/logo-sheet.html` (six marks, each at 32/64/200px, on the silver gradient
and on navy, single colour, plus beside the Fraunces wordmark). Candidate source files in
`brand/candidates/`.

1. **Loaded truck, geometric** (`01-truck.svg`) — a faceted silhouette: chassis, separated
   wheels, cab, and one bold triangular junk peak above the bed. First pass was an unreadable
   blob at 32px (wheels and cab fused into the mound with no negative space); reworked with a
   single peak and a visible gap between the chassis and the wheels. Reads as a loaded truck
   now, not a bare hauler. Strongest "expected" direction, but still the busiest of the six at
   the smallest size.
2. **Monogram H, cleared space** (`02-monogram.svg`) — two uprights, a crossbar broken into two
   blocks with a gap between them, and one small square detached and floating above-right, as if
   pulled out of the mark. Reads as a crisp H at every size tested, including 32px, and the gap
   plus the detached chip read as intentional rather than accidental even that small. Pairs
   cleanly with the wordmark as a lockup.
3. **Abstract cleared volume** (`03-cleared-space.svg`) — an open crate (front face plus a
   receding open top, drawn as a flat trapezoid, not a peaked roof) with a solid block lifted
   above and to the side. First pass read as a birdhouse because the open-top line met the
   dashed connector at a point, which looked like a roof ridge; reworked to a flat trapezoid
   lid and dropped the connecting arrow, which was leaving a bookmark-shaped notch in the block.
   Now reads as "something lifted out," but it is still the most cluttered of the six at 32px,
   two distinct shapes plus a gap is a lot to resolve that small.
4. **Shield badge, trust cue** (`04-badge.svg`) — a rounded shield outline with a single upward
   chevron inside, restrained, no crest, no comic proportions. Reads clean at every size,
   borrows calm trust cues from security and insurance marks without tipping into clipart.
5. **Custom-cut H glyph** (`05-wordmark-h.svg`) — a standalone serif-style H with one chamfered
   top corner, meant to double as the cut used inside the H of the full wordmark. Reads fine but
   the chamfer nearly disappears at 32px, so at small sizes it is functionally identical to a
   plain block H. Conceptually redundant next to #2, which carries a more visible detail at the
   same size.
6. **Full becoming empty** (`06-before-after.svg`) — one square, the upper-left triangle solid
   (full), the rest an outline (cleared). Renders the cleanest of all six at every size, but it
   is the most abstract: without the wordmark next to it, nothing about it says junk removal.
   Works as a supporting device (e.g. a section divider or a loading state) more than as the
   primary mark.

## Ranking
1. Monogram H (#2) — picked for the live files.
2. Shield badge (#4) — strong second, a safe alternate if the client wants something more
   literal-trust than literal-junk.
3. Loaded truck (#1) — the most expected direction, now legible after rework, good if the client
   specifically wants a vehicle in the mark again.
4. Custom-cut H glyph (#5) — solid but redundant next to #2.
5. Full becoming empty (#6) — best pure geometry, weakest standalone recognition.
6. Cleared volume / crate (#3) — honestly the weakest of the six even after two rounds; still
   the busiest silhouette at 32px and the least distinctive of the group.

## Why the Monogram (#2) is live now
It is the only one of the six that is simultaneously the most legible at 32px, the most ownable
(nobody else in the DFW junk-removal category is running a cut-crossbar H), and the one that
carries the brand idea (something is missing, something was cleared) without needing a truck,
a cape, or a shield to say it. It also sits comfortably on both the silver gradient and navy
without a second colour, and the single detached chip is the one sharp detail the brief asked
for without crowding the mark.

`assets/logo-mark.svg` (icon only, viewBox 0 0 48 56) and `assets/logo.svg` (icon + "Hero's /
JUNK REMOVAL" text, viewBox 0 0 260 56) are now the monogram, fill `#0E1621`, so the header,
the intro overlay and the favicon fallback all pick it up automatically since those pages
reference these two files by path and were not touched. `assets/logo-lockup.svg` is new, a
horizontal mark plus "Hero's Junk Removal" plus a small "VETERAN OWNED · DFW" line, for anywhere
a wider lockup is useful (email signatures, printed estimates, truck door decal reference).

## Still not good enough
- Direction #3 needs a third pass or should be dropped from the set entirely if the client asks
  for more options later; it is carrying its own weight the least at small sizes.
- No dark-mode-specific spacing has been tuned; the monogram uses the same proportions on both
  backgrounds. Worth a contrast check on an actual phone screen in daylight, not just this
  screenshot, before this goes on a truck door or a yard sign.
- The single-colour requirement is honestly met (fill is one flat colour, no gradients, no
  strokes-plus-fills mixing) but nobody has proofed these at true favicon size (16px) yet, only
  down to 32px as the brief specified.
