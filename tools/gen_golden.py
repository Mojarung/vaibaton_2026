"""Генератор размеченного датасета вариаций.

Запуск: uv run python -m tools.gen_golden [--seed 7] [--rounds 40]
[--out datasets/golden/generated.jsonl]
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.golden_values import (  # noqa: E402
    AUTHORITIES,
    CITIES,
    COUNTRIES,
    REGIONS,
    SEP_FLAT,
    SEP_HOUSE,
    SEP_STREET,
    TRANSLIT,
    VILLAGES,
    Builder,
    address,
    card_forms,
    date_formats,
    date_parts,
    fio_forms,
    inflect,
    inn10,
    inn12,
    passport_forms,
    person,
    phone_forms,
    snils,
)

CONTEXTS = {
    "PERSON": [
        "ФИО: {v}",
        "Клиент {v} просит перевыпустить карту.",
        "Заявитель: {v}",
        "Звонил {v}, просил перезвонить.",
        "Ответственный сотрудник {v}.",
        "Получатель перевода - {v}.",
    ],
    "BIRTH_DATE": [
        "Дата рождения: {v}",
        "родился {v} года",
        "д.р. {v}",
        "{v} г.р.",
        "Клиентка родилась {v}, сейчас ей нужен кредит.",
        "Date of birth: {v}",
        "дата рождения - {v} г.",
    ],
    "PASSPORT_DATE": [
        "Дата выдачи: {v}",
        "Паспорт выдан {v} года.",
        "дата выдачи паспорта {v}",
    ],
    "PHONE": [
        "тел.: {v}",
        "Телефон {v}",
        "Позвоните мне по номеру {v}, я на связи.",
        "моб. {v}",
        "контактный номер: {v}",
        "Звоните на {v} после 18:00.",
    ],
    "EMAIL": [
        "email: {v}",
        "E-mail {v}",
        "Пришлите выписку на {v}, пожалуйста.",
        "почта: {v}",
    ],
    "INN": [
        "ИНН: {v}",
        "ИНН {v}",
        "Мой ИНН {v}.",
        "Идентификационный номер налогоплательщика: {v}",
    ],
    "BANK_CARD": [
        "карта {v}",
        "Номер карты: {v}",
        "Переведите 500 рублей на карту {v}.",
        "Карта Visa {v} заблокирована.",
        "PAN: {v}",
    ],
    "CVV": [
        "CVV: {v}",
        "CVV2 {v}",
        "cvc {v}",
        "код безопасности {v}",
        "три цифры на обороте: {v}",
    ],
    "PIN": [
        "PIN: {v}",
        "пин-код {v}",
        "ПИН-код карты: {v}",
        "pin code {v}",
        "Мой пин {v}, не говорите никому.",
    ],
    "CARDHOLDER": [
        "Держатель карты: {v}",
        "Имя на карте: {v}",
        "cardholder: {v}",
        "Владелец карты {v}",
    ],
    "SNILS": [
        "СНИЛС: {v}",
        "СНИЛС {v}",
        "страховой номер {v}",
    ],
    "DRIVER_LICENSE": [
        "ВУ: {v}",
        "водительское удостоверение {v}",
        "в/у {v}",
        "Права: {v}",
        "Водительское удостоверение № {v} действительно.",
    ],
    "DEPARTMENT_CODE": [
        "код подразделения: {v}",
        "к/п {v}",
        "код подр. {v}",
        "Код подразделения {v}.",
    ],
    "PASSPORT_AUTHORITY": [
        "Кем выдан: {v}",
        "Орган, выдавший паспорт: {v}",
        "Паспорт выдан {v}.",
    ],
    "PASSPORT": [
        "Паспорт: {v}",
        "паспорт гражданина РФ {v}",
        "Паспортные данные: {v}",
        "Предъявил паспорт {v} на кассе.",
    ],
    "ADDRESS": [
        "Адрес: {v}",
        "проживает по адресу: {v}",
        "Адрес регистрации: {v}",
        "Доставьте по адресу {v}.",
    ],
}


class _IdCounter:
    """Сквозной счётчик id примеров, создаётся один раз на генерацию."""

    def __init__(self) -> None:
        self._n = 0

    def next(self) -> str:
        self._n += 1
        return f"gen-{self._n:05d}"


def emit(
    out: list,
    rng: random.Random,
    ids: _IdCounter,
    category: str,
    variant: str,
    items: list,
    bare: bool = True,
) -> None:
    """Добавляет голый пример (если bare) и пример в случайном шаблоне типа."""
    ptype = next(c[1] for c in items if isinstance(c, tuple) and c[1] != "TRAP")
    if bare:
        idx = [i for i, c in enumerate(items) if isinstance(c, tuple) and c[1] != "TRAP"]
        if len(idx) == 1:
            out.append(
                Builder()
                .extend([items[idx[0]]])
                .build(ids.next(), category, f"bare:{variant}", "as_is")
            )
    template = rng.choice(CONTEXTS[ptype])
    prefix, _, suffix = template.partition("{v}")
    ctx_items = [prefix, *items, suffix]
    r = rng.random()
    if r < 0.6:
        reg = "as_is"
    elif r < 0.8:
        reg = "upper"
    else:
        reg = "lower"
    out.append(Builder().extend(ctx_items).build(ids.next(), category, f"ctx:{variant}", reg))


def gen_names_dates(out: list, rng: random.Random, ids: _IdCounter) -> None:
    p = person(rng)
    forms = fio_forms(p, "nominative")
    for form, value in forms.items():
        bare = form in ("fio", "iof", "f_io")
        emit(out, rng, ids, "PERSON", f"fio:{form}", [(value, "PERSON")], bare=bare)
    d, m, y = date_parts(rng, 1950, 2005)
    formats = date_formats(d, m, y)
    for fmt, value in formats.items():
        bare = fmt.startswith(("dd.", "text"))
        emit(out, rng, ids, "BIRTH_DATE", f"date:{fmt}", [(value, "BIRTH_DATE")], bare=bare)
    d, m, y = date_parts(rng, 2005, 2025)
    formats = date_formats(d, m, y)
    fmt = rng.choice(list(formats.keys()))
    emit(
        out,
        rng,
        ids,
        "PASSPORT_DATE",
        f"issue:{fmt}",
        [(formats[fmt], "PASSPORT_DATE")],
        bare=False,
    )


def gen_numbers(out: list, rng: random.Random, ids: _IdCounter) -> None:
    for form in phone_forms(rng):
        emit(out, rng, ids, "PHONE", f"phone:{form}", [(form, "PHONE")], bare=rng.random() < 0.4)
    for form in card_forms(rng):
        emit(out, rng, ids, "BANK_CARD", f"card:{form}", [(form, "BANK_CARD")], bare=True)
    for name, items in passport_forms(rng):
        bare = name in ("s4_n", "s2_s2_n", "seria_nomer")
        emit(out, rng, ids, "PASSPORT", f"passport:{name}", items, bare=bare)
    for name, items in address(rng):
        bare = name in ("full_post", "city_street_bld")
        emit(out, rng, ids, "ADDRESS", f"addr:{name}", items, bare=bare)


def gen_small(out: list, rng: random.Random, ids: _IdCounter) -> None:
    p = person(rng)
    surname = p["sur"]
    local = surname.lower().translate(TRANSLIT)
    r = rng.random()
    if r < 0.33:
        local = (
            p["first"][0].lower().translate(TRANSLIT) + "." + surname.lower().translate(TRANSLIT)
        )
    elif r < 0.66:
        local = surname.lower().translate(TRANSLIT) + str(rng.randint(70, 99))
    domain = rng.choice(
        ["mail.ru", "yandex.ru", "gmail.com", "bk.ru", "inbox.ru", "corp.alfa-client.ru"]
    )
    email = f"{local}@{domain}"
    emit(out, rng, ids, "EMAIL", "email", [(email, "EMAIL")], bare=True)

    emit(out, rng, ids, "INN", "inn12", [(inn12(rng), "INN")], bare=True)
    emit(out, rng, ids, "INN", "inn10", [(inn10(rng), "INN")], bare=False)

    cvv = str(rng.randint(100, 999))
    emit(out, rng, ids, "CVV", "cvv", [(cvv, "CVV")], bare=rng.random() < 0.3)
    pin = str(rng.randint(1000, 9999))
    emit(out, rng, ids, "PIN", "pin", [(pin, "PIN")], bare=rng.random() < 0.3)

    holder = (
        f"{p['sur'].lower().translate(TRANSLIT).upper()} "
        f"{p['first'].lower().translate(TRANSLIT).upper()}"
    )
    emit(out, rng, ids, "CARDHOLDER", "holder", [(holder, "CARDHOLDER")], bare=True)

    emit(out, rng, ids, "SNILS", "snils", [(snils(rng), "SNILS")], bare=True)

    series = rng.choice(
        [
            f"{rng.randint(10, 99)} {rng.randint(10, 99)}",
            f"{rng.randint(1000, 9999)}",
            f"{rng.randint(10, 99)}{rng.choice(['АВ', 'ТК', 'МС'])}",
        ]
    )
    number = f"{rng.randint(100000, 999999)}"
    emit(
        out,
        rng,
        ids,
        "DRIVER_LICENSE",
        "dl",
        [(f"{series} {number}", "DRIVER_LICENSE")],
        bare=False,
    )

    code = f"{rng.randint(0, 999):03d}-{rng.randint(0, 999):03d}"
    emit(out, rng, ids, "DEPARTMENT_CODE", "dept", [(code, "DEPARTMENT_CODE")], bare=True)

    authority = rng.choice(AUTHORITIES)
    emit(
        out,
        rng,
        ids,
        "PASSPORT_AUTHORITY",
        "authority",
        [(authority, "PASSPORT_AUTHORITY")],
        bare=False,
    )


def gen_cases(out: list, rng: random.Random, ids: _IdCounter) -> None:
    p = person(rng)
    frames = [
        ("дат", "Прошу выдать кредит {v}.", "dative"),
        ("твор", "Договор заключён с {v} на 5 лет.", "instrumental"),
        ("род", "Заявление от {v} принято.", "genitive"),
        ("предл", "Речь о {v}, клиенте с 2015 года.", "prepositional"),
        ("дат2", "Направить ответ {v} до пятницы.", "dative"),
        ("род2", "Доверенность на имя {v} оформлена.", "genitive"),
    ]
    form = rng.choice(["fio", "iof", "if", "fi"])
    case_name, template, case = rng.choice(frames)
    value = fio_forms(p, case)[form]
    prefix, _, suffix = template.partition("{v}")
    items = [prefix, (value, "PERSON"), suffix]
    out.append(
        Builder().extend(items).build(ids.next(), "PERSON", f"case_{case_name}:{form}", "as_is")
    )


def gen_citizenship_birth(out: list, rng: random.Random, ids: _IdCounter) -> None:
    country_nom, country_gen = rng.choice(COUNTRIES)
    city = rng.choice(CITIES)
    region = rng.choice(REGIONS)
    village = rng.choice(VILLAGES)

    way = rng.randint(0, 3)
    if way == 0:
        items = ["Гражданство: ", (country_nom, "CITIZENSHIP")]
    elif way == 1:
        items = ["гражданин ", (country_gen, "CITIZENSHIP")]
    elif way == 2:
        items = ["Клиентка, гражданка ", (country_gen, "CITIZENSHIP"), ", ВНЖ нет."]
    else:
        items = [(country_nom, "CITIZENSHIP")]
    out.append(Builder().extend(items).build(ids.next(), "CITIZENSHIP", "citizenship", "as_is"))

    way = rng.randint(0, 4)
    if way == 0:
        items = ["Место рождения: г. ", (city, "BIRTH_PLACE")]
    elif way == 1:
        items = ["Место рождения: ", (city, "BIRTH_PLACE")]
    elif way == 2:
        items = [
            "родился в ",
            (inflect(city, "prepositional", "Geox"), "BIRTH_PLACE"),
            " в семье инженеров",
        ]
    elif way == 3:
        items = [
            "Место рождения: с. ",
            (village, "BIRTH_PLACE"),
            " ",
            (region, "BIRTH_PLACE"),
            " обл.",
        ]
    else:
        items = ["уроженец г. ", (inflect(city, "genitive", "Geox"), "BIRTH_PLACE")]
    out.append(Builder().extend(items).build(ids.next(), "BIRTH_PLACE", "birth_place", "as_is"))


def gen_foreign(out: list, rng: random.Random, ids: _IdCounter) -> None:
    way = rng.randint(0, 5)
    if way == 0:
        series = f"{rng.randint(70, 79)}"
        number = f"{rng.randint(1000000, 9999999)}"
        items = ["Загранпаспорт: ", (f"{series} {number}", "FOREIGN_DOCUMENT")]
    elif way == 1:
        series = f"{rng.randint(80, 89)}"
        number = f"{rng.randint(1000000, 9999999)}"
        items = ["ВНЖ: ", (f"{series} {number}", "FOREIGN_DOCUMENT")]
    elif way == 2:
        roman = rng.choice(["I", "II", "III", "IV", "V"])
        letters = rng.choice(["МЮ", "ИК", "РУ", "ЛО"])
        number = f"{rng.randint(100000, 999999)}"
        items = ["Свидетельство о рождении: ", (f"{roman}-{letters} {number}", "FOREIGN_DOCUMENT")]
    elif way == 3:
        series = rng.choice(["АБ", "АК", "МО"])
        number = f"{rng.randint(1000000, 9999999)}"
        items = ["Военный билет: ", (f"{series} {number}", "FOREIGN_DOCUMENT")]
    elif way == 4:
        series = f"{rng.randint(70, 79)}"
        number = f"{rng.randint(1000000, 9999999)}"
        items = [
            "заграничный паспорт серия ",
            (series, "FOREIGN_DOCUMENT"),
            " номер ",
            (number, "FOREIGN_DOCUMENT"),
        ]
    else:
        series = f"{rng.randint(80, 89)}"
        number = f"{rng.randint(1000000, 9999999)}"
        items = ["вид на жительство № ", (f"{series} {number}", "FOREIGN_DOCUMENT")]
    out.append(Builder().extend(items).build(ids.next(), "FOREIGN_DOCUMENT", "foreign", "as_is"))


def gen_complex(out: list, rng: random.Random, ids: _IdCounter) -> None:
    p = person(rng)
    forms = fio_forms(p, "nominative")
    d, m, y = date_parts(rng, 1960, 2002)
    birth = date_formats(d, m, y)["dd.mm.yyyy"]
    passport_series = f"{rng.randint(1000, 9999)}"
    passport_number = f"{rng.randint(100000, 999999)}"
    authority = rng.choice(AUTHORITIES)
    dept = f"{rng.randint(100, 999)}-{rng.randint(100, 999)}"
    city = rng.choice(CITIES)
    house = str(rng.randint(1, 99))
    apt = str(rng.randint(1, 200))
    phone = rng.choice(phone_forms(rng))
    inn = inn12(rng)
    sn = snils(rng)

    items = [
        "ФИО: ",
        (forms["fio"], "PERSON"),
        "\nДата рождения: ",
        (birth, "BIRTH_DATE"),
        "\nПаспорт: серия ",
        (passport_series, "PASSPORT"),
        " номер ",
        (passport_number, "PASSPORT"),
        "\nКем выдан: ",
        (authority, "PASSPORT_AUTHORITY"),
        "\nКод подразделения: ",
        (dept, "DEPARTMENT_CODE"),
        "\nАдрес регистрации: г. ",
        (city, "ADDRESS"),
        ", ул. Садовая, д. ",
        (house, "ADDRESS"),
        SEP_FLAT,
        (apt, "ADDRESS"),
        "\nТелефон: ",
        (phone, "PHONE"),
        "\nИНН: ",
        (inn, "INN"),
        "\nСНИЛС: ",
        (sn, "SNILS"),
    ]
    out.append(Builder().extend(items).build(ids.next(), "COMPLEX", "anketa", "as_is"))

    card = rng.choice(card_forms(rng))
    pin = str(rng.randint(1000, 9999))
    items = [
        "Оператор: Назовите номер карты.\nКлиент: ",
        (card, "BANK_CARD"),
        ".\nОператор: Не называйте CVV.\nКлиент: Меня зовут ",
        (f"{p['first']} {p['patr']}", "PERSON"),
        ", мой пин ",
        (pin, "PIN"),
        ".",
    ]
    out.append(Builder().extend(items).build(ids.next(), "COMPLEX", "dialog", "as_is"))

    dative = fio_forms(p, "dative")["fi"]
    city = rng.choice(CITIES)
    items = [
        "Составь вежливое письмо клиенту ",
        (dative, "PERSON"),
        ". Карта ",
        (card, "BANK_CARD"),
        " перевыпущена и доставлена по адресу г. ",
        (city, "ADDRESS"),
        ", ул. Садовая, д. 5. Поэт ",
        ("Пушкин", "TRAP"),
        " тут ни при чём.",
    ]
    out.append(Builder().extend(items).build(ids.next(), "COMPLEX", "prompt", "as_is"))


TRAPS = [
    ["поэт ", ("Александр Пушкин", "TRAP"), " написал «Евгения Онегина»"],
    ["роман ", ("Льва Толстого", "TRAP"), " «Война и мир» изучают в школе"],
    [
        "адрес отделения банка г. ",
        ("Москва", "TRAP"),
        SEP_STREET,
        ("Тверская", "TRAP"),
        SEP_HOUSE,
        ("1", "TRAP"),
    ],
    ["наш офис на ул. ", ("Пушкина", "TRAP"), SEP_HOUSE, ("10", "TRAP")],
    ["горячая линия банка ", ("8 800 100-00-00", "TRAP"), ", звонок бесплатный"],
    ["встреча назначена на ", ("22.09.2026", "TRAP"), " в 10:00"],
    ["договор № ", ("1234567890", "TRAP"), " от ", ("01.02.2020", "TRAP"), " расторгнут"],
    ["сумма перевода ", ("15 000", "TRAP"), " руб."],
    ["версия приложения ", ("2.3.1", "TRAP"), " вышла в ", ("2024", "TRAP"), " году"],
    [("Юрий Гагарин", "TRAP"), " первым полетел в космос"],
    ["в ", ("1990", "TRAP"), " году банк открыл первый филиал"],
    [
        "ПАО «Альфа-Банк», ИНН ",
        ("7728168971", "TRAP"),
        ", г. ",
        ("Москва", "TRAP"),
        SEP_STREET,
        ("Каланчевская", "TRAP"),
        SEP_HOUSE,
        ("27", "TRAP"),
    ],
    ["погода в ", ("Москве", "TRAP"), " сегодня солнечная"],
    ["памятник ", ("Петру I", "TRAP"), " стоит на набережной"],
    ["картина ", ("Ильи Репина", "TRAP"), " «Бурлаки на Волге»"],
    ["номер заказа ", ("4581234", "TRAP"), ", трек ", ("RA123456789RU", "TRAP")],
    ["филиал банка на пр-те ", ("Мира", "TRAP"), SEP_HOUSE, ("5", "TRAP"), ", с 9 до 18"],
    ["отчёт за период с ", ("01.01.2025", "TRAP"), " по ", ("31.03.2025", "TRAP")],
    ["станция метро «", ("Пушкинская", "TRAP"), "» закрыта на ремонт"],
    ["композитор ", ("Пётр Чайковский", "TRAP"), " родился в Воткинске"],
    ["колл-центр ", ("8 (800) 200-00-00", "TRAP"), " круглосуточно"],
    ["курс доллара ", ("92,15", "TRAP"), " на ", ("15.09.2026", "TRAP")],
]


def gen_traps(out: list, rng: random.Random, ids: _IdCounter, rounds: int) -> None:
    for i in range(rounds * 2):
        items = TRAPS[i % len(TRAPS)]
        r = rng.random()
        if r < 0.5:
            reg = "as_is"
        elif r < 0.75:
            reg = "upper"
        else:
            reg = "lower"
        out.append(Builder().extend(items).build(ids.next(), "TRAP", f"trap:{i % len(TRAPS)}", reg))
    p = person(rng)
    surname = "Пушкин" if not p["female"] else "Пушкина"
    fio = f"{surname} {p['first']} {p['patr']}"
    items = ["Клиент ", (fio, "PERSON"), ", паспорт ", ("4509 123456", "PASSPORT")]
    out.append(Builder().extend(items).build(ids.next(), "COMPLEX", "reverse", "as_is"))


def generate(seed: int, rounds: int) -> list[dict]:
    """Генерирует размеченный датасет вариаций."""
    ids = _IdCounter()
    rng = random.Random(seed)
    out: list[dict] = []
    for _ in range(rounds):
        gen_names_dates(out, rng, ids)
        gen_numbers(out, rng, ids)
        gen_small(out, rng, ids)
        gen_cases(out, rng, ids)
        gen_citizenship_birth(out, rng, ids)
        gen_foreign(out, rng, ids)
        gen_complex(out, rng, ids)
    gen_traps(out, rng, ids, rounds)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--rounds", type=int, default=40)
    parser.add_argument(
        "--out", type=Path, default=ROOT / "datasets" / "golden" / "generated.jsonl"
    )
    args = parser.parse_args()

    examples = generate(args.seed, args.rounds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.writelines(json.dumps(ex, ensure_ascii=False) + "\n" for ex in examples)
    print(f"всего: {len(examples)}")
    for cat, count in sorted(Counter(ex["category"] for ex in examples).items()):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()
