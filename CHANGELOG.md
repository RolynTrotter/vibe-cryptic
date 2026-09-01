# Changelog

Versions follow [semantic versioning](https://semver.org). While the major
version is 0, the setting pipeline is still being proven end to end and the
puzzle document schema may change between minor versions.

## [0.2.0] — 2026-08-31

The device taxonomy, and two more things the validator can prove rather than
take on trust.

**Added**

- `references/devices.md` and `references/fairness.md` — each device's
  mechanics and failure modes, the Ximenean fairness rules, and worked pairs
  clueing the same answer badly and well with identical wordplay, so the
  difference is visibly the surface.
- `references/indicators.json` and `references/abbreviations.json`, which the
  validator reads rather than merely citing.
- An `abbreviation` check kind, verified against the table. Steps that were
  passing unverified — `model` giving T, `king` giving R, `church` giving CE —
  are now genuinely checked, and an unknown abbreviation is rejected with what
  the letters do abbreviate.
- An indicator-versus-device check that names the device a misplaced indicator
  actually suggests, since such a clue usually wants moving rather than
  discarding.

**Fixed**

- The skill archive now ships `references/`, without which an installed skill
  failed on import.

**Not yet**

Semantic steps are still unverified: `Team` giving SIDE and `Louse` giving NIT
pass unchecked, because a synonym needs a thesaurus or a model rather than a
table. The skill says so rather than implying the validator covers everything.

## [0.1.0] — 2026-08-31

First release. The delivery half of the north star works; the generation half
is still driven by hand, with the validator as the backstop.

**What ships**

- The `cryptic-setter` skill: grid conventions for barred and blocked grids,
  the device taxonomy and Ximenean fairness rules, the puzzle document format,
  and the validate-then-publish loop.
- The puzzle document schema, which every pipeline stage reads and writes.
- The validator: grid symmetry and checking conventions, slot fit, crossing
  agreement, enumerations, definition placement, and wordplay that actually
  builds its answer.
- The solver UI — one dependency-free HTML file — and the page builder that
  binds a puzzle document into it, either as a standalone page or as a body to
  publish as an Artifact.
- The calibration fixtures: a barred grid, a blocked grid, and a deliberately
  broken copy whose eleven planted defects the checks must catch.
- Two ways to install: a skill bundle for chat, and the plugin marketplace for
  Claude Code.

**Not yet**

Grid filling and clue writing are still done by the model rather than by the
scripts, and the independent coherence and quality reviews are discipline in
the skill rather than enforced subagents. The pipeline has not been run end to
end for a full 15x15, which is why this is 0.1.0 and not 1.0.0.
