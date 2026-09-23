"""Конвертация открытого бенчмарка redmadrobot-rnd/pii_benchmark в наш формат JSONL.

Запуск: uv run --no-project --with datasets python tools/convert_rmr.py reports/rmr_bench.jsonl

Разметка у набора своя: адреса организаций и регионы вне личного контекста там
тоже считаются ПДн, а служебные слова адреса входят в спан. Поэтому precision на
нём занижена, смотреть стоит на полноту по типам. Примеры с метками вне наших
типов (URL, IP, ОМС и прочее) пропускаются целиком.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Соответствие меток набора нашим типам.
LABEL_MAP = {
    "FIRST_NAME": "PERSON",
    "LAST_NAME": "PERSON",
    "MIDDLE_NAME": "PERSON",
    "STREET": "ADDRESS",
    "HOUSE": "ADDRESS",
    "CITY": "ADDRESS",
    "REGION": "ADDRESS",
    "COUNTRY": "ADDRESS",
    "DISTRICT": "ADDRESS",
    "PHONE": "PHONE",
    "EMAIL": "EMAIL",
    "PASSPORT": "PASSPORT",
    "INN": "INN",
    "SNILS": "SNILS",
    "DRIVER_LICENSE": "DRIVER_LICENSE",
    "CREDIT_CARD": "BANK_CARD",
    "BIRTH_CERTIFICATE": "FOREIGN_DOCUMENT",
    "MILITARY_ID": "FOREIGN_DOCUMENT",
}


def align(text: str, tokens: list[str]) -> list[tuple[int, int]] | None:
    """Находит позиции токенов в тексте последовательным find."""
    offsets: list[tuple[int, int]] = []
    pos = 0
    for tok in tokens:
        idx = text.find(tok, pos)
        if idx == -1:
            idx = text.lower().find(tok.lower(), pos)
        if idx == -1:
            return None
        offsets.append((idx, idx + len(tok)))
        pos = idx + len(tok)
    return offsets


def bio_spans(offsets: list[tuple[int, int]], tags: list[str]) -> list[tuple[str, int, int]]:
    """Собирает спаны из BIO-разметки."""
    spans: list[tuple[str, int, int]] = []
    for (start, end), tag in zip(offsets, tags, strict=True):
        if tag == "O":
            continue
        if tag.startswith("I-") and spans and tag[2:] == spans[-1][0]:
            s, e = spans[-1][1], spans[-1][2]
            spans[-1] = (spans[-1][0], s, max(e, end))
            continue
        label = tag.removeprefix("B-")
        spans.append((label, start, end))
    return spans


def convert_row(n: int, row: dict, skipped: dict) -> dict | None:
    """Переводит одну строку набора в наш формат."""
    text = row["text"]
    tokens = json.loads(row["tokens"])
    tags = json.loads(row["ner_tags"])
    offsets = align(text, tokens)
    if offsets is None:
        skipped["align"] += 1
        return None
    spans = bio_spans(offsets, tags)

    mapped: list[tuple[str, int, int]] = []
    for label, start, end in spans:
        our = LABEL_MAP.get(label)
        if our is None:
            skipped["unmapped_label"] += 1
            return None
        mapped.append((our, start, end))

    # Склеиваем соседние PERSON через пробелы.
    merged: list[tuple[str, int, int]] = []
    for our, start, end in mapped:
        if merged and our == "PERSON" and merged[-1][0] == "PERSON":
            prev_start, prev_end = merged[-1][1], merged[-1][2]
            if text[prev_end:start].strip(" ") == "":
                merged[-1] = ("PERSON", prev_start, end)
                continue
        merged.append((our, start, end))

    pii = []
    for our, start, end in merged:
        value = text[start:end]
        occurrence = text.count(value, 0, start) + 1
        pii.append({"value": value, "type": our, "occurrence": occurrence})

    return {
        "id": f"rmr-{n:04d}",
        "category": "RMR" if pii else "CLEAN",
        "variant": "rmr",
        "text": text,
        "pii": pii,
        "not_pii": [],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("out", type=Path)
    args = parser.parse_args()

    from datasets import load_dataset  # noqa: PLC0415

    ds = load_dataset("redmadrobot-rnd/pii_benchmark", split="test")
    skipped = {"align": 0, "unmapped_label": 0}
    written = 0
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        for n, row in enumerate(ds, 1):
            example = convert_row(n, row, skipped)
            if example is None:
                continue
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
            written += 1
    print(f"записано: {written}")
    print(f"пропущено align: {skipped['align']}")
    print(f"пропущено unmapped_label: {skipped['unmapped_label']}")


if __name__ == "__main__":
    main()
