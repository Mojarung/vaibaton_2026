"""Правдоподобные подставные значения того же формата."""

from __future__ import annotations

import random

from ..core.validators import digits as _digits

MALE_NAMES = ["Александр", "Дмитрий", "Сергей", "Андрей", "Алексей", "Максим", "Иван", "Николай"]
FEMALE_NAMES = ["Елена", "Ольга", "Наталья", "Татьяна", "Ирина", "Анна", "Мария", "Светлана"]
MALE_SURNAMES = ["Иванов", "Петров", "Сидоров", "Кузнецов", "Смирнов", "Волков", "Соколов"]
FEMALE_SURNAMES = ["Иванова", "Петрова", "Сидорова", "Кузнецова", "Смирнова", "Волкова", "Соколова"]
MALE_PATRONYMICS = [
    "Александрович",
    "Дмитриевич",
    "Сергеевич",
    "Андреевич",
    "Иванович",
    "Николаевич",
]
FEMALE_PATRONYMICS = [
    "Александровна",
    "Дмитриевна",
    "Сергеевна",
    "Андреевна",
    "Ивановна",
    "Николаевна",
]
CITIES = ["Кострома", "Вологда", "Тверь", "Рязань", "Калуга", "Орёл", "Псков", "Смоленск"]
STREETS = ["Садовая", "Лесная", "Школьная", "Центральная", "Парковая", "Набережная", "Советская"]
REGIONS = ["Костромская", "Тверская", "Рязанская", "Калужская", "Орловская", "Псковская"]
COUNTRIES = ["Российская Федерация", "Республика Беларусь", "Республика Казахстан"]
LATIN_NAMES = ["IVAN", "DMITRY", "SERGEY", "ANDREY", "ALEXEY", "MAXIM", "NIKOLAY"]
LATIN_SURNAMES = ["IVANOV", "PETROV", "SIDOROV", "KUZNETSOV", "SMIRNOV", "VOLKOV", "SOKOLOV"]


def _pick(options: list[str], original: str, rng: random.Random) -> str:
    """Случайный вариант, не похожий на исходные слова: «Иванов» не превратится в «Иванович»."""
    stems = {w.lower()[:4] for w in original.replace(".", " ").split() if len(w) >= 4}
    fresh = [o for o in options if o.lower()[:4] not in stems]
    return rng.choice(fresh or options)


def _gender(original: str) -> str:
    low = original.lower()
    if low.endswith(("а", "я", "вна", "чна", "ова", "ева", "ина")):
        return "female"
    return "male"


def _replace_digits(value: str, rng: random.Random) -> str:
    """Меняет цифры, сохраняя длину и разделители; первая цифра не становится нулём."""
    out = []
    first = True
    for ch in value:
        if ch.isdigit():
            if first:
                out.append(str(rng.randint(1, 9)))
                first = False
            else:
                out.append(str(rng.randint(0, 9)))
        else:
            out.append(ch)
    return "".join(out)


def _date(value: str, rng: random.Random) -> str:
    parts = [
        p
        for p in value.replace(".", " ").replace("/", " ").replace("-", " ").split()
        if p.isdigit()
    ]
    if len(parts) != 3:
        return _replace_digits(value, rng)
    year = rng.randint(1955, 2003)
    out = []
    for p in parts:
        if len(p) == 4:
            out.append(str(year))
        elif len(p) == 2 and len(parts[2]) == 2:
            out.append(f"{year % 100:02d}")
        else:
            out.append(str(rng.randint(1, 12)).zfill(len(p)))
    return value.replace(parts[0], out[0]).replace(parts[1], out[1]).replace(parts[2], out[2])


def _luhn_digit(partial: str) -> str:
    total = 0
    for i, ch in enumerate(reversed(partial)):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return str((10 - total % 10) % 10)


def _synthesize_person(original: str, rng: random.Random) -> str:
    gender = _gender(original)
    words = original.split()
    if len(words) >= 3:
        surname = FEMALE_SURNAMES if gender == "female" else MALE_SURNAMES
        patronymic = FEMALE_PATRONYMICS if gender == "female" else MALE_PATRONYMICS
        name = FEMALE_NAMES if gender == "female" else MALE_NAMES
        return f"{_pick(surname, original, rng)} {_pick(name, original, rng)} {_pick(patronymic, original, rng)}"
    if len(words) == 2:
        name = FEMALE_NAMES if gender == "female" else MALE_NAMES
        surname = FEMALE_SURNAMES if gender == "female" else MALE_SURNAMES
        if "." in original:
            return f"{_pick(surname, original, rng)} {_pick(name, original, rng)[0]}."
        return f"{_pick(name, original, rng)} {_pick(surname, original, rng)}"
    surname = FEMALE_SURNAMES if gender == "female" else MALE_SURNAMES
    return _pick(surname, original, rng)


def _synthesize_cardholder(_original: str, rng: random.Random) -> str:
    return f"{rng.choice(LATIN_NAMES)} {rng.choice(LATIN_SURNAMES)}"


def _synthesize_email(_original: str, rng: random.Random) -> str:
    return f"user{rng.randint(1000, 99999)}@example.org"


def _synthesize_citizenship(_original: str, rng: random.Random) -> str:
    return rng.choice(COUNTRIES)


def _synthesize_passport_authority(_original: str, rng: random.Random) -> str:
    return f"ОВД района {rng.choice(STREETS)} г. {rng.choice(CITIES)}"


def _synthesize_birth_place(_original: str, rng: random.Random) -> str:
    return rng.choice(CITIES)


def _synthesize_bank_card(original: str, rng: random.Random) -> str:
    base = _replace_digits(original, rng)
    d = _digits(base)
    if len(d) >= 2:
        check = _luhn_digit(d[:-1])
        base = base[::-1].replace(d[-1], check, 1)[::-1]
    return base


def _synthesize_phone(original: str, rng: random.Random) -> str:
    d = _digits(original)
    keep = 2 if len(d) == 11 else (1 if len(d) == 10 else 0)
    out = []
    digit_idx = 0
    for ch in original:
        if ch.isdigit():
            if digit_idx < keep:
                out.append(ch)
            else:
                out.append(str(rng.randint(0, 9)))
            digit_idx += 1
        else:
            out.append(ch)
    return "".join(out)


def _synthesize_address(subtype: str | None, original: str, rng: random.Random) -> str:
    if subtype == "CITY":
        return rng.choice(CITIES)
    if subtype == "STREET":
        return rng.choice(STREETS)
    if subtype == "REGION":
        return rng.choice(REGIONS)
    if subtype == "COUNTRY":
        return "Россия"
    if subtype == "DISTRICT":
        return rng.choice(STREETS)
    if any(c.isdigit() for c in original):
        return _replace_digits(original, rng)
    return rng.choice(CITIES)


# Диспетчер по типу: функция-генератор подставного значения.
_GENERATORS: dict[str, callable] = {
    "PERSON": _synthesize_person,
    "CARDHOLDER": _synthesize_cardholder,
    "EMAIL": _synthesize_email,
    "CITIZENSHIP": _synthesize_citizenship,
    "PASSPORT_AUTHORITY": _synthesize_passport_authority,
    "BIRTH_DATE": _date,
    "PASSPORT_DATE": _date,
    "BIRTH_PLACE": _synthesize_birth_place,
    "BANK_CARD": _synthesize_bank_card,
    "PHONE": _synthesize_phone,
    "ADDRESS": _synthesize_address,
}


def synthesize(kind: str, subtype: str | None, original: str, rng: random.Random) -> str:
    """Подставное значение того же формата."""
    gen = _GENERATORS.get(kind)
    if gen is not None:
        if kind == "ADDRESS":
            return gen(subtype, original, rng)
        return gen(original, rng)
    if any(c.isdigit() for c in original):
        return _replace_digits(original, rng)
    return f"{kind.lower().replace('_', '-')}-{rng.randint(100, 999)}"
