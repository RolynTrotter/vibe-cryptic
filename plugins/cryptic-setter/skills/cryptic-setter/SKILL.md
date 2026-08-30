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

All commands assume `$ROOT` is `${CLAUDE_PLUGIN_ROOT}`.

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

Entries only cross on checked squares, so the fill is far freer than it looks: a
7-letter entry in this lattice is pinned at just four positions, and the letters
between them are yours to choose.

Work the checked squares as their own small lattice. Choose the long entries
first, since they carry the most constraints, then fill the short ones around
them. Prefer words you can imagine cluing — a word that is merely in the
dictionary but has no definition and no decomposition is a trap you set for
yourself three steps later.

## 3. Write the clues

For each entry, work backward: **answer -> definition -> wordplay -> surface.**

Enumerate the mechanics *first* and apply taste *second*. Sound options judged
by taste beats taste inventing options and hoping they are sound.

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
- Abbreviations must be standard and defensible, not invented.

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
and that the wordplay arithmetic actually works.

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

For a page to open from disk instead, drop `--artifact-body`:

```bash
python3 $ROOT/scripts/build_ui.py puzzle.json -o puzzle.html
```

## What is not automated yet

Grid filling and clue writing are done by you, with the validator as the
backstop. Automatic fill, generated clue candidates, the independent checker
subagents, and local rework of failed corners are tracked as open issues on
https://github.com/RolynTrotter/vibe-cryptic. Until those land, the discipline
in steps 5 and 6 is what keeps the puzzles honest.
