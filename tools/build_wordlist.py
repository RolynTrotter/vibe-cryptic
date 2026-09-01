#!/usr/bin/env python3
"""Rebuild the banded word list from its public-domain sources.

Run by hand when the sources change; the output is committed, because CI has no
network and the skill must work from a checkout.

    python3 tools/build_wordlist.py

The bands answer the question the fill actually asks — not "is this a word" but
"can I write a fair clue for it".

  common    words a solver meets often, and a setter can clue without apology.
  extended  real words that earn their place only when the grid demands them.

A word being in the dictionary and a word being cluable are different tests, and
only the second one matters here.
"""

import argparse
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(REPO, "plugins", "cryptic-setter", "data")

# Both sources are public domain, which is why they are these two and not the
# better-known frequency lists: the Google 10000 list is derived from an LDC
# corpus its distributor says not to use commercially without a licence.
SOURCES = {
    "extended": (
        "https://raw.githubusercontent.com/dolph/dictionary/master/enable1.txt",
        "ENABLE (Enhanced North American Benchmark LExicon), released to the "
        "public domain by Alan Beale.",
    ),
    "common": (
        "https://raw.githubusercontent.com/dolph/dictionary/master/popular.txt",
        "The popular-words subset distributed alongside ENABLE.",
    ),
}

MIN_LENGTH, MAX_LENGTH = 3, 15


def fetch(url):
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read().decode("utf-8", "ignore")


def words(text):
    out = set()
    for line in text.splitlines():
        word = line.strip().lower()
        if word.isalpha() and MIN_LENGTH <= len(word) <= MAX_LENGTH:
            out.add(word)
    return out


def exclusions(path):
    """Exact words and stems the fill must never use. See the file's header."""
    exact, stems = set(), []
    if not os.path.exists(path):
        return exact, stems
    with open(path) as fh:
        for line in fh:
            entry = line.strip().lower()
            if not entry or entry.startswith("#"):
                continue
            if entry.startswith("*") and entry.endswith("*"):
                stems.append(entry.strip("*"))
            else:
                exact.add(entry)
    return exact, stems


def allowed(word, exact, stems):
    return word not in exact and not any(stem in word for stem in stems)


def write(path, band, entries, provenance):
    with open(path, "w") as fh:
        fh.write(f"# vibe-cryptic word list — band: {band}\n#\n")
        for line in provenance:
            fh.write(f"# {line}\n")
        fh.write(f"#\n# {len(entries):,} entries, {MIN_LENGTH}-{MAX_LENGTH} letters, "
                 "lower case, one per line.\n")
        fh.write("# Rebuild with tools/build_wordlist.py.\n")
        for word in sorted(entries):
            fh.write(word + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=DATA)
    args = parser.parse_args()

    common_text = fetch(SOURCES["common"][0])
    extended_text = fetch(SOURCES["extended"][0])
    common, extended = words(common_text), words(extended_text)

    exact, stems = exclusions(os.path.join(args.out, "words-excluded.txt"))
    before = len(common) + len(extended)
    common = {w for w in common if allowed(w, exact, stems)}
    extended = {w for w in extended if allowed(w, exact, stems)}
    print(f"excluded {before - len(common) - len(extended)} words "
          f"({len(exact)} exact, {len(stems)} stems)")

    stray = common - extended
    if stray:
        print(f"note: {len(stray)} common words are not in the extended list; "
              "keeping them", file=sys.stderr)
    band_common = common
    band_extended = extended - common

    os.makedirs(args.out, exist_ok=True)
    write(os.path.join(args.out, "words-common.txt"), "common", band_common,
          [SOURCES["common"][1],
           "Public domain. Words a setter can clue without apology."])
    write(os.path.join(args.out, "words-extended.txt"), "extended", band_extended,
          [SOURCES["extended"][1],
           "Public domain. Real words for when the grid leaves no choice;",
           "prefer the common band and reach here only under constraint."])
    print(f"common   {len(band_common):,}")
    print(f"extended {len(band_extended):,}")


if __name__ == "__main__":
    main()
