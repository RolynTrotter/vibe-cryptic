# AGENTS.md

Guidance for allkens working in this repo. Read this before touching anything.

## What this project is

A pipeline that **writes** cryptic crosswords, and a UI that serves them. The
README holds the north star and the seven-stage pipeline; the open issues hold
the work. Read the README first — the stage numbers used throughout the code
and the tickets refer to it.

## House conventions

**Tradition: Harper's-style.** Two grid styles are supported, set by
`grid.style`. *Barred* grids — what Harper's publishes — have no black squares:
entries are separated by bars drawn on cell edges. *Blocked* grids separate them
with black squares. Barred is the Harper's default; blocked is a legitimate
style and the older fixture uses it.

The same checking conventions govern both, because they are about unchecked
letters rather than about blocks, and barred grids have unchecked letters too
(a bar can cut a run down to a single square). The validator enforces: 180°
rotational symmetry of whatever separates the entries, no entry under three
letters, every square belonging to at least one entry, never two consecutive
unchecked letters in an entry, and checked first and last letters.
Clues follow the Ximenean fairness rules set out in the skill at
`plugins/cryptic-setter/skills/cryptic-setter/SKILL.md` — definition at one end,
wordplay that yields the answer exactly, indicators that govern their fodder.

**No build step.** Pipeline code is Python 3 with no third-party dependencies.
The solver UI is a single dependency-free HTML file. A skill that needs
`npm install` before it runs is a skill that breaks in half the places it runs.

**The puzzle document is the contract.** Every stage reads and writes
`plugins/cryptic-setter/schema/puzzle.schema.json`. Don't invent side-channels between stages; if a
stage needs to tell a later stage something, it belongs in the document.

**Answers are not grid fills.** `answer` is what the clue yields; `grid_fill`
is what gets written in the squares. They differ in variety cryptics, which is
where this project is heading. Never assume they're the same — use the
accessor, not the field.

## Working rules

- `make check` must pass before you commit. It runs the calibration tests over
  both fixtures, which in turn run the grid conventions, crossing consistency,
  enumerations, and — where the mechanics allow it — whether the wordplay
  actually builds the answer.
- Fixtures in `plugins/cryptic-setter/fixtures/` are the calibration set.
  `*-good.json` must validate clean; `*-bad.json` must fail, with each defect
  labelled by what it is and asserted in `scripts/test_fixtures.py`. If you make
  a checker stricter, the bad fixture is where you prove it.
- Never loosen a check to make a clue pass. If a clue fails the validator, the
  clue is wrong until proven otherwise.
- The skill ships two ways from one source, so keep them from drifting. `SKILL.md`
  resolves everything against `$ROOT` — `${CLAUDE_PLUGIN_ROOT}` in a plugin
  install, the folder holding `SKILL.md` in the chat bundle — so never hardcode
  either layout. Anything the skill reads at runtime must be listed in
  `PAYLOAD` in `tools/build_skill_bundle.py`, or it will not ship. `make bundle`
  proves it by running the staged copy from outside the repo.
- The version lives in two manifests, `plugin.json` and `marketplace.json`, and
  they must agree with the tag. `CHANGELOG.md` needs a section before a version
  can release. `make release-check` is what the release workflow runs; see
  `RELEASING.md`.

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

## Layout

Everything the skill needs at runtime lives inside the plugin, because a plugin
whose scripts sit outside it is broken the moment someone installs it elsewhere.

```
.claude-plugin/marketplace.json     so the repo is an installable marketplace
plugins/cryptic-setter/
  .claude-plugin/plugin.json
  skills/cryptic-setter/SKILL.md    the skill itself
  schema/puzzle.schema.json         the contract between stages
  scripts/                          validator, clue checks, page builder
  ui/solver.html                    the solver, one dependency-free file
  fixtures/                         the calibration set
tools/                              release tooling, not shipped to users
.github/workflows/                  ci on every push, release on every tag
Makefile                            short aliases for the nested paths
```
