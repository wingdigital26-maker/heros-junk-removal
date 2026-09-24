"""
Round 15 fix, item 2: drop the outline "Call (214) 277-9069" button from the
rail card (scripts/body_rail.py's CARD template) on already-applied pages.
The header and hero CTA already carry the tel: link, so the rail card keeps
only the red "Text a photo, get a price" button.

Scoped to body_rail.py's own target_files() list so it never touches the
homepage FAQ card or blog sidebar cards, which are a different markup owner.

Idempotent: a page missing the line is left untouched. Byte-safe (LF
preserved, no bytes touched outside the matched line).

Usage: python scripts/remove_rail_call_btn.py --apply
"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import body_rail

LINE = '          <a class="btn btn--quiet" href="tel:+12142779069">Call (214) 277-9069</a>\n'


def process(path: pathlib.Path, apply: bool) -> str:
    raw = path.read_bytes()
    text = raw.decode("utf-8")

    if LINE not in text:
        return "skip (no quiet call button found)"

    new_text = text.replace(LINE, "", 1)

    if apply:
        path.write_bytes(new_text.encode("utf-8"))
        return "removed"
    return "would remove"


def main():
    apply = "--apply" in sys.argv
    for path in body_rail.target_files():
        rel = path.relative_to(body_rail.ROOT)
        result = process(path, apply)
        print(f"{rel}: {result}")


if __name__ == "__main__":
    main()
