"""Разметка примеров: ⟦значение|ТИП⟧ для ПДн и ⟪ловушка⟫ для not_pii.

Позиции и occurrence считаются по очищенному тексту автоматически.
"""

import re

ALIASES = {
    "PER": "PERSON",
    "BD": "BIRTH_DATE",
    "BP": "BIRTH_PLACE",
    "PASS": "PASSPORT",
    "CIT": "CITIZENSHIP",
    "AUTH": "PASSPORT_AUTHORITY",
    "DEPT": "DEPARTMENT_CODE",
    "PDATE": "PASSPORT_DATE",
    "DL": "DRIVER_LICENSE",
    "ADDR": "ADDRESS",
    "EMAIL": "EMAIL",
    "PHONE": "PHONE",
    "INN": "INN",
    "CARD": "BANK_CARD",
    "CVV": "CVV",
    "PIN": "PIN",
    "HOLDER": "CARDHOLDER",
    "SNILS": "SNILS",
    "FDOC": "FOREIGN_DOCUMENT",
}
TYPES = sorted(set(ALIASES.values()))

_TOKEN = re.compile(r"⟦([^⟦⟧⟪⟫]+?)\|([A-Z_]+)⟧|⟪([^⟦⟧⟪⟫]+?)⟫", re.DOTALL)

EXAMPLES: list[dict] = []


def occurrence_at(text: str, value: str, start: int) -> int:
    """1-based номер вхождения value (с перекрытиями), которое начинается в start."""
    k, pos = 0, text.find(value)
    while pos != -1 and pos <= start:
        k += 1
        if pos == start:
            return k
        pos = text.find(value, pos + 1)
    raise ValueError(f"value {value!r} not found at {start}")


def parse(marked: str) -> tuple[str, list[tuple[int, int, str]], list[tuple[int, int]]]:
    out, pii, traps = [], [], []
    cursor, length = 0, 0
    for m in _TOKEN.finditer(marked):
        chunk = marked[cursor:m.start()]
        out.append(chunk)
        length += len(chunk)
        if m.group(1) is not None:
            value, alias = m.group(1), m.group(2)
            if alias not in ALIASES and alias not in TYPES:
                raise ValueError(f"unknown type {alias!r} in {marked!r}")
            pii.append((length, length + len(value), ALIASES.get(alias, alias)))
        else:
            value = m.group(3)
            traps.append((length, length + len(value)))
        out.append(value)
        length += len(value)
        cursor = m.end()
    out.append(marked[cursor:])
    text = "".join(out)
    for bad in "⟦⟧⟪⟫":
        if bad in text:
            raise ValueError(f"unbalanced markup in {marked!r}")
    return text, pii, traps


def E(category: str, variant: str, marked: str) -> None:
    text, pii, traps = parse(marked)
    EXAMPLES.append({
        "category": category,
        "variant": variant,
        "text": text,
        "pii": [
            {
                "value": text[s:e],
                "type": t,
                "occurrence": occurrence_at(text, text[s:e], s),
                "start": s,
                "end": e,
            }
            for s, e, t in pii
        ],
        "not_pii": [text[s:e] for s, e in traps],
    })
