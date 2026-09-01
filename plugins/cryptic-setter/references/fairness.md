# Fairness and surface

Two separate standards. **Fairness** is whether a competent solver could get
there and feel the answer was earned. **Surface** is whether the clue reads as
ordinary English about something else. A clue can be scrupulously fair and still
be a dull, mechanical slog; it can read beautifully and still cheat.

Soundness — does the wordplay build the answer, letter for letter — is a third
thing again, and it is the one the validator settles. This file is about the two
it cannot.

## The fairness rules

These are not stylistic preferences. Breaking one produces a clue that a solver
cannot fairly be expected to get.

**The definition sits at one end.** Never buried mid-clue. The solver's first
job is to find the boundary between definition and wordplay, and a definition in
the middle makes that guesswork. The single exception is an &lit, where the whole
clue is both.

**The wordplay yields the answer exactly.** Every letter accounted for, none
spare, none borrowed from elsewhere. "Nearly right" is wrong.

**Indicators govern their fodder.** An anagram indicator must sit where it can
plausibly apply to the letters being anagrammed. Position is part of the
grammar, not decoration.

**Every word does a job.** Each word is part of the definition, part of the
wordplay, an indicator, or a link word. A word that is none of those is padding,
and padding misleads the solver about where the clue's seams are. This is the
rule most often broken in service of a nicer surface, and the trade is not
worth making.

**Abbreviations are standard.** If you cannot point at a dictionary or at
established crossword usage, you have invented it. `abbreviations.json` is the
working list; extend it with things you can defend rather than working around
the check.

**Anagram fodder appears literally.** Never a synonym of the fodder — an
indirect anagram gives the solver no way to know which word to scramble.

**The definition matches the answer's part of speech, number and tense.** A
plural answer needs a plural definition; a past-tense answer needs a past-tense
definition.

**Homophones survive an accent.** If it only rhymes in one region, say so or
drop it.

## Surface

The wordplay is the machine; the surface is the paint. A solver reads the
surface first and should be misled by it — that misdirection is the game.

The test: **does the clue read as a sentence someone might actually write about
something else entirely?** If it reads as a list of components with connective
tissue, the surface has failed even where the mechanics are perfect.

### Worked examples

The same answers, clued badly and well. In each pair the wordplay is identical —
only the surface changes.

**ACROBAT** (anagram of CAB ROTA)

> Bad: *Anagram of cab rota gives a tumbler (7)*
> Good: **Tumbler upset cab rota (7)**

The bad one announces the mechanism. "Anagram of" is a stage direction, not an
indicator. The good one says something a person could say — a gymnast disrupted
the taxi schedule — and "upset" does the indicating without breaking character.

**BALLOON** (BALL + O + ON)

> Bad: *Dance, nothing, on — this swells (7)*
> Good: **Dance with nothing on, and swell (7)**

Same three parts in the same order. The bad version is a parts list held
together by punctuation. The good one is a single cheeky image, and "with
nothing on" carries both the O and the ON without seeming to try.

**ROMANCE** (ROMAN + CE)

> Bad: *Roman church makes a love story (7)*
> Good: **Ancient Italian church offers a love story (7)**

The bad one leaves ROMAN barely disguised — it is nearly the answer's own
letters sitting in plain sight. "Ancient Italian" makes the solver do the work
of finding ROMAN, which is the work the clue exists to set.

**LEA** (LEAD minus its last letter)

> Bad: *Lead without its end, a meadow (3)*
> Good: **Endless lead for the meadow (3)**

The bad one explains the deletion in prose. "Endless" is the same instruction
compressed into a word that also reads naturally.

### What separates them

- **Never name the device.** "Anagram of", "reversed", "hidden in" as bald
  instructions are confessions. Use indicators that also mean something on the
  surface.
- **Prefer a surface from one world.** Cab rotas, dance floors, meadows. A clue
  whose words come from three unrelated domains reads as machinery.
- **Punctuation is free.** Solvers may repunctuate at will, so use it for the
  surface reading and expect the solver to ignore it.
- **Capital letters mislead legitimately.** A capital at the start of a clue
  tells the solver nothing.
- **Short is usually better.** Extra words are usually padding, and padding is a
  fairness fault.

## Across the whole puzzle

Individually sound clues can still make a bad puzzle.

- **Vary the devices.** Two-thirds anagrams fails even when every anagram is
  sound. The fixtures run about 30% anagram, 30% charade, and the rest spread
  across hidden, reversal, deletion, container and double definition.
- **Don't reuse an indicator.** The same word indicating the same device twice
  in one grid is a missed opportunity at best.
- **Don't reuse a trick.** Two clues with the same shape feel like one clue.
- **Spread the difficulty.** A few ways in, a few hard ones, most in the middle.
- **Watch for repeated roots.** IDEA and IDEAS in one grid is a fill fault that
  shows up as a cluing problem.
