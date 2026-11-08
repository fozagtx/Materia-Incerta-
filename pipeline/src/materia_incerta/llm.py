"""LLM provider adapter: Nebius Token Factory, via its OpenAI-compatible API.

Only `score.py` calls this, and only from `python -m materia_incerta score`.
`run --all` never does: it reads the response cache.

Configuration, all from the environment:
- LLM_API_KEY   bearer key (secret, never logged)
- LLM_MODEL     model ID as Nebius lists it, e.g. meta-llama/Llama-3.3-70B-Instruct
- LLM_BASE_URL  optional, defaults to Nebius Token Factory

Any other OpenAI-compatible endpoint works by changing LLM_BASE_URL.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field

NEBIUS_BASE_URL = "https://api.tokenfactory.nebius.com/v1"

#: transport(url, headers, body) -> (status code, response text)
Transport = Callable[[str, dict[str, str], bytes], tuple[int, str]]

RETRY_STATUS = {408, 409, 429, 500, 502, 503, 504}


class LLMError(RuntimeError):
    """The provider refused or failed a request."""


def urllib_transport(url: str, headers: dict[str, str], body: bytes, *, timeout: float = 120) -> tuple[int, str]:
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")


@dataclass
class OpenAICompatibleClient:
    """Chat-completions client that asks for JSON matching a schema.

    It first sends `response_format: json_schema`. If the provider rejects
    that (HTTP 400 naming response_format or json_schema), it switches to
    `json_object` for the rest of the run. Either way, score.py validates the
    answer against the Pydantic schema, so a malformed reply never passes.
    """

    model: str
    api_key: str = field(repr=False)
    base_url: str = NEBIUS_BASE_URL
    temperature: float = 0.0
    max_tokens: int = 800
    max_attempts: int = 4
    transport: Transport = urllib_transport
    sleep: Callable[[float], None] = time.sleep
    json_mode: str = "json_schema"

    def _payload(self, prompt: str, schema: dict) -> dict:
        if self.json_mode == "json_schema":
            response_format = {
                "type": "json_schema",
                "json_schema": {"name": "comparison_response", "schema": schema},
            }
        else:
            response_format = {"type": "json_object"}
        return {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "response_format": response_format,
        }

    def complete_json(self, prompt: str, schema: dict) -> str:
        url = self.base_url.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        attempt = 0
        while True:
            attempt += 1
            body = json.dumps(self._payload(prompt, schema)).encode("utf-8")
            status, text = self.transport(url, headers, body)
            if status == 200:
                return _content(text)
            lowered = text.lower()
            if (
                status == 400
                and self.json_mode == "json_schema"
                and ("response_format" in lowered or "json_schema" in lowered)
            ):
                self.json_mode = "json_object"
                attempt -= 1  # a format switch is not a failed attempt
                continue
            if status in RETRY_STATUS and attempt < self.max_attempts:
                self.sleep(min(2 ** attempt, 30))
                continue
            raise LLMError(f"{url} returned HTTP {status}: {_short(text)}")


def _content(text: str) -> str:
    try:
        data = json.loads(text)
        content = data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise LLMError(f"unexpected response shape: {_short(text)}") from exc
    if not isinstance(content, str) or not content.strip():
        raise LLMError("model returned empty content")
    return _strip_fences(content)


def _strip_fences(content: str) -> str:
    """Some models wrap JSON in ```json fences even in JSON mode."""
    s = content.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else ""
        if s.rstrip().endswith("```"):
            s = s.rstrip()[:-3]
    return s.strip()


def _short(text: str, limit: int = 300) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit] + "..."


def client_from_env(env: dict[str, str] | None = None) -> OpenAICompatibleClient:
    env = dict(os.environ) if env is None else env
    key = env.get("LLM_API_KEY", "").strip()
    model = env.get("LLM_MODEL", "").strip()
    if not key or not model:
        raise RuntimeError(
            "set LLM_API_KEY and LLM_MODEL to score live "
            "(LLM_MODEL is a Nebius model ID, e.g. meta-llama/Llama-3.3-70B-Instruct)"
        )
    return OpenAICompatibleClient(
        model=model,
        api_key=key,
        base_url=env.get("LLM_BASE_URL", "").strip() or NEBIUS_BASE_URL,
    )
