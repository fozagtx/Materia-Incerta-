"""Apply the paper's scoring to feature comparisons.

1. Map each match class to a score (good 2, partial 1, no match -2, absent 0).
2. Average the scores within each feature category.
3. Degree of congruence (DoC) = categories with a positive mean minus
   categories with a negative mean.
4. Label: Strong at DoC >= 5, Moderate at 3 to 4, Weak below 3.

DoC as defined above is always an integer, so the unresolved range between 4
and 5 can only be reached by a non-integer input. label_for() raises on it
rather than guessing; reproduce.py reports whether the paper's own values ever
land there (docs/open-questions.md, Q1).
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from . import config
from .schemas import Candidate, CandidateScore, FeatureComparison, Label, MatchClass, ScoreSource


class ThresholdGapError(ValueError):
    """Raised for a DoC strictly between Moderate's max and Strong's min."""


def score_of(match_class: MatchClass) -> int:
    try:
        return config.MATCH_SCORES[match_class]
    except KeyError:
        raise ValueError(f"unknown match class {match_class!r}") from None


def category_means(classes_by_category: Mapping[str, Sequence[MatchClass]]) -> dict[str, float]:
    """Mean score per category. Categories with no comparisons are omitted."""
    means: dict[str, float] = {}
    for category, classes in classes_by_category.items():
        if not classes:
            continue
        means[category] = sum(score_of(c) for c in classes) / len(classes)
    return means


def congruence(means: Mapping[str, float]) -> tuple[int, int, int]:
    """Return (positive categories, negative categories, DoC)."""
    pos = sum(1 for m in means.values() if m > 0)
    neg = sum(1 for m in means.values() if m < 0)
    return pos, neg, pos - neg


def label_for(doc: float) -> Label:
    if doc >= config.STRONG_MIN:
        return "Strong"
    if config.MODERATE_MAX < doc < config.STRONG_MIN:
        raise ThresholdGapError(
            f"DoC {doc} falls between {config.MODERATE_MAX} and {config.STRONG_MIN}; "
            "the paper's handling is unresolved (docs/open-questions.md, Q1)"
        )
    if doc >= config.MODERATE_MIN:
        return "Moderate"
    return "Weak"


def competition_ranks(values: Mapping[str, float]) -> dict[str, int]:
    """1-based ranks, highest value first; ties share the best rank (1, 1, 3)."""
    ordered = sorted(values.values(), reverse=True)
    return {key: 1 + ordered.index(v) for key, v in values.items()}


@dataclass(frozen=True)
class _Group:
    lemma_tag: str
    dmm_id: str


def classes_by_candidate(
    comparisons: Iterable[FeatureComparison], source: ScoreSource
) -> dict[str, dict[str, list[MatchClass]]]:
    """candidate_key -> category -> classes, for one score source.

    A candidate is included for the model source only if every one of its
    comparisons has a model class, so partial runs never yield a label.
    """
    out: dict[str, dict[str, list[MatchClass]]] = defaultdict(lambda: defaultdict(list))
    incomplete: set[str] = set()
    for comp in comparisons:
        cls = comp.expert_class if source == "expert" else comp.model_class
        if cls is None:
            incomplete.add(comp.candidate_key)
            continue
        out[comp.candidate_key][comp.category].append(cls)
    return {
        key: dict(cats) for key, cats in out.items() if key not in incomplete
    }


def score_candidates(
    candidates: Sequence[Candidate],
    comparisons: Sequence[FeatureComparison],
    source: ScoreSource,
) -> list[CandidateScore]:
    """Score every candidate that has a complete set of classes for `source`.

    Ranks are computed within each (lemma_tag, dmm_id) group.
    """
    by_cand = classes_by_candidate(comparisons, source)
    groups: dict[_Group, list[Candidate]] = defaultdict(list)
    for cand in candidates:
        if cand.candidate_key in by_cand:
            groups[_Group(cand.lemma_tag, cand.dmm_id)].append(cand)

    rows: list[CandidateScore] = []
    for group in sorted(groups, key=lambda g: (g.lemma_tag, g.dmm_id)):
        members = sorted(groups[group], key=lambda c: c.candidate_key)
        computed = {}
        for cand in members:
            means = category_means(by_cand[cand.candidate_key])
            pos, neg, doc = congruence(means)
            computed[cand.candidate_key] = (means, pos, neg, doc)
        ranks = competition_ranks({k: v[3] for k, v in computed.items()})
        for cand in members:
            means, pos, neg, doc = computed[cand.candidate_key]
            rows.append(
                CandidateScore(
                    candidate_key=cand.candidate_key,
                    lemma_tag=cand.lemma_tag,
                    dmm_id=cand.dmm_id,
                    source=source,
                    category_means=dict(sorted(means.items())),
                    positive_categories=pos,
                    negative_categories=neg,
                    degree_of_congruence=doc,
                    label=label_for(doc),
                    rank=ranks[cand.candidate_key],
                )
            )
    return rows
