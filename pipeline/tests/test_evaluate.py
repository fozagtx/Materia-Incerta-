import pytest

from materia_incerta.evaluate import (
    CLASS_ORDER,
    assign_split,
    cohen_kappa,
    invented_evidence,
    load_split,
)
from materia_incerta.schemas import FeatureComparison


def test_kappa_known_values():
    a = ["good", "good", "absent", "absent"]
    b = ["good", "absent", "absent", "absent"]
    assert cohen_kappa(a, b, CLASS_ORDER, weighted=False) == pytest.approx(0.5)
    assert cohen_kappa(a, b, CLASS_ORDER, weighted=True) == pytest.approx(0.5)
    assert cohen_kappa(a, a, CLASS_ORDER, weighted=True) == pytest.approx(1.0)
    assert cohen_kappa([], [], CLASS_ORDER, weighted=True) is None


def test_weighted_kappa_penalises_far_disagreements_more():
    exp = ["good", "no_match", "partial", "absent"] * 5
    near = ["partial", "no_match", "partial", "absent"] * 5
    far = ["no_match", "no_match", "partial", "absent"] * 5
    assert cohen_kappa(exp, near, CLASS_ORDER, weighted=True) > cohen_kappa(exp, far, CLASS_ORDER, weighted=True)


def test_invented_evidence_counts_matches_on_expert_absent():
    def c(i, e, m):
        return FeatureComparison(comparison_id=str(i), candidate_key="k", category="c",
                                 ancient_detail_id="a", expert_class=e, model_class=m)
    out = invented_evidence([c(1, "absent", "good"), c(2, "absent", "absent"),
                             c(3, "absent", "no_match"), c(4, "good", "good")])
    assert out["n_expert_absent"] == 3
    assert out["match_claim_rate"] == pytest.approx(1 / 3)
    assert out["any_claim_rate"] == pytest.approx(2 / 3)
    assert out["comparison_ids"] == ["1"]


def test_split_is_assigned_once_by_name(tmp_path):
    path = tmp_path / "split.json"
    tags = [f"name-{i:02d}" for i in range(50)]
    split = assign_split(tags, path, seed=1)
    assert len(split.tuning) == 10 and len(split.held_out) == 40
    assert set(split.tuning) | set(split.held_out) == set(tags)
    assert load_split(path) == split
    with pytest.raises(FileExistsError):
        assign_split(tags, path, seed=1)
    # Same seed, same names: same split.
    assert assign_split(list(reversed(tags)), tmp_path / "again.json", seed=1) == split


def test_demo_benchmark_reports_by_partition(demo_built):
    import json

    bench = json.loads((demo_built.site_data / "benchmark.json").read_text())["benchmark"]
    assert set(bench["partitions"]) == {"tuning", "held_out"}
    assert "Not accuracy" in bench["wording"]
    tuning = bench["partitions"]["tuning"]
    assert tuning["detail"]["n"] > 0
    assert tuning["invented_evidence"]["match_claim_rate"] > 0
    assert tuning["memorisation"]["kappa_gap"] is not None
    # Held-out names have not been scored by the model in the demo.
    assert bench["partitions"]["held_out"]["detail"]["n"] == 0
