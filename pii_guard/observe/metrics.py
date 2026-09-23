"""Метрики Prometheus."""

from __future__ import annotations

import os

from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from prometheus_client.multiprocess import MultiProcessCollector

PREFIX = os.environ.get("METRICS_PREFIX", "pii")

TIME_BUCKETS = [0.0005, 0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]


def _name(suffix: str) -> str:
    return f"{PREFIX}_{suffix}"


class Metrics:
    """Все метрики сервиса. Синглтон: метрики регистрируются один раз."""

    _instance: Metrics | None = None

    def __new__(cls) -> Metrics:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self.requests_total = Counter(
            _name("requests_total"), "Всего запросов", ["route", "system", "status"]
        )
        self.request_seconds = Histogram(
            _name("request_seconds"), "Время обработки запроса", ["route"], buckets=TIME_BUCKETS
        )
        self.stage_seconds = Histogram(
            _name("stage_seconds"), "Время этапа обработки", ["stage"], buckets=TIME_BUCKETS
        )
        self.entities_total = Counter(
            _name("entities_total"), "Найденные сущности", ["type", "system"]
        )
        self.tokens_total = Counter(_name("tokens_total"), "Токены по направлению", ["direction"])
        self.chars_total = Counter(_name("chars_total"), "Символы по направлению", ["direction"])
        self.rejected_total = Counter(_name("rejected_total"), "Отклонённые запросы", ["reason"])
        self.degraded_total = Counter(
            _name("degraded_total"), "Деградация компонента", ["component"]
        )
        self.inflight_requests = Gauge(
            _name("inflight_requests"), "Запросы в обработке", multiprocess_mode="livesum"
        )
        self.llm_seconds = Histogram(_name("llm_seconds"), "Время ответа LLM", buckets=TIME_BUCKETS)
        self.llm_tokens_total = Counter(
            _name("llm_tokens_total"), "Токены LLM по направлению", ["direction"]
        )


def render() -> tuple[bytes, str]:
    """Возвращает байты и content type."""
    multiproc = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
    if multiproc:
        registry = CollectorRegistry()
        MultiProcessCollector(registry)
        return generate_latest(registry), "text/plain; version=0.0.4; charset=utf-8"
    return generate_latest(), "text/plain; version=0.0.4; charset=utf-8"
