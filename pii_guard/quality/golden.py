"""Формат золотого датасета: JSONL, позиции вычисляются поиском подстроки."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import orjson


@dataclass(frozen=True, slots=True)
class GoldSpan:
    """Золотой спан: позиции и тип."""

    start: int
    end: int
    type: str


@dataclass(slots=True)
class Example:
    """Один пример золотого датасета."""

    id: str
    category: str
    variant: str
    text: str
    pii: list[GoldSpan]
    traps: list[tuple[int, int]] = None  # type: ignore[assignment]


def locate(text: str, value: str, occurrence: int = 1) -> tuple[int, int]:
    """Ищет n-е вхождение подстроки."""
    pos = 0
    for _i in range(occurrence):
        idx = text.find(value, pos)
        if idx == -1:
            raise ValueError(f"вхождение {occurrence} не найдено")
        pos = idx + 1
    return (idx, idx + len(value))


def parse_example(raw: dict) -> Example:
    """Превращает словарь в Example."""
    pii = [
        GoldSpan(*locate(raw["text"], item["value"], item.get("occurrence", 1)), item["type"])
        for item in raw.get("pii", [])
    ]
    traps = [locate(raw["text"], t) for t in raw.get("not_pii", [])]
    return Example(
        id=raw["id"],
        category=raw.get("category", "UNKNOWN"),
        variant=raw.get("variant", ""),
        text=raw["text"],
        pii=pii,
        traps=traps,
    )


def load(path: str | Path) -> list[Example]:
    """Читает JSONL-файл."""
    p = Path(path)
    examples: list[Example] = []
    with open(p, encoding="utf-8") as f:
        for lineno, raw_line in enumerate(f, 1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                raw = orjson.loads(line)
                examples.append(parse_example(raw))
            except (ValueError, KeyError) as exc:
                raise ValueError(f"{p.name}:{lineno}: {exc}") from exc
    return examples


def dump(examples: list[Example], path: str | Path) -> None:
    """Пишет примеры в JSONL."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "wb") as f:
        for ex in examples:
            raw = {
                "id": ex.id,
                "category": ex.category,
                "variant": ex.variant,
                "text": ex.text,
                "pii": [
                    {"value": ex.text[span.start : span.end], "type": span.type} for span in ex.pii
                ],
                "not_pii": [ex.text[s:e] for s, e in ex.traps],
            }
            f.write(orjson.dumps(raw) + b"\n")
