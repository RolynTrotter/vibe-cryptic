# vibe-cryptic

Instead of solving, have the allken _write_ the cryptic crosswords!

## The north star

> I ask Claude in chat for a cryptic crossword, and I get back a link I can open
> in a browser (or receive by some other delivery mechanism) and solve. Good UI,
> real clues, no duds.

That's the whole target. Everything in this repo exists to make that one sentence
true, repeatably, at a quality a human setter would sign their name to.

Concretely, the finished experience is:

```
me:      "give me a cryptic for Thursday, 15x15, jazz theme"
allken:  ...
allken:  https://.../puzzles/2026-09-03-jazz  ← opens, solvable, actually good
```

The deliverable of this project is a **skill** (usable by Claude Code and by any
other allken) that runs the full setting pipeline end to end, plus the solver UI
that the resulting puzzle is served into.

## Why this is hard

Setting is not solving in reverse. A solver gets a clue and searches for one
answer. A setter starts with a grid full of constraints and has to invent, for
every entry, a clue that is *simultaneously*:

- **fair** — definition + wordplay, both leading to exactly the answer;
- **sound** — the wordplay actually assembles the letters, no cheating;
- **surface-smooth** — reads as a natural sentence about something else;
- **original** — not a chestnut, not lifted from a published puzzle, not one
  we've already used ourselves;
- **compatible** — the answer fits a grid slot whose crossing letters are all
  themselves cluable words.

Any one of those is tractable. The product is the hard part, and it's why the
pipeline below has explicit, independent review stages rather than one big
"write me a crossword" prompt.

## The pipeline

Seven stages. Each is a separable unit of work with its own inputs, outputs, and
failure mode. Stages 5 and 6 run as **subagents** so their judgement is genuinely
independent of the agent that wrote the clue — a setter marking their own
homework is the single most likely way this project produces bad puzzles.

| # | Stage | What it does | Status |
|---|-------|--------------|--------|
| 1 | **Constraints** | Extra fun restrictions: daily themes, holiday-shaped grids, ninas, pangrams, letter bans. | v2 |
| 2 | **Seed fill** | Place the thematic/major words into the grid space. | v1 |
| 3 | **Full fill** | Fill the remaining slots until the board is complete and every entry is a real, cluable word. | v1 |
| 4 | **Clue writing** | For each entry, work backward: answer → definition → wordplay → surface. The most complex and varied stage. | v1 |
| 5 | **Coherence check** | Independent subagent verifies each ⟨answer, definition, wordplay⟩ triplet: does the definition fit the answer, does the wordplay actually build the letters, and has this clue been used before (plagiarism / scooping / our own back catalogue)? | v1 |
| 6 | **Quality assessment** | Independent subagent scores surface reading, fairness, elegance, difficulty consistency. Flags from stage 5 or 6 mean the clue is rewritten or the entry is discarded. | v1 |
| 7 | **Local rework** | When an entry is discarded, algorithmically re-fill that section, re-check every overlapping word, rewrite the clues that changed, and repeat. | v2 |

Stages 1 and 7 are explicitly deferred. v1 can survive without themes, and it can
survive a failed entry by retrying the fill from scratch — slower, but correct.

## Architecture sketch

```
  request ──▶ [1] constraints ──▶ [2] seed fill ──▶ [3] full fill
                                                          │
                                                     grid + entries
                                                          │
                                                          ▼
                                                  [4] clue writing
                                                          │
                                        ┌─────────────────┴─────────────────┐
                                        ▼                                   ▼
                             [5] coherence subagent            [6] quality subagent
                                        └─────────────────┬─────────────────┘
                                                          │ pass?
                                              no ──▶ [7] local rework ──┐
                                                          │ yes         │
                                                          ▼             │
                                                  puzzle document ◀─────┘
                                                          │
                                                          ▼
                                                    solver UI + link
```

Two artifacts flow through the system:

- **the puzzle document** — a single serialisable object (grid geometry, entries,
  clues, metadata, provenance) that every stage reads and writes. Getting this
  schema right early is what lets the stages stay independent.
- **the clue ledger** — the record of every ⟨answer, wordplay⟩ pair we have ever
  published, so stage 5 can catch us repeating ourselves.

## Using it

The skill installs two ways, from the same source.

**In regular chat.** Download `cryptic-setter-<version>.zip` from the
[latest release](https://github.com/RolynTrotter/vibe-cryptic/releases/latest)
and upload it under Settings -> Capabilities -> Skills.

**In Claude Code.** The repo is a plugin marketplace, so it installs in one
step and tracks `main`:

```
/plugin marketplace add RolynTrotter/vibe-cryptic
/plugin install cryptic-setter@vibe-cryptic
```

Either way, then ask for a crossword. To work on the repo directly:

```
make check                                  # calibration tests
make build PUZZLE=path/to/puzzle.json       # standalone page
make body  PUZZLE=path/to/puzzle.json       # body to publish as an Artifact
make bundle                                 # the chat skill bundle
```

Nothing needs installing to run those — Python 3 and a browser, no packages.
Cutting a release is [RELEASING.md](RELEASING.md).

## Repo layout

Everything the skill needs at runtime lives inside the plugin, because a plugin
whose scripts sit outside it breaks the moment someone installs it elsewhere.

```
.claude-plugin/marketplace.json     makes the repo an installable marketplace
plugins/cryptic-setter/
  .claude-plugin/plugin.json
  skills/cryptic-setter/SKILL.md    the skill itself
  schema/puzzle.schema.json         the contract every stage reads and writes
  scripts/                          validator, clue checks, page builder
  ui/solver.html                    the solver, one dependency-free file
  fixtures/                         the calibration set: a barred grid, a
                                    blocked one, and a deliberately broken copy
tools/                              release tooling: the chat skill bundler
.github/workflows/                  checks on every push, releases on every tag
```

Still to come, as the pipeline lands: a wordlist, the fill scripts, the device
taxonomy reference, and the clue ledger.

## Roadmap

**v0 — skeleton — done.** Puzzle document schema, a hand-set example puzzle, and
a solver UI that renders and checks it. Proves the delivery half of the north
star before any generation exists: a validated document becomes a page at a link
today, with the grid and clues written by hand and the validator enforcing that
every clue's wordplay actually builds its answer.

**v1 — the pipeline.** Stages 2–6. A request in chat produces a real, reviewed,
15x15 puzzle at a link. Failed entries cause a full re-fill rather than a local
patch.

**v2 — polish.** Stages 1 and 7: themes, ninas, holiday grids, and surgical
local rework instead of start-over.

## Glossary

- **entry** — a word placed in the grid (what solvers call an "answer").
- **slot** — a light in the grid awaiting an entry, with its crossing constraints.
- **surface** — the way a clue reads as ordinary English, ignoring its cryptic function.
- **nina** — a hidden message spelled out by particular grid squares.
- **chestnut** — a clue so well-worn that reusing it is a mark against you.
