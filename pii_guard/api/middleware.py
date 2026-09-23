"""Граничный ASGI-middleware: лимиты, request_id, учёт и быстрый /process."""

from __future__ import annotations

import secrets
import time

import orjson
import structlog

from ..observe.metrics import Metrics
from .fast_process import PATH, handle_process

log = structlog.get_logger()
_metrics = Metrics()

_QUIET_PATHS = {"/health", "/health/live", "/health/ready", "/metrics", "/stats", "/favicon.ico"}


class BoundaryMiddleware:
    """Чистый ASGI-middleware, не BaseHTTPMiddleware."""

    def __init__(self, app, max_concurrent: int, max_body: int, live) -> None:
        self.app = app
        self.max_concurrent = max_concurrent
        self.max_body = max_body
        self.live = live
        self.active = 0

    def _content_length(self, scope: dict) -> int:
        """Длина тела из заголовка content-length; 0, если нет или не число."""
        headers = scope.get("headers") or []
        for name, value in headers:
            if name == b"content-length":
                try:
                    return int(value)
                except ValueError:
                    return 0
        return 0

    def _wrap_send(self, send, request_id: str):
        """Оборачивает send, добавляя заголовки и запоминая статус."""
        holder = {"status": 500}

        async def wrapped_send(message):
            if message["type"] == "http.response.start":
                holder["status"] = message["status"]
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode()))
                headers.append((b"cache-control", b"no-store"))
                message["headers"] = headers
            await send(message)

        return wrapped_send, holder

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = secrets.token_hex(8)
        state = {"request_id": request_id, "log": {}}
        scope["state"] = state

        content_length = self._content_length(scope)
        route = self._route(scope)
        if content_length > self.max_body:
            _metrics.rejected_total.labels(reason="body_too_large").inc()
            await self._reject(send, 413, "body_too_large", request_id)
            return
        if self.active >= self.max_concurrent:
            _metrics.rejected_total.labels(reason="overloaded").inc()
            await self._reject(send, 429, "overloaded", request_id, retry_after="1")
            return

        self.active += 1
        _metrics.inflight_requests.inc()
        start = time.perf_counter()
        wrapped_send, holder = self._wrap_send(send, request_id)

        try:
            if (
                scope["method"] == "POST"
                and scope["path"] == PATH
                and hasattr(scope["app"], "state")
            ):
                ctx = scope["app"].state.ctx
                if ctx is not None:
                    await handle_process(ctx, scope, receive, wrapped_send, state)
                    return
            await self.app(scope, receive, wrapped_send)
        finally:
            self.active -= 1
            _metrics.inflight_requests.dec()
            elapsed = (time.perf_counter() - start) * 1000
            self._account(route, holder["status"], elapsed, state)

    def _route(self, scope: dict) -> str:
        route = scope.get("route")
        if route is not None:
            return getattr(route, "path", "unmatched")
        path = scope.get("path", "")
        if path == PATH or path in _QUIET_PATHS:
            return path
        return "unmatched"

    async def _reject(
        self, send, status: int, error: str, request_id: str, retry_after: str | None = None
    ) -> None:
        body = orjson.dumps(
            {"error": error, "message": "Запрос отклонён", "request_id": request_id}
        )
        headers = [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode()),
            (b"x-request-id", request_id.encode()),
            (b"cache-control", b"no-store"),
        ]
        if retry_after:
            headers.append((b"retry-after", retry_after.encode()))
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": body})

    def _account(self, route, status, elapsed, state) -> None:
        log_dict = state["log"]
        system = log_dict.get("system", "-")
        tokens_in = log_dict.get("tokens_in", 0)
        tokens_out = log_dict.get("tokens_out", 0)
        _metrics.requests_total.labels(route=route, system=system, status=str(status)).inc()
        _metrics.request_seconds.labels(route=route).observe(elapsed / 1000)
        if tokens_in:
            _metrics.tokens_total.labels(direction="in").inc(tokens_in)
        if tokens_out:
            _metrics.tokens_total.labels(direction="out").inc(tokens_out)
        if route in _QUIET_PATHS:
            return
        self.live.observe(elapsed, tokens_in, status >= 500)
        log.info(
            "request.done",
            request_id=state["request_id"],
            route=route,
            status=status,
            elapsed_ms=round(elapsed, 3),
            **log_dict,
        )
