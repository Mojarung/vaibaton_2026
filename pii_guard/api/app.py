"""Сборка FastAPI-приложения."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress
from pathlib import Path

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from ..core.engine import Detector
from ..errors import ApiError
from ..llm.client import LLMClient, LLMError
from ..mask.masker import Masker
from ..observe.live import LiveStats
from ..observe.logging import configure_logging
from ..policy.registry import SystemRegistry
from ..service import ProtectionService
from ..settings import get_settings
from ..store.vault import Vault
from .deps import AppContext
from .middleware import BoundaryMiddleware
from .routes_admin import router as admin_router
from .routes_chat import router as chat_router
from .routes_ops import router as ops_router
from .routes_process import router as process_router
from .routes_v1 import router as v1_router

log = structlog.get_logger()


async def _build_context(settings, live: LiveStats) -> AppContext:
    detector = Detector(settings.config_dir)
    registry = detector.registry
    systems = SystemRegistry(settings.config_dir / "systems.yaml", set(registry.names()))
    vault = await Vault.create(
        settings.redis_url,
        settings.vault_key.get_secret_value(),
        settings.store_prefix,
    )
    llm = LLMClient(
        settings.llm_base_url,
        settings.llm_api_key.get_secret_value(),
        settings.llm_model,
        settings.llm_timeout_seconds,
        settings.llm_verify_tls,
    )
    masker = Masker(registry)
    service = ProtectionService(detector, masker, vault)
    return AppContext(
        settings=settings,
        detector=detector,
        systems=systems,
        service=service,
        vault=vault,
        llm=llm,
        live=live,
    )


def _resolve_paths(changes: list[tuple]) -> set[Path]:
    return {Path(c[1]).resolve() for c in changes}


async def _watch_detection(context: AppContext) -> None:
    import watchfiles  # noqa: PLC0415 — ленивая загрузка: watchfiles нужен только при слежении

    config_dir = context.settings.config_dir
    async for changes in watchfiles.awatch(config_dir, debounce=300, recursive=True):
        paths = set(await asyncio.to_thread(_resolve_paths, changes))
        if paths and all(p.name == "systems.yaml" for p in paths):
            continue
        if all(p.name.startswith(".") or p.suffix == ".tmp" for p in paths):
            continue
        try:
            await asyncio.to_thread(context.reload_detection)
            log.info("detection.reloaded", rules=len(context.detector.rules))
        except Exception:
            log.exception("detection.reload_failed")


def _request_id(request: Request) -> str | None:
    state = getattr(request, "state", None)
    if state is None:
        return None
    return getattr(state, "request_id", None)


def _add_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(request: Request, exc: ApiError) -> JSONResponse:
        log_state = getattr(request.state, "log", None)
        if isinstance(log_state, dict):
            log_state["error"] = exc.code
        return JSONResponse(
            status_code=exc.status,
            content={
                "error": exc.code,
                "message": exc.message,
                "request_id": _request_id(request),
            },
        )

    @app.exception_handler(LLMError)
    async def _llm_error(request: Request, exc: LLMError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status,
            content={
                "error": exc.code,
                "message": "Внешняя LLM недоступна, данные не переданы",
                "request_id": _request_id(request),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        fields = []
        for err in exc.errors():
            loc = err.get("loc", ())
            fields.append(".".join(str(x) for x in loc if x != "body"))
        return JSONResponse(
            status_code=422,
            content={
                "error": "invalid_request",
                "fields": fields,
                "request_id": _request_id(request),
            },
        )

    @app.exception_handler(Exception)
    async def _generic_error(request: Request, exc: Exception) -> JSONResponse:
        log.error("request.failed", error=type(exc).__name__, request_id=_request_id(request))
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": "Внутренняя ошибка",
                "request_id": _request_id(request),
            },
        )


def create_app(settings=None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level, settings.app_name)
    live = LiveStats()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        context = await _build_context(settings, live)
        app.state.ctx = context
        tasks = [
            asyncio.create_task(context.systems.watch()),
            asyncio.create_task(_watch_detection(context)),
        ]
        if context.vault.redis is not None:
            tasks.append(
                asyncio.create_task(
                    context.live.publish_loop(context.vault.redis, settings.store_prefix)
                )
            )
        log.info(
            "app.started",
            store=context.vault.backend,
            rules=len(context.detector.rules),
            systems=len(context.systems._systems),
            llm=context.llm.configured,
        )
        try:
            yield
        finally:
            for task in tasks:
                task.cancel()
            for task in tasks:
                with suppress(asyncio.CancelledError):
                    await task
            await context.llm.close()
            await context.vault.close()

    app = FastAPI(
        title=f"{settings.app_name}: модуль безопасности персональных данных",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        BoundaryMiddleware,
        max_concurrent=settings.max_concurrent,
        max_body=settings.max_body_bytes,
        live=live,
    )
    app.include_router(process_router)
    app.include_router(v1_router)
    app.include_router(chat_router)
    app.include_router(admin_router)
    app.include_router(ops_router)
    _add_error_handlers(app)
    return app


app = create_app()
