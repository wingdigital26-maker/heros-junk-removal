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
