"""Валидатор blind2.jsonl: подстроки, occurrence, пересечения, контрольные суммы, схема.

Запуск: uv run --no-project python datasets/golden/blind2_src/validate.py [path]
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

from common import CATEGORIES, TYPES, digits, inn_ok, luhn_ok, snils_ok

DEFAULT = Path(__file__).resolve().parent.parent / "blind2.jsonl"
ID_RE = re.compile(r"^b2-\d{4}$")


def nth_pos(text: str, value: str, n: int) -> int:
    start, idx = 0, -1
    for _ in range(n):
        idx = text.find(value, start)
        if idx == -1:
            return -1
        start = idx + 1
    return idx


def check_checksum(span: dict) -> str | None:
    d, t = digits(span["value"]), span["type"]
    if t == "BANK_CARD" and not (13 <= len(d) <= 19 and luhn_ok(d)):
        return f"карта не проходит Луна: {span['value']!r}"
    if t == "INN" and not inn_ok(d):
        return f"ИНН с неверной контрольной суммой: {span['value']!r}"
    if t == "SNILS" and not snils_ok(d):
        return f"СНИЛС с неверной контрольной суммой: {span['value']!r}"
    return None


def check_record(rec: dict) -> list[str]:
    errs = []
    keys = {"id", "category", "variant", "text", "pii", "not_pii"}
    if set(rec) != keys:
        return [f"неверный набор ключей: {sorted(rec)}"]
    if not ID_RE.match(rec["id"]):
        errs.append(f"плохой id {rec['id']!r}")
    if rec["category"] not in CATEGORIES:
        errs.append(f"неизвестная category {rec['category']!r}")
    if rec["category"] == "CLEAN" and rec["pii"]:
        errs.append("CLEAN с непустым pii")
    text, ranges = rec["text"], []
    for span in rec["pii"]:
        value = span["value"]
        if span["type"] not in TYPES:
            errs.append(f"неизвестный тип {span['type']!r}")
        if not value or value != value.strip():
            errs.append(f"пустое значение или пробелы по краям: {value!r}")
        pos = nth_pos(text, value, span["occurrence"])
        if span["occurrence"] < 1 or pos == -1:
            errs.append(f"нет вхождения #{span['occurrence']} для {value!r}")
            continue
        ranges.append((pos, pos + len(value), value))
        if (msg := check_checksum(span)) is not None:
            errs.append(msg)
    ranges.sort()
    for (s1, e1, v1), (s2, e2, v2) in zip(ranges, ranges[1:]):
        if s2 < e1:
            errs.append(f"спаны пересекаются: {v1!r} и {v2!r}")
    pii_values = {s["value"] for s in rec["pii"]}
    for trap in rec["not_pii"]:
        if trap not in text:
            errs.append(f"not_pii не подстрока: {trap!r}")
        if trap in pii_values:
            errs.append(f"not_pii совпадает с pii: {trap!r}")
    return errs


def validate(records: list[dict]) -> list[str]:
    errors = []
    ids = Counter(r.get("id") for r in records)
    errors += [f"дубликат id {i}" for i, c in ids.items() if c > 1]
    texts = Counter(r.get("text") for r in records)
    errors += [f"дубликат текста: {t[:60]!r}" for t, c in texts.items() if c > 1]
    for rec in records:
        errors += [f"{rec.get('id')}: {e}" for e in check_record(rec)]
    return errors


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    errors = validate(records)
    for e in errors:
        print(e)
    cats = Counter(r["category"] for r in records)
    types = Counter(s["type"] for r in records for s in r["pii"])
    print(f"примеров: {len(records)}, ошибок: {len(errors)}")
    print("category:", dict(sorted(cats.items(), key=lambda kv: -kv[1])))
    print("спаны по типам:", dict(sorted(types.items(), key=lambda kv: -kv[1])))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
