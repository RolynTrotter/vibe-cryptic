#!/usr/bin/env python3
"""Draw a grid that already obeys the conventions.

    python3 scripts/grid.py --size 11 -o grid.json
    python3 scripts/grid.py --style barred --size 5x7 -o grid.json

The conventions — 180-degree symmetry, nothing under three letters, no two
consecutive unchecked letters, checked letters at both ends of every entry —
are cheap for a program to satisfy and expensive for a person to satisfy by
eye. Drawing a pattern by hand and running the validator until it stops
complaining is the slowest way to reach a grid nobody will ever comment on.

So the geometry is generated from a lattice that satisfies the conventions by
construction, then handed to the same `check_grid` the validator runs. What
comes out is a puzzle document with a grid and no entries, which is what
fill.py wants.
"""

import argparse
import itertools
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import puzzle as puzzle_mod

MIN_ENTRY = 3

# How often a row or column gets broken into shorter entries. One break is
# nearly always right: it leaves a long entry and a short one, or two of middle
# length. Never breaking leaves a full-width answer, and breaking twice leaves
# nothing but three-letter ones — both legal, both duller to clue. These weights
# give an 11x11 roughly the length spread of the hand-set fixture.
SPLIT_WEIGHTS = {0: 0.05, 1: 0.85, 2: 0.10}


def parse_size(text):
    """'11' or '5x7', read as ROWSxCOLS."""
    parts = text.lower().split("x")
    try:
        numbers = [int(p) for p in parts]
    except ValueError:
        raise SystemExit(f"size {text!r} is not a number or ROWSxCOLS")
    if len(numbers) == 1:
        numbers *= 2
    if len(numbers) != 2:
        raise SystemExit(f"size {text!r} is not a number or ROWSxCOLS")
    height, width = numbers
    if height < 5 or width < 5:
        raise SystemExit("a grid smaller than 5x5 has no room for a cryptic")
    return height, width


def _segments_ok(length, cuts):
    """Do blocks at `cuts` leave every run at least MIN_ENTRY long?"""
    previous = -1
    for cut in sorted(cuts):
        if cut - previous - 1 < MIN_ENTRY:
            return False
        previous = cut
    return length - previous - 1 >= MIN_ENTRY


def _bars_ok(length, bars):
    """Do bars drawn after the indices in `bars` leave every run long enough?"""
    previous = -1
    for bar in sorted(bars):
        if bar - previous < MIN_ENTRY:
            return False
        previous = bar
    return length - 1 - previous >= MIN_ENTRY


def _choose(rng, options_by_size):
    """Pick a break set, weighted towards one break per row or column."""
    sizes = [k for k in sorted(options_by_size) if options_by_size[k]]
    weights = [SPLIT_WEIGHTS.get(k, 0.05) for k in sizes]
    size = rng.choices(sizes, weights=weights)[0]
    return rng.choice(options_by_size[size])


def _options(length, candidates, allowed, max_breaks=2):
    """Every legal break set, grouped by how many breaks it has."""
    grouped = {}
    for size in range(max_breaks + 1):
        grouped[size] = [
            combo for combo in itertools.combinations(candidates, size)
            if allowed(length, combo)
        ]
    return grouped


def blocked_grid(height, width, rng):
    """Block the odd/odd lattice, then break long entries symmetrically.

    The lattice alone — every square on an odd row and an odd column blocked —
    already satisfies every convention: entries run the full width or height,
    and their letters alternate checked and unchecked starting and ending
    checked. Breaking an entry means blocking one of its unchecked squares,
    which is why the extra blocks never disturb the crossings.
    """
    blocks = {(r, c) for r in range(height) for c in range(width)
              if r % 2 and c % 2}

    across_options = _options(width, [c for c in range(width) if c % 2],
                              _segments_ok)
    for row in range(0, height, 2):
        partner = height - 1 - row
        if partner <= row:
            continue  # a self-paired row can only stay whole and stay symmetric
        for col in _choose(rng, across_options):
            blocks.add((row, col))
            blocks.add((partner, width - 1 - col))

    down_options = _options(height, [r for r in range(height) if r % 2],
                            _segments_ok)
    for col in range(0, width, 2):
        partner = width - 1 - col
        if partner <= col:
            continue
        for row in _choose(rng, down_options):
            blocks.add((row, col))
            blocks.add((height - 1 - row, partner))

    return {
        "style": "blocked",
        "symmetry": "rotational-180",
        "pattern": [
            "".join("#" if (r, c) in blocks else "." for c in range(width))
            for r in range(height)
        ],
    }


def barred_grid(height, width, rng):
    """Bar every row and column into runs of at least three.

    With no run shorter than three in either direction, every square belongs to
    both an across and a down entry, so the grid is fully checked — the dense,
    heavily-crossed shape a barred puzzle is for. It is harder to fill than a
    blocked grid of the same size, which is why barred grids are smaller.
    """
    right = [set() for _ in range(height)]
    below = [set() for _ in range(width)]

    row_options = _options(width, list(range(width - 1)), _bars_ok)
    for row in range(height):
        partner = height - 1 - row
        if partner < row:
            continue
        if partner == row:
            # A row that is its own mirror can only take a self-mirroring set.
            choices = {
                size: [c for c in combos
                       if set(c) == {width - 2 - bar for bar in c}]
                for size, combos in row_options.items()
            }
            right[row] = set(_choose(rng, choices))
            continue
        bars = _choose(rng, row_options)
        right[row] = set(bars)
        right[partner] = {width - 2 - bar for bar in bars}

    col_options = _options(height, list(range(height - 1)), _bars_ok)
    for col in range(width):
        partner = width - 1 - col
        if partner < col:
            continue
        if partner == col:
            choices = {
                size: [r for r in combos
                       if set(r) == {height - 2 - bar for bar in r}]
                for size, combos in col_options.items()
            }
            below[col] = set(_choose(rng, choices))
            continue
        bars = _choose(rng, col_options)
        below[col] = set(bars)
        below[partner] = {height - 2 - bar for bar in bars}

    return {
        "style": "barred",
        "symmetry": "rotational-180",
        "bars": {
            "right": ["".join("|" if c in right[r] else "." for c in range(width))
                      for r in range(height)],
            "below": ["".join("-" if r in below[c] else "." for c in range(width))
                      for r in range(height)],
        },
    }


def document(grid, meta):
    return {"schema_version": "0.1", "meta": meta, "grid": grid, "entries": []}


def build(height, width, style, rng, meta, attempts=200):
    """Draw grids until one passes the validator's own grid checks."""
    draw = barred_grid if style == "barred" else blocked_grid
    last = None
    for _ in range(attempts):
        doc = document(draw(height, width, rng), meta)
        pz = puzzle_mod.Puzzle(doc=doc)
        if not puzzle_mod.grid_shape_errors(pz):
            pz.slots = puzzle_mod.enumerate_slots(pz)
            pz.checked = puzzle_mod.compute_checked(pz.slots)
        errors = puzzle_mod.check_grid(pz)
        if not errors:
            return pz, None
        last = errors
    return None, last


def render(pz):
    """The grid as the solver would see it, so nobody has to read the JSON."""
    lines = []
    if pz.style == "blocked":
        for r in range(pz.height):
            lines.append(" ".join("#" if not pz.is_light(r, c) else "."
                                  for c in range(pz.width)))
        return lines
    for r in range(pz.height):
        row = ""
        for c in range(pz.width):
            row += "." + ("|" if pz.bar_right(r, c) else " ")
        lines.append(row.rstrip())
        if r < pz.height - 1:
            lines.append("".join("- " if pz.bar_below(r, c) else "  "
                                 for c in range(pz.width)).rstrip())
    return [line for line in lines if line]


def summarise(pz):
    lengths = sorted(slot.length for slot in pz.slots.values())
    spread = {}
    for length in lengths:
        spread[length] = spread.get(length, 0) + 1
    squares = sum(1 for r in range(pz.height) for c in range(pz.width)
                  if pz.is_light(r, c))
    return {
        "entries": len(pz.slots),
        "lengths": spread,
        "lights": squares,
        "checked": len(pz.checked),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", default="11", metavar="N|ROWSxCOLS",
                        help="11 for 11x11, or 5x7 for five rows of seven")
    parser.add_argument("--style", choices=["blocked", "barred"],
                        default="blocked")
    parser.add_argument("--title", default="Untitled")
    parser.add_argument("--setter", default="Anonymous")
    parser.add_argument("--date")
    parser.add_argument("--difficulty",
                        choices=["gentle", "standard", "tough", "fiendish"],
                        default="standard")
    parser.add_argument("--random-seed", type=int, default=None)
    parser.add_argument("-o", "--out")
    args = parser.parse_args()

    height, width = parse_size(args.size)
    if args.style == "blocked" and (height % 2 == 0 or width % 2 == 0):
        raise SystemExit(
            "a blocked cryptic grid needs odd dimensions, so that the block "
            f"lattice is symmetric — {height}x{width} cannot be. Try "
            f"{height | 1}x{width | 1}."
        )

    meta = {"title": args.title, "setter": args.setter,
            "difficulty": args.difficulty}
    if args.date:
        meta["date"] = args.date

    rng = random.Random(args.random_seed)
    pz, errors = build(height, width, args.style, rng, meta)
    if pz is None:
        print("could not draw a grid this size that satisfies the conventions;",
              file=sys.stderr)
        print("the last attempt failed on:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    stats = summarise(pz)
    print(f"{args.style} {height}x{width}: {stats['entries']} entries to clue, "
          f"{stats['checked']} of {stats['lights']} squares checked")
    print("  lengths: " + ", ".join(f"{n}x{count}" for n, count in
                                    sorted(stats["lengths"].items())))
    for line in render(pz):
        print("  " + line)

    if args.out:
        directory = os.path.dirname(os.path.abspath(args.out))
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(args.out, "w") as fh:
            json.dump(pz.doc, fh, indent=2)
            fh.write("\n")
        print(f"wrote {args.out}")
        print(f"next: python3 {os.path.join('$ROOT', 'scripts', 'fill.py')} "
              f"{args.out} -o filled.json")
    else:
        json.dump(pz.doc, sys.stdout, indent=2)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
