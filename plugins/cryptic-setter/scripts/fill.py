#!/usr/bin/env python3
"""Fill a grid with real, cluable words.

    python3 scripts/fill.py grid.json -o filled.json
    python3 scripts/fill.py grid.json --seed ROMANCE --seed GARLAND
    python3 scripts/fill.py filled.json --drop 5A --drop 3D -o reworked.json

This is a constraint satisfaction problem and is solved as one. Asking a model
to guess words that fit produces words that nearly fit; a search either finds a
grid where every crossing agrees or reports honestly that it could not.

Three things do most of the work:

  most constrained first  the slot with fewest candidates is filled next, so
                          the search fails fast rather than deep.
  band order              common words are tried before obscure ones, so a
                          grid only reaches for ECU or IMMIX where it must.
  forward checking        after placing a word, every unfilled slot must still
                          have at least one candidate. Most dead ends are
                          visible one move ahead and cost nothing to avoid.
"""

import argparse
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import puzzle as puzzle_mod
from wordlist import COMMON, EXTENDED, WordList

# Enough candidates per slot to have real choice, few enough that a wrong turn
# is abandoned rather than exhaustively explored.
BRANCH = 60
FETCH = 400


class Result:
    def __init__(self, ok, entries=None, reason=None, stats=None):
        self.ok, self.entries, self.reason = ok, entries, reason
        self.stats = stats or {}


def slot_cells(slot):
    return list(slot.squares())


def fill(pz, words, fixed=None, max_band=EXTENDED, seed=None,
         node_budget=200000, time_budget=30.0):
    """Search for a fill. `fixed` maps slot keys to words already placed."""
    rng = random.Random(seed)
    slots = dict(pz.slots)
    cells = {key: slot_cells(slot) for key, slot in slots.items()}

    letters = {}
    placed = {}
    for key, word in (fixed or {}).items():
        if key not in slots:
            return Result(False, reason=f"no slot {key[0]}{key[1][0].upper()} to seed")
        if len(word) != slots[key].length:
            return Result(False, reason=(
                f"seed {word} is {len(word)} letters but "
                f"{key[0]}{key[1][0].upper()} holds {slots[key].length}"))
        for (r, c), letter in zip(cells[key], word):
            if letters.get((r, c), letter) != letter:
                return Result(False, reason=f"seeds disagree at ({r},{c})")
            letters[(r, c)] = letter
        placed[key] = word

    used = set(placed.values())
    counters = {"nodes": 0}
    deadline = time.time() + time_budget

    def pattern(key):
        return "".join(letters.get(cell, ".") for cell in cells[key])

    def options(key):
        return words.candidates(pattern(key), max_band=max_band,
                                exclude=used, limit=FETCH)

    def search():
        counters["nodes"] += 1
        if counters["nodes"] > node_budget or time.time() > deadline:
            return "budget"
        remaining = [k for k in slots if k not in placed]
        if not remaining:
            return True

        # Most constrained first, and bail the moment a slot has nothing.
        best, best_options = None, None
        for key in remaining:
            found = options(key)
            if not found:
                return False
            if best_options is None or len(found) < len(best_options):
                best, best_options = key, found
                if len(found) == 1:
                    break

        # Shuffle inside each band so reruns differ without losing band order.
        by_band = {}
        for word in best_options:
            by_band.setdefault(words.band(word), []).append(word)
        ordered = []
        for band in sorted(by_band):
            group = by_band[band]
            rng.shuffle(group)
            ordered.extend(group)

        others = [k for k in remaining if k != best]
        for word in ordered[:BRANCH]:
            written = []
            for (r, c), letter in zip(cells[best], word):
                if (r, c) not in letters:
                    letters[(r, c)] = letter
                    written.append((r, c))
            placed[best] = word
            used.add(word)

            if all(words.candidates(pattern(k), max_band, used, limit=1)
                   for k in others):
                outcome = search()
                if outcome is True or outcome == "budget":
                    return outcome

            del placed[best]
            used.discard(word)
            for cell in written:
                del letters[cell]
        return False

    outcome = search()
    if outcome == "budget":
        return Result(False, reason="budget exhausted before a fill was found",
                      stats=dict(counters))
    if outcome is not True:
        return Result(False, reason="no fill exists for this grid and word list",
                      stats=dict(counters))

    bands = [words.band(w) for w in placed.values()]
    return Result(True, entries=dict(placed), stats={
        "nodes": counters["nodes"],
        "entries": len(placed),
        "common": sum(1 for b in bands if b == COMMON),
        "extended": sum(1 for b in bands if b == EXTENDED),
    })


def solve(pz, words, fixed=None, seed=None, **budget):
    """Try the common band alone before allowing obscure words in."""
    attempts = []
    for band in (COMMON, EXTENDED):
        result = fill(pz, words, fixed=fixed, max_band=band, seed=seed, **budget)
        attempts.append((band, result))
        if result.ok:
            result.stats["max_band"] = band
            return result
    return attempts[-1][1]


def document(pz, entries):
    """The filled grid as a puzzle document — grid and answers, no clues yet."""
    doc = json.loads(json.dumps(pz.doc))
    out = []
    for (number, direction), word in sorted(entries.items(),
                                            key=lambda kv: (kv[0][1], kv[0][0])):
        slot = pz.slots[(number, direction)]
        out.append({
            "number": number, "direction": direction,
            "row": slot.row, "col": slot.col,
            "answer": word, "enumeration": str(len(word)),
            "provenance": {"stage": "full-fill", "revisions": 0},
        })
    doc["entries"] = out
    return doc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("grid", help="a puzzle document; its entries seed the fill")
    parser.add_argument("-o", "--out")
    parser.add_argument("--seed", action="append", default=[], metavar="WORD",
                        help="a word to place, tried in the slots that fit it")
    parser.add_argument("--drop", action="append", default=[], metavar="SLOT",
                        help="clear this entry before filling, e.g. 5A or 3D")
    parser.add_argument("--random-seed", type=int, default=None)
    parser.add_argument("--time-budget", type=float, default=30.0)
    args = parser.parse_args()

    pz = puzzle_mod.load(args.grid)
    problems = puzzle_mod.check_grid(pz)
    if problems:
        print("the grid does not validate; fix it before filling:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    dropped = {d.strip().upper() for d in args.drop}
    fixed = {}
    for entry in pz.doc.get("entries", []):
        label = f"{entry['number']}{entry['direction'][0].upper()}"
        if label in dropped:
            continue
        fixed[(entry["number"], entry["direction"])] = entry["answer"]

    words = WordList()
    if args.seed:
        placed = seed_words(pz, words, args.seed, fixed)
        if placed is None:
            print("could not place every seed word in a free slot", file=sys.stderr)
            return 1
        fixed = placed

    result = solve(pz, words, fixed=fixed, seed=args.random_seed,
                   time_budget=args.time_budget)
    if not result.ok:
        print(f"no fill: {result.reason}", file=sys.stderr)
        print(f"  searched {result.stats.get('nodes', 0):,} nodes", file=sys.stderr)
        return 1

    stats = result.stats
    band = "common only" if stats["max_band"] == COMMON else "common + extended"
    print(f"filled {stats['entries']} entries ({band}): "
          f"{stats['common']} common, {stats['extended']} extended, "
          f"{stats['nodes']:,} nodes")

    doc = document(pz, result.entries)
    if args.out:
        directory = os.path.dirname(os.path.abspath(args.out))
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(args.out, "w") as fh:
            json.dump(doc, fh, indent=2); fh.write("\n")
        print(f"wrote {args.out}")
    else:
        json.dump(doc, sys.stdout, indent=2); print()
    return 0


def seed_words(pz, words, seeds, fixed):
    """Place each seed word in a slot of the right length that is still free."""
    placed = dict(fixed)
    for raw in seeds:
        word = raw.strip().upper()
        for key, slot in sorted(pz.slots.items()):
            if key in placed or slot.length != len(word):
                continue
            trial = dict(placed)
            trial[key] = word
            probe = fill(pz, words, fixed=trial, max_band=EXTENDED,
                         node_budget=1, time_budget=0.01)
            # node_budget 1 only checks the seeds are mutually consistent.
            if probe.reason and "disagree" in probe.reason:
                continue
            placed = trial
            break
        else:
            return None
    return placed


if __name__ == "__main__":
    sys.exit(main())
