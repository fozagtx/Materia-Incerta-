"""Join candidates to LOTUS and build the compound ledger.

LOTUS identifies organisms by name, so organism names are resolved to accepted
WCVP IDs first (reconcile.WcvpIndex). After that, compounds join on wcvp_id
and InChIKey only.

Ledger labels for one historical name:
- robust: reported for every candidate that has enough LOTUS records
- id_dependent: reported for some candidates but not others
- no_data: no candidate of the name has enough LOTUS records

Per candidate, a compound is "reported", "not_reported" or "no_data".
"not_reported" never means absent: LOTUS only lists what has been published.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from . import config
from .reconcile import WcvpIndex, name_to_accepted
from .schemas import CandidateChemStatus, Candidate, CompoundRecord, LedgerEntry, LedgerLabel

LOTUS_COLUMNS = {
    "inchikey": "structure_inchikey",
    "organism": "organism_name",
    "doi": "reference_doi",
    "name": "structure_nameTraditional",
    "pathway": "structure_taxonomy_npclassifier_01pathway",
    "superclass": "structure_taxonomy_npclassifier_02superclass",
    "class": "structure_taxonomy_npclassifier_03class",
}


def load_lotus(path: Path, index: WcvpIndex, wanted: set[str] | None = None) -> list[CompoundRecord]:
    """Read a LOTUS frozen export and keep rows that resolve to `wanted` WCVP IDs."""
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = [c for c in LOTUS_COLUMNS.values() if c not in df.columns]
    if missing:
        raise ValueError(f"{path}: missing LOTUS columns {missing}; check the LOTUS version")
    df = df[list(LOTUS_COLUMNS.values())].rename(columns={v: k for k, v in LOTUS_COLUMNS.items()})
    resolved = name_to_accepted(index, df["organism"].tolist())
    df["wcvp_id"] = df["organism"].map(resolved)
    df = df[df["wcvp_id"].notna() & (df["inchikey"] != "")]
    if wanted is not None:
        df = df[df["wcvp_id"].isin(wanted)]

    records: list[CompoundRecord] = []
    for (wcvp_id, inchikey), grp in df.groupby(["wcvp_id", "inchikey"], sort=True):
        first = grp.iloc[0]
        dois = tuple(sorted({d for d in grp["doi"] if d}))
        records.append(
            CompoundRecord(
                inchikey=inchikey,
                wcvp_id=wcvp_id,
                compound_name=first["name"] or None,
                pathway=first["pathway"] or None,
                superclass=first["superclass"] or None,
                compound_class=first["class"] or None,
                dois=dois,
            )
        )
    return records


def candidate_coverage(
    candidates: Sequence[Candidate], records: Sequence[CompoundRecord]
) -> dict[str, int]:
    """Distinct compounds per candidate wcvp_id (0 for no records)."""
    counts: dict[str, int] = defaultdict(int)
    for r in records:
        counts[r.wcvp_id] += 1
    return {c.wcvp_id: counts.get(c.wcvp_id, 0) for c in candidates if c.wcvp_id}


def ledger_label(present: dict[str, bool], has_data: dict[str, bool]) -> LedgerLabel:
    """Label one compound for one name.

    present: taxon -> compound listed in LOTUS for that taxon
    has_data: taxon -> taxon has at least the minimum number of LOTUS records
    """
    with_data = [t for t, ok in has_data.items() if ok]
    if not with_data:
        return "no_data"
    if all(present.get(t, False) for t in with_data):
        return "robust"
    return "id_dependent"


def candidate_status(present: bool, has_data: bool) -> CandidateChemStatus:
    if present:
        return "reported"
    return "not_reported" if has_data else "no_data"


def build_ledger(
    candidates: Sequence[Candidate],
    records: Sequence[CompoundRecord],
    *,
    min_records: int = config.LOTUS_MIN_RECORDS,
) -> list[LedgerEntry]:
    """One ledger per historical name, pooling its candidates across DMM plants.

    A species suggested for two DMM plants of the same name counts once.
    Candidates without a WCVP ID cannot be joined; they are listed as unjoined.
    """
    by_lemma: dict[str, list[Candidate]] = defaultdict(list)
    for c in candidates:
        by_lemma[c.lemma_tag].append(c)
    by_taxon: dict[str, dict[str, CompoundRecord]] = defaultdict(dict)
    for r in records:
        by_taxon[r.wcvp_id][r.inchikey] = r

    entries: list[LedgerEntry] = []
    for lemma in sorted(by_lemma):
        taxa = sorted({c.wcvp_id for c in by_lemma[lemma] if c.wcvp_id})
        unjoined = tuple(sorted({c.candidate_key for c in by_lemma[lemma] if not c.wcvp_id}))
        has_data = {t: len(by_taxon.get(t, {})) >= min_records for t in taxa}
        compounds = sorted({ik for t in taxa for ik in by_taxon.get(t, {})})
        for ik in compounds:
            present = {t: ik in by_taxon.get(t, {}) for t in taxa}
            hits = [by_taxon[t][ik] for t in taxa if present[t]]
            entries.append(
                LedgerEntry(
                    lemma_tag=lemma,
                    inchikey=ik,
                    compound_name=hits[0].compound_name,
                    pathway=hits[0].pathway,
                    compound_class=hits[0].compound_class,
                    label=ledger_label(present, has_data),
                    status_by_candidate={
                        t: candidate_status(present[t], has_data[t]) for t in taxa
                    },
                    candidates_with_data=sum(has_data.values()),
                    candidates_total=len(taxa) + len(unjoined),
                    unjoined_candidates=unjoined,
                    dois=tuple(sorted({d for h in hits for d in h.dois})),
                )
            )
    return entries
