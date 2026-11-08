import json

import pytest
from pydantic import ValidationError

from materia_incerta.mask import NameLexicon
from materia_incerta.schemas import CacheEntry, ComparisonRequest, ComparisonResponse
from materia_incerta.score import (
    PROMPT_VERSION,
    ResponseCache,
    build_prompt,
    cache_key,
    enforce_evidence,
    parse_response,
    score_comparisons,
)

REQ = ComparisonRequest(
    comparison_id="c1",
    category="leaf",
    ancient_text="The leaves are like those of [PLANT], small and rounded.",
    modern_text="Leaves 1-2 cm, orbicular, glabrous.",
)


def test_valid_response_parses():
    raw = json.dumps({
        "match_class": "partial",
        "reason": "Both describe small round leaves.",
        "ancient_quote": "small and rounded",
        "modern_quote": "Leaves 1-2 cm, orbicular",
    })
    resp = parse_response(raw, REQ)
    assert resp.match_class == "partial"


@pytest.mark.parametrize(
    "payload",
    [
        {"match_class": "maybe", "reason": "x"},
        {"match_class": "good"},
        {"match_class": "good", "reason": ""},
        {"match_class": "good", "reason": "x", "confidence": 0.9},
        "not json",
    ],
)
def test_invalid_responses_are_rejected(payload):
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    with pytest.raises(ValueError):
        parse_response(raw, REQ)


def test_schema_forbids_extra_fields():
    with pytest.raises(ValidationError):
        ComparisonResponse(match_class="good", reason="x", extra="y")  # type: ignore[call-arg]


def test_match_without_quote_becomes_absent():
    resp = ComparisonResponse(match_class="good", reason="looks right")
    out = enforce_evidence(resp, REQ)
    assert out.match_class == "absent"
    assert "coerced from good" in out.reason


def test_invented_quote_becomes_absent():
    resp = ComparisonResponse(
        match_class="good", reason="x", ancient_quote="small and rounded", modern_quote="leaves heart-shaped"
    )
    assert enforce_evidence(resp, REQ).match_class == "absent"


def test_quote_match_ignores_case_and_whitespace():
    resp = ComparisonResponse(
        match_class="no_match", reason="x", ancient_quote="SMALL  and\nrounded", modern_quote="glabrous"
    )
    assert enforce_evidence(resp, REQ).match_class == "no_match"


def test_absent_needs_no_quote():
    resp = ComparisonResponse(match_class="absent", reason="modern text silent")
    assert enforce_evidence(resp, REQ) == resp


def test_cache_key_depends_on_model_and_prompt():
    p = build_prompt(REQ, NameLexicon())
    assert cache_key("m1", p) != cache_key("m2", p)
    assert cache_key("m1", p) != cache_key("m1", p + " ")
    assert cache_key("m1", p) == cache_key("m1", p)
    assert len(PROMPT_VERSION) > 0


def test_cache_roundtrip_and_key_check(tmp_path):
    cache = ResponseCache(tmp_path)
    entry = CacheEntry(cache_key="ab" * 32, model="m", prompt_version=PROMPT_VERSION, prompt="p", raw_response="{}")
    cache.put(entry)
    assert cache.get(entry.cache_key) == entry
    assert cache.get("cd" * 32) is None
    # A file whose content names another key is refused.
    path = tmp_path / "ab" / f"{'ab' * 32}.json"
    path.write_text(entry.model_copy(update={"cache_key": "ef" * 32}).model_dump_json())
    with pytest.raises(ValueError):
        cache.get(entry.cache_key)


def test_offline_misses_are_reported_not_fatal(demo_tables, tmp_path):
    comps = demo_tables["feature_comparisons"]
    out, report = score_comparisons(
        comps, demo_tables["historical_names"], demo_tables["dmm_plants"], demo_tables["candidates"],
        ResponseCache(tmp_path / "empty"), model="none",
    )
    assert report.cache_hits == 0 and report.live_calls == 0
    assert len(report.missing) == len(comps)
    assert all(c.model_class is None for c in out)
