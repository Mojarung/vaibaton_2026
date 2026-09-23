"""Маршрут POST /process для OpenAPI и как образец поведения."""

from __future__ import annotations

import orjson
from fastapi import APIRouter, Request

from ..errors import ApiError
from ..service import estimate_tokens
from .deps import current_system, log_outcome

router = APIRouter()

MAX_PAYLOAD_ID = 256


def parse_body(body: bytes, max_chars: int) -> tuple[str, str]:
    """Разбирает JSON и возвращает (payload, payload_id)."""
    try:
        data = orjson.loads(body)
    except Exception as exc:
        raise ApiError("invalid_json", 400, "Некорректный JSON") from exc
    if not isinstance(data, dict):
        raise ApiError("invalid_request", 422, "Тело запроса должно быть объектом")
    payload = data.get("payload")
    payload_id = data.get("payload_id")
    if isinstance(payload_id, int) and not isinstance(payload_id, bool):
        payload_id = str(payload_id)
    if not isinstance(payload, str):
        raise ApiError("invalid_request", 422, "Поле payload обязательно и должно быть строкой")
    if not isinstance(payload_id, str) or not payload_id or len(payload_id) > MAX_PAYLOAD_ID:
        raise ApiError("invalid_request", 422, "Поле payload_id обязательно и должно быть строкой")
    if len(payload) > max_chars:
        raise ApiError("payload_too_large", 413, "Текст слишком длинный")
    return payload, payload_id


@router.post(
    "/process",
    summary="Маскирование или демаскирование по паре",
    description=(
        "Первый запрос с новым payload_id маскирует, запрос с тем же id и полученной "
        "маской возвращает исходник. Эндпоинт идемпотентен."
    ),
)
async def process(request: Request) -> dict:
    body = await request.body()
    payload, payload_id = parse_body(body, request.app.state.ctx.settings.max_text_chars)
    system = current_system(request)
    outcome = await request.app.state.ctx.service.process(system, payload, payload_id)
    log_outcome(
        request,
        outcome.direction,
        outcome.counts,
        outcome.stages_ms,
        len(payload),
        estimate_tokens(payload),
    )
    return {"result": outcome.result}
