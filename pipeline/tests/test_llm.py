"""Nebius adapter, tested through a fake transport: no network, no key."""

import json

import pytest

from materia_incerta.llm import NEBIUS_BASE_URL, LLMError, OpenAICompatibleClient, client_from_env
from materia_incerta.score import ResponseCache, response_schema, score_comparisons

GOOD = json.dumps({"match_class": "absent", "reason": "modern text silent"})


def ok(content: str) -> tuple[int, str]:
    return 200, json.dumps({"choices": [{"message": {"role": "assistant", "content": content}}]})


class FakeTransport:
    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = []

    def __call__(self, url, headers, body):
        self.calls.append((url, headers, json.loads(body)))
        return self.replies.pop(0)


def client(transport, **kw):
    return OpenAICompatibleClient(model="Qwen/Qwen3-235B-A22B-Instruct-2507", api_key="sk-test",
                                  transport=transport, sleep=lambda s: None, **kw)


def test_request_shape():
    t = FakeTransport(ok(GOOD))
    out = client(t).complete_json("compare these", response_schema())
    assert out == GOOD
    url, headers, payload = t.calls[0]
    assert url == f"{NEBIUS_BASE_URL}/chat/completions"
    assert headers["Authorization"] == "Bearer sk-test"
    assert payload["model"] == "Qwen/Qwen3-235B-A22B-Instruct-2507"
    assert payload["messages"] == [{"role": "user", "content": "compare these"}]
    assert payload["temperature"] == 0.0
    assert payload["response_format"]["type"] == "json_schema"
    assert payload["response_format"]["json_schema"]["schema"] == response_schema()


def test_falls_back_to_json_mode_when_schema_output_is_rejected():
    t = FakeTransport(
        (400, '{"error": "response_format json_schema is not supported for this model"}'),
        ok(GOOD),
        ok(GOOD),
    )
    c = client(t)
    assert c.complete_json("p1", {}) == GOOD
    assert c.complete_json("p2", {}) == GOOD
    formats = [call[2]["response_format"]["type"] for call in t.calls]
    assert formats == ["json_schema", "json_object", "json_object"]


def test_retries_rate_limits_and_server_errors():
    t = FakeTransport((429, "slow down"), (503, "busy"), ok(GOOD))
    assert client(t).complete_json("p", {}) == GOOD
    assert len(t.calls) == 3


def test_gives_up_after_max_attempts():
    t = FakeTransport(*[(503, "busy")] * 4)
    with pytest.raises(LLMError, match="HTTP 503"):
        client(t).complete_json("p", {})


def test_auth_errors_fail_fast_without_leaking_the_key():
    t = FakeTransport((401, '{"error": "invalid api key"}'))
    with pytest.raises(LLMError) as exc:
        client(t).complete_json("p", {})
    assert len(t.calls) == 1
    assert "sk-test" not in str(exc.value)
    assert "sk-test" not in repr(client(t))


def test_strips_markdown_fences():
    t = FakeTransport(ok(f"```json\n{GOOD}\n```"))
    assert client(t).complete_json("p", {}) == GOOD


@pytest.mark.parametrize("reply", [(200, "not json"), (200, '{"choices": []}'), ok("   ")])
def test_bad_response_shapes_raise(reply):
    with pytest.raises(LLMError):
        client(FakeTransport(reply)).complete_json("p", {})


def test_client_from_env():
    with pytest.raises(RuntimeError, match="LLM_API_KEY"):
        client_from_env({})
    c = client_from_env({"LLM_API_KEY": "k", "LLM_MODEL": "m"})
    assert c.base_url == NEBIUS_BASE_URL and c.model == "m"
    c = client_from_env({"LLM_API_KEY": "k", "LLM_MODEL": "m", "LLM_BASE_URL": "https://example.test/v1"})
    assert c.base_url == "https://example.test/v1"


def test_end_to_end_with_scoring_and_cache(demo_tables, tmp_path):
    """A live-style run through the adapter fills the cache; a rerun is all cache hits."""
    comps = demo_tables["feature_comparisons"][:3]
    args = (comps, demo_tables["historical_names"], demo_tables["dmm_plants"], demo_tables["candidates"])
    cache = ResponseCache(tmp_path)
    c = client(FakeTransport(ok(GOOD), ok("{not valid"), ok(GOOD)))
    out, report = score_comparisons(*args, cache, model=c.model, client=c)
    assert report.live_calls == 3 and report.scored == 2
    assert report.invalid == [comps[1].comparison_id]
    assert out[1].model_class is None

    again, report2 = score_comparisons(*args, cache, model=c.model)
    assert report2.cache_hits == 3 and report2.live_calls == 0
    assert [x.model_class for x in again] == [x.model_class for x in out]
