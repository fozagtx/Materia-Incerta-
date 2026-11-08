"""Command line: `python -m materia_incerta <command>`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import tables
from .config import Paths
from .run import STAGES, RunOptions, run


def _cmd_run(args: argparse.Namespace, paths: Paths) -> int:
    if args.all:
        stages = STAGES
    elif args.stage:
        stages = tuple(args.stage)
    else:
        print("pass --all or one or more --stage", file=sys.stderr)
        return 2
    if args.skip_ingest:
        stages = tuple(s for s in stages if s != "ingest")
    run(
        paths,
        RunOptions(
            stages=stages,
            allow_repro_mismatch=args.allow_repro_mismatch,
            strict_cache=args.strict_cache,
        ),
    )
    return 0


def _cmd_download(args: argparse.Namespace, paths: Paths) -> int:
    from .download import download
    from .sources import Sources

    report = download(Sources.load(paths.sources), paths.raw, only=set(args.only or []) or None, force=args.force)
    for key, items in report.items():
        for item in items:
            print(f"{key}: {item}")
    if report["no_url"]:
        print(f"{len(report['no_url'])} file(s) have no URL in {paths.sources}", file=sys.stderr)
    return 0


def _cmd_split(args: argparse.Namespace, paths: Paths) -> int:
    from .evaluate import assign_split

    names = tables.read_table(paths.interim, "historical_names")
    split = assign_split([n.lemma_tag for n in names], paths.split)
    print(f"wrote {paths.split}: {len(split.tuning)} tuning, {len(split.held_out)} held out. Commit it.")
    return 0


def _cmd_score(args: argparse.Namespace, paths: Paths) -> int:
    """Live scoring. Restricted to the tuning partition unless --held-out-run."""
    from .evaluate import load_split
    from .score import PROMPT_VERSION, ResponseCache, client_from_env, score_comparisons

    split = load_split(paths.split)
    if split is None:
        print("assign and commit the split first: python -m materia_incerta split", file=sys.stderr)
        return 2
    partition = "held_out" if args.held_out_run else "tuning"
    lemmas = set(split.held_out if args.held_out_run else split.tuning)
    if args.names:
        wanted = set(args.names.split(","))
        outside = wanted - lemmas
        if outside:
            print(f"not in the {partition} partition: {sorted(outside)}", file=sys.stderr)
            return 2
        lemmas = wanted
    elif not args.confirm_full_run:
        print(
            f"scoring all {len(lemmas)} {partition} names is a full pass; "
            "AGENTS.md says to ask first. Re-run with --confirm-full-run, or pass --names.",
            file=sys.stderr,
        )
        return 2
    if args.held_out_run and not args.reason:
        print("--held-out-run needs --reason (recorded in the run log)", file=sys.stderr)
        return 2

    try:
        client = client_from_env()
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    names = tables.read_table(paths.interim, "historical_names")
    plants = tables.read_table(paths.interim, "dmm_plants")
    cands = tables.read_table(paths.interim, "candidates")
    comps = tables.read_table(paths.interim, "feature_comparisons")
    cache = ResponseCache(paths.cache)
    _, report = score_comparisons(
        comps, names, plants, cands, cache,
        model=client.model, client=client, only_lemmas=lemmas, unmasked=args.unmasked,
    )
    paths.scoring.parent.mkdir(parents=True, exist_ok=True)
    meta = json.loads(paths.scoring.read_text()) if paths.scoring.exists() else {}
    meta.update({"model": client.model, "prompt_version": PROMPT_VERSION})
    if args.unmasked:
        meta["memorisation"] = True
    paths.scoring.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
    with paths.run_log.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "partition": partition,
            "names": sorted(lemmas),
            "model": client.model,
            "prompt_version": PROMPT_VERSION,
            "unmasked": args.unmasked,
            "live_calls": report.live_calls,
            "cache_hits": report.cache_hits,
            "invalid": len(report.invalid),
            "reason": args.reason,
        }, sort_keys=True) + "\n")
    print(f"score: {report.live_calls} live calls, {report.cache_hits} cached, "
          f"{report.scored} valid, {len(report.invalid)} invalid answers")
    return 0


def _cmd_export(args: argparse.Namespace, paths: Paths) -> int:
    run(paths, RunOptions(stages=("export",)))
    return 0


def _cmd_demo(args: argparse.Namespace, paths: Paths) -> int:
    from .demo import run_demo

    root = paths.root / "data" / "demo"
    out = Path(args.out) if args.out else paths.site_data
    run_demo(root, site_data=out)
    print(f"synthetic demo exported to {out}. Run `python -m materia_incerta export` to restore.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="materia_incerta")
    p.add_argument("--root", help="repo root (default: this checkout)")
    sub = p.add_subparsers(dest="command", required=True)

    r = sub.add_parser("run", help="run pipeline stages offline from the response cache")
    r.add_argument("--all", action="store_true", help="every stage, in order")
    r.add_argument("--stage", action="append", choices=STAGES)
    r.add_argument("--skip-ingest", action="store_true", help="start from existing interim tables")
    r.add_argument("--allow-repro-mismatch", action="store_true")
    r.add_argument("--strict-cache", action="store_true", help="fail on missing cached responses")
    r.set_defaults(func=_cmd_run)

    d = sub.add_parser("download", help="fetch files listed in pipeline/sources.toml")
    d.add_argument("--only", action="append", help="source key, e.g. wcvp")
    d.add_argument("--force", action="store_true")
    d.set_defaults(func=_cmd_download)

    s = sub.add_parser("split", help="assign the tuning/held-out split once")
    s.set_defaults(func=_cmd_split)

    sc = sub.add_parser("score", help="live LLM scoring into the cache")
    sc.add_argument("--names", help="comma-separated lemma tags")
    sc.add_argument("--confirm-full-run", action="store_true")
    sc.add_argument("--held-out-run", action="store_true")
    sc.add_argument("--reason", help="why this run happens (required for held-out runs)")
    sc.add_argument("--unmasked", action="store_true", help="memorisation test only")
    sc.set_defaults(func=_cmd_score)

    e = sub.add_parser("export", help="write site JSON from interim tables")
    e.set_defaults(func=_cmd_export)

    dm = sub.add_parser("demo", help="export synthetic data to the site for frontend work")
    dm.add_argument("--out", help="output directory (default: client/public/data)")
    dm.set_defaults(func=_cmd_demo)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    paths = Paths.under(Path(args.root).resolve()) if args.root else Paths()
    from .ingest import IngestNotReady
    from .llm import LLMError
    from .mask import MaskingError
    from .run import ReproductionFailed

    try:
        return args.func(args, paths)
    except (IngestNotReady, ReproductionFailed, MaskingError, FileNotFoundError, LLMError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
