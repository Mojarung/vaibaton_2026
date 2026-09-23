"""Валидаторы значений. Имя функции совпадает с именем валидатора в YAML."""

from __future__ import annotations

import datetime
from collections.abc import Callable

Validator = Callable[[str], bool]


def digits(value: str) -> str:
    return "".join(c for c in value if c.isdigit())


def luhn(value: str) -> bool:
    d = digits(value)
    if not (13 <= len(d) <= 19):
        return False
    if len(set(d)) == 1:
        return False
    total = 0
    for i, ch in enumerate(reversed(d)):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def _inn_control(d: str, weights: list[int]) -> int:
    total = sum(int(ch) * w for ch, w in zip(d, weights, strict=True))
    return (total % 11) % 10


def inn(value: str) -> bool:
    d = digits(value)
    if len(set(d)) < 2:
        return False
    if len(d) == 10:
        weights = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        return _inn_control(d[:9], weights) == int(d[9])
    if len(d) == 12:
        w11 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        w12 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        return _inn_control(d[:10], w11) == int(d[10]) and _inn_control(d[:11], w12) == int(d[11])
    return False


def inn12(value: str) -> bool:
    return len(digits(value)) == 12 and inn(value)


def snils(value: str) -> bool:
    d = digits(value)
    if len(d) != 11:
        return False
    if len(set(d)) == 1:
        return False
    total = sum(int(d[i]) * (9 - i) for i in range(9))
    total %= 101
    if total == 100:
        total = 0
    return total == int(d[9:11])


def phone_digits(value: str) -> bool:
    return 10 <= len(digits(value)) <= 15


def not_repeated(value: str) -> bool:
    d = digits(value)
    if not d:
        return True
    return len(set(d)) > 1


def _split_numeric_date(value: str) -> list[int]:
    return [int(part) for part in "".join(c if c.isdigit() else " " for c in value).split()]


def date_any(value: str) -> bool:
    parts = _split_numeric_date(value)
    if len(parts) != 3:
        return True
    a, b, c = parts
    if a > 31:
        return _try_date((a, b, c)) or _try_date((a, c, b))
    year = c
    if year < 100:
        year = 1900 + year if year > 30 else 2000 + year
    return _try_date((year, b, a)) or _try_date((year, a, b))


def _try_date(parts: tuple[int, int, int]) -> bool:
    y, m, d = parts
    if not (1900 <= y <= 2100):
        return False
    try:
        datetime.date(y, m, d)
    except ValueError:
        return False
    return True


def _year_of(value: str) -> int | None:
    parts = _split_numeric_date(value)
    for p in parts:
        if 1000 <= p <= 9999:
            return p
    if len(parts) == 3 and parts[2] < 100:
        return 1900 + parts[2] if parts[2] > 30 else 2000 + parts[2]
    return None


def birth_like(value: str) -> bool:
    year = _year_of(value)
    if year is None:
        return False
    return 1920 <= year <= datetime.date.today().year - 14


def plausible_birth(value: str) -> bool:
    year = _year_of(value)
    if year is None:
        return True
    return 1900 <= year <= datetime.date.today().year


def issue_like(value: str) -> bool:
    year = _year_of(value)
    if year is None:
        return False
    return 1990 <= year <= datetime.date.today().year


VALIDATORS: dict[str, Validator] = {
    "luhn": luhn,
    "inn": inn,
    "inn12": inn12,
    "snils": snils,
    "phone_digits": phone_digits,
    "not_repeated": not_repeated,
    "date_any": date_any,
    "birth_like": birth_like,
    "plausible_birth": plausible_birth,
    "issue_like": issue_like,
}
