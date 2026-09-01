"""The word list, and fast answers to "what fits here?".

The fill asks the same question thousands of times per grid — six letters,
`.A..E.`, nothing already used — so the answer has to be cheap. Words are
bucketed by length, and within a length an index maps (position, letter) to the
words carrying that letter there. A pattern is then the intersection of one set
per fixed letter, which is small because the rarest letter narrows it first.

Indexes are built per length on first use. A puzzle touches a handful of
lengths, so paying for all thirteen up front would be waste.
"""

import os

DATA = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
)

# Lower is better. The fill tries a whole band before reaching into the next,
# so a grid only uses obscure words where it genuinely has no choice.
COMMON, EXTENDED = 0, 1
BAND_FILES = [("common", "words-common.txt"), ("extended", "words-extended.txt")]
BAND_NAMES = ["common", "extended"]

ANY = "."


class WordList:
    def __init__(self, data_dir=DATA, max_band=EXTENDED):
        self.data_dir = data_dir
        self.max_band = max_band
        self._words = {}     # length -> [word, ...], common band first
        self._bands = {}     # length -> [band, ...] parallel to _words
        self._index = {}     # length -> {(pos, letter): {index, ...}}
        self._band_of = {}   # word -> band
        self._load()

    def _load(self):
        for band, filename in BAND_FILES[: self.max_band + 1]:
            path = os.path.join(self.data_dir, filename)
            with open(path) as fh:
                for line in fh:
                    if line.startswith("#"):
                        continue
                    word = line.strip().upper()
                    if not word:
                        continue
                    index = BAND_NAMES.index(band)
                    self._band_of[word] = index
        for word, band in sorted(self._band_of.items(), key=lambda kv: (kv[1], kv[0])):
            self._words.setdefault(len(word), []).append(word)
            self._bands.setdefault(len(word), []).append(band)

    # ------------------------------------------------------------------ query
    def _ensure_index(self, length):
        if length in self._index:
            return self._index[length]
        index = {}
        for position, word in enumerate(self._words.get(length, ())):
            for slot, letter in enumerate(word):
                index.setdefault((slot, letter), set()).add(position)
        self._index[length] = index
        return index

    def _matching_positions(self, pattern):
        """Indices into the length bucket whose words match, or None for all."""
        length = len(pattern)
        fixed = [(i, ch) for i, ch in enumerate(pattern) if ch != ANY]
        if not fixed:
            return None
        index = self._ensure_index(length)
        # Start from the most selective letter so the intersection stays small.
        sets = []
        for slot, letter in fixed:
            found = index.get((slot, letter))
            if not found:
                return set()
            sets.append(found)
        sets.sort(key=len)
        result = sets[0]
        for other in sets[1:]:
            result = result & other
            if not result:
                break
        return result

    def candidates(self, pattern, max_band=EXTENDED, exclude=(), limit=None):
        """Words matching the pattern, best band first."""
        pattern = pattern.upper()
        words = self._words.get(len(pattern))
        if not words:
            return []
        bands = self._bands[len(pattern)]
        positions = self._matching_positions(pattern)
        chosen = range(len(words)) if positions is None else sorted(positions)
        out = []
        for position in chosen:
            if bands[position] > max_band:
                continue
            word = words[position]
            if word in exclude:
                continue
            out.append(word)
            if limit and len(out) >= limit:
                break
        return out

    def has_match(self, pattern, max_band=EXTENDED, exclude=()):
        """Is there at least one candidate? Used for forward checking."""
        return bool(self.candidates(pattern, max_band, exclude, limit=1))

    def band(self, word):
        return self._band_of.get(word.upper())

    def contains(self, word):
        return word.upper() in self._band_of

    def stats(self):
        return {
            "words": len(self._band_of),
            "by_band": {
                BAND_NAMES[b]: sum(1 for v in self._band_of.values() if v == b)
                for b in range(self.max_band + 1)
            },
        }
