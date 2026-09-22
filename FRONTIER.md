# FRONTIER.md - heros-v3 depth memory (committed)

Current LEVEL: 1 (broad sweep). Round: 2.

| id | parent_id | label | level | status | last_round | source | note |
|---|---|---|---|---|---|---|---|
| R1 | - | 84 inner pages load styles.css while index.html loads style.css: one site, two design systems | 1 | done | 2 | jack | chrome unified across all 81 pages; body components still on styles.css, see R9 |
| R2 | - | contact.html field `company` has no visible label (W12 FAIL, phone + desktop) | 1 | pruned | 2 | verifier | FALSE POSITIVE: it is a spam honeypot, see REJECTED.md. Linter fixed instead |
| R3 | - | contact.html first-viewport image contact-480/1100.webp is lazy (W20 FAIL) | 1 | open | 1 | verifier | conversion_lint round 1 |
| R4 | - | about.html first-viewport card-estate-480.webp is lazy at 375px (W20 FAIL) | 1 | open | 1 | verifier | conversion_lint round 1 |
| R5 | - | all 85 pages fetch Fraunces + Source Sans 3 from Google's CDN (W21) | 1 | done | 2 | verifier | self-hosted, 2 files, 89,968 bytes, 0 third-party requests |
| R6 | - | nav labels and primary CTA differ between homepage and inner pages | 1 | done | 2 | jack | one nav on all 81 pages |
| R9 | R1 | inner-page BODY components still come from the legacy styles.css, loaded before style.css | 2 | open | 2 | jack | drain styles.css, then delete it |
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
