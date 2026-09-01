---
name: cryptic-setter
description: Write (set) a cryptic crossword and publish it as a solvable page at a link. Use when someone asks for a cryptic crossword to be made, set, written, or generated, wants clues written for given answers, wants a crossword grid filled, or wants an existing puzzle document validated, checked for soundness, or turned into a playable page. Not for solving an existing crossword.
---

# Setting a cryptic crossword

Setting is not solving in reverse. A solver gets one clue and searches for one
answer; a setter starts with a grid full of mutual constraints and must invent,
for every entry, a clue that is fair, mechanically sound, smooth to read, and
original — all at once. Work through the stages below in order and let the
validator, not your own confidence, decide when a clue is correct.

All commands below use `$ROOT` for the root of this skill. Installed as part of
the `cryptic-setter` plugin, that is `${CLAUDE_PLUGIN_ROOT}`; installed on its
own from the release bundle, it is the directory holding this file, which keeps
`scripts/`, `schema/`, `ui/` and `fixtures/` beside it. Set it once before
running anything, and check that `$ROOT/scripts/validate.py` exists.

## 1. Settle the shape

Ask only what you cannot sensibly default. Defaults: 11x11, standard difficulty,
no theme, today's date. Then pick a grid.

Two validated grids ship with the skill and can be reused outright:
`$ROOT/fixtures/behind-bars-good.json` (barred, 5x7) and
`$ROOT/fixtures/first-light-good.json` (blocked, 11x11).

Pick a style with `grid.style`. **Barred** — what Harper's publishes — has no
black squares; entries are separated by bars on cell edges, written as two
full-size arrays where `|` marks a bar on a cell's right edge and `-` a bar
beneath it:

```json
"grid": { "style": "barred", "bars": {
    "right": ["..|....", "...|...", ".......", "..|....", "...|..."],
    "below": [".-.....", ".......", ".......", ".....-.", "......."] } }
```

**Blocked** separates entries with black squares, written as a pattern of `#`
and `.`. Barred grids are more heavily checked, so they are harder to fill and
give the solver more help.

The same conventions govern both, since they concern unchecked letters rather
than blocks:

- 180-degree rotational symmetry of whatever separates the entries.
- Every entry at least 3 letters, and every square belonging to some entry.
- **Never two consecutive unchecked letters** in an entry.
- The first and last letter of every entry is checked.

In a barred grid a square goes unchecked when a bar cuts its run in one
direction down to a single letter — that square then belongs only to the entry
running the other way. It is the same fairness question as a blocked grid's
unches, so the same rules apply.

The lattice that satisfies these cheaply (blocked style): block every
odd-row/odd-column square,
then break long entries by blocking (even row, odd column) squares to split an
across, and (odd row, even column) squares to split a down. Keep the block set
symmetric. The validator checks all of this, so draft a pattern and run it.

## 2. Fill the grid

Use the search. Filling by hand is slow and produces grids whose crossings
almost agree.

```bash
python3 $ROOT/scripts/fill.py grid.json -o filled.json
python3 $ROOT/scripts/fill.py grid.json --seed ROMANCE --seed GARLAND -o filled.json
```

The input is a puzzle document with a grid; any entries it already carries are
kept and the rest are filled around them. `--seed WORD` places a word in the
first slot of the right length that can still take it, which is how a theme
gets into the grid. A 15x15 fills in under a second.

The word list is banded, and the search tries the whole **common** band before
allowing anything from **extended**. The report says which it needed:

```
filled 32 entries (common only): 32 common, 0 extended, 43 nodes
```

A fill that reached into the extended band is not wrong, but it is a warning:
those words are real and obscure, and you will be cluing them shortly. If a
grid keeps needing them, the pattern is too constrained — change it rather than
fighting the clues later.

If the search reports no fill, the grid and the word list cannot satisfy each
other. Change the block or bar pattern, or drop a seed; do not lower the band
floor to force it through.

To rework a corner, drop the entries and refill around what remains:

```bash
python3 $ROOT/scripts/fill.py filled.json --drop 5A --drop 3D -o reworked.json
```

Check the result before cluing it:

```bash
python3 $ROOT/scripts/validate.py --allow-unclued filled.json
```

`--allow-unclued` is right here and nowhere else: a filled grid has no clues
yet, and that is a stage rather than a fault.

## 3. Write the clues

For each entry, work backward: **answer -> definition -> wordplay -> surface.**

Enumerate the mechanics *first* and apply taste *second*. Sound options judged
by taste beats taste inventing options and hoping they are sound.

Two references carry the detail, and the checking stages cite the same ones, so
a disagreement between writing and checking can be settled by pointing at a
section rather than argued:

- `$ROOT/references/devices.md` — each device's mechanics, what makes it sound,
  and how it usually goes wrong.
- `$ROOT/references/fairness.md` — the fairness rules, and worked examples of
  the same answer clued badly and well.

Two more are read by the validator, not just by you:

- `$ROOT/references/indicators.json` — which words signal which device. An
  indicator declared for a device whose list does not contain it is an error,
  and the error names the device the word *does* suggest.
- `$ROOT/references/abbreviations.json` — the abbreviations a setter may fairly
  use. Use the `abbreviation` check kind for these and they get verified; an
  invented abbreviation is rejected.

Devices, with what each needs:

| Device | Mechanic | Needs |
|---|---|---|
| anagram | fodder rearranged into the answer | fodder present in the clue, plus an indicator |
| charade | parts joined in order | each part separately clued |
| container | one part inside another | an insertion or surrounding indicator |
| hidden | answer spans consecutive words | a concealment indicator |
| reversal | letters run backwards | a reversal indicator; in a down clue it may mean upwards |
| deletion | letters removed from a longer word | an indicator naming what goes |
| letter_selection | initials, finals, alternates | an indicator naming the rule |
| homophone | sounds like the answer | a "we hear" indicator |
| double_definition | two definitions, no wordplay | nothing else — but both must genuinely define |
| and_lit | whole clue is both definition and wordplay | rare; worth the effort when it lands |

Fairness rules that are not negotiable:

- The definition sits at one end of the clue, never buried mid-clue (an &lit is
  the sole exception, where the whole clue is both).
- The wordplay yields the answer **exactly** — every letter accounted for, none
  spare, none borrowed.
- Indicators must be positioned so they actually govern their fodder.
- Anagram fodder appears literally in the clue; a hidden word hides in words the
  solver can actually see.
- Abbreviations must be standard and defensible, not invented. Declare them
  with the `abbreviation` check kind so the table verifies them.
- Every word must do a job: definition, wordplay, indicator, or link. A word
  doing none of those is padding, which is a fairness fault, not a style one.

Then make the surface read as natural English about something else entirely.
"Craig rolled a smoke" is a clue; "Anagram of CRAIG gives a smoke" is a
confession. Vary the devices across the grid — a puzzle that is two-thirds
anagrams fails even when every clue is individually sound.

## 4. Record it as a puzzle document

Write a JSON document conforming to `$ROOT/schema/puzzle.schema.json`. Copy the
shape from `$ROOT/fixtures/first-light-good.json`.

Two things setters get wrong here:

- `answer` is what the clue yields; `grid_fill` is what goes in the squares.
  They differ only in a variety cryptic, where the solver modifies the answer
  before entering it. If any entry is modified, `meta.instructions` must tell
  the solver the gimmick, or the puzzle is unsolvable.
- `clue.wordplay.checks` are machine-verifiable assertions — the anagram's
  fodder, the hidden word's source, the charade's parts. Fill them in. They are
  what lets the next step catch you being wrong.

## 5. Validate until clean

```bash
python3 $ROOT/scripts/validate.py puzzle.json
```

This checks grid conventions, that entries fit their slots and agree at every
crossing, that enumerations match, that definitions appear where they claim to,
that indicators signal the device they are declared for, that abbreviations are
standard, and that the wordplay arithmetic actually works.

Semantic steps — "Team" giving SIDE, "nipper" giving BITER — are still declared
as `literal` and go unverified. Treat those as the weak point of any clue you
write, because nothing else will catch them yet.

**Never loosen a check to make a clue pass.** A failing clue is wrong until
proven otherwise; fix the clue, or discard the entry and refill that corner. If
you genuinely believe the checker is wrong, add the case to
`$ROOT/fixtures/first-light-bad.json` and prove it.

## 6. Review the clues independently

Soundness is not quality. Before publishing, review each clue cold — ideally in
a fresh subagent that has not seen the reasoning that produced it, because a
setter marking their own homework is the most reliable way to ship a bad puzzle.
Judge three things separately and say which is failing:

1. **Soundness** — does the wordplay build the answer, letter for letter?
2. **Fairness** — could a competent solver get there without insider knowledge?
3. **Quality** — does the surface read as natural English about something else?

Also check the puzzle as a whole: device variety, difficulty spread, and no
indicator or trick used twice.

## 7. Publish

```bash
python3 $ROOT/scripts/build_ui.py puzzle.json --artifact-body -o /tmp/puzzle-body.html
```

Then publish that file with the Artifact tool and give the solver the URL. The
build refuses to run on a document that does not validate, which is deliberate.

Without an Artifact tool that takes a file, build the standalone page instead —
it opens from disk with no server and no network — and hand the solver the file
itself, or paste its body into whatever HTML surface you do have:

```bash
python3 $ROOT/scripts/build_ui.py puzzle.json -o puzzle.html
```

## What is not automated yet

Grid filling and clue writing are done by you, with the validator as the
backstop. Automatic fill, generated clue candidates, the independent checker
subagents, and local rework of failed corners are tracked as open issues on
https://github.com/RolynTrotter/vibe-cryptic. Until those land, the discipline
in steps 5 and 6 is what keeps the puzzles honest.
