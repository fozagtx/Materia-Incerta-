"""Benchmark model scoring against the published expert scoring.

Every number here is agreement with expert scoring. No ground truth exists for
these identifications, so nothing here measures accuracy.

Also holds the tuning/held-out split. The split is assigned once, by
historical name, and written to pipeline/config/split.json; assign_split()
refuses to overwrite it.
"""

from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from collections.abc import Sequence
from pathlib import Path

from . import config
from .schemas import CandidateScore, FeatureComparison, MatchClass, Split

#: Ordinal order for weighted kappa, from the score values (-2, 0, 1, 2).
#: Linear weights on rank, not on score. Confirm before the held-out run.
CLASS_ORDER: tuple[MatchClass, ...] = ("no_match", "absent", "partial", "good")

#: Proposed bars from the PRD. Fix these before the held-out run.
BARS = {
    "detail_kappa_min": 0.6,
    "invented_evidence_max": 0.10,
}


# ---------------------------------------------------------------------------
# Split
# ---------------------------------------------------------------------------


def assign_split(
    lemma_tags: Sequence[str], path: Path, *, n_tuning: int = 10, seed: int = config.RANDOM_SEED
) -> Split:
    """Assign names to tuning and held-out partitions once, then commit the file."""
    if path.exists():
        raise FileExistsError(
            f"{path} exists. The split is fixed; changing it needs team sign-off (AGENTS.md)."
        )
    tags = sorted(set(lemma_tags))
    if len(tags) <= n_tuning:
        raise ValueError(f"need more than {n_tuning} names, got {len(tags)}")
    rng = random.Random(seed)
    tuning = sorted(rng.sample(tags, n_tuning))
    held_out = sorted(t for t in tags if t not in tuning)
    split = Split(seed=seed, tuning=tuple(tuning), held_out=tuple(held_out))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(split.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return split


def load_split(path: Path) -> Split | None:
    if not path.exists():
        return None
    return Split.model_validate_json(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


def cohen_kappa(a: Sequence[str], b: Sequence[str], order: Sequence[str], weighted: bool) -> float | None:
    """Cohen's kappa; linear weights on category rank when `weighted`."""
    if len(a) != len(b):
        raise ValueError("length mismatch")
    n = len(a)
    if n == 0:
        return None
    k = len(order)
    pos = {c: i for i, c in enumerate(order)}
    obs = [[0.0] * k for _ in range(k)]
    for x, y in zip(a, b):
        obs[pos[x]][pos[y]] += 1
    row = [sum(r) for r in obs]
    col = [sum(obs[i][j] for i in range(k)) for j in range(k)]

    def w(i: int, j: int) -> float:
        if weighted:
            return abs(i - j) / (k - 1)
        return 0.0 if i == j else 1.0

    observed = sum(w(i, j) * obs[i][j] for i in range(k) for j in range(k)) / n
    expected = sum(w(i, j) * row[i] * col[j] for i in range(k) for j in range(k)) / (n * n)
    if expected == 0:
        return 1.0 if observed == 0 else None
    return 1.0 - observed / expected


def detail_agreement(comparisons: Sequence[FeatureComparison]) -> dict:
    pairs = [(c.expert_class, c.model_class) for c in comparisons if c.expert_class and c.model_class]
    exp = [p[0] for p in pairs]
    mod = [p[1] for p in pairs]
    baseline = ["good"] * len(exp)
    share_good = (Counter(exp)["good"] / len(exp)) if exp else None
    return {
        "n": len(pairs),
        "kappa_weighted": cohen_kappa(exp, mod, CLASS_ORDER, weighted=True),
        "kappa_unweighted": cohen_kappa(exp, mod, CLASS_ORDER, weighted=False),
        "exact_agreement": (sum(e == m for e, m in pairs) / len(pairs)) if pairs else None,
        "baseline_always_good_exact": share_good,
        "baseline_always_good_kappa_weighted": cohen_kappa(exp, baseline, CLASS_ORDER, weighted=True),
        "confusion": {
            e: {m: sum(1 for x, y in pairs if x == e and y == m) for m in CLASS_ORDER}
            for e in CLASS_ORDER
        },
    }


def invented_evidence(comparisons: Sequence[FeatureComparison]) -> dict:
    """How often the model claims a match where experts marked the detail absent."""
    absent = [c for c in comparisons if c.expert_class == "absent" and c.model_class]
    matches = [c for c in absent if c.model_class in ("good", "partial")]
    any_claim = [c for c in absent if c.model_class != "absent"]
    n = len(absent)
    return {
        "n_expert_absent": n,
        "match_claim_rate": len(matches) / n if n else None,
        "any_claim_rate": len(any_claim) / n if n else None,
        "comparison_ids": sorted(c.comparison_id for c in matches),
    }


def label_agreement(expert: Sequence[CandidateScore], model: Sequence[CandidateScore]) -> dict:
    exp = {s.candidate_key: s.label for s in expert}
    mod = {s.candidate_key: s.label for s in model}
    keys = sorted(set(exp) & set(mod))
    order = {lab: i for i, lab in enumerate(config.LABEL_ORDER)}
    exact = sum(exp[k] == mod[k] for k in keys)
    within = sum(abs(order[exp[k]] - order[mod[k]]) <= 1 for k in keys)
    moderate = sum(exp[k] == "Moderate" for k in keys)
    n = len(keys)
    return {
        "n": n,
        "exact": exact / n if n else None,
        "within_one": within / n if n else None,
        "baseline_always_moderate_exact": moderate / n if n else None,
        "disagreements": [
            {"candidate_key": k, "expert": exp[k], "model": mod[k]} for k in keys if exp[k] != mod[k]
        ],
    }


def _groups(scores: Sequence[CandidateScore]) -> dict[tuple[str, str], list[CandidateScore]]:
    g: dict[tuple[str, str], list[CandidateScore]] = defaultdict(list)
    for s in scores:
        g[(s.lemma_tag, s.dmm_id)].append(s)
    return g


def ranking_agreement(expert: Sequence[CandidateScore], model: Sequence[CandidateScore]) -> dict:
    """Top-candidate agreement on groups with several candidates.

    A group agrees when the model's top set and the expert top set overlap.
    The random baseline is the expected agreement of a uniformly random top pick.
    """
    eg, mg = _groups(expert), _groups(model)
    rows = []
    for key in sorted(set(eg) & set(mg)):
        e, m = eg[key], mg[key]
        if len(e) < 2 or {s.candidate_key for s in e} != {s.candidate_key for s in m}:
            continue
        e_top = {s.candidate_key for s in e if s.rank == 1}
        m_top = {s.candidate_key for s in m if s.rank == 1}
        rows.append(
            {
                "lemma_tag": key[0],
                "dmm_id": key[1],
                "n_candidates": len(e),
                "agree": bool(e_top & m_top),
                "random_baseline": len(e_top) / len(e),
            }
        )
    n = len(rows)
    return {
        "n_groups": n,
        "top_agreement": sum(r["agree"] for r in rows) / n if n else None,
        "baseline_random": sum(r["random_baseline"] for r in rows) / n if n else None,
        "groups": rows,
    }


def stability_summary(scores: Sequence[CandidateScore]) -> dict:
    """Share of multi-candidate groups whose unique top candidate keeps first
    place in at least STABLE_TOP_SHARE of resamples. Groups with a tie at the
    top have no unique top candidate and count as not stable."""
    rows = []
    for (lemma, dmm), members in sorted(_groups(scores).items()):
        if len(members) < 2:
            continue
        tops = [s for s in members if s.rank == 1]
        share = tops[0].first_rank_share if len(tops) == 1 else None
        rows.append(
            {
                "lemma_tag": lemma,
                "dmm_id": dmm,
                "top_candidate": tops[0].candidate_key if len(tops) == 1 else None,
                "first_rank_share": share,
                "stable": share is not None and share >= config.STABLE_TOP_SHARE,
            }
        )
    n = len(rows)
    return {
        "threshold": config.STABLE_TOP_SHARE,
        "n_groups": n,
        "stable_share": sum(r["stable"] for r in rows) / n if n else None,
        "groups": rows,
    }


def memorisation_gap(masked: Sequence[FeatureComparison], unmasked: Sequence[FeatureComparison]) -> dict:
    """Agreement with experts for masked vs unmasked runs on the same items."""
    m = detail_agreement(masked)
    u = detail_agreement(unmasked)
    gap = None
    if m["kappa_weighted"] is not None and u["kappa_weighted"] is not None:
        gap = u["kappa_weighted"] - m["kappa_weighted"]
    return {"masked": m, "unmasked": u, "kappa_gap": gap}


def benchmark(
    comparisons: Sequence[FeatureComparison],
    scores: Sequence[CandidateScore],
    split: Split | None,
    cand_lemma: dict[str, str],
    *,
    unmasked: Sequence[FeatureComparison] | None = None,
) -> dict:
    """All benchmark tables, reported separately for each partition."""
    expert = [s for s in scores if s.source == "expert"]
    model = [s for s in scores if s.source == "model"]

    def part(lemma: str) -> str:
        if split is None:
            return "unsplit"
        return split.partition_of(lemma) or "unassigned"

    partitions: dict[str, dict] = {}
    names = sorted({part(lm) for lm in cand_lemma.values()} | {part(s.lemma_tag) for s in scores})
    for p in names:
        comps = [c for c in comparisons if part(cand_lemma[c.candidate_key]) == p]
        exp_p = [s for s in expert if part(s.lemma_tag) == p]
        mod_p = [s for s in model if part(s.lemma_tag) == p]
        partitions[p] = {
            "detail": detail_agreement(comps),
            "invented_evidence": invented_evidence(comps),
            "labels": label_agreement(exp_p, mod_p),
            "ranking": ranking_agreement(exp_p, mod_p),
            "stability_expert": stability_summary(exp_p),
            "stability_model": stability_summary(mod_p) if mod_p else None,
        }
        if unmasked is not None:
            unm = [c for c in unmasked if part(cand_lemma[c.candidate_key]) == p]
            ids = {c.comparison_id for c in unm if c.model_class}
            partitions[p]["memorisation"] = memorisation_gap(
                [c for c in comps if c.comparison_id in ids], unm
            )

    return {
        "wording": "Agreement with published expert scoring. Not accuracy: no ground truth exists.",
        "bars": BARS,
        "class_order": list(CLASS_ORDER),
        "split": None if split is None else json.loads(split.model_dump_json()),
        "partitions": partitions,
    }
