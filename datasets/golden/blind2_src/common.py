"""Общие утилиты слепого датасета blind2: сборка примеров, контрольные суммы, генераторы значений.

Пример собирается из частей: обычная строка - текст без разметки, ``P(value, type)`` -
размеченный ПДн, ``N(value)`` - ловушка, которую маскировать нельзя. Позиции и
``occurrence`` считаются автоматически, поэтому спаны всегда совпадают с текстом.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

SEED = 20260922
TYPES = (
    "PERSON", "BIRTH_DATE", "BIRTH_PLACE", "PASSPORT", "CITIZENSHIP", "PASSPORT_AUTHORITY",
    "DEPARTMENT_CODE", "PASSPORT_DATE", "DRIVER_LICENSE", "ADDRESS", "EMAIL", "PHONE", "INN",
    "BANK_CARD", "CVV", "PIN", "CARDHOLDER", "SNILS", "FOREIGN_DOCUMENT",
)
CATEGORIES = TYPES + ("TRAP", "COMPLEX", "CLEAN")
NBSP = " "


@dataclass(frozen=True)
class P:
    """Размеченный фрагмент ПДн."""

    value: str
    type: str


@dataclass(frozen=True)
class N:
    """Фрагмент-ловушка: попадает в текст и в not_pii."""

    value: str


def count_before(text: str, value: str, pos: int) -> int:
    """Сколько вхождений value (с перекрытием) начинается раньше pos."""
    count, start = 0, 0
    while True:
        idx = text.find(value, start)
        if idx == -1 or idx >= pos:
            return count
        count += 1
        start = idx + 1


def make(category: str, variant: str, *parts: object) -> dict:
    """Собирает пример из частей; id проставляется при сборке всего датасета."""
    text, spans, not_pii = "", [], []
    for part in parts:
        if isinstance(part, P):
            spans.append((len(text), part))
            text += part.value
        elif isinstance(part, N):
            not_pii.append(part.value)
            text += part.value
        elif isinstance(part, str):
            text += part
        else:
            raise TypeError(f"неизвестная часть примера: {part!r}")
    pii = [
        {"value": p.value, "type": p.type, "occurrence": count_before(text, p.value, pos) + 1}
        for pos, p in spans
    ]
    return {"category": category, "variant": variant, "text": text, "pii": pii,
            "not_pii": list(dict.fromkeys(not_pii))}


# ---------------------------------------------------------------- контрольные суммы

def digits(value: str) -> str:
    return "".join(ch for ch in value if ch.isdigit())


def luhn_ok(number: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(number)):
        d = int(ch)
        if i % 2 == 1:
            d = d * 2 - 9 if d * 2 > 9 else d * 2
        total += d
    return total % 10 == 0


def luhn_complete(prefix: str) -> str:
    for last in "0123456789":
        if luhn_ok(prefix + last):
            return prefix + last
    raise AssertionError("недостижимо")


_INN10_W = (2, 4, 10, 3, 5, 9, 4, 6, 8)
_INN11_W = (7, 2, 4, 10, 3, 5, 9, 4, 6, 8)
_INN12_W = (3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8)


def _ctrl(body: str, weights: tuple[int, ...]) -> str:
    return str(sum(int(d) * w for d, w in zip(body, weights)) % 11 % 10)


def inn_ok(value: str) -> bool:
    if len(value) == 10:
        return value[9] == _ctrl(value[:9], _INN10_W)
    if len(value) == 12:
        return value[10] == _ctrl(value[:10], _INN11_W) and value[11] == _ctrl(value[:11], _INN12_W)
    return False


def snils_ctrl(body: str) -> str:
    total = sum(int(d) * (9 - i) for i, d in enumerate(body))
    if total > 101:
        total %= 101
    return "00" if total in (100, 101) else f"{total:02d}"


def snils_ok(value: str) -> bool:
    return len(value) == 11 and value[9:] == snils_ctrl(value[:9])


# ---------------------------------------------------------------- генераторы значений

class Gen:
    """Детерминированный генератор значений поверх одного random.Random."""

    def __init__(self, seed: int = SEED) -> None:
        self.r = random.Random(seed)

    def pick(self, seq):
        return self.r.choice(seq)

    def num(self, n: int, first_nonzero: bool = True) -> str:
        head = str(self.r.randint(1, 9)) if first_nonzero else str(self.r.randint(0, 9))
        return head + "".join(str(self.r.randint(0, 9)) for _ in range(n - 1))

    def card(self, bin_prefix: str | None = None, length: int = 16) -> str:
        prefix = bin_prefix or self.pick(("4276", "5469", "2202", "4279", "5536", "4817", "2200", "5213"))
        return luhn_complete(prefix + self.num(length - 1 - len(prefix), first_nonzero=False))

    def card_fmt(self, sep: str = " ", **kw) -> str:
        c = self.card(**kw)
        return sep.join(c[i:i + 4] for i in range(0, len(c), 4))

    def inn12(self) -> str:
        body = self.pick(("77", "50", "78", "16", "54", "66", "23", "02")) + self.num(8, False)
        body += _ctrl(body, _INN11_W)
        return body + _ctrl(body, _INN12_W)

    def inn10(self) -> str:
        body = self.pick(("77", "78", "50", "54")) + self.num(7, False)
        return body + _ctrl(body, _INN10_W)

    def snils(self) -> str:
        body = self.num(9)
        return body + snils_ctrl(body)

    def snils_fmt(self, style: str = "std") -> str:
        s = self.snils()
        if style == "std":
            return f"{s[:3]}-{s[3:6]}-{s[6:9]} {s[9:]}"
        if style == "dash":
            return f"{s[:3]}-{s[3:6]}-{s[6:9]}-{s[9:]}"
        if style == "space":
            return f"{s[:3]} {s[3:6]} {s[6:9]} {s[9:]}"
        return s

    def phone_body(self) -> tuple[str, str]:
        return self.pick(("916", "903", "925", "999", "977", "985", "912", "921", "960", "951")), self.num(7)

    def phone(self, style: str = "std") -> str:
        code, n = self.phone_body()
        a, b, c = n[:3], n[3:5], n[5:]
        return {
            "std": f"+7 ({code}) {a}-{b}-{c}",
            "eight": f"8 ({code}) {a}-{b}-{c}",
            "plain": f"8{code}{n}",
            "plus": f"+7{code}{n}",
            "spaces": f"8 {code} {a} {b} {c}",
            "dashes": f"8-{code}-{a}-{b}-{c}",
            "seven": f"7({code}){a}{b}{c}",
            "nbsp": f"+7{NBSP}{code}{NBSP}{a}{NBSP}{b}{NBSP}{c}",
            "dots": f"8.{code}.{a}.{b}.{c}",
        }[style]

    def passport(self) -> tuple[str, str]:
        region = self.pick(("45", "46", "40", "65", "92", "03", "60", "18", "71"))
        return region + self.pick(("08", "12", "15", "17", "19", "20", "21", "23")), self.num(6)

    def date(self, y0: int = 1950, y1: int = 2004) -> tuple[int, int, int]:
        return self.r.randint(1, 28), self.r.randint(1, 12), self.r.randint(y0, y1)

    def dept(self) -> str:
        return f"{self.pick(('770', '500', '780', '160', '540', '660', '230', '610'))}-{self.num(3, False)}"


MONTHS_GEN = ("января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа",
              "сентября", "октября", "ноября", "декабря")


def fmt_date(d: int, m: int, y: int, style: str = "dot") -> str:
    return {
        "dot": f"{d:02d}.{m:02d}.{y}",
        "slash": f"{d:02d}/{m:02d}/{y}",
        "iso": f"{y}-{m:02d}-{d:02d}",
        "words": f"{d} {MONTHS_GEN[m - 1]} {y}",
        "short": f"{d:02d}.{m:02d}.{y % 100:02d}",
        "dash": f"{d:02d}-{m:02d}-{y}",
        "quote": f"«{d:02d}» {MONTHS_GEN[m - 1]} {y}",
        "space": f"{d:02d} {m:02d} {y}",
    }[style]
