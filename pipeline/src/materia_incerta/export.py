"""Write the JSON the static site reads (client/public/data/).

Files:
- manifest.json   versions, seed, constants, sources and licences
- index.json      one row per historical name for the name index
- names/<lemma_tag>.json   the full plant case
- benchmark.json  evaluation tables and the reproduction check

Output is deterministic: sorted keys, no timestamps. Source text and model
reasons are left out unless republishing is allowed (config.REPUBLISH_SOURCE_TEXT).
"""

from __future__ import annotations

import json
import re
import shutil
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from . import __version__, config
from .schemas import (
    Candidate,
    CandidateScore,
    DmmPlant,
    FeatureComparison,
    HistoricalName,
    LedgerEntry,
    Split,
)

SAFE_SLUG = re.compile(r"^[A-Za-z0-9._-]+$")


@dataclass
class ExportInput:
    names: Sequence[HistoricalName] = ()
    dmm_plants: Sequence[DmmPlant] = ()
    candidates: Sequence[Candidate] = ()
    comparisons: Sequence[FeatureComparison] = ()
    scores: Sequence[CandidateScore] = ()
    ledger: Sequence[LedgerEntry] = ()
    lotus_coverage: dict[str, int] = field(default_factory=dict)
    benchmark: dict | None = None
    reproduce: dict | None = None
    sources: list[dict] = field(default_factory=list)
    split: Split | None = None
    scoring: dict | None = None
    synthetic: bool = False
    republish_text: bool = config.REPUBLISH_SOURCE_TEXT


def _write(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _score_view(s: CandidateScore | None) -> dict | None:
    if s is None:
        return None
    return {
        "degree_of_congruence": s.degree_of_congruence,
        "positive_categories": s.positive_categories,
        "negative_categories": s.negative_categories,
        "category_means": s.category_means,
        "label": s.label,
        "rank": s.rank,
        "label_share": s.label_share,
        "label_distribution": s.label_distribution,
        "first_rank_share": s.first_rank_share,
        "rank_distribution": s.rank_distribution,
    }


def _badge(expert_scores: Sequence[CandidateScore]) -> dict | None:
    """Index badge from expert-score stability.

    For names with several candidates for a DMM plant: the lowest first-rank
    share of a unique top candidate across those plants. A tie at the top
    gives kind "tied" and share 0. Otherwise: the lowest label share among
    its candidates.
    """
    if not expert_scores:
        return None
    groups: dict[str, list[CandidateScore]] = defaultdict(list)
    for s in expert_scores:
        groups[s.dmm_id].append(s)
    multi = [g for g in groups.values() if len(g) > 1]
    if multi:
        shares = []
        tied = False
        for g in multi:
            tops = [s for s in g if s.rank == 1]
            if len(tops) == 1:
                shares.append(tops[0].first_rank_share or 0.0)
            else:
                tied = True
                shares.append(0.0)
        kind, share = ("tied" if tied else "first_rank"), min(shares)
    else:
        kind, share = "label", min(s.label_share or 0.0 for s in expert_scores)
    level = "high" if share >= config.STABLE_TOP_SHARE else "medium" if share >= 0.5 else "low"
    return {"kind": kind, "share": round(share, 6), "level": level}


def export_site(data: ExportInput, out: Path) -> dict[str, int]:
    names_dir = out / "names"
    if names_dir.exists():
        shutil.rmtree(names_dir)
    names_dir.mkdir(parents=True, exist_ok=True)

    plants = {p.dmm_id: p for p in data.dmm_plants}
    cands_by_lemma: dict[str, list[Candidate]] = defaultdict(list)
    for c in data.candidates:
        cands_by_lemma[c.lemma_tag].append(c)
    scores: dict[tuple[str, str], CandidateScore] = {(s.candidate_key, s.source): s for s in data.scores}
    comps_by_cand: dict[str, list[FeatureComparison]] = defaultdict(list)
    for comp in data.comparisons:
        comps_by_cand[comp.candidate_key].append(comp)
    ledger_by_lemma: dict[str, list[LedgerEntry]] = defaultdict(list)
    for e in data.ledger:
        ledger_by_lemma[e.lemma_tag].append(e)
    text = data.republish_text

    index_rows = []
    for name in sorted(data.names, key=lambda n: n.lemma_tag):
        if not SAFE_SLUG.match(name.lemma_tag):
            raise ValueError(f"lemma tag {name.lemma_tag!r} is not safe as a file name")
        cands = sorted(cands_by_lemma[name.lemma_tag], key=lambda c: c.candidate_key)
        plant_views = []
        for dmm_id in name.dmm_ids:
            plant = plants.get(dmm_id)
            members = [c for c in cands if c.dmm_id == dmm_id]
            members.sort(
                key=lambda c: (
                    scores.get((c.candidate_key, "expert")).rank if (c.candidate_key, "expert") in scores else 999,
                    c.candidate_key,
                )
            )
            cand_views = []
            evidence = []
            for c in members:
                cand_views.append(
                    {
                        "candidate_key": c.candidate_key,
                        "source_name": c.source_name,
                        "wcvp_id": c.wcvp_id,
                        "accepted_name": c.accepted_name,
                        "in_east_med": c.in_east_med,
                        "hazard": c.hazard,
                        "reconcile_note": c.reconcile_note,
                        "paper_label": c.paper_label,
                        "expert": _score_view(scores.get((c.candidate_key, "expert"))),
                        "model": _score_view(scores.get((c.candidate_key, "model"))),
                        "lotus_compounds": data.lotus_coverage.get(c.wcvp_id) if c.wcvp_id else None,
                        "has_lotus_data": (
                            c.wcvp_id is not None
                            and data.lotus_coverage.get(c.wcvp_id, 0) >= config.LOTUS_MIN_RECORDS
                        ),
                    }
                )
                for comp in sorted(comps_by_cand[c.candidate_key], key=lambda x: (x.category, x.comparison_id)):
                    evidence.append(
                        {
                            "comparison_id": comp.comparison_id,
                            "candidate_key": comp.candidate_key,
                            "category": comp.category,
                            "ancient_detail_id": comp.ancient_detail_id,
                            "ancient_text": comp.ancient_text if text else None,
                            "modern_text": comp.modern_text if text else None,
                            "comparative": comp.comparative,
                            "expert_class": comp.expert_class,
                            "model_class": comp.model_class,
                            "model_reason": comp.model_reason if text else None,
                        }
                    )
            plant_views.append(
                {
                    "dmm_id": dmm_id,
                    "chapter": plant.chapter if plant else None,
                    "plant_type": plant.plant_type if plant else None,
                    "detail_level": plant.detail_level if plant else None,
                    "details": [
                        {
                            "detail_id": d.detail_id,
                            "category": d.category,
                            "text": d.text if text else None,
                            "comparative": d.comparative,
                        }
                        for d in (plant.details if plant else ())
                    ],
                    "candidates": cand_views,
                    "evidence": evidence,
                }
            )

        ledger = sorted(
            ledger_by_lemma[name.lemma_tag],
            key=lambda e: ({"robust": 0, "id_dependent": 1, "no_data": 2}[e.label], e.compound_name or "", e.inchikey),
        )
        case = {
            "lemma_tag": name.lemma_tag,
            "greek_name": name.greek_name,
            "transliteration": name.transliteration,
            "partition": data.split.partition_of(name.lemma_tag) if data.split else None,
            "text_withheld": not text,
            "dmm_plants": plant_views,
            "ledger": {
                "min_records": config.LOTUS_MIN_RECORDS,
                "counts": {
                    lab: sum(1 for e in ledger if e.label == lab) for lab in ("robust", "id_dependent", "no_data")
                },
                "entries": [json.loads(e.model_dump_json()) for e in ledger],
            },
        }
        _write(names_dir / f"{name.lemma_tag}.json", case)

        expert_scores = [scores[(c.candidate_key, "expert")] for c in cands if (c.candidate_key, "expert") in scores]
        index_rows.append(
            {
                "lemma_tag": name.lemma_tag,
                "greek_name": name.greek_name,
                "transliteration": name.transliteration,
                "dmm_ids": list(name.dmm_ids),
                "candidate_count": len(cands),
                "hazard": any(c.hazard for c in cands),
                "has_model_scores": any((c.candidate_key, "model") in scores for c in cands),
                "stability": _badge(expert_scores),
            }
        )

    _write(out / "index.json", {"names": index_rows})
    _write(
        out / "benchmark.json",
        {
            "status": "ready" if data.benchmark else "not_run",
            "benchmark": data.benchmark,
            "reproduce": data.reproduce,
        },
    )
    _write(
        out / "manifest.json",
        {
            "pipeline_version": __version__,
            "synthetic": data.synthetic,
            "text_withheld": not text,
            "counts": {
                "names": len(data.names),
                "dmm_plants": len(data.dmm_plants),
                "candidates": len(data.candidates),
                "comparisons": len(data.comparisons),
            },
            "constants": {
                "match_scores": config.MATCH_SCORES,
                "strong_min": config.STRONG_MIN,
                "moderate_min": config.MODERATE_MIN,
                "moderate_max": config.MODERATE_MAX,
                "n_resamples": config.N_RESAMPLES,
                "random_seed": config.RANDOM_SEED,
                "stable_top_share": config.STABLE_TOP_SHARE,
                "lotus_min_records": config.LOTUS_MIN_RECORDS,
                "east_med_areas": sorted(config.EAST_MED_AREAS),
            },
            "scoring": data.scoring,
            "sources": data.sources,
        },
    )
    return {"names": len(index_rows)}
