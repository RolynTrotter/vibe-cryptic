---
name: cryptic-setter
description: Write (set) a cryptic crossword and publish it as a solvable page at a link. Use when someone asks for a cryptic crossword to be made, set, written, or generated, wants clues written for given answers, wants a crossword grid filled, or wants an existing puzzle document validated, checked for soundness, or turned into a playable page. Not for solving an existing crossword.
---

# Setting a cryptic crossword

Setting is not solving in reverse. A solver gets one clue and searches for one
answer; a setter starts with a grid full of mutual constraints and must invent,
for every entry, a clue that is fair, mechanically sound, smooth to read, and
original — all at once.

The geometry and the fill are solved problems here, one command each. The clues
are the work. Go straight to them: run the commands in order, and let the
validator, not your own confidence, decide when a clue is correct.

## Before the first command

`$ROOT` is the root of this skill — `${CLAUDE_PLUGIN_ROOT}` in a plugin
install, or the directory holding this file in a chat install, which keeps
`scripts/`, `schema/`, `ui/`, `references/` and `fixtures/` beside it. Set it
once, and check that `$ROOT/scripts/validate.py` exists.

**The scripts are run, not read.** Every one of them prints what it did or
names what is wrong, with the rule that was broken and usually the fix. The
validator's errors are the contract: they are what "correct" means here, and
they arrive in one second. Reading a checker to predict what it will say is the
slowest possible way to learn it. Nothing under `scripts/` needs opening, ever.

## 1. Draw a grid

Ask only what you cannot sensibly default. Defaults: 11x11, standard
difficulty, no theme, today's date.

```bash
python3 $ROOT/scripts/grid.py --size 11 --title "First Light" --setter "Alex" -o grid.json
```

It prints the shape, the clue count you are signing up for, and the pattern,
then writes a grid that already satisfies every convention — 180-degree
symmetry, nothing under three letters, no two consecutive unchecked letters,
checked letters at both ends of every entry. **Do not draw a pattern by hand or
edit the one it gives you.** Those conventions are cheap for the generator to
satisfy and slow for anyone else; hand-drawn patterns fail the validator on the
same four rules every time.

- Size sets the workload: 11x11 is about 24 clues, 13x13 about 28, 15x15 about
  34. Blocked grids need odd dimensions.
- `--style barred --size 5x7` gives the Harper's barred style: no black
  squares, bars between entries, every letter checked. Fully checked grids are
  much harder to fill, so keep them small — 5x7 or 7x7.
- `--random-seed N` if you want the same grid twice, or a different one. The
  printed length spread is worth a glance: a grid of mostly full-width entries
  is legal but a slog to clue, and redrawing costs a second.

## 2. Fill it

```bash
python3 $ROOT/scripts/fill.py grid.json -o filled.json
python3 $ROOT/scripts/fill.py grid.json --seed ROMANCE --seed GARLAND -o filled.json
```

Any entries already in the document are kept and the rest are filled around
them; `--seed WORD` places a word in the first slot that can still take it,
which is how a theme gets into the grid. A 15x15 fills in under a second.
Filling by hand is slow and produces grids whose crossings almost agree.

The word list is banded, and the search tries the whole **common** band before
allowing anything from **extended**. The report says which it needed:

```
filled 24 entries (common only): 24 common, 0 extended, 25 nodes
```

A fill that reached into the extended band is not wrong, but it is a warning:
those words are real and obscure, and you will be cluing them shortly. If a
grid keeps needing them, the pattern is too constrained — redraw it with a new
`--random-seed`, or go a size larger, rather than fighting the clues later.

If the search reports no fill, the grid and the word list cannot satisfy each
other. Redraw the grid or drop a seed. To rework one corner instead, drop those
entries and refill around what remains:

```bash
python3 $ROOT/scripts/fill.py filled.json --drop 5A --drop 3D -o reworked.json
```

## 3. Write the clues

`filled.json` is already the puzzle document — meta, grid, and one entry per
slot carrying its answer. All you add is a `clue` to each entry; nothing else in
the file needs touching. Save the result as `puzzle.json`, which is what the
last two steps read.

One complete entry, which is the whole shape you need:

```json
{
  "number": 7, "direction": "across", "row": 2, "col": 0,
  "answer": "TRAILED", "enumeration": "7",
  "clue": {
    "text": "Model who protested followed",
    "definition": { "text": "followed", "position": "trailing" },
    "wordplay": {
      "devices": ["charade"],
      "derivation": "T (Model T) + RAILED (protested) = TRAILED.",
      "indicators": [],
      "checks": [
        { "kind": "abbreviation", "source": "Model", "yields": "T" },
        { "kind": "literal", "source": "protested", "yields": "RAILED" },
        { "kind": "concatenation", "parts": ["T", "RAILED"], "yields": "TRAILED" }
      ]
    }
  }
}
```

Work backward for each entry: **answer -> definition -> wordplay -> surface.**
Enumerate the mechanics *first* and apply taste *second*. Sound options judged
by taste beats taste inventing options and hoping they are sound.

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

`checks` are the machine-verifiable assertions, and they are what catches you
being wrong. Each states what it `yields`, plus:

| kind | also needs | what the validator does with it |
|---|---|---|
| `anagram` | `fodder` | matches the letters, and refuses fodder already in order |
| `hidden` | `source` | finds the answer inside it, and finds it in the clue |
| `reversal` | `source` | reverses it |
| `concatenation` | `parts` (2+, in grid order) | joins them |
| `deletion` | `source`, `remove` | removes each occurrence and looks for the answer |
| `letter_selection` | `source`, `rule` | `initials`, `finals`, `alternates-odd`, `alternates-even`, `centres` |
| `abbreviation` | `source` — the phrase in the clue | checks the abbreviation table |
| `literal` | `source` | nothing: a synonym step, recorded so the derivation is complete |

One check must yield the answer itself, or the wordplay has stopped short.
A container is a `concatenation` whose middle part is the contents.

`answer` is what the clue yields; `grid_fill` is what goes in the squares. They
differ only in a variety cryptic, where the solver modifies the answer before
writing it in — and there `meta.instructions` must tell the solver the gimmick,
or the puzzle is unsolvable. The validator enforces that much.

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

**Looking a word up.** Which device a word signals, and what a word abbreviates
to, are one-line questions:

```bash
python3 $ROOT/scripts/lookup.py drunk          # -> anagram indicator
python3 $ROOT/scripts/lookup.py king           # -> K, R, ER
python3 $ROOT/scripts/lookup.py --device deletion   # the whole list for one device
```

`references/indicators.json` and `references/abbreviations.json` are inputs to
the validator. Ask them one word at a time; never read them through.

## 4. Validate until clean

```bash
python3 $ROOT/scripts/validate.py puzzle.json
```

This checks grid conventions, that entries fit their slots and agree at every
crossing, that enumerations match, that definitions appear where they claim to,
that indicators signal the device they are declared for, that abbreviations are
standard, and that the wordplay arithmetic actually works. Fix what it names
and run it again; the errors say which rule broke and, for an indicator or an
abbreviation, what the word does mean.

Between the fill and the clues, `--allow-unclued` accepts entries with no clue
yet. That is the only place for it.

Semantic steps — "Team" giving SIDE, "nipper" giving BITER — are declared as
`literal` and go unverified. Treat those as the weak point of any clue you
write, because nothing else will catch them yet.

**Never loosen a check to make a clue pass.** A failing clue is wrong until
proven otherwise; fix the clue, or drop that entry and refill the corner. If
you genuinely believe the checker is wrong, add the case to
`$ROOT/fixtures/first-light-bad.json` and prove it.

## 5. Review the clues independently

Soundness is not quality. Before publishing, review each clue cold — ideally in
a fresh subagent that has not seen the reasoning that produced it, because a
setter marking their own homework is the most reliable way to ship a bad puzzle.
Judge three things separately and say which is failing:

1. **Soundness** — does the wordplay build the answer, letter for letter?
2. **Fairness** — could a competent solver get there without insider knowledge?
3. **Quality** — does the surface read as natural English about something else?

Also check the puzzle as a whole: device variety, difficulty spread, and no
indicator or trick used twice.

## 6. Publish

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

## Opening a reference

Four files answer questions the steps above do not. Open one when you have the
question, not before — and open the part that answers it.

| The question | Where |
|---|---|
| How does this device work, and how does it go wrong? | `$ROOT/references/devices.md` |
| Is this surface good enough? Is this clue fair? | `$ROOT/references/fairness.md` |
| What may a field hold, exactly? | `$ROOT/schema/puzzle.schema.json` |
| What does a finished puzzle look like whole? | `$ROOT/fixtures/first-light-good.json` |

For a single word — which device it indicates, what it abbreviates to — use
`lookup.py` above rather than any of these.

## What is not automated yet

Grid geometry and fill are done for you; clue writing is yours, with the
validator as the backstop. Generated clue candidates, the independent checker
subagents, and automatic rework of failed corners are tracked as open issues on
https://github.com/RolynTrotter/vibe-cryptic. Until those land, the discipline
in steps 4 and 5 is what keeps the puzzles honest.
