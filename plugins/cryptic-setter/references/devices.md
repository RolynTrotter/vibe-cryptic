# Cryptic devices

The mechanics of each device, what it needs to be sound, and the way each one
usually goes wrong. The indicator vocabulary lives in `indicators.json`, which
the validator reads; this file explains what those lists are for.

A clue is normally **definition + wordplay**, with the definition at one end.
The wordplay is a second, independent route to the same answer — that redundancy
is what lets a solver be certain without any crossing letters.

## Anagram

Letters of the fodder rearranged into the answer.

- **Needs:** the fodder present *literally* in the clue, and an indicator.
- **Check:** `{"kind": "anagram", "fodder": "cab rota", "yields": "ACROBAT"}`
- **Goes wrong:** fodder that doesn't have the answer's letters (the commonest
  error and the easiest to catch); fodder given as a synonym rather than
  literally — an *indirect anagram*, which is unfair because the solver cannot
  know which synonym to scramble; an indicator that doesn't indicate disorder.

## Charade

Parts joined end to end, in grid order.

- **Needs:** each part separately clued. No indicator is required — the order of
  the clue does the work — though link words may join the parts.
- **Check:** a `concatenation` whose parts join to the answer, with an
  `abbreviation` or `literal` check for each part.
- **Goes wrong:** parts in the wrong order; a part that isn't fairly clued; in a
  down clue, "on" meaning *below* rather than *after*, which reverses the order.

## Container

One part placed inside another.

- **Needs:** an indicator, and the indicator must make the direction clear.
- **Check:** a `concatenation` of three parts — outer-start, contents, outer-end.
- **Goes wrong:** **direction**. "A in B" and "A around B" put the letters in
  opposite places, and a setter who writes the indicator for one while meaning
  the other has produced an unsound clue that still looks right. Check which
  half is doing the containing before you check anything else.

## Hidden

The answer spans consecutive words in the clue.

- **Needs:** a concealment indicator, and the answer must genuinely straddle a
  word boundary — a "hidden" word sitting inside a single word is weak, and one
  that *is* the word conceals nothing.
- **Check:** `{"kind": "hidden", "source": "cheap Ronaldo", "yields": "APRON"}`
- **Goes wrong:** the source not appearing in the clue; the span not actually
  containing the answer; a source contrived purely to hide the answer, which
  wrecks the surface.

## Reversal

The letters run backwards.

- **Needs:** a reversal indicator. Direction words are **not
  interchangeable**: "up", "raised", "climbing", "northward" reverse a *down*
  entry only; "back", "returned", "westward" suit an *across* entry. Using an
  up-word on an across clue is a fault even though the letters come out right.
- **Check:** `{"kind": "reversal", "source": "NIT", "yields": "TIN"}`
- **Goes wrong:** wrong-direction indicators; palindromes, where the reversal
  does nothing.

## Deletion

Letters removed from a longer word.

- **Needs:** an indicator that names *which* letters go. The three cases take
  completely different vocabulary: first letter ("beheaded", "headless"), last
  letter ("endless", "curtailed"), middle ("heartless", "gutted").
- **Check:** `{"kind": "deletion", "source": "lead", "remove": "D", "yields": "LEA"}`
- **Goes wrong:** removing letters the indicator doesn't license — "endless
  grace" is RACE only if you meant *beheaded*, and GRAC if you meant what you
  said.

## Letter selection

Initials, finals, alternates, or centres of a run of words.

- **Needs:** an indicator naming the rule, and the source words in the clue.
- **Check:** `{"kind": "letter_selection", "source": "resistance opposing
  dictatorship", "rule": "initials", "yields": "ROD"}`
- **Goes wrong:** miscounting; "odd" and "even" alternates being off by one;
  selection rules applied across words when the indicator implies within one.

## Homophone

The answer sounds like something else.

- **Needs:** a homophone indicator and a pronunciation that survives an accent.
- **Not machine-checkable.** The validator leaves these to human or model
  judgement, so the burden of proof is on the setter.
- **Goes wrong:** homophones that only work in one accent; near-homophones.

## Double definition

Two definitions, no wordplay at all.

- **Needs:** both halves to genuinely define the answer, ideally in unrelated
  senses. Nothing else — no indicator, no link beyond a word or two.
- **Not machine-checkable.**
- **Goes wrong:** one half being a stretch; the two senses being the same sense
  in different clothes, which gives the solver only one way in rather than two.

## Cryptic definition

One definition, read misleadingly.

- **Needs:** genuine misdirection, and fairness on second reading.
- **Not machine-checkable**, and the hardest device to do well. When it works
  the solver groans; when it fails they shrug.

## &lit (and literally so)

The entire clue is both the definition and the wordplay.

- **Needs:** both readings to work completely, over the same words. Usually
  marked with an exclamation mark.
- Rare and worth the effort when it lands. Set `definition.position` to
  `"whole"`.

## Spoonerism and substitution

Spoonerisms swap initial sounds and need Spooner named. Substitution replaces
one part with another and needs an indicator making both halves explicit.
Neither is machine-checkable; both are easy to do unfairly.

## On indicator lists

`indicators.json` is checked, not decorative: an indicator declared for a device
whose list doesn't contain it is an error, and the error names the device the
word *does* suggest. That hint matters — a misplaced indicator usually means a
clue that wants moving, not discarding.

Words legitimately appear under several devices. "Upset" anagrams in one clue
and reverses in another; "in" hides in one and contains in another. The check
passes if the indicator is listed under any device the clue declares.

Words that indicate **nothing** are the other half of the discipline. "Very",
"really", "quite" and "somewhat" are intensifiers, not anagram indicators. "And",
"with", "of" and "for" are link words joining definition to wordplay, and a link
word cannot double as an indicator. If a word in your clue is doing no work at
all, it is padding, and padding is a fairness fault rather than a stylistic one.
