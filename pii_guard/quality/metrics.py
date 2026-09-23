"""Метрики качества детекции.

Считаем только по буквам и цифрам: разделители вроде дефиса и пробела можно
скрывать или оставлять, на оценку это не влияет. Плюс отдельная прокси метрики
автопроверки — span similarity.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field

import regex as re

from .golden import Example

_TOKEN_RE = re.compile(r"[\p{L}\d]+|[^\p{L}\d\s]", re.VERSION1)
MARKER = "■"


def _to_sequence(text: str, spans: list[tuple[int, int]]) -> list[str]:
    """Сворачивает спаны в последовательность токенов с маркерами."""
    seq: list[str] = []
    cursor = 0
    for raw_start, end in sorted(spans):
        start = max(raw_start, cursor)
        gap = text[cursor:start]
        gap_tokens = _TOKEN_RE.findall(gap)
        seq.extend(gap_tokens)
        if start < end:
            nonspace_between = any(not c.isspace() for c in gap)
            if not seq or seq[-1] != MARKER or nonspace_between:
                seq.append(MARKER)
        cursor = max(cursor, end)
    seq.extend(_TOKEN_RE.findall(text[cursor:]))
    return seq


def _levenshtein(a: list[str], b: list[str]) -> int:
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def span_similarity(
    text: str, gold: list[tuple[int, int]], predicted: list[tuple[int, int]]
) -> float:
    """Сходство последовательностей золотых и предсказанных спанов."""
    a = _to_sequence(text, gold)
    b = _to_sequence(text, predicted)
    dist = _levenshtein(a, b)
    denom = max(len(a), len(b), 1)
    return 1.0 - dist / denom


@dataclass(slots=True)
class Report:
    """Копит статистику по примерам."""

    examples: int = 0
    gold_chars: int = 0
    leaked_chars: int = 0
    masked_chars: int = 0
    extra_chars: int = 0
    entities: Counter = field(default_factory=Counter)
    entities_full: Counter = field(default_factory=Counter)
    entities_partial: Counter = field(default_factory=Counter)
    traps: int = 0
    traps_hit: int = 0
    examples_with_leak: int = 0
    similarity_sum: float = 0.0
    by_category: dict = field(default_factory=lambda: defaultdict(lambda: [0, 0.0]))
    failures: list = field(default_factory=list)

    def _count_types(self, text: str, example: Example, coverage: set) -> set[str]:
        """Считает сущности по типам и возвращает типы с утечкой."""
        leaked_types: set[str] = set()
        for span in example.pii:
            alnum = [i for i in range(span.start, span.end) if i < len(text) and text[i].isalnum()]
            if not alnum:
                continue
            covered = [i for i in alnum if i in coverage]
            self.entities[span.type] += 1
            if len(covered) == len(alnum):
                self.entities_full[span.type] += 1
            elif covered:
                self.entities_partial[span.type] += 1
                leaked_types.add(span.type)
            else:
                leaked_types.add(span.type)
        return leaked_types

    def _count_chars(self, text: str, example: Example, coverage: set) -> tuple[set, set, set]:
        """Считает символы и возвращает (masked, leaked, extra)."""
        masked = {i for i in coverage if i < len(text) and text[i].isalnum()}
        gold = set()
        for span in example.pii:
            gold.update(
                i for i in range(span.start, span.end) if i < len(text) and text[i].isalnum()
            )
        leaked = gold - masked
        extra = masked - gold
        self.gold_chars += len(gold)
        self.masked_chars += len(masked)
        self.leaked_chars += len(leaked)
        self.extra_chars += len(extra)
        return masked, leaked, extra

    def _count_traps(self, text: str, example: Example, masked: set) -> int:
        """Считает ловушки и возвращает число задетых."""
        traps_hit_here = 0
        for s, e in example.traps:
            self.traps += 1
            if any(i in masked for i in range(s, e) if i < len(text) and text[i].isalnum()):
                self.traps_hit += 1
                traps_hit_here += 1
        return traps_hit_here

    def add(
        self, example: Example, predicted: list[tuple[int, int]], keep_failures: int = 400
    ) -> None:
        self.examples += 1
        text = example.text
        coverage = set()
        for s, e in predicted:
            coverage.update(range(s, e))

        leaked_types = self._count_types(text, example, coverage)
        masked, leaked, extra = self._count_chars(text, example, coverage)
        traps_hit_here = self._count_traps(text, example, masked)

        if leaked:
            self.examples_with_leak += 1

        sim = span_similarity(text, [(s.start, s.end) for s in example.pii], predicted)
        self.similarity_sum += sim
        self.by_category[example.category][0] += 1
        self.by_category[example.category][1] += sim

        if (leaked or extra or traps_hit_here) and len(self.failures) < keep_failures:
            self.failures.append(
                {
                    "id": example.id,
                    "category": example.category,
                    "variant": example.variant,
                    "leaked_types": sorted(leaked_types),
                    "extra_chars": len(extra),
                    "traps_hit": traps_hit_here,
                    "similarity": round(sim, 3),
                }
            )

    def summary(self) -> dict:
        char_recall = 1.0 if self.gold_chars == 0 else 1.0 - self.leaked_chars / self.gold_chars
        char_precision = (
            1.0 if self.masked_chars == 0 else 1.0 - self.extra_chars / self.masked_chars
        )
        total_entities = sum(self.entities.values())
        entity_recall_full = (
            sum(self.entities_full.values()) / total_entities if total_entities else 1.0
        )
        trap_fpr = self.traps_hit / self.traps if self.traps else 0.0
        span_sim = self.similarity_sum / self.examples if self.examples else 1.0
        return {
            "examples": self.examples,
            "char_recall": round(char_recall, 4),
            "char_precision": round(char_precision, 4),
            "entity_recall_full": round(entity_recall_full, 4),
            "examples_with_leak": self.examples_with_leak,
            "trap_false_positive_rate": round(trap_fpr, 4),
            "span_similarity": round(span_sim, 4),
        }

    def per_type(self) -> list[dict]:
        result = []
        for t in sorted(self.entities):
            total = self.entities[t]
            result.append(
                {
                    "type": t,
                    "entities": total,
                    "full": self.entities_full[t],
                    "partial": self.entities_partial[t],
                    "recall_full": round(self.entities_full[t] / total, 4) if total else 1.0,
                }
            )
        return result

    def per_category(self) -> dict:
        return {
            cat: {
                "examples": v[0],
                "similarity": round(v[1] / v[0], 4) if v[0] else 1.0,
            }
            for cat, v in sorted(self.by_category.items())
        }
