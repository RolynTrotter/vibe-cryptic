#!/usr/bin/env python3
"""Ask the tables one question at a time.

    python3 scripts/lookup.py drunk           # what device does this signal?
    python3 scripts/lookup.py king            # what does this abbreviate to?
    python3 scripts/lookup.py --device deletion   # indicators for one device

references/indicators.json and references/abbreviations.json exist so the
validator can check a clue. They are tables, not reading material: a setter
wants one word, and reading 16KB of table to find it is 16KB spent to learn
one line. This asks both tables about a word and prints what they say.
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import clues


def indicator_report(term):
    devices = sorted(d for d in clues.INDICATORS if clues.suggests(term, d))
    if devices:
        return [f"{term!r} is a recognised indicator for: {', '.join(devices)}"]
    return [f"{term!r} is not an indicator for any device. Declaring it as one "
            f"will be rejected; pick a word from --device <name>, or add it to "
            f"references/indicators.json if you can defend it."]


def abbreviation_report(term):
    lines = []
    forms = clues.ABBREVIATIONS.get(term.strip().lower())
    if forms:
        lines.append(f"{term!r} abbreviates to: {', '.join(forms)}")
    stands_for = clues.ABBREVIATION_OF.get(term.strip().upper())
    if stands_for:
        lines.append(f"{term.upper()} is the abbreviation for: "
                     f"{', '.join(sorted(stands_for))}")
    if not lines:
        lines.append(f"{term!r} has no entry in the abbreviation table, so an "
                     f"`abbreviation` check on it will be rejected.")
    return lines


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("term", nargs="?", help="a word from a clue")
    parser.add_argument("--device", help="list the indicators for one device")
    args = parser.parse_args()

    if args.device:
        entries = clues.INDICATORS.get(args.device)
        if entries is None:
            print(f"no device named {args.device!r}. The devices are: "
                  f"{', '.join(sorted(clues.INDICATORS))}", file=sys.stderr)
            return 1
        print(f"{args.device} indicators ({len(entries)}):")
        print("  " + ", ".join(entries))
        return 0

    if not args.term:
        parser.error("give a word to look up, or --device <name>")

    for line in indicator_report(args.term):
        print(line)
    for line in abbreviation_report(args.term):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
