"""Run pipeline stages in order. `run --all` is a full offline rebuild.

Each stage reads interim tables, writes interim tables, and never calls a
model: the score stage only reads the response cache. Live scoring is the
separate `score --live` command.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from . import config, tables
from .aggregate import score_candidates
from .chemistry import build_ledger, candidate_coverage, load_lotus
from .config import Paths
from .evaluate import benchmark, load_split
from .export import ExportInput, export_site
from .ingest import ingest
from .reconcile import WcvpIndex, reconcile
from .reproduce import reproduce
from .score import PROMPT_VERSION, ResponseCache, score_comparisons
from .sources import Sources
from .stability import add_stability

STAGES = (
    "ingest",
    "reconcile",
    "reproduce",
    "score",
    "aggregate",
    "stability",
    "chemistry",
    "evaluate",
    "export",
)


class ReproductionFailed(RuntimeError):
    pass


@dataclass
class RunOptions:
    stages: tuple[str, ...] = STAGES
    allow_repro_mismatch: bool = False
    #: Fail if any comparison of a scored name has no cached response.
    strict_cache: bool = False
    synthetic: bool = False


@dataclass
class RunContext:
    paths: Paths
    sources: Sources
    _wcvp: WcvpIndex | None = None
    log: list[str] = field(default_factory=list)

    def say(self, msg: str) -> None:
        self.log.append(msg)
        print(msg)

    def wcvp(self) -> WcvpIndex:
        if self._wcvp is None:
            names = self.sources.path_for("wcvp_names", self.paths.raw)
            dist = self.sources.path_for("wcvp_distribution", self.paths.raw)
            if names is None or not names.exists():
                raise FileNotFoundError(f"WCVP names file not found ({names}); run `download` first")
            self._wcvp = WcvpIndex.load(names, dist)
        return self._wcvp


def _json(path: Path) -> dict | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def stage_ingest(ctx: RunContext) -> None:
    counts = ingest(ctx.paths, ctx.sources)
    ctx.say(f"ingest: {counts}")


def stage_reconcile(ctx: RunContext) -> None:
    interim = ctx.paths.interim
    candidates = tables.read_table(interim, "candidates")
    manual = _json(ctx.paths.manual_wcvp) or {}
    out = reconcile(candidates, ctx.wcvp(), manual=manual)
    tables.write_table(interim, "candidates", out)
    unmatched = [c for c in out if c.wcvp_id is None]
    ctx.say(f"reconcile: {len(out) - len(unmatched)}/{len(out)} candidates matched to WCVP")
    for c in unmatched:
        ctx.say(f"  review by hand: {c.candidate_key}: {c.reconcile_note}")


def stage_reproduce(ctx: RunContext, opts: RunOptions) -> None:
    interim = ctx.paths.interim
    report = reproduce(tables.read_table(interim, "candidates"), tables.read_table(interim, "feature_comparisons"))
    _write_json(interim / "reproduce.json", {
        "checked": report.checked,
        "mismatches": [json.loads(r.model_dump_json()) for r in report.mismatches],
        "gap_values": report.gap_values,
        "ok": report.ok,
    })
    ctx.say(report.summary())
    if not report.ok and not opts.allow_repro_mismatch:
        raise ReproductionFailed(
            "expert-score reproduction failed; fix aggregate.py or ingest.py before any model work"
        )


def stage_score(ctx: RunContext, opts: RunOptions) -> None:
    interim = ctx.paths.interim
    meta = _json(ctx.paths.scoring)
    if meta is None:
        ctx.say("score: no pipeline/config/scoring.json yet; skipping model scores")
        return
    if meta.get("prompt_version") != PROMPT_VERSION:
        ctx.say(
            f"score: cache is for prompt {meta.get('prompt_version')!r}, code is {PROMPT_VERSION!r}; "
            "cache lookups will miss"
        )
    names = tables.read_table(interim, "historical_names")
    plants = tables.read_table(interim, "dmm_plants")
    cands = tables.read_table(interim, "candidates")
    comps = tables.read_table(interim, "feature_comparisons")
    cache = ResponseCache(ctx.paths.cache)
    model = meta["model"]

    scored, report = score_comparisons(comps, names, plants, cands, cache, model=model)
    tables.write_table(interim, "feature_comparisons", scored)
    ctx.say(f"score: {report.cache_hits} cached, {len(report.missing)} not yet scored, "
            f"{len(report.invalid)} invalid answers, {len(report.skipped_no_text)} without text")

    cand_lemma = {c.candidate_key: c.lemma_tag for c in cands}
    scored_lemmas = {cand_lemma[c.candidate_key] for c in scored if c.model_class}
    gaps = [c.comparison_id for c in scored if c.model_class is None and cand_lemma[c.candidate_key] in scored_lemmas]
    if gaps:
        msg = f"score: {len(gaps)} comparisons missing for names that were scored, e.g. {gaps[:5]}"
        if opts.strict_cache:
            raise LookupError(msg)
        ctx.say(msg)

    if meta.get("memorisation"):
        unm, rep = score_comparisons(comps, names, plants, cands, cache, model=model, unmasked=True)
        tables.write_table(interim, "feature_comparisons_unmasked", unm)
        ctx.say(f"score (unmasked): {rep.cache_hits} cached")


def stage_aggregate(ctx: RunContext) -> None:
    interim = ctx.paths.interim
    cands = tables.read_table(interim, "candidates")
    comps = tables.read_table(interim, "feature_comparisons")
    rows = score_candidates(cands, comps, "expert") + score_candidates(cands, comps, "model")
    tables.write_table(interim, "candidate_scores", rows)
    ctx.say(f"aggregate: {sum(r.source == 'expert' for r in rows)} expert, "
            f"{sum(r.source == 'model' for r in rows)} model candidate scores")


def feature_categories(comparisons) -> list[str]:
    cats = sorted({c.category for c in comparisons})
    if len(cats) != config.N_FEATURE_CATEGORIES:
        raise ValueError(
            f"expected {config.N_FEATURE_CATEGORIES} feature categories, found {len(cats)}: {cats}"
        )
    return cats


def stage_stability(ctx: RunContext) -> None:
    interim = ctx.paths.interim
    comps = tables.read_table(interim, "feature_comparisons")
    scores = tables.read_table(interim, "candidate_scores")
    rows = add_stability(scores, comps, feature_categories(comps))
    tables.write_table(interim, "candidate_scores", rows)
    ctx.say(f"stability: {config.N_RESAMPLES} resamples, seed {config.RANDOM_SEED}")


def stage_chemistry(ctx: RunContext) -> None:
    interim = ctx.paths.interim
    cands = tables.read_table(interim, "candidates")
    lotus = ctx.sources.path_for("lotus", ctx.paths.raw)
    if lotus is None or not lotus.exists():
        raise FileNotFoundError(f"LOTUS export not found ({lotus}); run `download` first")
    wanted = {c.wcvp_id for c in cands if c.wcvp_id}
    records = load_lotus(lotus, ctx.wcvp(), wanted)
    ledger = build_ledger(cands, records)
    tables.write_table(interim, "compound_records", records)
    tables.write_table(interim, "compound_ledger", ledger)
    ctx.say(f"chemistry: {len(records)} compound records, {len(ledger)} ledger entries")


def stage_evaluate(ctx: RunContext) -> None:
    interim = ctx.paths.interim
    cands = tables.read_table(interim, "candidates")
    comps = tables.read_table(interim, "feature_comparisons")
    scores = tables.read_table(interim, "candidate_scores")
    unmasked = (
        tables.read_table(interim, "feature_comparisons_unmasked")
        if tables.has_table(interim, "feature_comparisons_unmasked")
        else None
    )
    result = benchmark(
        comps,
        scores,
        load_split(ctx.paths.split),
        {c.candidate_key: c.lemma_tag for c in cands},
        unmasked=unmasked,
    )
    _write_json(interim / "benchmark.json", result)
    ctx.say(f"evaluate: partitions {sorted(result['partitions'])}")


def stage_export(ctx: RunContext, opts: RunOptions) -> None:
    interim = ctx.paths.interim

    def maybe(name: str) -> list:
        return tables.read_table(interim, name) if tables.has_table(interim, name) else []

    cands = maybe("candidates")
    records = maybe("compound_records")
    data = ExportInput(
        names=maybe("historical_names"),
        dmm_plants=maybe("dmm_plants"),
        candidates=cands,
        comparisons=maybe("feature_comparisons"),
        scores=maybe("candidate_scores"),
        ledger=maybe("compound_ledger"),
        lotus_coverage=candidate_coverage(cands, records),
        benchmark=_json(interim / "benchmark.json"),
        reproduce=_json(interim / "reproduce.json"),
        sources=ctx.sources.manifest(),
        split=load_split(ctx.paths.split),
        scoring=_json(ctx.paths.scoring),
        synthetic=opts.synthetic,
    )
    counts = export_site(data, ctx.paths.site_data)
    ctx.say(f"export: {counts['names']} names to {ctx.paths.site_data}")


def run(paths: Paths, opts: RunOptions | None = None) -> RunContext:
    opts = opts or RunOptions()
    unknown = set(opts.stages) - set(STAGES)
    if unknown:
        raise ValueError(f"unknown stages {sorted(unknown)}")
    ctx = RunContext(paths=paths, sources=Sources.load(paths.sources))
    for stage in STAGES:
        if stage not in opts.stages:
            continue
        if stage == "ingest":
            stage_ingest(ctx)
        elif stage == "reconcile":
            stage_reconcile(ctx)
        elif stage == "reproduce":
            stage_reproduce(ctx, opts)
        elif stage == "score":
            stage_score(ctx, opts)
        elif stage == "aggregate":
            stage_aggregate(ctx)
        elif stage == "stability":
            stage_stability(ctx)
        elif stage == "chemistry":
            stage_chemistry(ctx)
        elif stage == "evaluate":
            stage_evaluate(ctx)
        elif stage == "export":
            stage_export(ctx, opts)
    return ctx
