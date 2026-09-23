"""Зависимости и общий контекст приложения."""

from __future__ import annotations

import hmac
from dataclasses import dataclass

from fastapi import Request

from ..errors import ApiError


@dataclass(slots=True)
class AppContext:
    """Общий контекст приложения."""

    settings: object
    detector: object
    systems: object
    service: object
    vault: object
    llm: object
    live: object

    def reload_detection(self) -> None:
        """Перечитывает детекцию и политики после правки правил."""
        self.detector.reload()
        registry = self.detector.registry
        self.service.masker.registry = registry
        self.systems.known_types = set(registry.names())
        self.systems.load()


def ctx(request: Request) -> AppContext:
    return request.app.state.ctx


def current_system(request: Request):
    """Аутентифицирует систему по заголовкам."""
    api_key = request.headers.get("x-api-key")
    if not api_key:
        auth = request.headers.get("authorization", "")
        if auth.startswith("Bearer "):
            api_key = auth[len("Bearer ") :]
    system_id = request.headers.get("x-system-id")
    system = request.app.state.ctx.systems.authenticate(system_id, api_key)
    request.state.log["system"] = system.id
    return system


def require_admin(request: Request) -> None:
    """Проверяет админ-ключ."""
    settings = request.app.state.ctx.settings
    admin_key = settings.admin_key.get_secret_value()
    if not admin_key:
        raise ApiError("admin_disabled", 403, "Админ-API выключен: не задан ADMIN_KEY")
    provided = request.headers.get("x-admin-key", "")
    if not hmac.compare_digest(admin_key, provided):
        raise ApiError("admin_key_required", 403, "Неверный админ-ключ")


def log_outcome(
    request: Request,
    direction: str,
    counts: dict,
    stages: dict,
    chars: int,
    tokens_in: int,
    tokens_out: int = 0,
) -> None:
    """Дописывает итог запроса в словарь лога."""
    request.state.log["direction"] = direction
    request.state.log["entities"] = dict(counts)
    request.state.log["chars"] = chars
    request.state.log["tokens_in"] = tokens_in
    request.state.log["tokens_out"] = tokens_out
    request.state.log.update(stages)
