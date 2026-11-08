"""A small synthetic dataset that exercises every stage.

Nothing here is real: taxa, texts, compounds, DOIs and scores are invented,
except the genus Aristolochia, included so the hazard label shows. Tests use
it as their fixture, and `python -m materia_incerta demo` exports it to the
site (flagged synthetic) so the frontend can be built before the real data
exists.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import replace
from pathlib import Path

from . import tables
from .config import Paths
from .run import RunOptions, run
from .schemas import (
    BotanicalDetail,
    Candidate,
    DmmPlant,
    FeatureComparison,
    HistoricalName,
    MatchClass,
    Split,
)
from .score import PROMPT_VERSION, ResponseCache, score_comparisons

CATEGORIES = tuple(f"category-{i:02d}" for i in range(1, 14))
MODEL = "demo-model"
STATES = ("small", "large", "hairy", "smooth", "white", "yellow", "rounded", "pointed", "creeping", "upright")

NAMES = (
    HistoricalName(
        lemma_tag="demo-alpha",
        greek_name="δοκιμαστικόν",
        transliteration="dokimastikon",
        dmm_ids=("DEMO-01",),
    ),
    HistoricalName(
        lemma_tag="demo-beta",
        greek_name="παράδειγμα",
        transliteration="paradeigma",
        dmm_ids=("DEMO-02",),
    ),
    HistoricalName(
        lemma_tag="demo-gamma",
        greek_name="ὑπόδειγμα",
        transliteration="hypodeigma",
        dmm_ids=("DEMO-03a", "DEMO-03b"),
    ),
)

#: (candidate_key, lemma, dmm_id, source_name, verdicts per category)
#: Verdict "+" gives a positive category mean, "-" negative, "0" neutral.
CANDIDATES = (
    ("demo-alpha|DEMO-01|1", "demo-alpha", "DEMO-01", "Exemplaria prima", "+++++++-00000"),
    ("demo-alpha|DEMO-01|2", "demo-alpha", "DEMO-01", "Exemplaria secundula", "+++++--000000"),
    ("demo-alpha|DEMO-01|3", "demo-alpha", "DEMO-01", "Fictaria tertia", "+++---0000000"),
    ("demo-beta|DEMO-02|1", "demo-beta", "DEMO-02", "Modelia quarta", "+++++-0000000"),
    ("demo-beta|DEMO-02|2", "demo-beta", "DEMO-02", "Modelia quinta", "+++++--000000"),
    ("demo-gamma|DEMO-03a|1", "demo-gamma", "DEMO-03a", "Aristolochia fictiva", "++++++0000000"),
    ("demo-gamma|DEMO-03b|1", "demo-gamma", "DEMO-03b", "Specimenia sexta", "++--000000000"),
    ("demo-gamma|DEMO-03b|2", "demo-gamma", "DEMO-03b", "Specimenia septima", "+-00000000000"),
)

#: plant_name_id, status, genus, taxon_name, accepted id, native areas
WCVP = (
    ("D-1", "Accepted", "Exemplaria", "Exemplaria prima", "D-1", ("GRC", "TUR")),
    ("D-2", "Accepted", "Exemplaria", "Exemplaria secunda", "D-2", ("CYP",)),
    ("D-3", "Synonym", "Exemplaria", "Exemplaria secundula", "D-2", ()),
    ("D-4", "Accepted", "Fictaria", "Fictaria tertia", "D-4", ("LBS", "PAL")),
    ("D-5", "Accepted", "Modelia", "Modelia quarta", "D-5", ("GRC",)),
    ("D-6", "Accepted", "Modelia", "Modelia quinta", "D-6", ("KRI",)),
    ("D-7", "Accepted", "Aristolochia", "Aristolochia fictiva", "D-7", ("TUR",)),
    ("D-8", "Accepted", "Specimenia", "Specimenia sexta", "D-8", ("BZL",)),
)

#: organism name as LOTUS gives it -> compound numbers
LOTUS = {
    "Exemplaria prima": range(1, 11),
    "Exemplaria secundula": (1, 2, 3, 11, 12, 13),
    "Fictaria tertia": (1, 2, 14, 15, 16),
    "Modelia quarta": (17, 18, 19, 20, 21, 22, 23, 24),
    "Aristolochia fictiva": (25, 26, 27, 28, 29, 30, 31),
    "Specimenia sexta": (25, 32),
}
PATHWAYS = ("Terpenoids", "Alkaloids", "Shikimates and Phenylpropanoids", "Polyketides")

#: Deliberate model disagreements: comparison_id -> (class, quote both sides?)
MODEL_OVERRIDES: dict[str, tuple[MatchClass, bool]] = {
    "demo-alpha|DEMO-01|3#category-04#2": ("partial", True),
    # A match claimed where experts said absent: counts as invented evidence.
    "demo-alpha|DEMO-01|2#category-08#1": ("good", True),
    "demo-alpha|DEMO-01|2#category-09#1": ("good", True),
    # A match claimed without quotes: the evidence rule turns it into absent.
    "demo-beta|DEMO-02|1#category-01#1": ("good", False),
}

TUNING = ("demo-alpha", "demo-beta")
HELD_OUT = ("demo-gamma",)


def fake_inchikey(n: int) -> str:
    h = hashlib.sha256(f"demo-compound-{n}".encode()).hexdigest()
    letters = "".join(chr(ord("A") + int(c, 16)) for c in h)
    return f"{letters[:14]}-{letters[14:22]}SA-N"


def _classes_for(verdict: str, i: int) -> list[MatchClass]:
    if verdict == "+":
        return ["good"] if i % 2 == 0 else ["good", "partial"]
    if verdict == "-":
        return ["no_match"] if i % 2 == 0 else ["partial", "no_match"]
    return ["absent"]


def _state(*parts: object) -> str:
    h = int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest(), 16)
    return STATES[h % len(STATES)]


def build_tables() -> tuple[list[DmmPlant], list[Candidate], list[FeatureComparison]]:
    plants: dict[str, DmmPlant] = {}
    for name in NAMES:
        for dmm_id in name.dmm_ids:
            details = tuple(
                BotanicalDetail(
                    detail_id=f"{dmm_id}#{cat}",
                    category=cat,
                    text=f"Synthetic ancient detail for {cat}: the part is {_state(dmm_id, cat)}.",
                    comparative=(cat == "category-13"),
                )
                for cat in CATEGORIES
            )
            plants[dmm_id] = DmmPlant(
                dmm_id=dmm_id,
                chapter=f"Synthetic chapter {dmm_id}",
                plant_type="herb",
                detail_level="demo",
                names=(name.greek_name,),
                details=details,
            )

    cands: list[Candidate] = []
    comps: list[FeatureComparison] = []
    for key, lemma, dmm_id, source_name, verdicts in CANDIDATES:
        pos, neg = verdicts.count("+"), verdicts.count("-")
        doc = pos - neg
        label = "Strong" if doc >= 5 else "Moderate" if doc >= 3 else "Weak"
        cands.append(
            Candidate(
                candidate_key=key,
                lemma_tag=lemma,
                dmm_id=dmm_id,
                source_name=source_name,
                paper_doc=float(doc),
                paper_label=label,
            )
        )
        detail = {d.category: d for d in plants[dmm_id].details}
        for i, (cat, verdict) in enumerate(zip(CATEGORIES, verdicts)):
            for j, cls in enumerate(_classes_for(verdict, i), start=1):
                ancient_state = _state(dmm_id, cat)
                modern_state = ancient_state if cls == "good" else _state(key, cat, j, "m")
                cid = f"{key}#{cat}#{j}"
                comps.append(
                    FeatureComparison(
                        comparison_id=cid,
                        candidate_key=key,
                        category=cat,
                        ancient_detail_id=detail[cat].detail_id,
                        ancient_text=detail[cat].text,
                        modern_text=(
                            f"{source_name}, flora note {cid}: the part is {modern_state}."
                            if cls != "absent"
                            else f"{source_name}, flora note {cid}: not described."
                        ),
                        comparative=detail[cat].comparative,
                        expert_class=cls,
                    )
                )
    return list(plants.values()), cands, comps


class ScriptedClient:
    """Stands in for an LLM: answers from a table keyed by the flora note id."""

    model = MODEL

    def __init__(self, comps: list[FeatureComparison], *, unmasked: bool = False) -> None:
        self.by_id = {c.comparison_id: c for c in comps}
        self.unmasked = unmasked

    def complete_json(self, prompt: str, schema: dict) -> str:
        m = re.search(r"flora note (\S+):", prompt)
        if not m:
            raise ValueError("demo prompt without a flora note id")
        comp = self.by_id[m.group(1)]
        cls, quote = (comp.expert_class, True) if self.unmasked else MODEL_OVERRIDES.get(
            comp.comparison_id, (comp.expert_class, True)
        )
        ancient = re.search(r"the part is \w+", comp.ancient_text or "")
        modern = re.search(r"the part is \w+|not described", comp.modern_text or "")
        return json.dumps(
            {
                "match_class": cls,
                "reason": f"Synthetic response for {comp.category}.",
                "ancient_quote": ancient.group(0) if (quote and ancient and cls != "absent") else None,
                "modern_quote": modern.group(0) if (quote and modern and cls != "absent") else None,
            }
        )


def _write_raw(paths: Paths) -> None:
    wcvp_dir = paths.raw / "wcvp"
    wcvp_dir.mkdir(parents=True, exist_ok=True)
    header = "plant_name_id|ipni_id|taxon_rank|taxon_status|family|genus|species|taxon_name|taxon_authors|accepted_plant_name_id"
    lines = [header]
    for pid, status, genus, name, acc, _ in WCVP:
        lines.append(f"{pid}||Species|{status}|Demoaceae|{genus}|{name.split()[1]}|{name}|Demo|{acc}")
    (wcvp_dir / "wcvp_names.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")

    dist = ["plant_locality_id|plant_name_id|continent_code_l1|continent|region_code_l2|region|area_code_l3|area|introduced|extinct|location_doubtful"]
    n = 0
    for pid, _, _, _, _, areas in WCVP:
        for area in areas:
            n += 1
            dist.append(f"L{n}|{pid}|0|Demo|0|Demo|{area}|{area}|0|0|0")
    (wcvp_dir / "wcvp_distribution.csv").write_text("\n".join(dist) + "\n", encoding="utf-8")

    lotus_dir = paths.raw / "lotus"
    lotus_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        "structure_inchikey,organism_name,reference_doi,structure_nameTraditional,"
        "structure_taxonomy_npclassifier_01pathway,structure_taxonomy_npclassifier_02superclass,"
        "structure_taxonomy_npclassifier_03class"
    ]
    for organism, numbers in LOTUS.items():
        for k in numbers:
            rows.append(
                f"{fake_inchikey(k)},{organism},10.0000/demo.{k},Demo compound {k:02d},"
                f"{PATHWAYS[k % len(PATHWAYS)]},Demo superclass,Demo class"
            )
    (lotus_dir / "lotus_frozen.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")

    paths.sources.parent.mkdir(parents=True, exist_ok=True)
    paths.sources.write_text(
        """\
[sources.demo]
title = "Synthetic demo data"
citation = "Generated by materia_incerta.demo. Not real data."
version = "demo"
licence = "Synthetic"
licence_confirmed = true
republish = true

[[sources.demo.files]]
role = "wcvp_names"
path = "wcvp/wcvp_names.csv"

[[sources.demo.files]]
role = "wcvp_distribution"
path = "wcvp/wcvp_distribution.csv"

[[sources.demo.files]]
role = "lotus"
path = "lotus/lotus_frozen.csv"
""",
        encoding="utf-8",
    )


def build_demo(root: Path) -> Paths:
    """Write raw files, interim tables, cached responses and the split under `root`."""
    paths = Paths.under(root)
    _write_raw(paths)
    plants, cands, comps = build_tables()
    tables.write_table(paths.interim, "historical_names", NAMES)
    tables.write_table(paths.interim, "dmm_plants", plants)
    tables.write_table(paths.interim, "candidates", cands)
    tables.write_table(paths.interim, "feature_comparisons", comps)

    # Reconcile first: masking uses accepted names and synonyms.
    run(paths, RunOptions(stages=("reconcile",)))
    cands = tables.read_table(paths.interim, "candidates")
    cache = ResponseCache(paths.cache)
    for unmasked in (False, True):
        score_comparisons(
            comps, NAMES, plants, cands, cache,
            model=MODEL,
            client=ScriptedClient(comps, unmasked=unmasked),
            only_lemmas=set(TUNING),
            unmasked=unmasked,
        )
    paths.scoring.parent.mkdir(parents=True, exist_ok=True)
    paths.scoring.write_text(
        json.dumps({"model": MODEL, "prompt_version": PROMPT_VERSION, "memorisation": True}, indent=2) + "\n",
        encoding="utf-8",
    )
    paths.split.write_text(
        Split(seed=0, tuning=TUNING, held_out=HELD_OUT).model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    return paths


REBUILD_STAGES = ("reconcile", "reproduce", "score", "aggregate", "stability", "chemistry", "evaluate", "export")


def run_demo(root: Path, site_data: Path | None = None) -> Paths:
    paths = build_demo(root)
    if site_data is not None:
        paths = replace(paths, site_data=site_data)
    run(paths, RunOptions(stages=REBUILD_STAGES, synthetic=True))
    return paths
