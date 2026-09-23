"""Маршруты /v1: маскирование, демаскирование, сессии, типы."""

from __future__ import annotations

import re

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, Field

from ..errors import ApiError
from ..service import estimate_tokens
from .deps import current_system, log_outcome

router = APIRouter(prefix="/v1", tags=["mask"])

_SESSION_ID_RE = re.compile(r"^[0-9a-f]{32}$")


class MaskRequest(BaseModel):
    model_config = {"extra": "forbid"}

    text: str = Field(max_length=1_000_000)


class EntityOut(BaseModel):
    type: str
    subtype: str | None
    token: str
    start: int
    end: int
    source_start: int
    source_end: int


class MaskResponse(BaseModel):
    masked: str
    session_id: str | None
    entities: list[EntityOut]
    counts: dict
    elapsed_ms: float


class UnmaskRequest(BaseModel):
    model_config = {"extra": "forbid"}

    text: str = Field(max_length=2_000_000)
    session_id: str | None = None


class UnmaskResponse(BaseModel):
    text: str
    elapsed_ms: float


@router.post("/mask", response_model=MaskResponse)
async def mask(request: Request, body: MaskRequest) -> MaskResponse:
    system = current_system(request)
    outcome = await request.app.state.ctx.service.mask_session(system, body.text)
    log_outcome(
        request,
        outcome.direction,
        outcome.counts,
        outcome.stages_ms,
        len(body.text),
        estimate_tokens(body.text),
    )
    return MaskResponse(
        masked=outcome.result,
        session_id=outcome.session_id,
        entities=[
            EntityOut(
                type=e.type,
                subtype=e.subtype,
                token=e.token,
                start=e.start,
                end=e.end,
                source_start=e.source_start,
                source_end=e.source_end,
            )
            for e in outcome.entries
        ],
        counts=dict(outcome.counts),
        elapsed_ms=sum(outcome.stages_ms.values()),
    )


@router.post("/unmask", response_model=UnmaskResponse)
async def unmask(request: Request, body: UnmaskRequest) -> UnmaskResponse:
    system = current_system(request)
    if not system.policy.unmask:
        raise ApiError("unmask_disabled", 403, "Демаскирование отключено")
    if not body.session_id or not _SESSION_ID_RE.match(body.session_id):
        raise ApiError("invalid_session_id", 422, "Некорректный session_id")
    outcome = await request.app.state.ctx.service.unmask_session(system, body.text, body.session_id)
    log_outcome(
        request,
        outcome.direction,
        outcome.counts,
        outcome.stages_ms,
        len(body.text),
        estimate_tokens(body.text),
    )
    return UnmaskResponse(text=outcome.result, elapsed_ms=sum(outcome.stages_ms.values()))


@router.delete("/sessions/{session_id}", status_code=204)
async def forget_session(request: Request, session_id: str) -> Response:
    if not _SESSION_ID_RE.match(session_id):
        raise ApiError("invalid_session_id", 422, "Некорректный session_id")
    system = current_system(request)
    await request.app.state.ctx.service.forget_session(system, session_id)
    return Response(status_code=204)


@router.get("/types")
async def types(request: Request) -> dict:
    registry = request.app.state.ctx.detector.registry
    return {"types": [{"id": name, "label": registry.label(name)} for name in registry.names()]}
