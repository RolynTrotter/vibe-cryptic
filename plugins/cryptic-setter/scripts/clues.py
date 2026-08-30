"""Clue checking: does the wordplay actually build the answer?

This is the mechanical half of stage 5. It answers questions with letter-by-letter
answers — do the anagram letters match, is the hidden word really hidden there,
do the charade parts concatenate to the answer — and stays silent on questions of
taste. A clue that fails here is wrong, not merely unfashionable.
"""

import re

from puzzle import UNVERIFIABLE


def letters(text):
    """Strip a clue fragment to bare uppercase letters."""
    return re.sub(r"[^A-Za-z]", "", text).upper()


def _anagram(check):
    fodder, yields = letters(check["fodder"]), check["yields"]
    if sorted(fodder) != sorted(yields):
        extra = sorted((set(fodder) | set(yields)))
        detail = ", ".join(
            f"{ch}x{fodder.count(ch)}/{yields.count(ch)}"
            for ch in extra
            if fodder.count(ch) != yields.count(ch)
        )
        return (
            f"anagram fodder {check['fodder']!r} ({len(fodder)} letters) does not "
            f"rearrange to {yields} ({len(yields)}); counts differ on {detail}"
        )
    if fodder == yields:
        return f"anagram fodder {check['fodder']!r} is already {yields} — nothing is rearranged"
    return None


def _hidden(check):
    source, yields = letters(check["source"]), check["yields"]
    if yields not in source:
        return f"{yields} is not hidden in {check['source']!r}"
    if source == yields:
        return f"{check['source']!r} is exactly {yields}, so nothing is concealed"
    return None


def _reversal(check):
    source, yields = letters(check["source"]), check["yields"]
    if source[::-1] != yields:
        return f"{check['source']!r} reversed is {source[::-1]}, not {yields}"
    return None


def _concatenation(check):
    parts = [letters(p) for p in check["parts"]]
    joined = "".join(parts)
    if joined != check["yields"]:
        return (
            f"parts {' + '.join(parts)} join to {joined}, not {check['yields']}"
        )
    return None


def _deletion(check):
    source, remove, yields = letters(check["source"]), letters(check["remove"]), check["yields"]
    if remove not in source:
        return f"cannot delete {remove} from {source}: it is not there"
    # A deletion clue removes one occurrence; try each and see if any gives the answer.
    candidates = {
        source[:i] + source[i + len(remove):]
        for i in range(len(source) - len(remove) + 1)
        if source[i:i + len(remove)] == remove
    }
    if yields not in candidates:
        shown = ", ".join(sorted(candidates))
        return f"deleting {remove} from {source} gives {shown}, not {yields}"
    return None


def _letter_selection(check):
    words = [w for w in re.split(r"\s+", check["source"].strip()) if w]
    stripped = [letters(w) for w in words]
    rule = check["rule"]
    if rule == "initials":
        got = "".join(w[0] for w in stripped if w)
    elif rule == "finals":
        got = "".join(w[-1] for w in stripped if w)
    elif rule == "centres":
        got = "".join(w[len(w) // 2] for w in stripped if w)
    elif rule in ("alternates-odd", "alternates-even"):
        run = "".join(stripped)
        got = run[0::2] if rule == "alternates-odd" else run[1::2]
    else:
        return f"unknown letter-selection rule {rule!r}"
    if got != check["yields"]:
        return f"{rule} of {check['source']!r} gives {got}, not {check['yields']}"
    return None


_CHECKERS = {
    "anagram": _anagram,
    "hidden": _hidden,
    "reversal": _reversal,
    "concatenation": _concatenation,
    "deletion": _deletion,
    "letter_selection": _letter_selection,
    "literal": lambda check: None,  # nothing to verify; it documents the step
}


def check_clue(entry):
    """Structural and mechanical checks on one entry's clue."""
    label = f"{entry['number']}{entry['direction'][0].upper()}"
    errors = []
    clue = entry.get("clue")
    if clue is None:
        return [f"{label}: no clue"]

    text, answer = clue["text"], entry["answer"]
    definition = clue["definition"]
    position = definition.get("position")

    # The definition must be lifted from the clue, not paraphrased.
    if definition["text"].lower() not in text.lower():
        errors.append(
            f"{label}: definition {definition['text']!r} does not appear in the clue"
        )
    elif position == "leading" and not text.lower().startswith(definition["text"].lower()):
        errors.append(f"{label}: definition is marked leading but the clue does not start with it")
    elif position == "trailing" and not _ends_with(text, definition["text"]):
        errors.append(f"{label}: definition is marked trailing but the clue does not end with it")
    elif position == "whole" and letters(definition["text"]) != letters(text):
        errors.append(f"{label}: definition is marked whole (&lit) but is not the entire clue")

    wordplay = clue["wordplay"]
    for indicator in wordplay.get("indicators", []):
        if indicator.lower() not in text.lower():
            errors.append(f"{label}: indicator {indicator!r} does not appear in the clue")

    checks = wordplay.get("checks", [])
    # A hidden word has to hide inside words the solver can actually see.
    for check in checks:
        if check["kind"] == "hidden" and check["source"].lower() not in text.lower():
            errors.append(
                f"{label}: hidden source {check['source']!r} does not appear in the clue"
            )
    for i, check in enumerate(checks):
        checker = _CHECKERS.get(check["kind"])
        if checker is None:
            errors.append(f"{label}: unknown check kind {check['kind']!r}")
            continue
        problem = checker(check)
        if problem:
            errors.append(f"{label}: check {i + 1} ({check['kind']}) — {problem}")

    # The wordplay has to arrive at the answer, not merely near it.
    devices = set(wordplay["devices"])
    if checks:
        if not any(check["yields"] == answer for check in checks):
            reached = ", ".join(sorted({c["yields"] for c in checks}))
            errors.append(
                f"{label}: no check yields {answer} — the wordplay stops at {reached}"
            )
    elif not devices & UNVERIFIABLE:
        errors.append(
            f"{label}: devices {sorted(devices)} are mechanically checkable but no "
            "checks are given, so nothing verifies the wordplay"
        )

    # Anagram fodder has to be present in the clue for the solver to work with.
    # Fodder is often split by connecting words ("rat and brie cooked"), so each
    # word is checked separately rather than the phrase as a whole.
    for check in checks:
        if check["kind"] != "anagram":
            continue
        missing = [
            word for word in re.split(r"\s+", check["fodder"].strip())
            if word and word.lower() not in text.lower()
        ]
        if missing:
            errors.append(
                f"{label}: anagram fodder {' '.join(missing)!r} does not appear in the clue"
            )
    return errors


def _ends_with(text, fragment):
    trimmed = text.rstrip(" .!?,;:'\"")
    return trimmed.lower().endswith(fragment.lower().rstrip(" .!?,;:'\""))
