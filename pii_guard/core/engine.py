"""Движок детекции: правила, ФИО, цепочки адреса, контекст, разрешение пересечений."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

from .compact import compact
from .detect_address import AddressDetector
from .detect_person import PersonDetector
from .detect_rules import apply_rules
from .gazetteers import Gazetteers, Morph
from .resolve import apply_combo_rules, merge_adjacent, resolve_overlaps, single_value
from .rules import load_rules
from .spoken import spoken
from .textutil import tokenize
from .types import DetectionOptions, Span, TypeRegistry

CHUNK_SIZE = 6000
CHUNK_SEARCH = 1500

# Разделители по убыванию силы.
BOUNDARIES = ("\n\n", "\n", ". ", "; ", "! ", "? ", ", ", " ")

# Типографика: неразрывные пробелы в обычный, разные тире в дефис.
TYPOGRAPHY = str.maketrans(
    {
        "\u00a0": " ",  # неразрывный пробел
        "\u202f": " ",  # узкий неразрывный пробел
        "\u2009": " ",  # тонкий пробел
        "\u2007": " ",  # figure space
        "\u2010": "-",  # дефис
        "\u2011": "-",  # неразрывный дефис
        "\u2012": "-",  # figure dash
        "\u2013": "-",  # среднее тире
        "\u2014": "-",  # длинное тире
        "\u2212": "-",  # минус
    }
)


@dataclass(slots=True)
class DetectionResult:
    """Результат детекции: спаны, общее время и время по этапам."""

    spans: list[Span]
    elapsed_ms: float
    stages_ms: dict[str, float] = field(default_factory=dict)


def split_chunks(text: str, size: int = CHUNK_SIZE) -> list[tuple[int, int]]:
    """Режет текст на куски по границам записей и предложений."""
    n = len(text)
    if n <= size:
        return [(0, n)]
    chunks: list[tuple[int, int]] = []
    start = 0
    while start < n:
        end = min(start + size, n)
        if end < n:
            lo = max(start + size - CHUNK_SEARCH, start + 1)
            cut = -1
            for sep in BOUNDARIES:
                idx = text.rfind(sep, lo, end)
                if idx > start:
                    cut = idx + len(sep)
                    break
            if cut > start:
                end = cut
        chunks.append((start, end))
        start = end
    return chunks


class Detector:
    """Один экземпляр на процесс: словари и морфология грузятся один раз."""

    def __init__(self, config_dir: str | Path, use_morph: bool = True) -> None:
        self.config_dir = Path(config_dir)
        self.registry = TypeRegistry()
        self.rules = load_rules(self.config_dir / "rules", self.registry)
        self.gaz = Gazetteers.load(self.config_dir / "gazetteers", self.config_dir / "context.yaml")
        self.morph = Morph() if use_morph else None
        self.person = PersonDetector(self.gaz, self.morph)
        self.address = AddressDetector(self.config_dir / "address.yaml", self.gaz, self.morph)

    def reload(self) -> None:
        """Перечитывает правила, словари, контекст и адресный конфиг."""
        registry = TypeRegistry()
        rules = load_rules(self.config_dir / "rules", registry)
        gaz = Gazetteers.load(self.config_dir / "gazetteers", self.config_dir / "context.yaml")
        person = PersonDetector(gaz, self.morph)
        address = AddressDetector(self.config_dir / "address.yaml", gaz, self.morph)
        self.registry = registry
        self.rules = rules
        self.gaz = gaz
        self.person = person
        self.address = address

    def _map_view_spans(
        self, view_spans: list[Span], starts: list[int], ends: list[int], candidates: list[Span]
    ) -> None:
        """Переносит спаны из плотного вида обратно на исходные границы."""
        candidates.extend(
            Span(
                start=starts[span.start],
                end=ends[span.end - 1],
                type=span.type,
                confidence=span.confidence,
                priority=span.priority,
                rule=span.rule,
                subtype=span.subtype,
            )
            for span in view_spans
            if span.start < len(starts) and span.end - 1 < len(ends)
        )

    def _detect_views(
        self, text: str, options: DetectionOptions, stages: dict[str, float], candidates: list[Span]
    ) -> None:
        """Добавляет спаны из дополнительных видов текста (compact, spoken)."""
        for view_name, view_fn in (("compact", compact), ("spoken", spoken)):
            view_start = time.perf_counter()
            res = view_fn(text)
            if res is not None:
                dense, starts, ends = res
                if starts is not None and ends is not None:
                    view_spans = self._detect_view(dense, options, stages)
                    self._map_view_spans(view_spans, starts, ends, candidates)
            stages[view_name] = (time.perf_counter() - view_start) * 1000

    def _resolve(
        self, text: str, candidates: list[Span], options: DetectionOptions, stages: dict[str, float]
    ) -> list[Span]:
        """Разрешает пересечения, склеивает соседей и применяет single_value."""
        resolve_start = time.perf_counter()
        filtered = [s for s in candidates if s.type in options.entity_types and s.end > s.start]
        resolved = resolve_overlaps(filtered)
        merged = merge_adjacent(text, resolved)
        if not merged and getattr(options, "single_value_mode", False):
            tokens = tokenize(text)
            sv = single_value(text, tokens, options, self.gaz, self.morph)
            if sv is not None:
                merged = [sv]
        merged = apply_combo_rules(text, merged, options)
        stages["resolve"] = (time.perf_counter() - resolve_start) * 1000
        return merged

    def detect(self, text: str, options: DetectionOptions | None = None) -> DetectionResult:
        options = options or DetectionOptions()
        start = time.perf_counter()
        stages: dict[str, float] = {}
        text = text.translate(TYPOGRAPHY)

        candidates = self._detect_view(text, options, stages)
        self._detect_views(text, options, stages, candidates)
        merged = self._resolve(text, candidates, options, stages)

        elapsed = (time.perf_counter() - start) * 1000
        return DetectionResult(spans=merged, elapsed_ms=elapsed, stages_ms=stages)

    def _detect_view(
        self, text: str, options: DetectionOptions, stages: dict[str, float]
    ) -> list[Span]:
        spans: list[Span] = []
        for start, end in split_chunks(text):
            chunk = text[start:end]
            spans.extend(
                Span(
                    start=span.start + start,
                    end=span.end + start,
                    type=span.type,
                    confidence=span.confidence,
                    priority=span.priority,
                    rule=span.rule,
                    subtype=span.subtype,
                )
                for span in self._detect_chunk(chunk, options, stages)
            )
        return spans

    def _detect_chunk(
        self, chunk: str, options: DetectionOptions, stages: dict[str, float]
    ) -> list[Span]:
        tokens = tokenize(chunk)
        spans: list[Span] = []
        t = time.perf_counter()
        spans.extend(apply_rules(chunk, self.rules, options, self.gaz, self.morph))
        self._add(stages, "rules", time.perf_counter() - t)
        t = time.perf_counter()
        spans.extend(self.person.detect(chunk, tokens, options))
        self._add(stages, "person", time.perf_counter() - t)
        t = time.perf_counter()
        addr = self.address.detect(chunk, tokens, options)
        spans.extend(addr)
        addr_spans = [s for s in spans if s.type == "ADDRESS"]
        if addr_spans:
            kept = self.address.suppress_org(chunk, addr_spans, options)
            kept_ids = {id(s) for s in kept}
            spans = [s for s in spans if s.type != "ADDRESS" or id(s) in kept_ids]
        self._add(stages, "address", time.perf_counter() - t)
        return spans

    @staticmethod
    def _add(stages: dict[str, float], name: str, seconds: float) -> None:
        stages[name] = stages.get(name, 0.0) + seconds * 1000
