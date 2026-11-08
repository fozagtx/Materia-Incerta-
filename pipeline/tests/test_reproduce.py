import pytest

from materia_incerta import tables
from materia_incerta.reproduce import reproduce
from materia_incerta.run import ReproductionFailed, RunOptions, run


def test_demo_labels_reproduce_from_expert_scores(demo_tables):
    report = reproduce(demo_tables["candidates"], demo_tables["feature_comparisons"])
    assert report.checked == len(demo_tables["candidates"])
    assert report.mismatches == []
    assert report.ok


def test_a_wrong_paper_label_is_reported(demo_tables):
    cands = list(demo_tables["candidates"])
    cands[0] = cands[0].model_copy(update={"paper_label": "Weak", "paper_doc": 99.0})
    report = reproduce(cands, demo_tables["feature_comparisons"])
    assert [r.candidate_key for r in report.mismatches] == [cands[0].candidate_key]
    assert not report.ok


def test_paper_values_between_4_and_5_are_surfaced(demo_tables):
    cands = list(demo_tables["candidates"])
    cands[0] = cands[0].model_copy(update={"paper_doc": 4.5})
    report = reproduce(cands, demo_tables["feature_comparisons"])
    assert report.gap_values == [(cands[0].candidate_key, 4.5)]


def test_run_stops_when_reproduction_fails(fresh_demo):
    cands = tables.read_table(fresh_demo.interim, "candidates")
    cands[0] = cands[0].model_copy(update={"paper_label": "Strong" if cands[0].paper_label != "Strong" else "Weak"})
    tables.write_table(fresh_demo.interim, "candidates", cands)
    with pytest.raises(ReproductionFailed):
        run(fresh_demo, RunOptions(stages=("reproduce",)))
    run(fresh_demo, RunOptions(stages=("reproduce",), allow_repro_mismatch=True))
