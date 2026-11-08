"""Recompute the paper's labels from its own expert scores.

This is the check that aggregate.py implements the paper's method. It runs
before any model work, and `run --all` stops if it fails.
"""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel

from . import config
from .aggregate import ThresholdGapError, score_candidates
from .schemas import Candidate, FeatureComparison, Label


class ReproRow(BaseModel):
    candidate_key: str
    paper_doc: float | None
    computed_doc: int | None
    paper_label: Label | None
    computed_label: Label | None
    doc_match: bool | None
    label_match: bool | None
    note: str | None = None


class ReproReport(BaseModel):
    rows: list[ReproRow]
    #: Paper DoC values strictly between Moderate's max and Strong's min.
    gap_values: list[tuple[str, float]]

    @property
    def checked(self) -> int:
        return sum(1 for r in self.rows if r.label_match is not None)

    @property
    def mismatches(self) -> list[ReproRow]:
        return [r for r in self.rows if r.label_match is False or r.doc_match is False]

    @property
    def ok(self) -> bool:
        return self.checked > 0 and not self.mismatches

    def summary(self) -> str:
        lines = [
            f"reproduce: {self.checked} candidate labels checked, "
            f"{len(self.mismatches)} mismatches"
        ]
        for r in self.mismatches[:20]:
            lines.append(
                f"  {r.candidate_key}: paper {r.paper_label} ({r.paper_doc}) "
                f"vs computed {r.computed_label} ({r.computed_doc}) {r.note or ''}".rstrip()
            )
        if self.gap_values:
            lines.append(
                f"  {len(self.gap_values)} paper DoC values lie between "
                f"{config.MODERATE_MAX} and {config.STRONG_MIN}: see docs/open-questions.md Q1"
            )
        return "\n".join(lines)


def reproduce(
    candidates: Sequence[Candidate], comparisons: Sequence[FeatureComparison]
) -> ReproReport:
    try:
        scores = {s.candidate_key: s for s in score_candidates(candidates, comparisons, "expert")}
        gap_error = None
    except ThresholdGapError as exc:  # pragma: no cover - integer DoC cannot hit the gap
        scores, gap_error = {}, str(exc)

    rows: list[ReproRow] = []
    gaps: list[tuple[str, float]] = []
    for cand in sorted(candidates, key=lambda c: c.candidate_key):
        if cand.paper_doc is not None and config.MODERATE_MAX < cand.paper_doc < config.STRONG_MIN:
            gaps.append((cand.candidate_key, cand.paper_doc))
        s = scores.get(cand.candidate_key)
        if cand.paper_label is None and cand.paper_doc is None:
            continue
        if s is None:
            rows.append(
                ReproRow(
                    candidate_key=cand.candidate_key,
                    paper_doc=cand.paper_doc,
                    computed_doc=None,
                    paper_label=cand.paper_label,
                    computed_label=None,
                    doc_match=False if cand.paper_doc is not None else None,
                    label_match=False if cand.paper_label is not None else None,
                    note=gap_error or "no complete expert scores",
                )
            )
            continue
        rows.append(
            ReproRow(
                candidate_key=cand.candidate_key,
                paper_doc=cand.paper_doc,
                computed_doc=s.degree_of_congruence,
                paper_label=cand.paper_label,
                computed_label=s.label,
                doc_match=None if cand.paper_doc is None else cand.paper_doc == s.degree_of_congruence,
                label_match=None if cand.paper_label is None else cand.paper_label == s.label,
            )
        )
    return ReproReport(rows=rows, gap_values=gaps)
