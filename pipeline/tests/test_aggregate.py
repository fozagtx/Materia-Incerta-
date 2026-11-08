import pytest

from materia_incerta.aggregate import (
    ThresholdGapError,
    category_means,
    competition_ranks,
    congruence,
    label_for,
    score_candidates,
    score_of,
)
from materia_incerta.schemas import Candidate, FeatureComparison


def test_score_mapping():
    assert score_of("good") == 2
    assert score_of("partial") == 1
    assert score_of("no_match") == -2
    assert score_of("absent") == 0
    with pytest.raises(ValueError):
        score_of("maybe")  # type: ignore[arg-type]


def test_means_are_taken_within_categories_before_combining():
    means = category_means(
        {
            "leaf": ["good", "no_match"],  # 0: neutral
            "root": ["partial", "no_match"],  # -0.5: negative
            "stem": ["partial", "absent"],  # 0.5: positive
            "seed": ["absent"],  # 0: neutral
            "fruit": [],  # no comparisons: omitted
        }
    )
    assert means == {"leaf": 0.0, "root": -0.5, "stem": 0.5, "seed": 0.0}
    assert congruence(means) == (1, 1, 0)


@pytest.mark.parametrize(
    "doc,label",
    [
        (13, "Strong"),
        (6, "Strong"),
        (5, "Strong"),
        (4, "Moderate"),
        (3, "Moderate"),
        (3.5, "Moderate"),
        (2.999, "Weak"),
        (2, "Weak"),
        (0, "Weak"),
        (-13, "Weak"),
    ],
)
def test_label_thresholds(doc, label):
    assert label_for(doc) == label


@pytest.mark.parametrize("doc", [4.0001, 4.5, 4.999])
def test_values_between_4_and_5_are_not_guessed(doc):
    with pytest.raises(ThresholdGapError):
        label_for(doc)


def test_competition_ranks_share_ties():
    assert competition_ranks({"a": 5, "b": 5, "c": 1}) == {"a": 1, "b": 1, "c": 3}


def _comp(key, cat, expert, model=None, n=0):
    return FeatureComparison(
        comparison_id=f"{key}#{cat}#{n}",
        candidate_key=key,
        category=cat,
        ancient_detail_id=cat,
        expert_class=expert,
        model_class=model,
    )


def test_partial_model_runs_never_produce_a_label():
    cands = [Candidate(candidate_key=k, lemma_tag="x", dmm_id="d", source_name=k) for k in ("a", "b")]
    comps = [
        _comp("a", "c1", "good", "good"),
        _comp("a", "c2", "good", "good"),
        _comp("b", "c1", "good", "good"),
        _comp("b", "c2", "good", None),  # not yet scored
    ]
    expert = score_candidates(cands, comps, "expert")
    model = score_candidates(cands, comps, "model")
    assert {s.candidate_key for s in expert} == {"a", "b"}
    assert {s.candidate_key for s in model} == {"a"}


def test_ranks_are_within_each_dmm_plant():
    cands = [
        Candidate(candidate_key="a", lemma_tag="x", dmm_id="d1", source_name="a"),
        Candidate(candidate_key="b", lemma_tag="x", dmm_id="d2", source_name="b"),
    ]
    comps = [_comp("a", "c1", "good"), _comp("b", "c1", "no_match")]
    scores = {s.candidate_key: s for s in score_candidates(cands, comps, "expert")}
    assert scores["a"].rank == 1 and scores["b"].rank == 1
