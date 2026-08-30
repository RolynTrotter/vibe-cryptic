"""The puzzle document: loading, grid geometry, and structural checks.

Everything derived from the grid — slot positions, numbering, which squares are
checked, which entries cross which — is computed here rather than stored in the
document. Derived data in a file is data that goes stale.
"""

import json
import re
from dataclasses import dataclass, field

BLOCK = "#"
LIGHT = "."

# Devices whose mechanics a machine cannot settle. A homophone depends on an
# accent; a cryptic definition depends on a shared joke. These get judged by the
# review stages, not by the validator.
UNVERIFIABLE = {
    "homophone", "double_definition", "cryptic_definition", "spoonerism",
    "substitution",
}


@dataclass(frozen=True)
class Slot:
    number: int
    direction: str
    row: int
    col: int
    length: int

    @property
    def key(self):
        return (self.number, self.direction)

    @property
    def label(self):
        return f"{self.number}{self.direction[0].upper()}"

    def squares(self):
        for i in range(self.length):
            if self.direction == "across":
                yield self.row, self.col + i
            else:
                yield self.row + i, self.col


@dataclass
class Puzzle:
    doc: dict
    slots: dict = field(default_factory=dict)      # (number, direction) -> Slot
    checked: set = field(default_factory=set)      # squares in two slots

    @property
    def pattern(self):
        return self.doc["grid"]["pattern"]

    @property
    def height(self):
        return len(self.pattern)

    @property
    def width(self):
        return len(self.pattern[0]) if self.pattern else 0

    def is_light(self, r, c):
        return 0 <= r < self.height and 0 <= c < self.width and self.pattern[r][c] == LIGHT

    def entry_slot(self, entry):
        return self.slots.get((entry["number"], entry["direction"]))


def grid_fill(entry):
    """What actually goes in the squares.

    In a plain cryptic this is the answer. In a variety cryptic the solver
    modifies the answer before entering it, and the two diverge — so never read
    `answer` when you mean the grid.
    """
    return entry.get("grid_fill", entry["answer"])


def enumerate_slots(puzzle):
    """Find every slot and number it by crossword convention.

    A square starts an entry when it's a light, the square before it in that
    direction isn't, and there's room for at least two more letters. Numbers are
    assigned in reading order, shared between an across and a down that start on
    the same square.
    """
    slots, number = {}, 0
    for r in range(puzzle.height):
        for c in range(puzzle.width):
            if not puzzle.is_light(r, c):
                continue
            starts_across = not puzzle.is_light(r, c - 1) and puzzle.is_light(r, c + 1)
            starts_down = not puzzle.is_light(r - 1, c) and puzzle.is_light(r + 1, c)
            if not (starts_across or starts_down):
                continue
            number += 1
            if starts_across:
                length = 0
                while puzzle.is_light(r, c + length):
                    length += 1
                slots[(number, "across")] = Slot(number, "across", r, c, length)
            if starts_down:
                length = 0
                while puzzle.is_light(r + length, c):
                    length += 1
                slots[(number, "down")] = Slot(number, "down", r, c, length)
    return slots


def compute_checked(slots):
    """Squares covered by both an across and a down entry."""
    counts = {}
    for slot in slots.values():
        for square in slot.squares():
            counts[square] = counts.get(square, 0) + 1
    return {square for square, n in counts.items() if n > 1}


def load(path):
    with open(path) as fh:
        doc = json.load(fh)
    puzzle = Puzzle(doc=doc)
    if puzzle.pattern and len({len(row) for row in puzzle.pattern}) == 1:
        puzzle.slots = enumerate_slots(puzzle)
        puzzle.checked = compute_checked(puzzle.slots)
    return puzzle


# --------------------------------------------------------------------------
# Grid conventions
# --------------------------------------------------------------------------

def check_grid(puzzle):
    errors = []
    pattern = puzzle.pattern
    if len({len(row) for row in pattern}) != 1:
        return ["grid: rows are not all the same length"]

    symmetry = puzzle.doc["grid"].get("symmetry", "rotational-180")
    if symmetry == "rotational-180":
        for r in range(puzzle.height):
            for c in range(puzzle.width):
                mirror = pattern[puzzle.height - 1 - r][puzzle.width - 1 - c]
                if pattern[r][c] != mirror:
                    errors.append(
                        f"grid: not 180-degree symmetric at ({r},{c})"
                    )
                    break
            if errors:
                break

    # Every light must belong to an entry; a stranded square is unsolvable.
    covered = set()
    for slot in puzzle.slots.values():
        covered.update(slot.squares())
    for r in range(puzzle.height):
        for c in range(puzzle.width):
            if puzzle.is_light(r, c) and (r, c) not in covered:
                errors.append(f"grid: light at ({r},{c}) belongs to no entry")

    for slot in puzzle.slots.values():
        if slot.length < 3:
            errors.append(f"grid: {slot.label} is only {slot.length} letters (minimum 3)")

    if puzzle.doc["meta"].get("tradition", "us-cryptic") == "us-cryptic":
        errors += check_us_cryptic_conventions(puzzle)

    errors += check_connected(puzzle)
    return errors


def check_us_cryptic_conventions(puzzle):
    """The rules that make a US-style cryptic grid solvable.

    Unchecked letters are guesses; the conventions exist to make sure a solver
    never has to make two guesses in a row, and never has to guess at the ends
    of an entry where the wordplay is hardest to confirm.
    """
    errors = []
    for slot in puzzle.slots.values():
        squares = list(slot.squares())
        flags = [square in puzzle.checked for square in squares]
        if not flags[0] or not flags[-1]:
            which = "first" if not flags[0] else "last"
            errors.append(f"grid: {slot.label} has an unchecked {which} letter")
        for i in range(len(flags) - 1):
            if not flags[i] and not flags[i + 1]:
                errors.append(
                    f"grid: {slot.label} has consecutive unchecked letters at "
                    f"positions {i + 1} and {i + 2}"
                )
                break
    return errors


def check_connected(puzzle):
    """All lights must form one region, or the puzzle is two puzzles."""
    lights = {
        (r, c)
        for r in range(puzzle.height)
        for c in range(puzzle.width)
        if puzzle.is_light(r, c)
    }
    if not lights:
        return ["grid: no lights"]
    start = next(iter(lights))
    seen, stack = {start}, [start]
    while stack:
        r, c = stack.pop()
        for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if (nr, nc) in lights and (nr, nc) not in seen:
                seen.add((nr, nc))
                stack.append((nr, nc))
    if len(seen) != len(lights):
        return [f"grid: {len(lights) - len(seen)} lights are cut off from the rest"]
    return []


# --------------------------------------------------------------------------
# Entries against the grid
# --------------------------------------------------------------------------

def check_entries(puzzle):
    errors = []
    letters = {}  # square -> (letter, entry label)

    for slot_key in puzzle.slots:
        if not any(
            (e["number"], e["direction"]) == slot_key for e in puzzle.doc["entries"]
        ):
            number, direction = slot_key
            errors.append(f"entries: no entry for slot {number}{direction[0].upper()}")

    seen_keys = set()
    for entry in puzzle.doc["entries"]:
        label = f"{entry['number']}{entry['direction'][0].upper()}"
        key = (entry["number"], entry["direction"])
        if key in seen_keys:
            errors.append(f"{label}: duplicated")
            continue
        seen_keys.add(key)

        slot = puzzle.entry_slot(entry)
        if slot is None:
            errors.append(f"{label}: no such slot in the grid")
            continue
        if (entry["row"], entry["col"]) != (slot.row, slot.col):
            errors.append(
                f"{label}: says it starts at ({entry['row']},{entry['col']}) but "
                f"the grid puts it at ({slot.row},{slot.col})"
            )
        fill = grid_fill(entry)
        if len(fill) != slot.length:
            errors.append(
                f"{label}: fill {fill!r} is {len(fill)} letters, slot holds {slot.length}"
            )
            continue

        for (r, c), letter in zip(slot.squares(), fill):
            if (r, c) in letters and letters[(r, c)][0] != letter:
                other_letter, other_label = letters[(r, c)]
                errors.append(
                    f"{label}: wants {letter} at ({r},{c}) but {other_label} "
                    f"wants {other_letter}"
                )
            letters[(r, c)] = (letter, label)

        if "enumeration" in entry:
            counts = [int(n) for n in re.split(r"[,\- ]", entry["enumeration"])]
            if sum(counts) != len(entry["answer"]):
                errors.append(
                    f"{label}: enumeration ({entry['enumeration']}) totals "
                    f"{sum(counts)} but the answer has {len(entry['answer'])} letters"
                )
    return errors


def check_variety_instructions(puzzle):
    """A gimmick the solver isn't told about is not a gimmick, it's a bug."""
    modified = [
        e for e in puzzle.doc["entries"] if e.get("grid_fill", e["answer"]) != e["answer"]
    ]
    if modified and not puzzle.doc["meta"].get("instructions"):
        labels = ", ".join(f"{e['number']}{e['direction'][0].upper()}" for e in modified[:5])
        return [
            f"meta: {len(modified)} entries are modified before entry ({labels}) "
            "but meta.instructions is missing, so the solver is never told the gimmick"
        ]
    return []
