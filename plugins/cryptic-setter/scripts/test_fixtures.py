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

from validate import SCHEMA_PATH, validate_file

GOOD = os.path.join(ROOT, "fixtures", "first-light-good.json")
BAD = os.path.join(ROOT, "fixtures", "first-light-bad.json")

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
]


def main():
    with open(SCHEMA_PATH) as fh:
        schema = json.load(fh)
    failures = []

    good_errors = validate_file(GOOD, schema)
    if good_errors:
        failures.append(
            f"the good fixture should validate clean, but got {len(good_errors)} "
            f"error(s):\n    " + "\n    ".join(good_errors)
        )

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
    print(f"ok: good fixture clean; all {len(EXPECTED)} planted defects caught")
    print(f"    ({len(bad_errors)} errors reported on the bad fixture)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
