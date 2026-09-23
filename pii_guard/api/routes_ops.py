"""Служебные маршруты: демо, здоровье, метрики, статистика."""

from __future__ import annotations

from pathlib import Path

import orjson
import redis
from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse

from ..observe.live import summarize
from ..observe.metrics import render as render_metrics

router = APIRouter()

_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@router.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse("/demo")


@router.get("/demo", include_in_schema=False)
async def demo() -> HTMLResponse:
    html = (_STATIC_DIR / "demo.html").read_text(encoding="utf-8")
    return HTMLResponse(html, media_type="text/html; charset=utf-8")


@router.get("/health/live")
async def health_live() -> dict:
    return {"status": "ok"}


@router.get("/health/ready")
async def health_ready(request: Request) -> dict:
    ctx = request.app.state.ctx
    vault_ok = await ctx.vault.ping()
    llm = ctx.llm
    return {
        "status": "ok" if vault_ok else "degraded",
        "store": {"backend": ctx.vault.backend, "ok": vault_ok},
        "llm": {
            "configured": llm.configured,
            "model": llm.model if llm.configured else "demo",
        },
        "rules": len(ctx.detector.rules),
        "systems_version": ctx.systems.version,
    }


@router.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    body, content_type = render_metrics()
    return Response(content=body, media_type=content_type)


@router.get("/stats", include_in_schema=False)
async def stats(request: Request) -> dict:
    ctx = request.app.state.ctx
    snapshots = []
    if ctx.vault.redis is not None:
        try:
            keys = [
                key
                async for key in ctx.vault.redis.scan_iter(
                    match=f"{ctx.settings.store_prefix}:live:*", count=100
                )
            ]
            if keys:
                values = await ctx.vault.redis.mget(keys)
                snapshots.extend(orjson.loads(v) for v in values if v)
        except redis.exceptions.RedisError, OSError, orjson.JSONDecodeError:
            snapshots = []
    if not snapshots:
        snapshots = [ctx.live.snapshot()]
    return summarize(snapshots)
