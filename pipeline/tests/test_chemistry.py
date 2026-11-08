import pytest

from materia_incerta.chemistry import build_ledger, candidate_status, ledger_label, load_lotus
from materia_incerta.reconcile import WcvpIndex
from materia_incerta.schemas import Candidate, CompoundRecord


def _cand(key, wcvp_id, lemma="n"):
    return Candidate(candidate_key=key, lemma_tag=lemma, dmm_id="d", source_name=key, wcvp_id=wcvp_id)


def _records(wcvp_id, keys):
    return [CompoundRecord(inchikey=k, wcvp_id=wcvp_id, dois=(f"10.0/{k}",)) for k in keys]


def _ledger(cands, records, min_records=3):
    return {e.inchikey: e for e in build_ledger(cands, records, min_records=min_records)}


def test_robust_when_every_candidate_with_data_reports_it():
    cands = [_cand("a", "T1"), _cand("b", "T2")]
    recs = _records("T1", ["X", "A1", "A2"]) + _records("T2", ["X", "B1", "B2"])
    led = _ledger(cands, recs)
    assert led["X"].label == "robust"
    assert led["X"].status_by_candidate == {"T1": "reported", "T2": "reported"}


def test_id_dependent_when_some_candidates_with_data_lack_it():
    cands = [_cand("a", "T1"), _cand("b", "T2")]
    recs = _records("T1", ["X", "A1", "A2"]) + _records("T2", ["B1", "B2", "B3"])
    led = _ledger(cands, recs)
    assert led["X"].label == "id_dependent"
    assert led["X"].status_by_candidate == {"T1": "reported", "T2": "not_reported"}


def test_no_data_when_no_candidate_has_enough_records():
    cands = [_cand("a", "T1"), _cand("b", "T2")]
    recs = _records("T1", ["X"]) + _records("T2", ["Y", "Z"])
    led = _ledger(cands, recs)
    assert {e.label for e in led.values()} == {"no_data"}
    # A sparse taxon that lacks a compound is no_data, never "not reported".
    assert led["X"].status_by_candidate == {"T1": "reported", "T2": "no_data"}
    assert led["X"].candidates_with_data == 0


def test_sparse_candidate_does_not_count_against_robust():
    cands = [_cand("a", "T1"), _cand("b", "T2")]
    recs = _records("T1", ["X", "A1", "A2"]) + _records("T2", ["Y"])
    led = _ledger(cands, recs)
    assert led["X"].label == "robust"
    assert led["X"].status_by_candidate["T2"] == "no_data"
    assert led["X"].candidates_with_data == 1 and led["X"].candidates_total == 2
    # Reported only by the sparse taxon while another has data: depends on the ID.
    assert led["Y"].label == "id_dependent"


def test_candidate_without_any_records_is_no_data():
    cands = [_cand("a", "T1"), _cand("b", "T2")]
    led = _ledger(cands, _records("T1", ["X", "A1", "A2"]))
    assert led["X"].status_by_candidate["T2"] == "no_data"
    assert led["X"].label == "robust"


def test_unjoined_candidates_are_listed():
    cands = [_cand("a", "T1"), _cand("b", None)]
    led = _ledger(cands, _records("T1", ["X", "A1", "A2"]))
    assert led["X"].unjoined_candidates == ("b",)
    assert led["X"].candidates_total == 2


def test_same_species_for_two_dmm_plants_counts_once():
    cands = [
        Candidate(candidate_key="a1", lemma_tag="n", dmm_id="d1", source_name="a", wcvp_id="T1"),
        Candidate(candidate_key="a2", lemma_tag="n", dmm_id="d2", source_name="a", wcvp_id="T1"),
    ]
    led = _ledger(cands, _records("T1", ["X", "A1", "A2"]))
    assert led["X"].candidates_total == 1


def test_label_helpers():
    assert ledger_label({}, {}) == "no_data"
    assert candidate_status(True, False) == "reported"
    assert candidate_status(False, True) == "not_reported"
    assert candidate_status(False, False) == "no_data"


def test_lotus_joins_through_wcvp_synonyms(demo_built):
    from materia_incerta.sources import Sources

    src = Sources.load(demo_built.sources)
    index = WcvpIndex.load(src.path_for("wcvp_names", demo_built.raw), src.path_for("wcvp_distribution", demo_built.raw))
    records = load_lotus(src.path_for("lotus", demo_built.raw), index)
    by_taxon = {}
    for r in records:
        by_taxon.setdefault(r.wcvp_id, set()).add(r.inchikey)
    # LOTUS lists "Exemplaria secundula", a synonym of accepted D-2.
    assert len(by_taxon["D-2"]) == 6
    assert "D-3" not in by_taxon


def test_lotus_missing_columns_fail(tmp_path, demo_built):
    from materia_incerta.sources import Sources

    src = Sources.load(demo_built.sources)
    index = WcvpIndex.load(src.path_for("wcvp_names", demo_built.raw))
    bad = tmp_path / "lotus.csv"
    bad.write_text("inchikey,organism\nX,Y\n")
    with pytest.raises(ValueError, match="missing LOTUS columns"):
        load_lotus(bad, index)
