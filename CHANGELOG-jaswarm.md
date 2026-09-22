# CHANGELOG-jaswarm.md - heros-v3 (committed)

One dated digest per round, newest at the bottom.

## 2026-09-22 · Rounds 1-4 · heros-v3 (one batch, main session did the shared chrome)

| Lane | Change | Proof |
|---|---|---|
| visual | All 81 pages put on one nav, one footer, one favicon, one type stack. The black .emergency-strip is gone (it duplicated the nav's phone + text CTA, two filled primaries in one viewport). | 81/81 carry `<nav id="nav">`, 0 carry `header class="site"`, 0 carry emergency-strip |
| perf | Fonts self-hosted: 2 woff2, 89,968 B, preloaded. Source Sans 3 is ONE variable file for 400-700 (Google served the same 28,740 B file 3x). | about.html 428,000 -> 271,911 B, 3 third-party requests -> 0. Blog post 335,616 -> 179,541 B. Same -156 KB on both. |
| content | 53 of 81 pages had no action above the fold. Each got the CTA row services/index.html already used. | conversion_lint W1 FAIL -> PASS on contact + about |
| correctness | contact/about first-viewport images no longer lazy; brand link holds a 44px tap target under 600px; mobile burger script injected (the old inline onclick was removed with the old header, so mobile nav would have been dead on 80 pages). | round 4: conversion PASS on all 3 linted pages |
| gate | kit WARN, gate PASS, conversion PASS x3 | .visual/round-4/gate-report.md |
| tooling | 3 real bugs fixed in the /visual skill itself, not worked around here. | see below |

**/visual skill fixes (they were breaking every build, not just this one):**
- `visual_run.py` died mid-round on cp1252 stdout, so no loop-log row was ever written.
- `receipt_open.py` wrote `pinned tokens:` as a plain line while `visual_gate.py` required a `#` heading, so every route-kit build failed its own receipt check.
- `conversion_lint.py` reported spam honeypots as W12 "field with no visible label". Acting on that would have disabled the spam trap. Honeypots are now excluded from field checks.

**Committed:** 7240e0c (95 files) · **Open:** styles.css still supplies inner-page BODY components (FRONTIER R9) · **Not shipped:** nothing pushed, nothing merged, origin/main untouched
