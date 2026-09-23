"""Клиент внешней LLM. Получает только замаскированный текст."""

from __future__ import annotations

import time

import httpx
import regex as re
import structlog

from ..observe.metrics import Metrics

log = structlog.get_logger()
_metrics = Metrics()

# Плейсхолдер: [ФИО_1], [ТЕЛЕФОН_2] и т.п.
PLACEHOLDER_RE = re.compile(r"\[[\p{Lu}_]+_\d+\]", re.VERSION1)

SYSTEM_PROMPT = (
    "В тексте персональные данные заменены метками вида [ФИО_1], [ТЕЛЕФОН_2] и т.п. "
    "Сохраняй такие метки в ответе дословно, не раскрывай и не придумывай данные за ними."
)

_ALLOWED_PARAMS = {"temperature", "max_tokens", "top_p", "stop", "response_format"}


class LLMError(Exception):
    """Ошибка внешней LLM."""

    def __init__(self, code: str, status: int) -> None:
        super().__init__(code)
        self.code = code
        self.status = status


class LLMClient:
    """Клиент внешней LLM с демо-режимом."""

    def __init__(
        self, base_url: str, api_key: str, model: str, timeout: float, verify: bool
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.configured = bool(base_url)
        self.model = model
        self.timeout = timeout
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout, connect=5.0),
            verify=verify,
            headers=headers,
            limits=httpx.Limits(max_connections=200, max_keepalive_connections=50),
            follow_redirects=False,
        )

    def _upstream(self, messages: list[dict]) -> list[dict]:
        return [{"role": "system", "content": SYSTEM_PROMPT}, *messages]

    def _build_body(self, params: dict, upstream: list[dict]) -> dict:
        """Собирает тело запроса к LLM."""
        body = {
            "model": params.get("model") or self.model,
            "messages": upstream,
            "stream": False,
        }
        for key in _ALLOWED_PARAMS:
            if key in params and params[key] is not None:
                body[key] = params[key]
        return body

    def _parse_response(self, resp, t: float) -> dict:
        """Проверяет статус и разбирает ответ LLM."""
        _metrics.llm_seconds.observe(time.perf_counter() - t)
        if resp.status_code == 429:
            raise LLMError("llm_rate_limited", 429)
        if resp.status_code >= 400:
            log.warning("llm.error", status=resp.status_code)
            raise LLMError("llm_error", 502)
        try:
            data = resp.json()
        except Exception as exc:
            raise LLMError("llm_bad_response", 502) from exc
        try:
            data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError("llm_bad_response", 502) from exc
        usage = data.get("usage") or {}
        for key, direction in (("prompt_tokens", "prompt"), ("completion_tokens", "completion")):
            val = usage.get(key)
            if isinstance(val, int):
                _metrics.llm_tokens_total.labels(direction=direction).inc(val)
        return data

    async def complete(self, messages: list[dict], params: dict) -> dict:
        """Отправляет диалог в LLM и возвращает ответ в формате chat.completion."""
        upstream = self._upstream(messages)
        if not self.configured:
            return self._demo(upstream)
        body = self._build_body(params, upstream)
        t = time.perf_counter()
        try:
            resp = await self._client.post(f"{self.base_url}/chat/completions", json=body)
        except httpx.TimeoutException as exc:
            _metrics.llm_seconds.observe(time.perf_counter() - t)
            raise LLMError("llm_timeout", 504) from exc
        except httpx.HTTPError as exc:
            _metrics.llm_seconds.observe(time.perf_counter() - t)
            raise LLMError("llm_unavailable", 502) from exc
        return self._parse_response(resp, t)

    def _demo(self, upstream: list[dict]) -> dict:
        last = upstream[-1].get("content", "") if upstream else ""
        tokens = sorted(set(PLACEHOLDER_RE.findall(last)))
        if tokens:
            ref = "Данные клиента из запроса: " + ", ".join(tokens) + "."
        else:
            ref = "Персональных данных в запросе нет."
        content = (
            "Демо-ответ: внешняя LLM не настроена (LLM_BASE_URL пуст). Обращение обработано. " + ref
        )
        return {
            "id": "demo",
            "model": "demo",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0},
        }

    async def close(self) -> None:
        await self._client.aclose()
