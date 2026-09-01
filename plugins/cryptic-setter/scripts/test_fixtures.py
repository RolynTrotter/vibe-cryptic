#!/usr/bin/env python3
"""Calibration tests: the good fixture must pass, the bad one must fail precisely.

A checker that flags everything is as useless as one that flags nothing, so both
directions are asserted. Each expectation below names the defect planted in
fixtures/first-light-bad.json by the number in that file's meta.notes.

    python3 scripts/test_fixtures.py
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import clues
import fill as fill_mod
import puzzle as puzzle_mod
import wordlist as wordlist_mod
from validate import SCHEMA_PATH, validate_file

GOOD = os.path.join(ROOT, "fixtures", "first-light-good.json")
BAD = os.path.join(ROOT, "fixtures", "first-light-bad.json")
BARRED = os.path.join(ROOT, "fixtures", "behind-bars-good.json")

# (defect number, entry label, a distinctive fragment of the expected message)
EXPECTED = [
    (1, "3A", "does not rearrange to ACROBAT"),
    (2, "12A", "definition 'Garment' does not appear"),
    (3, "13A", "is not hidden in"),
    (4, "7A", "no check yields TRAILED"),
    (5, "9A", "indicator 'shuffled' does not appear"),
    (6, "16A", "enumeration"),
    (7, "1D", "marked leading but the clue does not start with it"),
    (8, "15A", "deleting E from LEAD gives LAD"),
    (9, "4D", "gives RBD, not ROD"),
    (10, "14D", "no checks are given"),
    (11, "8A", "slot holds 3"),
    (12, "5D", "abbreviates to O, NIL, LOVE, not Z"),
    (13, "16D", "does not suggest reversal, but it does suggest anagram"),
]


def barred_doc(bars_right, bars_below, size=5, symmetry="none"):
    """A minimal barred grid, for exercising the geometry checks directly."""
    rows = [
        "".join("|" if (r, c) in bars_right else "." for c in range(size))
        for r in range(size)
    ]
    cols = [
        "".join("-" if (r, c) in bars_below else "." for c in range(size))
        for r in range(size)
    ]
    return {
        "schema_version": "0.1",
        "meta": {"title": "grid check", "setter": "test"},
        "grid": {"style": "barred", "symmetry": symmetry,
                 "bars": {"right": rows, "below": cols}},
        "entries": [],
    }


# Geometry defects a barred grid can have, and the message each must produce.
# These are checked in memory rather than as fixture files because they are
# about the grid alone, with no entries or clues involved.
BARRED_CASES = [
    ("a bar with no symmetric partner",
     barred_doc({(0, 1)}, set(), symmetry="rotational-180"),
     "symmetric partner"),
    ("a square walled off from every entry",
     barred_doc({(0, 0)}, {(0, 0)}),
     "belongs to no entry"),
    ("an entry below the minimum length",
     barred_doc({(0, 1)}, set()),
     "letters (minimum 3)"),
    ("an entry starting on an unchecked square",
     barred_doc(set(), {(0, 0)}),
     "unchecked first letter"),
]


def check_barred_geometry():
    failures = []
    for label, doc, fragment in BARRED_CASES:
        pz = puzzle_mod.Puzzle(doc=doc)
        if not puzzle_mod.grid_shape_errors(pz):
            pz.slots = puzzle_mod.enumerate_slots(pz)
            pz.checked = puzzle_mod.compute_checked(pz.slots)
        errors = puzzle_mod.check_grid(pz)
        if not any(fragment in e for e in errors):
            failures.append(
                f"barred grid check missed {label}: no error containing "
                f"{fragment!r} (got {errors})"
            )
    return failures


def check_references_cover_the_schema():
    """Every device the schema allows must have an indicator list.

    Without this, adding a device to the schema and forgetting the table would
    make the indicator check pass vacuously for it — the worst kind of failure,
    since it looks like success.
    """
    with open(SCHEMA_PATH) as fh:
        schema = json.load(fh)
    devices = set(
        schema["$defs"]["clue"]["properties"]["wordplay"]["properties"]
        ["devices"]["items"]["enum"]
    )
    missing = sorted(devices - set(clues.INDICATORS))
    if missing:
        return [f"references/indicators.json has no entry for: {', '.join(missing)}"]
    return []


def check_wordlist():
    """The list has to be usable, banded, and free of what must never appear."""
    failures = []
    words = wordlist_mod.WordList()
    stats = words.stats()
    if stats["by_band"]["common"] < 20000 or stats["by_band"]["extended"] < 100000:
        failures.append(f"word list looks truncated: {stats}")

    # Band membership is the whole point: common words a setter can clue,
    # extended ones only when the grid leaves no choice.
    for word, expected in [("ROMANCE", wordlist_mod.COMMON),
                           ("BASSOON", wordlist_mod.COMMON),
                           ("IMMIX", wordlist_mod.EXTENDED),
                           ("OUTLAIN", wordlist_mod.EXTENDED)]:
        if words.band(word) != expected:
            failures.append(
                f"{word} is in band {words.band(word)}, expected {expected}")

    # The exclusion list is not decorative.
    for word in ["SHIT", "SLUT", "WHORE", "NIGGER", "RETARD", "CHICKENSHIT"]:
        if words.contains(word):
            failures.append(f"excluded word {word} is still in the list")
    # ...and it must not have taken ordinary words with it.
    for word in ["ASSESS", "CLASS", "COCKTAIL", "TITANIC", "ATTITUDE"]:
        if not words.contains(word):
            failures.append(f"{word} was excluded as collateral damage")

    # A pattern query returns only words that actually match it.
    for candidate in words.candidates("M.T..EE"):
        if len(candidate) != 7 or candidate[0] != "M" or candidate[2] != "T":
            failures.append(f"{candidate} does not match M.T..EE")
    if "MATINEE" not in words.candidates("M.T..EE"):
        failures.append("MATINEE is missing from the M.T..EE candidates")
    return failures


def check_fill():
    """Filling a real grid from scratch must produce a consistent grid."""
    failures = []
    with open(BARRED) as fh:
        doc = json.load(fh)
    doc["entries"] = []
    pz = puzzle_mod.Puzzle(doc=doc)
    pz.slots = puzzle_mod.enumerate_slots(pz)
    pz.checked = puzzle_mod.compute_checked(pz.slots)

    words = wordlist_mod.WordList()
    result = fill_mod.solve(pz, words, seed=11, time_budget=25.0)
    if not result.ok:
        return [f"could not fill the barred fixture's grid: {result.reason}"]
    if len(result.entries) != len(pz.slots):
        failures.append(
            f"filled {len(result.entries)} of {len(pz.slots)} slots")
    if len(set(result.entries.values())) != len(result.entries):
        failures.append("the fill repeated a word")

    # The real test: every crossing has to agree, which check_entries decides.
    filled = fill_mod.document(pz, result.entries)
    check = puzzle_mod.Puzzle(doc=filled)
    check.slots = puzzle_mod.enumerate_slots(check)
    check.checked = puzzle_mod.compute_checked(check.slots)
    failures += [f"filled grid: {e}" for e in puzzle_mod.check_entries(check)]
    for word in result.entries.values():
        if not words.contains(word):
            failures.append(f"the fill used {word}, which is not in the list")
    return failures


def main():
    with open(SCHEMA_PATH) as fh:
        schema = json.load(fh)
    failures = []

    for path, label in ((GOOD, "blocked"), (BARRED, "barred")):
        errors = validate_file(path, schema)
        if errors:
            failures.append(
                f"the {label} fixture should validate clean, but got "
                f"{len(errors)} error(s):\n    " + "\n    ".join(errors)
            )

    failures += check_barred_geometry()
    failures += check_references_cover_the_schema()
    failures += check_wordlist()
    failures += check_fill()

    bad_errors = validate_file(BAD, schema)
    if not bad_errors:
        failures.append("the bad fixture validated clean, so nothing is being checked")

    joined = "\n".join(bad_errors)
    for number, label, fragment in EXPECTED:
        if not any(line.startswith(f"{label}:") and fragment in line for line in bad_errors):
            failures.append(
                f"defect {number} ({label}) was not caught: no error matching "
                f"{fragment!r}"
            )

    # Anything flagged beyond the planted defects means the checks have drifted.
    unexplained = [
        line for line in bad_errors
        if not any(line.startswith(f"{label}:") for _, label, _ in EXPECTED)
    ]
    if unexplained:
        failures.append(
            "unexpected errors on the bad fixture (planted defects only, please):\n    "
            + "\n    ".join(unexplained)
        )

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(f"ok: both good fixtures clean; all {len(EXPECTED)} planted clue "
          f"defects caught")
    print(f"    ({len(bad_errors)} errors reported on the bad fixture; "
          f"{len(BARRED_CASES)} barred grid defects caught)")
    print("    word list banded and filtered; a grid fills from scratch and "
          "every crossing agrees")
    return 0


if __name__ == "__main__":
    sys.exit(main())
