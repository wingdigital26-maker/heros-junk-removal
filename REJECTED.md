# REJECTED.md - heros-v3 (committed)

One dated line per thing tried and reverted, disproven, or pruned, and why.
Every Level 3/4 build brief must read this so a later round never re-proposes it.

- 2026-09-22 "the hero 3D piece is broken / renders blank" - DISPROVEN. The
  poster webp is 42.7% opaque and paints correctly; the first screenshot was
  simply taken before the image decoded. Do not re-open this.
- 2026-09-22 "contact.html `company` field is missing a visible label (W12 FAIL)"
  - FALSE POSITIVE, do not fix. `company` is a spam honeypot: class `hp`, parked
    at left:-9999px by styles.css:194, `aria-hidden="true"`, `tabindex="-1"`, and
    the form's own submit handler drops any submission that fills it. Adding a
    visible label would disable the spam protection. Fixed in the TOOL instead:
    conversion_lint.py now excludes honeypot fields from the field checks.
