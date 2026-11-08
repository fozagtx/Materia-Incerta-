"""Measure how stable each label and ranking is under resampling.

For each (lemma_tag, dmm_id) group, draw the feature categories with
replacement (as many draws as there are categories), recompute every
candidate's degree of congruence from the drawn categories, then relabel and
rerank. The same draws are applied to every candidate in the group, and to the
expert and model scores, so the comparisons are paired.

Outputs per candidate:
- label_share: share of resamples that keep the full-data label
- label_distribution: share of resamples in each label
- first_rank_share: share of resamples in which the candidate ranks first,
  with ties at the top splitting the credit equally, so shares in a group sum to 1
- rank_distribution: share of resamples at each competition rank (ties share a rank)

First-rank share describes sensitivity to which features are counted. It is
not the probability that an identification is correct.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from collections.abc import Sequence

import numpy as np

from . import config
from .aggregate import category_means, classes_by_candidate
from .schemas import CandidateScore, FeatureComparison

_LABELS = np.array(["Weak", "Moderate", "Strong"])


def _group_seed(seed: int, lemma_tag: str, dmm_id: str) -> np.random.SeedSequence:
    digest = hashlib.sha256(f"{lemma_tag}|{dmm_id}".encode()).hexdigest()
    return np.random.SeedSequence([seed, int(digest[:16], 16)])


def _labels(doc: np.ndarray) -> np.ndarray:
    """Vectorised label_for() for integer DoC values."""
    if not np.all(doc == np.round(doc)):
        raise ValueError("resampled DoC must be integer")
    idx = np.where(doc >= config.STRONG_MIN, 2, np.where(doc >= config.MODERATE_MIN, 1, 0))
    return _LABELS[idx]


def resample_group(
    signs: np.ndarray,
    *,
    n_resamples: int,
    rng: np.random.Generator,
) -> dict[str, np.ndarray]:
    """Resample one group.

    signs: (n_candidates, n_categories) array of -1, 0, +1 (sign of each
    category mean). Returns doc (n_resamples, n_candidates), labels of the
    same shape, ranks of the same shape and first-rank credit of the same shape.
    """
    n_cand, n_cat = signs.shape
    # Drawing n_cat categories with replacement == multinomial counts.
    weights = rng.multinomial(n_cat, np.full(n_cat, 1.0 / n_cat), size=n_resamples)
    doc = weights @ signs.T  # (n_resamples, n_cand)
    labels = _labels(doc)
    # Competition rank: 1 + number of candidates with a strictly higher DoC.
    ranks = 1 + (doc[:, None, :] > doc[:, :, None]).sum(axis=2)
    top = doc == doc.max(axis=1, keepdims=True)
    credit = top / top.sum(axis=1, keepdims=True)
    return {"doc": doc, "labels": labels, "ranks": ranks, "credit": credit}


def add_stability(
    scores: Sequence[CandidateScore],
    comparisons: Sequence[FeatureComparison],
    categories: Sequence[str],
    *,
    n_resamples: int = config.N_RESAMPLES,
    seed: int = config.RANDOM_SEED,
) -> list[CandidateScore]:
    """Return copies of `scores` with the stability fields filled in."""
    if not categories:
        raise ValueError("no feature categories")
    categories = sorted(categories)

    out: list[CandidateScore] = []
    by_source: dict[str, list[CandidateScore]] = defaultdict(list)
    for s in scores:
        by_source[s.source].append(s)

    for source in sorted(by_source):
        source_scores = by_source[source]
        classes = classes_by_candidate(comparisons, source)  # type: ignore[arg-type]
        groups: dict[tuple[str, str], list[CandidateScore]] = defaultdict(list)
        for s in source_scores:
            groups[(s.lemma_tag, s.dmm_id)].append(s)

        for (lemma_tag, dmm_id) in sorted(groups):
            members = sorted(groups[(lemma_tag, dmm_id)], key=lambda s: s.candidate_key)
            signs = np.zeros((len(members), len(categories)), dtype=np.int64)
            for i, s in enumerate(members):
                means = category_means(classes[s.candidate_key])
                unknown = set(means) - set(categories)
                if unknown:
                    raise ValueError(f"{s.candidate_key}: categories not in list: {sorted(unknown)}")
                for j, cat in enumerate(categories):
                    m = means.get(cat, 0.0)
                    signs[i, j] = (m > 0) - (m < 0)
            # Sanity: the full-data DoC must equal the sum of signs.
            for i, s in enumerate(members):
                if int(signs[i].sum()) != s.degree_of_congruence:
                    raise AssertionError(f"{s.candidate_key}: DoC mismatch in stability")

            rng = np.random.default_rng(_group_seed(seed, lemma_tag, dmm_id))
            res = resample_group(signs, n_resamples=n_resamples, rng=rng)
            n_cand = len(members)
            for i, s in enumerate(members):
                labels_i = res["labels"][:, i]
                ranks_i = res["ranks"][:, i]
                label_dist = {lab: float(np.mean(labels_i == lab)) for lab in config.LABEL_ORDER}
                rank_dist = {
                    str(r): float(np.mean(ranks_i == r)) for r in range(1, n_cand + 1)
                }
                out.append(
                    s.model_copy(
                        update={
                            "label_share": round(label_dist[s.label], 6),
                            "label_distribution": {k: round(v, 6) for k, v in label_dist.items()},
                            "first_rank_share": round(float(res["credit"][:, i].mean()), 6),
                            "rank_distribution": {
                                k: round(v, 6) for k, v in rank_dist.items() if v > 0
                            },
                        }
                    )
                )
    return out
