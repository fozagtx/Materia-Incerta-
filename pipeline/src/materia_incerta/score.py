"""Score masked feature comparisons with an LLM, through a response cache.

The cache is the source of truth for a rebuild: `run --all` reads it and never
calls a model. A live call needs an explicit client, which the CLI only builds
when `--live` is passed and LLM_API_KEY / LLM_MODEL are set.

Evidence rule: every non-absent class must quote the ancient and the modern
text verbatim. A missing or unverifiable quote turns the class into absent,
and the coercion is recorded in the reason.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from pydantic import ValidationError

from .mask import NameLexicon, assert_masked, lexicon_for_name, mask
from .schemas import (
    CacheEntry,
    Candidate,
    ComparisonRequest,
    ComparisonResponse,
    DmmPlant,
    FeatureComparison,
    HistoricalName,
)

#: Bump this whenever the prompt text or the response schema changes.
#: The version is part of the cache key, so old responses are kept, not reused.
PROMPT_VERSION = "draft-0"

PROMPT_TEMPLATE = """\
You compare two botanical descriptions of one feature. Names have been replaced \
with [PLANT]. Do not guess which plant is meant.

Feature category: {category}

Ancient description:
<<<
{ancient_text}
>>>

Modern description:
<<<
{modern_text}
>>>

Classify how well the modern description matches the ancient one for this feature:
- "good": they describe the same state of the feature
- "partial": they overlap but differ in part
- "no_match": both describe the feature and they contradict
- "absent": one of them does not describe the feature

For any class other than "absent", copy the supporting words exactly into \
"ancient_quote" and "modern_quote". If you cannot quote both, answer "absent".

Answer with JSON only, matching this schema:
{schema}
"""


class CacheMissError(LookupError):
    """No cached response and no live client."""


class LLMClient(Protocol):
    """Minimal interface a provider adapter must implement."""

    model: str

    def complete_json(self, prompt: str, schema: dict) -> str:
        """Return the model's raw JSON text for `prompt`."""
        ...


def client_from_env() -> LLMClient:
    """Build the live client. The provider has not been chosen yet.

    When it is, implement an adapter with `complete_json` that requests
    structured output for `schema`, and return it here. Keys come only from
    LLM_API_KEY and LLM_MODEL.
    """
    if not os.environ.get("LLM_API_KEY") or not os.environ.get("LLM_MODEL"):
        raise RuntimeError("set LLM_API_KEY and LLM_MODEL to score live")
    raise NotImplementedError(
        "No LLM provider adapter yet. The team has not chosen a provider (AGENTS.md)."
    )


def response_schema() -> dict:
    return ComparisonResponse.model_json_schema()


def build_prompt(request: ComparisonRequest, lexicon: NameLexicon) -> str:
    """Render the prompt, refusing if any inserted field still holds a name.

    The gate checks every field that varies between plants. The template and
    schema are the same for every plant, so they can't leak which one is
    meant, and a stem that happens to match template words (genus Modelia vs
    "model") is not a leak.
    """
    for field_text in (request.category, request.ancient_text, request.modern_text):
        assert_masked(field_text, lexicon)
    return PROMPT_TEMPLATE.format(
        category=request.category,
        ancient_text=request.ancient_text,
        modern_text=request.modern_text,
        schema=json.dumps(response_schema(), sort_keys=True),
    )


def cache_key(model: str, prompt: str) -> str:
    payload = json.dumps(
        {"model": model, "prompt_version": PROMPT_VERSION, "prompt": prompt},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass
class ResponseCache:
    root: Path

    def _path(self, key: str) -> Path:
        return self.root / key[:2] / f"{key}.json"

    def get(self, key: str) -> CacheEntry | None:
        path = self._path(key)
        if not path.exists():
            return None
        entry = CacheEntry.model_validate_json(path.read_text(encoding="utf-8"))
        if entry.cache_key != key:
            raise ValueError(f"cache file {path} holds key {entry.cache_key}")
        return entry

    def put(self, entry: CacheEntry) -> None:
        path = self._path(entry.cache_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(entry.model_dump_json(indent=2), encoding="utf-8")


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def enforce_evidence(response: ComparisonResponse, request: ComparisonRequest) -> ComparisonResponse:
    """Turn any unsupported claim into absent."""
    if response.match_class == "absent":
        return response
    problems = []
    for side, quote, source in (
        ("ancient", response.ancient_quote, request.ancient_text),
        ("modern", response.modern_quote, request.modern_text),
    ):
        if quote is None:
            problems.append(f"no {side} quote")
        elif _norm(quote) not in _norm(source):
            problems.append(f"{side} quote not found in text")
    if not problems:
        return response
    return ComparisonResponse(
        match_class="absent",
        reason=f"[coerced from {response.match_class}: {'; '.join(problems)}] {response.reason}"[:2000],
        ancient_quote=None,
        modern_quote=None,
    )


def parse_response(raw: str, request: ComparisonRequest) -> ComparisonResponse:
    """Validate raw model output. Invalid output raises; it is never repaired."""
    try:
        response = ComparisonResponse.model_validate_json(raw)
    except ValidationError as exc:
        raise ValueError(f"{request.comparison_id}: invalid model response: {exc}") from exc
    return enforce_evidence(response, request)


_CLEARED = {
    "model_class": None,
    "model_reason": None,
    "model_ancient_quote": None,
    "model_modern_quote": None,
    "cache_key": None,
}


@dataclass
class ScoreReport:
    scored: int = 0
    cache_hits: int = 0
    live_calls: int = 0
    missing: list[str] = field(default_factory=list)
    skipped_no_text: list[str] = field(default_factory=list)


def score_comparisons(
    comparisons: Sequence[FeatureComparison],
    names: Sequence[HistoricalName],
    dmm_plants: Sequence[DmmPlant],
    candidates: Sequence[Candidate],
    cache: ResponseCache,
    *,
    model: str,
    client: LLMClient | None = None,
    only_lemmas: set[str] | None = None,
    unmasked: bool = False,
) -> tuple[list[FeatureComparison], ScoreReport]:
    """Fill model_class/model_reason from the cache, calling `client` on a miss.

    With client=None, misses are reported and left unscored.
    `unmasked=True` is only for the memorisation test; it skips masking but
    still uses its own cache keys, since the prompt differs.
    """
    report = ScoreReport()
    cand_by_key = {c.candidate_key: c for c in candidates}
    name_by_lemma = {n.lemma_tag: n for n in names}
    lexicons: dict[str, NameLexicon] = {}
    empty = NameLexicon()

    out: list[FeatureComparison] = []
    for comp in comparisons:
        cand = cand_by_key[comp.candidate_key]
        if only_lemmas is not None and cand.lemma_tag not in only_lemmas:
            out.append(comp)
            continue
        if comp.ancient_text is None or comp.modern_text is None:
            report.skipped_no_text.append(comp.comparison_id)
            out.append(comp.model_copy(update=_CLEARED))
            continue
        if cand.lemma_tag not in lexicons:
            lexicons[cand.lemma_tag] = lexicon_for_name(
                name_by_lemma[cand.lemma_tag], dmm_plants, candidates
            )
        lexicon = lexicons[cand.lemma_tag]
        if unmasked:
            ancient, modern, gate = comp.ancient_text, comp.modern_text, empty
        else:
            ancient, modern, gate = mask(comp.ancient_text, lexicon), mask(comp.modern_text, lexicon), lexicon
        request = ComparisonRequest(
            comparison_id=comp.comparison_id,
            category=comp.category,
            ancient_text=ancient,
            modern_text=modern,
        )
        prompt = build_prompt(request, gate)
        key = cache_key(model, prompt)
        entry = cache.get(key)
        if entry is None:
            if client is None:
                # Clear any earlier result: a rebuild reflects the cache only.
                report.missing.append(comp.comparison_id)
                out.append(comp.model_copy(update=_CLEARED))
                continue
            raw = client.complete_json(prompt, response_schema())
            entry = CacheEntry(
                cache_key=key,
                model=model,
                prompt_version=PROMPT_VERSION,
                prompt=prompt,
                raw_response=raw,
            )
            cache.put(entry)
            report.live_calls += 1
        else:
            report.cache_hits += 1
        response = parse_response(entry.raw_response, request)
        out.append(
            comp.model_copy(
                update={
                    "model_class": response.match_class,
                    "model_reason": response.reason,
                    "model_ancient_quote": response.ancient_quote,
                    "model_modern_quote": response.modern_quote,
                    "cache_key": key,
                }
            )
        )
        report.scored += 1
    return out, report
