"""Живая сводка за последние 60 секунд для эндпоинта /stats."""

from __future__ import annotations

import asyncio
import json
import os
import time
from bisect import bisect_left
from dataclasses import dataclass, field

import redis
import structlog

log = structlog.get_logger()

WINDOW = 60
# Границы гистограммы в миллисекундах, плюс корзина переполнения.
HIST_BOUNDS = [
    0.5,
    1,
    2,
    3,
    5,
    7.5,
    10,
    15,
    25,
    50,
    75,
    100,
    150,
    250,
    400,
    500,
    750,
    1000,
    2000,
    5000,
    10000,
]


@dataclass(slots=True)
class Bucket:
    """Данные одной секунды."""

    second: int
    requests: int = 0
    tokens: int = 0
    errors: int = 0
    hist: list[int] = field(default_factory=lambda: [0] * (len(HIST_BOUNDS) + 1))


class LiveStats:
    """Кольцо из 60 бакетов по индексу секунда по модулю 60."""

    def __init__(self) -> None:
        self.pid = os.getpid()
        self._buckets: list[Bucket | None] = [None] * WINDOW

    def _bucket(self, second: int) -> Bucket:
        idx = second % WINDOW
        b = self._buckets[idx]
        if b is None or b.second != second:
            b = Bucket(second=second)
            self._buckets[idx] = b
        return b

    def observe(self, elapsed_ms: float, tokens: int, error: bool) -> None:
        second = int(time.time())
        b = self._bucket(second)
        b.requests += 1
        b.tokens += tokens
        if error:
            b.errors += 1
        idx = bisect_left(HIST_BOUNDS, elapsed_ms)
        b.hist[idx] += 1

    def snapshot(self) -> dict:
        now = int(time.time())
        requests = tokens = errors = 0
        hist = [0] * (len(HIST_BOUNDS) + 1)
        per_second: dict[int, int] = {}
        for b in self._buckets:
            if b is None or now - b.second >= WINDOW:
                continue
            requests += b.requests
            tokens += b.tokens
            errors += b.errors
            for i, v in enumerate(b.hist):
                hist[i] += v
            per_second[b.second] = b.requests
        return {
            "pid": self.pid,
            "at": now,
            "requests": requests,
            "tokens": tokens,
            "errors": errors,
            "hist": hist,
            "per_second": per_second,
        }

    async def publish_loop(self, client, prefix: str) -> None:
        """Раз в секунду кладёт снимок в Redis; ошибки глотаются."""
        key = f"{prefix}:live:{self.pid}"
        while True:
            try:
                await client.set(key, _json_dumps(self.snapshot()), ex=5)
            except (redis.exceptions.RedisError, OSError) as exc:
                log.debug("live.publish_failed", error=type(exc).__name__)
            await asyncio.sleep(1)


def _json_dumps(obj) -> str:
    return json.dumps(obj)


def percentile(hist: list[int], q: float) -> float | None:
    """Верхняя граница корзины, в которую попадает квантиль."""
    total = sum(hist)
    if total == 0:
        return None
    target = total * q
    acc = 0
    for i, v in enumerate(hist):
        acc += v
        if acc >= target:
            if i >= len(HIST_BOUNDS):
                return HIST_BOUNDS[-1]
            return HIST_BOUNDS[i]
    return HIST_BOUNDS[-1]


def summarize(snapshots: list[dict]) -> dict:
    """Складывает снимки всех воркеров."""
    now = int(time.time())
    requests = errors = 0
    hist = [0] * (len(HIST_BOUNDS) + 1)
    per_second: dict[int, int] = {}
    earliest = now
    for snap in snapshots:
        requests += snap["requests"]
        errors += snap["errors"]
        for i, v in enumerate(snap["hist"]):
            hist[i] += v
        for raw_sec, cnt in snap["per_second"].items():
            sec = int(raw_sec)
            per_second[sec] = per_second.get(sec, 0) + cnt
            earliest = min(earliest, sec)
    window = max(1, now - earliest)
    rps_peak = max(per_second.values()) if per_second else 0
    return {
        "window_seconds": window,
        "workers": len(snapshots),
        "requests": requests,
        "errors": errors,
        "rps_avg": round(requests / window, 1),
        "tps_avg": round(sum(s["tokens"] for s in snapshots) / window, 1),
        "rps_peak": rps_peak,
        "latency_ms": {
            "p50_le": percentile(hist, 0.5),
            "p95_le": percentile(hist, 0.95),
            "p99_le": percentile(hist, 0.99),
        },
    }
