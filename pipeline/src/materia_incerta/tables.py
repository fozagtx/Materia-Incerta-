"""Read and write validated tables as JSON Lines.

Every row passes through its Pydantic model on the way in and on the way out,
so a malformed table fails loudly at the stage that produced it.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from .schemas import (
    Candidate,
    CandidateScore,
    CompoundRecord,
    DmmPlant,
    FeatureComparison,
    HistoricalName,
    LedgerEntry,
)

M = TypeVar("M", bound=BaseModel)

#: Interim table file names and their row models.
TABLES: dict[str, type[BaseModel]] = {
    "historical_names": HistoricalName,
    "dmm_plants": DmmPlant,
    "candidates": Candidate,
    "feature_comparisons": FeatureComparison,
    #: Same items scored without masking, for the memorisation test only.
    "feature_comparisons_unmasked": FeatureComparison,
    "candidate_scores": CandidateScore,
    "compound_records": CompoundRecord,
    "compound_ledger": LedgerEntry,
}


def table_path(interim: Path, name: str) -> Path:
    if name not in TABLES:
        raise KeyError(f"unknown table {name!r}")
    return interim / f"{name}.jsonl"


def write_rows(path: Path, rows: Iterable[BaseModel]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(row.model_dump_json())
            fh.write("\n")
            n += 1
    return n


def read_rows(path: Path, model: type[M]) -> list[M]:
    rows: list[M] = []
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            try:
                rows.append(model.model_validate(json.loads(line)))
            except Exception as exc:  # re-raise with location
                raise ValueError(f"{path}:{lineno}: {exc}") from exc
    return rows


def write_table(interim: Path, name: str, rows: Iterable[BaseModel]) -> int:
    model = TABLES[name]
    rows = list(rows)
    for row in rows:
        if not isinstance(row, model):
            raise TypeError(f"{name} expects {model.__name__}, got {type(row).__name__}")
    return write_rows(table_path(interim, name), rows)


def read_table(interim: Path, name: str) -> list:
    path = table_path(interim, name)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run the stage that produces {name!r} first."
        )
    return read_rows(path, TABLES[name])


def has_table(interim: Path, name: str) -> bool:
    return table_path(interim, name).exists()
