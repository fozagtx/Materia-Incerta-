"""A full rebuild from cached responses, with no network and no API key."""

import json
import socket
from dataclasses import replace

import pytest

from materia_incerta.config import Paths
from materia_incerta.demo import REBUILD_STAGES
from materia_incerta.ingest import IngestNotReady
from materia_incerta.run import RunOptions, run


@pytest.fixture
def offline(monkeypatch):
    def refuse(*args, **kwargs):
        raise OSError("network disabled in tests")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)


def _snapshot(paths: Paths) -> dict[str, str]:
    return {
        str(p.relative_to(paths.site_data)): p.read_text(encoding="utf-8")
        for p in sorted(paths.site_data.rglob("*.json"))
    }


def test_full_rebuild_offline_is_deterministic(fresh_demo, offline):
    run(fresh_demo, RunOptions(stages=REBUILD_STAGES, strict_cache=True))
    first = _snapshot(fresh_demo)
    assert {"index.json", "manifest.json", "benchmark.json"} <= set(first)
    assert {"names/demo-alpha.json", "names/demo-beta.json", "names/demo-gamma.json"} <= set(first)

    run(fresh_demo, RunOptions(stages=REBUILD_STAGES, strict_cache=True))
    assert _snapshot(fresh_demo) == first

    # Model scores come only from the cache.
    case = json.loads(first["names/demo-alpha.json"])
    cands = case["dmm_plants"][0]["candidates"]
    assert all(c["model"] is not None for c in cands)
    manifest = json.loads(first["manifest.json"])
    assert manifest["constants"]["n_resamples"] == 1000
    assert manifest["scoring"]["model"] == "demo-model"


def test_rebuild_from_a_different_directory_matches(fresh_demo, tmp_path_factory, offline):
    other = Paths.under(tmp_path_factory.mktemp("other"))
    from materia_incerta.demo import build_demo

    build_demo(other.root)
    run(fresh_demo, RunOptions(stages=REBUILD_STAGES))
    run(other, RunOptions(stages=REBUILD_STAGES))
    assert _snapshot(fresh_demo) == _snapshot(other)


def test_stale_model_results_do_not_survive_a_cache_miss(fresh_demo, offline):
    run(fresh_demo, RunOptions(stages=REBUILD_STAGES))
    for f in fresh_demo.cache.rglob("*.json"):
        f.unlink()
    run(fresh_demo, RunOptions(stages=REBUILD_STAGES))
    case = json.loads((fresh_demo.site_data / "names" / "demo-alpha.json").read_text())
    assert all(c["model"] is None for c in case["dmm_plants"][0]["candidates"])
    assert all(e["model_class"] is None for e in case["dmm_plants"][0]["evidence"])


def test_strict_cache_fails_on_missing_responses(fresh_demo, offline):
    # Remove one cached response for a scored name.
    victim = next(fresh_demo.cache.rglob("*.json"))
    victim.unlink()
    with pytest.raises(LookupError):
        run(fresh_demo, RunOptions(stages=REBUILD_STAGES, strict_cache=True))


def test_ingest_explains_what_is_missing(tmp_path, offline):
    paths = Paths.under(tmp_path)
    paths.sources.parent.mkdir(parents=True)
    from materia_incerta.config import REPO_ROOT

    paths.sources.write_text((REPO_ROOT / "pipeline" / "sources.toml").read_text())
    with pytest.raises(IngestNotReady, match="lardos_file_02"):
        run(paths, RunOptions(stages=("ingest",)))


def test_export_withholds_source_text_by_default(demo_built):
    case = json.loads((demo_built.site_data / "names" / "demo-alpha.json").read_text())
    assert case["text_withheld"] is True
    plant = case["dmm_plants"][0]
    assert all(d["text"] is None for d in plant["details"])
    assert all(e["ancient_text"] is None and e["modern_text"] is None and e["model_reason"] is None
               for e in plant["evidence"])
    # Comparative details stay flagged even without text.
    assert any(d["comparative"] for d in plant["details"])


def test_export_marks_synthetic_data(demo_built):
    manifest = json.loads((demo_built.site_data / "manifest.json").read_text())
    assert manifest["synthetic"] is True


def test_hazard_and_range_reach_the_site(demo_built):
    case = json.loads((demo_built.site_data / "names" / "demo-gamma.json").read_text())
    cands = {c["candidate_key"]: c for p in case["dmm_plants"] for c in p["candidates"]}
    assert cands["demo-gamma|DEMO-03a|1"]["hazard"]
    assert cands["demo-gamma|DEMO-03b|1"]["in_east_med"] is False
    assert cands["demo-gamma|DEMO-03b|2"]["wcvp_id"] is None
