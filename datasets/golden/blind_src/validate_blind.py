"""Проверка blind.jsonl: значения и ловушки найдены в тексте на заявленном вхождении.

Запуск: uv run python validate_blind.py path/to/blind.jsonl
Не зависит от генератора: читает только JSONL.
"""

import json
import sys
from collections import Counter
from pathlib import Path

TYPES = {
    "PERSON", "BIRTH_DATE", "BIRTH_PLACE", "PASSPORT", "CITIZENSHIP", "PASSPORT_AUTHORITY",
    "DEPARTMENT_CODE", "PASSPORT_DATE", "DRIVER_LICENSE", "ADDRESS", "EMAIL", "PHONE", "INN",
    "BANK_CARD", "CVV", "PIN", "CARDHOLDER", "SNILS", "FOREIGN_DOCUMENT",
}
SERVICE_WORDS = {"серия", "номер", "ул.", "д.", "кв.", "г.", "года", "г.р.", "тел.", "паспорт"}


def nth_index(text: str, value: str, n: int) -> int:
    pos, k = text.find(value), 0
    while pos != -1:
        k += 1
        if k == n:
            return pos
        pos = text.find(value, pos + 1)
    return -1


def digits(s: str) -> str:
    return "".join(ch for ch in s if ch.isdigit())


def inn_ok(s: str) -> bool:
    d = digits(s)
    w10, w11, w12 = [2, 4, 10, 3, 5, 9, 4, 6, 8], [7, 2, 4, 10, 3, 5, 9, 4, 6, 8], \
        [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]

    def chk(ds, ws):
        return str(sum(int(a) * b for a, b in zip(ds, ws)) % 11 % 10)

    if len(d) == 10:
        return chk(d[:9], w10) == d[9]
    if len(d) == 12:
        return chk(d[:10], w11) == d[10] and chk(d[:11], w12) == d[11]
    return False


def snils_ok(s: str) -> bool:
    d = digits(s)
    if len(d) != 11:
        return False
    total = sum(int(x) * (9 - i) for i, x in enumerate(d[:9]))
    c = total if total < 100 else 0 if total in (100, 101) else total % 101 % 100
    return f"{c:02d}" == d[9:]


def luhn_ok(s: str) -> bool:
    d = digits(s)
    total = 0
    for i, ch in enumerate(reversed(d)):
        n = int(ch)
        if i % 2 == 1:
            n = n * 2 - 9 if n * 2 > 9 else n * 2
        total += n
    return len(d) >= 13 and total % 10 == 0


def validate(path: Path) -> int:
    errors, warnings = [], []
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    ids = Counter(r["id"] for r in rows)
    errors += [f"duplicate id {i}" for i, n in ids.items() if n > 1]
    texts = Counter(r["text"] for r in rows)
    warnings += [f"duplicate text: {t[:60]!r}" for t, n in texts.items() if n > 1]

    for r in rows:
        rid, text = r["id"], r["text"]
        for key in ("id", "category", "variant", "text", "pii", "not_pii"):
            if key not in r:
                errors.append(f"{rid}: missing key {key}")
        spans = []
        for p in r["pii"]:
            v, t, occ = p["value"], p["type"], p["occurrence"]
            if t not in TYPES:
                errors.append(f"{rid}: unknown type {t}")
            if v != v.strip() or not v:
                errors.append(f"{rid}: value has outer whitespace {v!r}")
            if v.lower() in SERVICE_WORDS:
                errors.append(f"{rid}: service word labeled as value {v!r}")
            pos = nth_index(text, v, occ)
            if pos == -1:
                errors.append(f"{rid}: {v!r} occurrence {occ} not found")
                continue
            if "start" in p and (p["start"] != pos or p["end"] != pos + len(v)):
                errors.append(f"{rid}: {v!r} start/end mismatch ({p['start']} vs {pos})")
            spans.append((pos, pos + len(v), v, t))
            sub = r.get("subvariant", r["variant"])
            if "invalid" not in sub:
                if t == "INN" and not inn_ok(v):
                    errors.append(f"{rid}: INN checksum invalid {v!r}")
                if t == "SNILS" and digits(v) and not snils_ok(v):
                    errors.append(f"{rid}: SNILS checksum invalid {v!r}")
                if t == "BANK_CARD" and not luhn_ok(v):
                    errors.append(f"{rid}: card Luhn invalid {v!r}")
        spans.sort()
        for a, b in zip(spans, spans[1:]):
            if b[0] < a[1]:
                errors.append(f"{rid}: overlapping spans {a[2]!r} / {b[2]!r}")
        for trap in r["not_pii"]:
            if trap not in text:
                errors.append(f"{rid}: not_pii {trap!r} not in text")
                continue
            pos = text.find(trap)
            while pos != -1:
                end = pos + len(trap)
                if any(s < end and pos < e for s, e, _, _ in spans):
                    warnings.append(f"{rid}: not_pii {trap!r} overlaps a PII span at {pos}")
                pos = text.find(trap, pos + 1)

    cat = Counter(r["category"] for r in rows)
    var = Counter(r["variant"] for r in rows)
    span_types = Counter(p["type"] for r in rows for p in r["pii"])
    ex_with_type = Counter(t for r in rows for t in {p["type"] for p in r["pii"]})
    traps_total = sum(len(r["not_pii"]) for r in rows)
    no_pii = sum(1 for r in rows if not r["pii"])

    print(f"file: {path}")
    print(f"examples: {len(rows)}; pii spans: {sum(span_types.values())}; "
          f"not_pii strings: {traps_total}; examples without pii: {no_pii}")
    print("\nper category:")
    for k, n in sorted(cat.items(), key=lambda x: (-x[1], x[0])):
        print(f"  {k:<20} {n}")
    print("\nper variant:")
    for k, n in sorted(var.items(), key=lambda x: (-x[1], x[0])):
        print(f"  {k:<26} {n}")
    print("\nper PII type (spans / examples containing the type):")
    for t in sorted(TYPES):
        print(f"  {t:<20} {span_types[t]:>4} / {ex_with_type[t]}")
    missing = [t for t in TYPES if ex_with_type[t] < 12]
    if missing:
        errors.append(f"types with <12 examples: {missing}")
    for w in warnings:
        print("WARN", w)
    for e in errors:
        print("ERROR", e)
    print(f"\n{'OK' if not errors else 'FAILED'}: {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(validate(Path(sys.argv[1] if len(sys.argv) > 1 else "blind.jsonl")))
