"""Сервис, связывающий детектор, маскировщик и хранилище."""

from __future__ import annotations

import secrets
import time
from collections import Counter
from dataclasses import dataclass, field

import structlog

from .core.types import Span
from .errors import ApiError
from .mask.masker import Masker, MaskResult
from .mask.restore import restore_positional, restore_tokens
from .observe.metrics import Metrics

CHARS_PER_TOKEN = 3.5
FAILSAFE_TYPE = "FAILSAFE"

_metrics = Metrics()


def estimate_tokens(text: str) -> int:
    """Грубая оценка токенов для TPS на русском."""
    if not text:
        return 0
    return max(1, round(len(text) / CHARS_PER_TOKEN))


@dataclass(slots=True)
class Outcome:
    """Результат обработки запроса."""

    result: str
    direction: str
    counts: Counter
    stages_ms: dict
    session_id: str | None = None
    entries: list = field(default_factory=list)


class ProtectionService:
    """Связывает детектор, маскировщик и хранилище."""

    def __init__(self, detector, masker: Masker, vault) -> None:
        self.detector = detector
        self.masker = masker
        self.vault = vault
        self.log = structlog.get_logger()

    def _detect(self, text: str, system, stages: dict) -> list[Span]:
        t = time.perf_counter()
        try:
            spans = self.detector.detect(text, system.options).spans
        except Exception as e:  # noqa: BLE001 — fail-closed: при сбое маскируем весь текст
            self.log.error("detect.failed_closed", error=type(e).__name__, length=len(text))
            if text:
                return [
                    Span(
                        start=0,
                        end=len(text),
                        type=FAILSAFE_TYPE,
                        confidence=1.0,
                        priority=200,
                        rule="failsafe",
                    )
                ]
            return []
        elapsed = time.perf_counter() - t
        stages["detect_ms"] = round(elapsed * 1000, 3)
        _metrics.stage_seconds.labels(stage="detect").observe(elapsed)
        return spans

    def new_session(self, system):
        return self.masker.session(
            system.policy.mask_mode,
            system.policy.type_modes,
            system.policy.placeholder_lang,
        )

    def mask_text(self, text: str, system, session, stages: dict) -> MaskResult:
        spans = self._detect(text, system, stages)
        t = time.perf_counter()
        result = session.mask(text, spans)
        stages["mask_ms"] = round((time.perf_counter() - t) * 1000, 3)
        for span_type, count in result.counts.items():
            _metrics.entities_total.labels(type=span_type, system=system.id).inc(count)
        return result

    def _build_record(self, text: str, mask_result: MaskResult, session) -> dict:
        return {
            "src": self.vault.digest(text),
            "msk": self.vault.digest(mask_result.text),
            "masked": mask_result.text,
            "entries": [[e.start, e.end, e.original] for e in mask_result.entries],
            "tokens": session.token_map,
        }

    def _add_store(self, stages: dict, seconds: float) -> None:
        stages["store_ms"] = stages.get("store_ms", 0.0) + seconds * 1000
        _metrics.stage_seconds.labels(stage="store").observe(seconds)

    async def _vault_get(self, address: str, stages: dict):
        t = time.perf_counter()
        try:
            return await self.vault.get(address)
        finally:
            self._add_store(stages, time.perf_counter() - t)

    async def _vault_put(
        self, address: str, record: dict, ttl: int, only_new: bool, stages: dict
    ) -> bool:
        t = time.perf_counter()
        try:
            return await self.vault.put(address, record, ttl, only_new=only_new)
        finally:
            self._add_store(stages, time.perf_counter() - t)

    async def _vault_delete(self, address: str, stages: dict) -> None:
        t = time.perf_counter()
        try:
            await self.vault.delete(address)
        finally:
            self._add_store(stages, time.perf_counter() - t)

    def _restore(self, payload: str, record: dict, stages: dict) -> Outcome:
        if self.vault.digest(payload) == record["msk"]:
            result = restore_positional(payload, [tuple(e) for e in record["entries"]])
            direction = "unmask"
        else:
            result, _ = restore_tokens(payload, record["tokens"])
            direction = "unmask_tokens"
        return Outcome(result=result, direction=direction, counts=Counter(), stages_ms=stages)

    @staticmethod
    def _has_token(payload: str, tokens: dict) -> bool:
        return any(tok in payload for tok in tokens)

    async def process(self, system, payload: str, payload_id: str) -> Outcome:
        """Контракт автопроверки: маска/демаска по паре payload_id."""
        stages: dict = {}
        session = self.new_session(system)
        address = self.vault.address("pair", system.id, payload_id)
        record = await self._vault_get(address, stages)
        src = self.vault.digest(payload)

        if record is not None:
            if src == record["src"] and src != record["msk"]:
                return Outcome(
                    result=record["masked"],
                    direction="mask_retry",
                    counts=Counter(),
                    stages_ms=stages,
                )
            if src == record["msk"] or self._has_token(payload, record["tokens"]):
                if not system.policy.unmask:
                    raise ApiError("unmask_disabled", 403, "Демаскирование отключено")
                return self._restore(payload, record, stages)

        mask_result = self.mask_text(payload, system, session, stages)
        record = self._build_record(payload, mask_result, session)
        existed = await self._vault_get(address, stages) is not None
        landed = await self._vault_put(
            address, record, system.policy.ttl_seconds, only_new=not existed, stages=stages
        )
        if not landed:
            current = await self._vault_get(address, stages)
            if current is not None and current["src"] == src:
                return Outcome(
                    result=current["masked"],
                    direction="mask_retry",
                    counts=Counter(),
                    stages_ms=stages,
                )
            await self._vault_put(
                address, record, system.policy.ttl_seconds, only_new=False, stages=stages
            )
        return Outcome(
            result=mask_result.text,
            direction="mask",
            counts=mask_result.counts,
            stages_ms=stages,
        )

    async def mask_session(self, system, text: str) -> Outcome:
        """Маскирование для /v1/mask с сохранением сессии."""
        stages: dict = {}
        session = self.new_session(system)
        mask_result = self.mask_text(text, system, session, stages)
        session_id = None
        if system.policy.unmask and mask_result.entries:
            session_id = secrets.token_hex(16)
            address = self.vault.address("session", system.id, session_id)
            record = self._build_record(text, mask_result, session)
            await self._vault_put(
                address, record, system.policy.ttl_seconds, only_new=False, stages=stages
            )
        return Outcome(
            result=mask_result.text,
            direction="mask",
            counts=mask_result.counts,
            stages_ms=stages,
            session_id=session_id,
            entries=mask_result.entries,
        )

    async def unmask_session(self, system, text: str, session_id: str) -> Outcome:
        if not system.policy.unmask:
            raise ApiError("unmask_disabled", 403, "Демаскирование отключено")
        stages: dict = {}
        address = self.vault.address("session", system.id, session_id)
        record = await self._vault_get(address, stages)
        if record is None:
            raise ApiError("session_not_found", 404, "Сессия не найдена или истёк срок хранения")
        return self._restore(text, record, stages)

    async def forget_session(self, system, session_id: str) -> None:
        stages: dict = {}
        address = self.vault.address("session", system.id, session_id)
        await self._vault_delete(address, stages)
