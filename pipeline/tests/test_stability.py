import json

import numpy as np

from materia_incerta.run import feature_categories
from materia_incerta.stability import add_stability, resample_group


def _expert(scores):
    return [s for s in scores if s.source == "expert"]


def _run(demo_tables, seed):
    comps = demo_tables["feature_comparisons"]
    scores = [s.model_copy(update={"label_share": None}) for s in demo_tables["candidate_scores"]]
    return add_stability(scores, comps, feature_categories(comps), seed=seed)


def test_same_seed_gives_identical_output(demo_tables):
    a = _run(demo_tables, 7)
    b = _run(demo_tables, 7)
    assert [json.loads(s.model_dump_json()) for s in a] == [json.loads(s.model_dump_json()) for s in b]


def test_different_seed_changes_output(demo_tables):
    a = {s.candidate_key: s.label_share for s in _expert(_run(demo_tables, 7))}
    b = {s.candidate_key: s.label_share for s in _expert(_run(demo_tables, 8))}
    assert a != b


def test_shares_are_distributions(demo_tables):
    out = _run(demo_tables, 7)
    groups = {}
    for s in out:
        assert abs(sum(s.label_distribution.values()) - 1) < 1e-6
        assert abs(sum(s.rank_distribution.values()) - 1) < 1e-6
        assert s.label_share == s.label_distribution[s.label]
        groups.setdefault((s.source, s.lemma_tag, s.dmm_id), []).append(s.first_rank_share)
    for shares in groups.values():
        assert abs(sum(shares) - 1) < 1e-5


def test_single_candidate_always_ranks_first(demo_tables):
    out = _run(demo_tables, 7)
    single = [s for s in out if s.dmm_id == "DEMO-03a"]
    assert single and all(s.first_rank_share == 1.0 for s in single)


def test_resample_keeps_category_count_and_sign_logic():
    signs = np.array([[1] * 13, [0] * 13])
    res = resample_group(signs, n_resamples=200, rng=np.random.default_rng(0))
    assert (res["doc"][:, 0] == 13).all()
    assert (res["doc"][:, 1] == 0).all()
    assert (res["labels"][:, 0] == "Strong").all()
    assert (res["credit"][:, 0] == 1).all()
