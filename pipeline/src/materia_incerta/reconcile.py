"""Map candidate species to WCVP IDs, synonyms and native range.

This is the one stage that matches on plant names, because that's how the
source files and LOTUS identify taxa. Every later stage joins on wcvp_id.

WCVP is read from the two pipe-delimited files in the full download:
wcvp_names.csv and wcvp_distribution.csv. Matches that are missing or
ambiguous get a reconcile_note for review by hand; they are never guessed.
"""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from . import config
from .schemas import Candidate

NAME_COLUMNS = (
    "plant_name_id",
    "taxon_rank",
    "taxon_status",
    "genus",
    "taxon_name",
    "taxon_authors",
    "accepted_plant_name_id",
)
DIST_COLUMNS = ("plant_name_id", "area_code_l3", "introduced", "extinct", "location_doubtful")


def normalise_name(name: str) -> str:
    """Canonical form for name matching: single spaces, no hybrid sign, lower-case."""
    name = name.replace("×", " ").replace(" ", " ")
    name = re.sub(r"\s+", " ", name).strip()
    return name.casefold()


def _read_pipe(path: Path, columns: Sequence[str]) -> pd.DataFrame:
    df = pd.read_csv(path, sep="|", dtype=str, keep_default_na=False, quoting=3)
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"{path}: missing WCVP columns {missing}; check the WCVP version")
    return df[list(columns)]


@dataclass
class WcvpIndex:
    """Lookup tables built from one WCVP snapshot."""

    #: normalised taxon_name -> list of plant_name_id (homonyms possible)
    by_name: dict[str, list[str]] = field(default_factory=dict)
    #: plant_name_id -> row dict
    rows: dict[str, dict[str, str]] = field(default_factory=dict)
    #: accepted plant_name_id -> synonym taxon_names
    synonyms: dict[str, list[str]] = field(default_factory=dict)
    #: accepted plant_name_id -> native level-3 area codes
    native_areas: dict[str, set[str]] = field(default_factory=dict)

    @classmethod
    def load(cls, names_csv: Path, distribution_csv: Path | None = None) -> "WcvpIndex":
        names = _read_pipe(names_csv, NAME_COLUMNS)
        idx = cls()
        by_name: dict[str, list[str]] = defaultdict(list)
        synonyms: dict[str, list[str]] = defaultdict(list)
        for row in names.to_dict("records"):
            pid = row["plant_name_id"]
            idx.rows[pid] = row
            by_name[normalise_name(row["taxon_name"])].append(pid)
            acc = row["accepted_plant_name_id"]
            if row["taxon_status"] == "Synonym" and acc:
                synonyms[acc].append(row["taxon_name"])
        idx.by_name = dict(by_name)
        idx.synonyms = {k: sorted(set(v)) for k, v in synonyms.items()}
        if distribution_csv is not None and distribution_csv.exists():
            dist = _read_pipe(distribution_csv, DIST_COLUMNS)
            native: dict[str, set[str]] = defaultdict(set)
            for row in dist.to_dict("records"):
                if row["introduced"] == "0" and row["extinct"] == "0" and row["location_doubtful"] == "0":
                    native[row["plant_name_id"]].add(row["area_code_l3"])
            idx.native_areas = dict(native)
        return idx

    def accepted_id(self, plant_name_id: str) -> str | None:
        row = self.rows.get(plant_name_id)
        if row is None:
            return None
        if row["taxon_status"] == "Accepted":
            return plant_name_id
        acc = row["accepted_plant_name_id"]
        if acc and self.rows.get(acc, {}).get("taxon_status") == "Accepted":
            return acc
        return None

    def resolve(self, name: str) -> tuple[str | None, str | None]:
        """Return (accepted plant_name_id, note). A note means review by hand."""
        ids = self.by_name.get(normalise_name(name), [])
        if not ids:
            return None, f"no WCVP name matches {name!r}"
        accepted = {a for a in (self.accepted_id(i) for i in ids) if a}
        if not accepted:
            return None, f"{name!r} matches only unplaced or unresolved WCVP names"
        if len(accepted) > 1:
            return None, f"{name!r} is ambiguous in WCVP: {sorted(accepted)}"
        acc = accepted.pop()
        note = None
        if self.rows[ids[0]]["taxon_status"] != "Accepted" or len(ids) > 1:
            note = f"resolved via synonymy to {self.rows[acc]['taxon_name']}"
        return acc, note


def reconcile(
    candidates: Sequence[Candidate],
    index: WcvpIndex,
    *,
    manual: dict[str, str] | None = None,
) -> list[Candidate]:
    """Fill WCVP fields. `manual` maps candidate_key -> plant_name_id for
    names reviewed by hand; it wins over automatic matching."""
    manual = manual or {}
    out: list[Candidate] = []
    for cand in candidates:
        if cand.candidate_key in manual:
            acc, note = index.accepted_id(manual[cand.candidate_key]), "manual match"
            if acc is None:
                note = f"manual match {manual[cand.candidate_key]!r} is not an accepted WCVP id"
        else:
            acc, note = index.resolve(cand.source_name)
        if acc is None:
            out.append(cand.model_copy(update={"wcvp_id": None, "reconcile_note": note}))
            continue
        row = index.rows[acc]
        areas = index.native_areas.get(acc)
        genus = row["genus"] or None
        out.append(
            cand.model_copy(
                update={
                    "wcvp_id": acc,
                    "accepted_name": row["taxon_name"],
                    "accepted_genus": genus,
                    "synonyms": tuple(index.synonyms.get(acc, [])),
                    "in_east_med": None if areas is None else bool(areas & config.EAST_MED_AREAS),
                    "hazard": config.HAZARDOUS_GENERA.get(genus or ""),
                    "reconcile_note": note,
                }
            )
        )
    return out


def name_to_accepted(index: WcvpIndex, names: Sequence[str]) -> dict[str, str | None]:
    """Resolve many names at once (used to map LOTUS organisms to WCVP)."""
    return {n: index.resolve(n)[0] for n in sorted(set(names))}
