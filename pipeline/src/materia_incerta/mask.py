"""Remove plant names from text before it reaches a model.

Matching ignores case and diacritics (so "ἄλυσσον", "Alysson" and "ALYSSON"
are the same to it), and each term also yields Latin/Greek transliteration
variants (kh/ch, k/c, ai/ae, oi/oe, ou/u, y/u) and a stem that matches any
ending, so "aristolokhia" also catches "Aristolochia" and "aristolochic".

`assert_masked` is the gate: score.py calls it on every prompt and refuses
to send one that still contains a term.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass, field

PLACEHOLDER = "[PLANT]"

#: Stems shorter than this are matched only as whole words.
MIN_STEM = 5

# Endings stripped to form a stem (normalised, so already lower-case ASCII).
_ENDINGS = ("ion", "ium", "eia", "ea", "os", "on", "um", "us", "is", "es", "ia", "a", "e", "i", "o", "y")

# Pairwise spelling swaps between Greek transliteration and Latin forms.
_SWAPS = (
    ("kh", "ch"),
    ("ph", "f"),
    ("k", "c"),
    ("ai", "ae"),
    ("oi", "oe"),
    ("ou", "u"),
    ("y", "u"),
    ("ei", "i"),
)


class MaskingError(RuntimeError):
    """A prompt still contains a plant name, synonym or transliteration."""


def _fold_char(ch: str) -> str:
    decomposed = unicodedata.normalize("NFKD", ch)
    base = "".join(c for c in decomposed if not unicodedata.combining(c))
    return base.casefold()


def fold(text: str) -> str:
    """Lower-case and strip diacritics."""
    return "".join(_fold_char(c) for c in text)


def _fold_with_map(text: str) -> tuple[str, list[int]]:
    """Fold text and return, for each folded char, its index in `text`."""
    out: list[str] = []
    index: list[int] = []
    for i, ch in enumerate(text):
        folded = _fold_char(ch)
        out.append(folded)
        index.extend([i] * len(folded))
    return "".join(out), index


def _variants(word: str) -> set[str]:
    """Spelling variants of one folded word, by applying swaps both ways."""
    variants = {word}
    for a, b in _SWAPS:
        for v in list(variants):
            if a in v:
                variants.add(v.replace(a, b))
            if b in v:
                variants.add(v.replace(b, a))
    return variants


def _stem(word: str) -> str:
    for ending in _ENDINGS:
        if word.endswith(ending) and len(word) - len(ending) >= MIN_STEM:
            return word[: -len(ending)]
    return word


def _term_tokens(term: str) -> list[str]:
    # Split binomials and phrases into words; drop abbreviations like "subsp."
    words = re.split(r"[\s\-‐–—/,;()]+", fold(term))
    return [w.strip(".'’\"") for w in words if len(w.strip(".'’\"")) >= 3]


@dataclass
class NameLexicon:
    """Every term to hide for one historical name and its candidates."""

    terms: set[str] = field(default_factory=set)
    _pattern: re.Pattern[str] | None = field(default=None, repr=False)

    @classmethod
    def from_terms(cls, terms: Iterable[str]) -> "NameLexicon":
        lex = cls()
        for term in terms:
            if term and term.strip():
                lex.terms.add(term.strip())
        return lex

    def _alternatives(self) -> list[str]:
        alts: set[str] = set()
        for term in self.terms:
            whole = fold(term)
            if len(whole) >= 3:
                alts.add(re.escape(whole))
            for word in _term_tokens(term):
                for v in _variants(word):
                    stem = _stem(v)
                    if len(stem) >= MIN_STEM and stem != v:
                        # Stem plus any word characters: catches other endings.
                        alts.add(re.escape(stem) + r"\w*")
                    else:
                        alts.add(re.escape(v))
        # Longest first so the regex prefers the fullest match.
        return sorted(alts, key=len, reverse=True)

    @property
    def pattern(self) -> re.Pattern[str] | None:
        if self._pattern is None:
            alts = self._alternatives()
            if not alts:
                return None
            self._pattern = re.compile(r"(?<!\w)(?:" + "|".join(alts) + r")(?!\w)")
        return self._pattern

    def spans(self, text: str) -> list[tuple[int, int]]:
        """Character spans of `text` that match a term."""
        pat = self.pattern
        if pat is None:
            return []
        folded, index = _fold_with_map(text)
        spans: list[tuple[int, int]] = []
        for m in pat.finditer(folded):
            if m.start() == m.end():
                continue
            start = index[m.start()]
            end = index[m.end() - 1] + 1
            # Extend over trailing combining marks of the last char.
            while end < len(text) and unicodedata.combining(text[end]):
                end += 1
            spans.append((start, end))
        return spans


def mask(text: str, lexicon: NameLexicon, placeholder: str = PLACEHOLDER) -> str:
    spans = lexicon.spans(text)
    if not spans:
        return text
    out: list[str] = []
    pos = 0
    for start, end in spans:
        if start < pos:
            continue
        out.append(text[pos:start])
        out.append(placeholder)
        pos = end
    out.append(text[pos:])
    return "".join(out)


def find_leaks(text: str, lexicon: NameLexicon) -> list[str]:
    """Substrings of `text` that the lexicon would mask."""
    return [text[s:e] for s, e in lexicon.spans(text)]


def assert_masked(text: str, lexicon: NameLexicon) -> None:
    leaks = find_leaks(text, lexicon)
    if leaks:
        raise MaskingError(f"prompt contains {len(leaks)} unmasked name(s): {sorted(set(leaks))}")


def lexicon_for_name(name, dmm_plants, candidates) -> NameLexicon:
    """All terms for one historical name: its own forms, its DMM plants' names,
    and every candidate's accepted name, synonyms, genus and common names.

    Candidates for all DMM plants of the name are pooled, so one candidate's
    name can't leak into another's comparison.
    """
    terms: list[str] = [name.greek_name, name.transliteration, *name.name_variants]
    for plant in dmm_plants:
        if plant.dmm_id in name.dmm_ids:
            terms.extend(plant.names)
    for cand in candidates:
        if cand.lemma_tag != name.lemma_tag:
            continue
        terms.append(cand.source_name)
        if cand.accepted_name:
            terms.append(cand.accepted_name)
        if cand.accepted_genus:
            terms.append(cand.accepted_genus)
        terms.extend(cand.synonyms)
        terms.extend(cand.common_names)
    return NameLexicon.from_terms(terms)
