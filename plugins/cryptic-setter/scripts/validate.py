#!/usr/bin/env python3
"""Validate puzzle documents.

    python3 scripts/validate.py fixtures/*.json
    python3 scripts/validate.py --expect-fail fixtures/starter-bad.json

Runs three layers: the JSON Schema, the structural checks that compare entries
against the grid, and the mechanical clue checks. Exits non-zero if anything
fails, so it can sit in front of a commit.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import clues
import minischema
import puzzle as puzzle_mod

SCHEMA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "schema",
    "puzzle.schema.json",
)


def validate_file(path, schema):
    """Return a list of problems with the document at path."""
    try:
        with open(path) as fh:
            doc = json.load(fh)
    except json.JSONDecodeError as exc:
        return [f"not valid JSON: {exc}"]

    errors = minischema.validate(doc, schema)
    if errors:
        return errors  # the later layers assume a well-formed document

    pz = puzzle_mod.load(path)
    errors += puzzle_mod.check_grid(pz)
    errors += puzzle_mod.check_entries(pz)
    errors += puzzle_mod.check_variety_instructions(pz)
    for entry in doc["entries"]:
        errors += clues.check_clue(entry)
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+")
    parser.add_argument(
        "--expect-fail",
        action="store_true",
        help="invert the exit code: for the deliberately-bad fixtures, which "
             "prove the checks catch anything at all",
    )
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    with open(SCHEMA_PATH) as fh:
        schema = json.load(fh)

    any_failed = False
    for path in args.paths:
        errors = validate_file(path, schema)
        if errors:
            any_failed = True
            print(f"{path}: {len(errors)} problem(s)")
            for error in errors:
                print(f"  - {error}")
        elif not args.quiet:
            print(f"{path}: ok")

    if args.expect_fail:
        if not any_failed:
            print("expected failures, but everything validated clean", file=sys.stderr)
            return 1
        print("(failures above are expected for this fixture)")
        return 0
    return 1 if any_failed else 0


if __name__ == "__main__":
    sys.exit(main())
