# v2 CONVERSION CONTRACT — non-negotiable build rules

Derived from the round 1 forensic audit of v1. Every one of these is a defect we measured in v1.
A page that violates any rule below is not shippable. The visual loop may not override these.

## 1. Every page can be called from, always
- EVERY page carries a working `tel:` link. No exceptions. v1 had 14 service pages with none.
- The phone number is visible ABOVE THE FOLD on every page type, including the homepage.
- FORBIDDEN: any rule resembling `body.home .topbar{display:none}`. The homepage is the most
  visited page and must be the easiest to call from, not the hardest.
- A build check greps every built page for `tel:` and fails the build if any page lacks one.

## 2. Anything that looks like a call button IS a call
- If a control has a phone icon, or its class or label says call, its href starts with `tel:`.
- v1's `.cb-call` pointed at `contact`. That exact bug is now a build failure.
- The mobile sticky bar offers two real actions: CALL (tel:) and TEXT (sms:). Both real hrefs.

## 3. The funnel is measured from day one
- Analytics on every page. v1 had zero across 79 files, which is why "3 calls" means nothing.
- Tracked events, minimum: phone click, text click, form submit, form success, form FAILURE,
  estimator start, estimator complete.
- Form failure must be tracked. A silent form is how a site loses leads invisibly.

## 4. No single point of failure on contact
- v1 routed everything through one third-party form handler into one Gmail inbox, unverified.
- v2: form submit must succeed or visibly fail, and on failure the page shows the phone number
  and text option immediately. Never a dead end.
- The form is on every page type, not just 2 of 79.

## 5. Price anxiety is answered on the page
- v1 had zero dollar figures sitewide while promising "a firm price."
- Category evidence: 46% of haulers refuse to quote before an on-site visit, so transparency is
  a real differentiator here, not table stakes.
- v2 shows how pricing works (truck-fill fractions, ~1/8 load increments, 1 cubic yard is about
  a washer or dryer) even before exact dollars are available.
- BLOCKER: real dollar amounts must come from Jack or Hero's. NEVER invent a price.
  Until supplied, the estimator outputs load fraction and an itemized list, not fabricated money.

## 6. Informational pages must route to hire-intent
- Every blog post carries a contextual CTA back to the matching service page plus a call path.
- v1 posts were dead ends with only generic nav and footer.
- Posts that steer readers to free/DIY disposal get reframed toward "or we handle it today."

## 7. Mobile is the primary target
- Designed at 390px first. Call and text targets are thumb-reachable and at least 44px.
- Verified in a real mobile viewport render, not assumed.

## 8. URL PRESERVATION — the highest project risk (round 2 adversarial lane)
The v1 site has 79 indexed pages pulling real traffic. A from-scratch rebuild is the single
most likely way to DESTROY that traffic. Documented redesign failures trace to changed URLs,
lost internal links, and copy that drops the city and service keywords.
- EVERY v1 URL either keeps its exact path in v2, or gets a 301 to its closest equivalent.
- A migration map is produced BEFORE launch, URL by URL, and checked.
- Every ported page keeps its city and service words in the H1, title, and URL.
- Internal linking density is matched or improved, never reduced.
- No page is deleted without an explicit redirect decision recorded.
This ranks equal to "get real prices" as a launch blocker.

## 9. PRIMARY CTA IS TEXT A PHOTO, PHONE SECOND (round 2 customer-voice lane)
Evidence: across ~70 real reviews and a 50-company mystery shop, the category's number one
trust killer is the price rising once the truck is in the driveway. Four independent cases:
$25 quoted became $189, $280 prepaid became $580, $480 negotiated to $340 and still lost.
Only 7 of 50 companies gave a firm price by phone.
- v2's primary CTA: TEXT A PHOTO, GET A FIRM PRICE. This directly attacks the category defect.
- Phone stays visible and prominent as the secondary path for urgent and older callers.
- A blind lead form is NEVER the primary CTA. Not one review in the sample praised a form.
- The promise made must be one Hero's can keep. Wording must come back to Jack before launch,
  because "firm price" is a commitment the business has to honor.

## 10. PROOF IS PERSONAL, NOT CORPORATE
- Real, verified: 4.9 stars, 11 Google reviews. Veteran-owned. Family-owned, Todd and son Nash.
- NEVER lead with the review COUNT. Competitors show 900+ and 8,000+; 11 loses that comparison.
  Lead with the 4.9 rating, veteran-owned, family-owned, owner on the job.
- 5-star reviews name the crew by first name almost every time. Trust is personal, not brand.
  Put the real people on the page.
- Speed language that earns praise: arrived within about 2 hours, same day. Only claim what is true.

## 11. SPEED TO RESPONSE IS A DESIGN REQUIREMENT
The largest measured lift in adjacent case studies was speed-to-callback, not any widget.
A lead the site captures but nobody answers fast is worth nothing. Whatever v2 captures must
route somewhere Hero's actually sees immediately.

## 12. DEFINE SUCCESS BEFORE LAUNCH
Never compare v2's numbers to the old "4,000", which came from an unknown tool and may include
heavy bot traffic (bot share of web traffic runs 35-63% by measurement method).
Success = tracked tel: clicks, sms: clicks, and form completions per page. Not one monthly number.
