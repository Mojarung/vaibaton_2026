"""Быстрый путь POST /process без FastAPI-роутинга."""

from __future__ import annotations

import orjson
import structlog

from ..errors import ApiError
from ..service import estimate_tokens
from .deps import AppContext
from .routes_process import parse_body

log = structlog.get_logger()

PATH = "/process"


async def _read_body(receive, max_body: int) -> bytes:
    chunks: list[bytes] = []
    size = 0
    while True:
        message = await receive()
        if message["type"] == "http.disconnect":
            raise ApiError("body_too_large", 413, "Тело запроса слишком большое")
        chunk = message.get("body", b"")
        chunks.append(chunk)
        size += len(chunk)
        if size > max_body:
            raise ApiError("body_too_large", 413, "Тело запроса слишком большое")
        if not message.get("more_body"):
            break
    return b"".join(chunks)


def _api_key(scope: dict) -> str | None:
    headers = scope.get("headers") or []
    api_key = None
    for name, value in headers:
        if name == b"x-api-key":
            api_key = value.decode("latin-1")
    if not api_key:
        for name, value in headers:
            if name == b"authorization" and value.startswith(b"Bearer "):
                api_key = value[len(b"Bearer ") :].decode("latin-1")
    return api_key


async def _send_json(send, status: int, payload: dict, request_id: str) -> None:
    body = orjson.dumps(payload)
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode()),
                (b"x-request-id", request_id.encode()),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})


async def handle_process(ctx: AppContext, scope: dict, receive, send, state: dict) -> None:
    """Обрабатывает POST /process как голое ASGI-приложение."""
    request_id = state["request_id"]
    log_dict = state["log"]
    try:
        body = await _read_body(receive, ctx.settings.max_body_bytes)
        payload, payload_id = parse_body(body, ctx.settings.max_text_chars)
        system = ctx.systems.authenticate(scope.get("x-system-id"), _api_key(scope))
        log_dict["system"] = system.id
        outcome = await ctx.service.process(system, payload, payload_id)
        log_dict["direction"] = outcome.direction
        log_dict["entities"] = dict(outcome.counts)
        log_dict["chars"] = len(payload)
        log_dict["tokens_in"] = estimate_tokens(payload)
        log_dict["tokens_out"] = 0
        log_dict.update(outcome.stages_ms)
        await _send_json(send, 200, {"result": outcome.result}, request_id)
    except ApiError as exc:
        log_dict["error"] = exc.code
        await _send_json(
            send,
            exc.status,
            {"error": exc.code, "message": exc.message, "request_id": request_id},
            request_id,
        )
    except Exception as exc:  # noqa: BLE001 — последний рубеж: любой сбой отдаём как 500
        log.error("request.failed", error=type(exc).__name__, request_id=request_id)
        await _send_json(
            send,
            500,
            {"error": "internal_error", "message": "Внутренняя ошибка", "request_id": request_id},
            request_id,
        )
