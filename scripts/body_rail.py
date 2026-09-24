"""
Round 13 fix, item 1: give inner pages a right rail so the body column stops
sitting inset from the hero's left edge with the right ~540px empty.

Wraps the existing body section(s) - the plain <section> block(s) between the
page-hero and the warm contact section - in <div class="rail"> with
<div class="rail-body"> on the left and <aside class="rail-aside"> holding the
homepage FAQ card's "Send the photo now" markup on the right (copied
byte-for-byte from index.html, same href).

Idempotent: if a file already has class="rail" it is skipped, so a rerun is a
no-op. Byte-safe (LF preserved, no bytes touched outside the matched span).

Usage: python scripts/body_rail.py --apply
       python scripts/body_rail.py            (dry run, lists what would change)
"""
import re
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

SERVICES_EXCLUDE = set()  # round 14: services/index.html now gets the rail too,
                          # it was the one inner page left on a centered narrow
                          # column with no rail card, off the shared grid.

CARD = (
    '      <div class="card">\n'
    '        <h2 style="font-size:1.4rem">Send the photo now</h2>\n'
    '        <p>Open 7am to 8pm, every day. Text a photo and we text back a firm price before anyone drives out.</p>\n'
    '        <div class="cta-row" style="justify-content:flex-start; margin-top:1.6rem">\n'
    '          <a class="btn btn--primary" href="sms:+12142779069?&amp;body=Hi%2C%20here%20is%20a%20photo%20of%20what%20I%20need%20gone.">Text a photo, get a price</a>\n'
    '          <a class="btn btn--quiet" href="tel:+12142779069">Call (214) 277-9069</a>\n'
    '        </div>\n'
    '      </div>'
)

BODY_RE = re.compile(r'(<section>[\s\S]*?)(?=<section class="section section--warm" id="contact">)')


def target_files():
    files = [ROOT / "about.html", ROOT / "areas.html"]
    for p in sorted((ROOT / "services").glob("*.html")):
        if p.name in SERVICES_EXCLUDE:
            continue
        files.append(p)
    return files


def process(path: pathlib.Path, apply: bool) -> str:
    raw = path.read_bytes()
    text = raw.decode("utf-8")

    if 'class="rail"' in text:
        return "skip (already applied)"

    m = BODY_RE.search(text)
    if not m:
        return "SKIP (no body/contact section match)"

    body = m.group(1)
    # the body sections carry their own centered style="max-width:820px" wrap;
    # the rail track already caps the left column at 62ch, so drop the inline
    # cap and let .rail-body .wrap fill the track (style.css owns the rest).
    body = body.replace(' style="max-width:820px"', "")
    body = body.rstrip("\n")

    wrapped = (
        '<div class="rail">\n'
        '<div class="rail-body">\n'
        + body + "\n"
        '</div>\n'
        '<aside class="rail-aside">\n'
        + CARD + "\n"
        '</aside>\n'
        '</div>\n\n'
    )

    new_text = text[: m.start()] + wrapped + text[m.end():]

    if apply:
        path.write_bytes(new_text.encode("utf-8"))
        return "applied"
    return "would apply"


def main():
    apply = "--apply" in sys.argv
    for path in target_files():
        rel = path.relative_to(ROOT)
        result = process(path, apply)
        print(f"{rel}: {result}")


if __name__ == "__main__":
    main()
