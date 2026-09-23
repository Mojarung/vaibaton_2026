"""Реестр систем: загрузка политик, аутентификация, горячая перезагрузка."""

from __future__ import annotations

import hmac
import os
import re
from dataclasses import dataclass
from pathlib import Path

import structlog
import yaml

from ..core.types import DetectionOptions
from ..errors import ApiError
from .models import SystemPolicy, SystemsFile

log = structlog.get_logger()

_SYSTEM_ID_RE = re.compile(r"^[a-z0-9_-]{1,48}$")

_HEADER = (
    "# Политики систем-потребителей.\n"
    "# Файл перечитывается на лету. Запрос без заголовков X-System-Id и X-Api-Key\n"
    "# обслуживает default_system. Админ-API (PUT и DELETE /admin/systems/{id})\n"
    "# перезаписывает файл целиком.\n"
)


@dataclass(frozen=True, slots=True)
class ResolvedSystem:
    """Собранная система: политика, опции детекции, типы."""

    id: str
    policy: SystemPolicy
    options: DetectionOptions
    entity_types: frozenset[str]


class SystemRegistry:
    """Реестр систем с горячей перезагрузкой."""

    def __init__(self, path: str | Path, known_types: set[str]) -> None:
        self.path = Path(path)
        self.known_types = known_types
        self.version = 0
        self._systems: dict[str, ResolvedSystem] = {}
        self._default_system = "default"
        self.load()

    @property
    def default_system(self) -> str:
        return self._default_system

    def load(self) -> None:
        """Читает YAML и собирает все системы; подмена целиком после успеха."""
        with open(self.path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        file = SystemsFile.model_validate(data)
        defaults = SystemPolicy.model_validate(file.defaults or {})
        systems: dict[str, ResolvedSystem] = {}
        for sid, raw in file.systems.items():
            systems[sid] = self._build(sid, defaults, raw)
        if file.default_system not in systems:
            raise ValueError(f"Система по умолчанию {file.default_system!r} не описана")
        self._systems = systems
        self._default_system = file.default_system
        self.version += 1

    def _build(self, sid: str, defaults: SystemPolicy, raw: dict) -> ResolvedSystem:
        if not _SYSTEM_ID_RE.match(sid):
            raise ValueError(f"Недопустимый id системы: {sid!r}")
        merged = defaults.model_dump()
        merged.update(raw)
        policy = SystemPolicy.model_validate(merged)
        types = set(self.known_types) if policy.entity_types == "all" else set(policy.entity_types)
        types -= set(policy.exclude_types)
        referenced = set(types)
        referenced |= set(policy.type_modes)
        for rule in policy.combo_rules:
            referenced.add(rule.type)
            referenced |= set(rule.requires)
        unknown = referenced - self.known_types
        if unknown:
            raise ValueError(f"Система {sid}: неизвестные типы ПДн {sorted(unknown)}")
        combo = tuple(
            (rule.type, frozenset(rule.requires), rule.window) for rule in policy.combo_rules
        )
        options = DetectionOptions(
            entity_types=frozenset(types),
            contextual=policy.contextual,
            single_value_mode=policy.single_value_mode,
            bare_date_policy=policy.bare_date_policy,
            combo_rules=combo,
        )
        return ResolvedSystem(id=sid, policy=policy, options=options, entity_types=frozenset(types))

    def get(self, system_id: str) -> ResolvedSystem:
        return self._systems[system_id]

    def authenticate(self, system_id: str, api_key: str | None) -> ResolvedSystem:
        sid = system_id or self._default_system
        system = self._systems.get(sid)
        if system is None:
            raise ApiError("unknown_system", 401, "Система не зарегистрирована")
        if not system.policy.enabled:
            raise ApiError("system_disabled", 403, "Система отключена")
        env_name = system.policy.api_key_env
        if env_name:
            expected = os.environ.get(env_name, "")
            provided = api_key or ""
            if not expected or not provided or not hmac.compare_digest(expected, provided):
                raise ApiError("invalid_api_key", 401, "Неверный ключ API")
        return system

    def update_system(self, sid: str, patch: dict) -> ResolvedSystem:
        data = self._read_raw()
        systems = data.get("systems", {})
        merged = dict(systems.get(sid, {}))
        merged.update(patch)
        defaults = SystemPolicy.model_validate(data.get("defaults") or {})
        system = self._build(sid, defaults, merged)
        systems[sid] = merged
        data["systems"] = systems
        self._write_raw(data)
        self.load()
        return system

    def delete_system(self, sid: str) -> None:
        data = self._read_raw()
        if sid == data.get("default_system", "default"):
            raise ApiError("cannot_delete_default", 409, "Систему по умолчанию удалить нельзя")
        systems = data.get("systems", {})
        if sid not in systems:
            raise ApiError("unknown_system", 404, "Система не найдена")
        del systems[sid]
        data["systems"] = systems
        self._write_raw(data)
        self.load()

    def _read_raw(self) -> dict:
        with open(self.path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _write_raw(self, data: dict) -> None:
        tmp = self.path.with_name(f".systems-{os.getpid()}.yaml")
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(_HEADER)
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
        os.replace(tmp, self.path)

    async def watch(self, on_reload=None) -> None:
        """Асинхронный цикл на watchfiles.awatch."""
        import watchfiles  # noqa: PLC0415 — ленивая загрузка: watchfiles нужен только при слежении

        async for _changes in watchfiles.awatch(
            self.path.parent, stop_event=None, debounce=200, recursive=False
        ):
            try:
                self.load()
                log.info("config.reloaded", file=str(self.path), version=self.version)
                if on_reload is not None:
                    on_reload()
            except Exception:
                log.exception("config.reload_failed", file=str(self.path))
