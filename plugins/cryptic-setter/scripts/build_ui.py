#!/usr/bin/env python3
"""Bind a puzzle document to the solver UI and emit a page.

    python3 scripts/build_ui.py fixtures/first-light-good.json -o dist/first-light.html
    python3 scripts/build_ui.py puzzle.json --artifact-body -o body.html

Standalone output is a complete HTML file that opens from disk. Artifact-body
output is the same page without the document skeleton, ready to publish as an
Artifact (which supplies its own head and body).
"""

import argparse
import base64
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import puzzle as puzzle_mod
from validate import SCHEMA_PATH, validate_file

TEMPLATE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui", "solver.html"
)
START, END = "<!-- ARTIFACT-BODY-START -->", "<!-- ARTIFACT-BODY-END -->"

# Obfuscation, not encryption. The answers are in the page because the page has
# to check them offline; this only stops them being read at a glance.
OBFUSCATION_KEY = "cryptic"


def obfuscate(text, key=OBFUSCATION_KEY):
    raw = bytes(
        ch ^ ord(key[i % len(key)]) for i, ch in enumerate(text.encode("utf-8"))
    )
    return {"b64": base64.b64encode(raw).decode("ascii"), "key": key}


def solution_string(pz):
    """The filled grid, row-major, with '#' for blocks."""
    cells = [
        ["#" if pz.pattern[r][c] == puzzle_mod.BLOCK else " " for c in range(pz.width)]
        for r in range(pz.height)
    ]
    for entry in pz.doc["entries"]:
        slot = pz.entry_slot(entry)
        if slot is None:
            continue
        for (r, c), letter in zip(slot.squares(), puzzle_mod.grid_fill(entry)):
            cells[r][c] = letter
    return "".join("".join(row) for row in cells)


def puzzle_id(doc):
    meta = doc["meta"]
    slug = "".join(
        ch.lower() if ch.isalnum() else "-" for ch in meta["title"]
    ).strip("-")
    return f"{meta.get('date', 'undated')}-{slug}"


def build_payload(pz):
    doc = pz.doc
    entries = []
    for entry in sorted(doc["entries"], key=lambda e: (e["direction"], e["number"])):
        clue = entry.get("clue")
        entries.append({
            "n": entry["number"],
            "dir": entry["direction"],
            "clue": clue["text"] if clue else "(clue missing)",
            "enumeration": entry.get("enumeration", str(len(entry["answer"]))),
        })
    meta = {
        k: v for k, v in doc["meta"].items()
        if k in ("title", "setter", "date", "difficulty", "instructions")
    }
    return {
        "id": puzzle_id(doc),
        "meta": meta,
        "pattern": pz.pattern,
        "entries": entries,
        "solution": obfuscate(solution_string(pz)),
    }


def render(payload, artifact_body=False):
    with open(TEMPLATE) as fh:
        html = fh.read()

    if artifact_body:
        start = html.index(START) + len(START)
        html = html[start:html.index(END)].strip()
        # An Artifact supplies its own document skeleton, but the title tag has
        # to travel with the body or the page has no name.
        title = payload["meta"].get("title", "Cryptic Crossword")
        html = f"<title>{title}</title>\n" + html

    marker = '<script id="puzzle-data" type="application/json">null</script>'
    if marker not in html:
        raise SystemExit("template is missing its puzzle-data placeholder")
    # </ inside the JSON would end the script element early.
    data = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
    return html.replace(
        marker,
        f'<script id="puzzle-data" type="application/json">{data}</script>',
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("puzzle")
    parser.add_argument("-o", "--out", required=True)
    parser.add_argument(
        "--artifact-body", action="store_true",
        help="emit only the page body, for publishing as an Artifact",
    )
    parser.add_argument(
        "--skip-validation", action="store_true",
        help="build even if the document does not validate (for debugging only)",
    )
    args = parser.parse_args()

    if not args.skip_validation:
        with open(SCHEMA_PATH) as fh:
            schema = json.load(fh)
        errors = validate_file(args.puzzle, schema)
        if errors:
            print(f"{args.puzzle} does not validate; refusing to build:", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
            return 1

    pz = puzzle_mod.load(args.puzzle)
    html = render(build_payload(pz), artifact_body=args.artifact_body)

    directory = os.path.dirname(os.path.abspath(args.out))
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(args.out, "w") as fh:
        fh.write(html)
    print(f"wrote {args.out} ({len(html):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
