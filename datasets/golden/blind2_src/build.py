"""Сборка слепого датасета blind2.jsonl (детерминированно, фиксированный seed).

Запуск из корня проекта:
    uv run --no-project python datasets/golden/blind2_src/build.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from clean import clean
from common import Gen
from complex_a import BUILDERS_A
from complex_b import BUILDERS_B
from singles_contacts import address, email, phone
from singles_docs import department_code, driver_license, foreign_document, passport, passport_authority, passport_date
from singles_finance import bank_card, cardholder, cvv, inn, pin, snils
from singles_person import birth_date, birth_place, citizenship, person
from traps import traps
from validate import validate

OUT = Path(__file__).resolve().parent.parent / "blind2.jsonl"
COMPLEX_FILLS = 4
SINGLES = (person, birth_date, birth_place, citizenship, passport, passport_authority, department_code,
           passport_date, driver_license, foreign_document, address, email, phone, inn, bank_card, cvv, pin,
           cardholder, snils)


def collect() -> list[dict]:
    g = Gen()
    records: list[dict] = []
    for fn in SINGLES:
        records += fn(g)
    records += traps(g)
    for builder in BUILDERS_A + BUILDERS_B:
        seen: set[str] = set()
        made = 0
        while made < COMPLEX_FILLS:
            rec = builder(g, made)
            if rec["text"] in seen:
                continue
            seen.add(rec["text"])
            records.append(rec)
            made += 1
    records += clean()
    return [{"id": f"b2-{i:04d}", **rec} for i, rec in enumerate(records, start=1)]


def main() -> int:
    records = collect()
    errors = validate(records)
    if errors:
        print("\n".join(errors))
        print(f"ошибок: {len(errors)}, файл не записан")
        return 1
    with OUT.open("w", encoding="utf-8", newline="\n") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"записано {len(records)} примеров в {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
