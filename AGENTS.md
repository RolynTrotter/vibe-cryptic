# AGENTS.md

Guidance for allkens working in this repo. Read this before touching anything.

## What this project is

A pipeline that **writes** cryptic crosswords, and a UI that serves them. The
README holds the north star and the seven-stage pipeline; the open issues hold
the work. Read the README first — the stage numbers used throughout the code
and the tickets refer to it.

## House conventions

**Tradition: Harper's-style.** Grids follow US cryptic conventions — 180°
rotational symmetry, roughly half the letters checked, never two consecutive
unchecked letters in an entry, first and last letters of every entry checked.
Clues follow the Ximenean fairness rules in
`skills/cryptic-setter/references/` — definition at one end, wordplay that
yields the answer exactly, indicators that govern their fodder.

**No build step.** Pipeline code is Python 3 with no third-party dependencies.
The solver UI is a single dependency-free HTML file. A skill that needs
`npm install` before it runs is a skill that breaks in half the places it runs.

**The puzzle document is the contract.** Every stage reads and writes
`schema/puzzle.schema.json`. Don't invent side-channels between stages; if a
stage needs to tell a later stage something, it belongs in the document.

**Answers are not grid fills.** `answer` is what the clue yields; `grid_fill`
is what gets written in the squares. They differ in variety cryptics, which is
where this project is heading. Never assume they're the same — use the
accessor, not the field.

## Working rules

- `python3 scripts/validate.py fixtures/*.json` must pass before you commit.
  It checks grid conventions, crossing consistency, enumerations, and — where
  the mechanics allow it — whether the wordplay actually builds the answer.
- Fixtures in `fixtures/` are the calibration set. `*-good.json` must validate
  clean; `*-bad.json` must fail, with each defect labelled by what it is. If
  you make the validator stricter, the bad fixture is where you prove it.
- Never loosen a check to make a clue pass. If a clue fails the validator, the
  clue is wrong until proven otherwise.

## Reviewing clues

When you are asked to check a clue, you are checking three separate things and
they should not bleed into each other:

1. **Soundness** — does the wordplay build the answer, letter for letter?
2. **Fairness** — could a competent solver get there without insider knowledge?
3. **Quality** — does the surface read as natural English about something else?

A clue can be sound and unfair, or sound and fair and dull. Say which one is
failing.

## What not to do

- Don't mark your own homework. The review stages (5 and 6) run as subagents
  precisely so they don't see the reasoning that produced the clue. Preserve
  that separation.
- Don't add a dependency to make something 10% nicer.
- Don't commit generated puzzles to the repo unless they're fixtures.
