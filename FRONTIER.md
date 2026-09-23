# FRONTIER.md - heros-v3 depth memory (committed)

Current LEVEL: 2 (section deep-dive). Round: 5.

| id | parent_id | label | level | status | last_round | source | note |
|---|---|---|---|---|---|---|---|
| R1 | - | 84 inner pages load styles.css while index.html loads style.css: one site, two design systems | 1 | done | 2 | jack | chrome unified across all 81 pages; body components still on styles.css, see R9 |
| R2 | - | contact.html field `company` has no visible label (W12 FAIL, phone + desktop) | 1 | pruned | 2 | verifier | FALSE POSITIVE: it is a spam honeypot, see REJECTED.md. Linter fixed instead |
| R3 | - | contact.html first-viewport image contact-480/1100.webp is lazy (W20 FAIL) | 1 | open | 1 | verifier | conversion_lint round 1 |
| R4 | - | about.html first-viewport card-estate-480.webp is lazy at 375px (W20 FAIL) | 1 | open | 1 | verifier | conversion_lint round 1 |
| R5 | - | all 85 pages fetch Fraunces + Source Sans 3 from Google's CDN (W21) | 1 | done | 2 | verifier | self-hosted, 2 files, 89,968 bytes, 0 third-party requests |
| R6 | - | nav labels and primary CTA differ between homepage and inner pages | 1 | done | 2 | jack | one nav on all 81 pages |
| R9 | R1 | inner-page BODY components still come from the legacy styles.css, loaded before style.css | 2 | open | 5 | jack | DIRECTION SET 2026-09-22: homepage patterns win, see STEERING.md. Drain styles.css, then delete it |
| R10 | R1 | favicon differed per page: inner pages used a navy data-URI truck from the pre-v3 palette | 1 | done | 2 | verifier | unified to assets/logo-mark.svg |
| R7 | - | styles.css carries 33 raw hex + 60 raw px off-token (A3) | 1 | candidate | 1 | drain-check | may be moot once R1 lands |
| R8 | - | brand/logo link tap target under 44px (A7) on home and inner pages | 1 | open | 1 | verifier | conversion_lint round 1 |

## SUCCESS CRITERIA (scored every round)
1. Every page in this build shares ONE stylesheet, one nav, one footer, one CTA label.
2. `visual_run.py .` exits PASS: kit, gate, and conversion clean on every linted page.
3. From any inner page a stranger can reach the text-a-photo action in the first viewport.
4. No page makes a render-blocking third-party font request.
5. Both Fable judges pass all four Stripe axes at 4 or better with no slop tells.
6. Homepage and a representative inner page do not regress in page weight or request count.

| R11 | R9 | inner-page FAQ is white boxed cards while the homepage FAQ is a plain hairline list | 2 | open | 5 | verifier | BOTH judges named this independently; needs Jack's direction call |
| R12 | R9 | inner pages close on the old black "Get a Free Estimate" band; the homepage closes on the warm "Send the photo now." block | 2 | open | 5 | verifier | Judge A |
| R13 | R9 | services grid puts 7 cards in a 3-col layout: orphan card + an empty two-thirds row (blank-region + rule-of-three) | 2 | open | 5 | verifier | Judge C |
| R14 | - | 29 kicker eyebrows in the old teal/navy palette, absent from the approved homepage | 1 | done | 5 | verifier | removed across 28 pages |
| R15 | - | 101 middle-dot meta strings (eyebrow-microlabels tell) | 1 | done | 5 | verifier | rewritten as sentences |
| R16 | - | unverifiable "hundreds of DFW garages" count and "certified refrigerant recovery" implying Hero's holds the cert | 1 | done | 5 | verifier | Judge A automatic-fail trigger; copy corrected, the true recycler fact kept |

## Round 4 judge scores (both Fable 5.1, 3 permuted orderings each)
Judge A fidelity: Utility 4, Usability 4, Craft 3, Beauty 3 - FAIL, better_than_previous true
Judge C slop:     Utility 4, Usability 3, Craft 3, Beauty 3 - FAIL, better_than_previous true
Bar is all four axes at 4+. Craft and Beauty are held down by ONE root cause:
inner pages still run a second design system BELOW the unified chrome (R11-R13).
