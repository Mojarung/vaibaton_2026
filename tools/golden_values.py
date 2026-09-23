"""Словари и генераторы значений для датасета вариаций."""

from __future__ import annotations

import random

import pymorphy3

_MORPH = pymorphy3.MorphAnalyzer()

SEP_STREET = ", ул. "
SEP_HOUSE = ", д. "
SEP_FLAT = ", кв. "

MALE_NAMES = [
    "Иван",
    "Пётр",
    "Сергей",
    "Алексей",
    "Дмитрий",
    "Андрей",
    "Михаил",
    "Николай",
    "Владимир",
    "Олег",
    "Артём",
    "Максим",
    "Кирилл",
    "Егор",
    "Роман",
    "Виктор",
    "Юрий",
    "Григорий",
    "Тимур",
    "Руслан",
]
FEMALE_NAMES = [
    "Анна",
    "Мария",
    "Елена",
    "Ольга",
    "Наталья",
    "Татьяна",
    "Ирина",
    "Светлана",
    "Юлия",
    "Екатерина",
    "Дарья",
    "Ксения",
    "Полина",
    "Алёна",
    "Вера",
    "Надежда",
    "Любовь",
    "Галина",
    "Софья",
    "Алиса",
]
MALE_PATRONYMICS = [
    "Иванович",
    "Петрович",
    "Сергеевич",
    "Алексеевич",
    "Дмитриевич",
    "Андреевич",
    "Михайлович",
    "Николаевич",
    "Владимирович",
    "Олегович",
    "Юрьевич",
    "Ильич",
]
FEMALE_PATRONYMICS = [
    "Ивановна",
    "Петровна",
    "Сергеевна",
    "Алексеевна",
    "Дмитриевна",
    "Андреевна",
    "Михайловна",
    "Николаевна",
    "Владимировна",
    "Олеговна",
    "Юрьевна",
    "Ильинична",
]

_MALE_SURNAMES = [
    "Иванов",
    "Петров",
    "Смирнов",
    "Кузнецов",
    "Соколов",
    "Попов",
    "Лебедев",
    "Козлов",
    "Новиков",
    "Морозов",
    "Волков",
    "Соловьёв",
    "Васильев",
    "Зайцев",
    "Павлов",
    "Семёнов",
    "Голубев",
    "Виноградов",
    "Богданов",
    "Воробьёв",
    "Фёдоров",
    "Михайлов",
    "Беляев",
    "Тарасов",
    "Белов",
    "Комаров",
    "Орлов",
    "Киселёв",
    "Макаров",
    "Андреев",
    "Ковалёв",
    "Ильин",
    "Гусев",
    "Титов",
    "Кузьмин",
    "Кудрявцев",
    "Баранов",
    "Куликов",
    "Алексеев",
    "Степанов",
    "Яковлев",
    "Сорокин",
    "Сергеев",
    "Романов",
    "Захаров",
    "Борисов",
    "Королёв",
    "Герасимов",
    "Пономарёв",
    "Григорьев",
    "Лазарев",
    "Медведев",
    "Ершов",
    "Никитин",
    "Соболев",
    "Рябов",
    "Поляков",
    "Цветков",
    "Данилов",
    "Жуков",
    "Фролов",
    "Журавлёв",
    "Николаев",
    "Крылов",
    "Максимов",
    "Сидоров",
    "Осипов",
    "Белоусов",
    "Федотов",
    "Дорофеев",
    "Егоров",
    "Матвеев",
    "Бобров",
    "Дмитриев",
    "Калинин",
    "Анисимов",
    "Петухов",
    "Антонов",
    "Тимофеев",
    "Никифоров",
    "Веселов",
    "Филиппов",
    "Марков",
    "Большаков",
    "Суханов",
    "Миронов",
    "Ширяев",
    "Александров",
    "Коновалов",
    "Шестаков",
    "Казаков",
    "Ефимов",
    "Денисов",
    "Громов",
    "Фомин",
    "Давыдов",
    "Мельников",
    "Щербаков",
    "Блинов",
    "Колесников",
    "Карпов",
    "Афанасьев",
    "Власов",
    "Маслов",
    "Исаков",
    "Тихонов",
    "Аксёнов",
    "Гаврилов",
    "Родионов",
    "Котов",
    "Горбунов",
    "Кудряшов",
    "Быков",
    "Зуев",
    "Третьяков",
    "Савельев",
    "Панов",
    "Рыбаков",
    "Суворов",
    "Абрамов",
    "Воронов",
    "Мухин",
    "Архипов",
    "Трофимов",
    "Мартынов",
    "Емельянов",
    "Мещеряков",
    "Майоров",
    "Владимиров",
    "Агеев",
    "Медведев",
    "Дементьев",
    "Самсонов",
    "Ларионов",
    "Ермаков",
    "Масленников",
    "Богданов",
    "Костин",
    "Бирюков",
    "Шаров",
    "Зыков",
    "Бычков",
    "Крюков",
    "Овчинников",
    "Ситников",
    "Стрелков",
    "Гущин",
    "Тетерин",
    "Колобов",
    "Субботин",
    "Фокин",
    "Блохин",
    "Селиверстов",
    "Пестов",
    "Кондратьев",
    "Силин",
    "Меркушев",
    "Лыткин",
    "Туров",
    "Сергеев",
    "Зубков",
    "Артамонов",
    "Балашов",
    "Прохоров",
    "Одинцов",
    "Сафонов",
    "Кулагин",
    "Копылов",
    "Лавров",
    "Чистяков",
    "Барсуков",
    "Сазонов",
    "Корнилов",
    "Астафьев",
    "Наумов",
    "Логинов",
    "Горшков",
    "Кириллов",
    "Орехов",
    "Ефимов",
    "Черных",
    "Белкин",
    "Лапин",
    "Гончаров",
    "Шубин",
    "Агафонов",
    "Лукин",
    "Ларионов",
    "Москвин",
    "Буров",
    "Шевелёв",
    "Корчагин",
    "Сычёв",
    "Беспалов",
    "Смирнов",
    "Курочкин",
    "Рогов",
    "Шилов",
    "Гуляев",
    "Курбатов",
    "Скворцов",
    "Дроздов",
    "Калинин",
    "Березин",
    "Галкин",
    "Дорохов",
    "Шувалов",
    "Панкратов",
    "Шишкин",
    "Крысанов",
    "Мальцев",
    "Носов",
    "Харитонов",
    "Князев",
    "Гордеев",
    "Лукоянов",
    "Федосеев",
    "Зимин",
    "Пахомов",
    "Шипилов",
    "Рожков",
    "Логинов",
    "Сысоев",
    "Климов",
    "Гордеев",
    "Шевченко",
    "Ковальчук",
    "Бондаренко",
    "Кравченко",
    "Ткаченко",
    "Гончаренко",
    "Мельниченко",
    "Сидоренко",
    "Закревский",
    "Вишневский",
    "Покровский",
    "Ахмедов",
    "Алиев",
    "Гасанов",
    "Ибрагимов",
    "Хасанов",
    "Юсупов",
    "Каримов",
    "Сафин",
    "Галиев",
    "Гарипов",
    "Шарипов",
    "Валиев",
    "Мамедов",
    "Оганесян",
    "Саркисян",
    "Петросян",
    "Геворкян",
    "Беридзе",
    "Кацнельсон",
    "Рабинович",
    "Цой",
    "Ли",
    "Пак",
]


def _female_surname(male: str) -> str:
    if male.endswith("ский"):
        return male[:-2] + "ая"
    if male.endswith("цкий"):
        return male[:-2] + "ая"
    if male.endswith(("ов", "ев", "ёв", "ин", "ын")):
        return male + "а"
    return male


MALE_SURNAMES = _MALE_SURNAMES
FEMALE_SURNAMES = [_female_surname(s) for s in _MALE_SURNAMES]

CITIES = [
    "Москва",
    "Тула",
    "Казань",
    "Самара",
    "Воронеж",
    "Пермь",
    "Уфа",
    "Омск",
    "Томск",
    "Тверь",
    "Рязань",
    "Калуга",
    "Курск",
    "Липецк",
    "Иркутск",
    "Хабаровск",
    "Владивосток",
    "Ярославль",
    "Кострома",
    "Иваново",
    "Сочи",
    "Краснодар",
    "Ростов-на-Дону",
    "Нижний Новгород",
    "Санкт-Петербург",
    "Екатеринбург",
    "Новосибирск",
    "Челябинск",
    "Красноярск",
    "Волгоград",
    "Саратов",
    "Тюмень",
    "Барнаул",
    "Пенза",
    "Смоленск",
    "Брянск",
    "Орёл",
    "Белгород",
    "Мурманск",
    "Архангельск",
]
VILLAGES = [
    "Ивановка",
    "Петровское",
    "Сосновка",
    "Берёзовка",
    "Никольское",
    "Александровка",
    "Покровка",
    "Михайловка",
    "Жуковка",
    "Раздоры",
    "Горки",
    "Малиновка",
]
REGIONS = [
    "Московская",
    "Тульская",
    "Калужская",
    "Тверская",
    "Рязанская",
    "Воронежская",
    "Самарская",
    "Ленинградская",
    "Свердловская",
    "Новосибирская",
    "Нижегородская",
    "Ярославская",
]
DISTRICTS = [
    "Одинцовский",
    "Щёкинский",
    "Ленинский",
    "Раменский",
    "Пушкинский",
    "Истринский",
    "Заокский",
    "Богородский",
    "Центральный",
    "Советский",
]
STREETS = [
    "Лесная",
    "Садовая",
    "Советская",
    "Молодёжная",
    "Школьная",
    "Полевая",
    "Набережная",
    "Заречная",
    "Гагарина",
    "Ленина",
    "Мира",
    "Пушкина",
    "Зелёная",
    "Строителей",
    "Первомайская",
    "Кирова",
    "Профсоюзная",
    "Тверская",
    "Большая Полянка",
    "Новый Арбат",
    "Маршала Жукова",
    "8 Марта",
]
STREET_TYPES = [
    "ул.",
    "улица",
    "пр-т",
    "проспект",
    "пер.",
    "переулок",
    "б-р",
    "бульвар",
    "ш.",
    "шоссе",
]

AUTHORITIES = [
    "ОВД района Хамовники г. Москвы",
    "ГУ МВД России по г. Москве",
    "УФМС России по Тульской обл.",
    "ОУФМС России по гор. Москве по району Митино",
    "ТП № 12 ОУФМС России по Московской обл. в Одинцовском р-не",
    "Отделом УФМС России по Калужской области в Ленинском округе г. Калуги",
    "МВД по Республике Татарстан",
    "ГУ МВД России по Свердловской области",
    "Отделением УФМС России по Воронежской обл. в Советском р-не г. Воронежа",
    "УМВД России по Тверской области",
    "ОВМ ОМВД России по Щёкинскому району",
    "МП УФМС России в г. Сочи",
]

# Пары именительный-родительный.
COUNTRIES = [
    ("РФ", "РФ"),
    ("Российская Федерация", "Российской Федерации"),
    ("Россия", "России"),
    ("Республика Беларусь", "Республики Беларусь"),
    ("Казахстан", "Казахстана"),
    ("Узбекистан", "Узбекистана"),
    ("Армения", "Армении"),
    ("Кыргызстан", "Кыргызстана"),
]

MONTHS_GENITIVE = [
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
]

DAYS_GENITIVE = [
    "первого",
    "второго",
    "третьего",
    "четвёртого",
    "пятого",
    "шестого",
    "седьмого",
    "восьмого",
    "девятого",
    "десятого",
    "одиннадцатого",
    "двенадцатого",
    "тринадцатого",
    "четырнадцатого",
    "пятнадцатого",
    "шестнадцатого",
    "семнадцатого",
    "восемнадцатого",
    "девятнадцатого",
    "двадцатого",
    "двадцать первого",
    "двадцать второго",
    "двадцать третьего",
    "двадцать четвёртого",
    "двадцать пятого",
    "двадцать шестого",
    "двадцать седьмого",
    "двадцать восьмого",
]

TRANSLIT = str.maketrans(
    {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "д": "d",
        "е": "e",
        "ё": "e",
        "ж": "zh",
        "з": "z",
        "и": "i",
        "й": "y",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "kh",
        "ц": "ts",
        "ч": "ch",
        "ш": "sh",
        "щ": "shch",
        "ъ": "",
        "ы": "y",
        "ь": "",
        "э": "e",
        "ю": "yu",
        "я": "ya",
    }
)


def _occurrence(text: str, value: str, start: int) -> int:
    count = 0
    pos = 0
    while True:
        idx = text.find(value, pos)
        if idx == -1:
            break
        count += 1
        if idx == start:
            break
        pos = idx + 1
    return count


class Builder:
    """Собирает текст из кусков и помнит точные позиции."""

    def __init__(self) -> None:
        self._chunks: list = []

    def t(self, text: str) -> Builder:
        self._chunks.append(text)
        return self

    def v(self, value: str, ptype: str) -> Builder:
        self._chunks.append((value, ptype))
        return self

    def trap(self, value: str) -> Builder:
        self._chunks.append((value, "TRAP"))
        return self

    def extend(self, items: list) -> Builder:
        for item in items:
            if isinstance(item, str):
                self.t(item)
            elif isinstance(item, tuple):
                if item[1] == "TRAP":
                    self.trap(item[0])
                else:
                    self.v(item[0], item[1])
        return self

    def build(self, ident: str, category: str, variant: str, case: str | None = None) -> dict:
        text = "".join(c[0] if isinstance(c, tuple) else c for c in self._chunks)
        pii: list[tuple[int, int, str]] = []
        traps: list[tuple[int, int]] = []
        pos = 0
        for chunk in self._chunks:
            if isinstance(chunk, str):
                pos += len(chunk)
            else:
                value, ptype = chunk
                start = pos
                end = pos + len(value)
                if ptype == "TRAP":
                    traps.append((start, end))
                else:
                    pii.append((start, end, ptype))
                pos = end
        suffix = ""
        if case == "upper":
            text = text.upper()
            suffix = "+upper"
        elif case == "lower":
            text = text.lower()
            suffix = "+lower"
        pii_out = []
        for start, end, ptype in pii:
            value = text[start:end]
            pii_out.append(
                {"value": value, "type": ptype, "occurrence": _occurrence(text, value, start)}
            )
        not_pii = [text[s:e] for s, e in traps]
        return {
            "id": ident,
            "category": category,
            "variant": variant + suffix,
            "text": text,
            "pii": pii_out,
            "not_pii": not_pii,
        }


def _gender_matches(tag, female: bool | None) -> bool:
    if female is True:
        return "femn" in tag
    if female is False:
        return "masc" in tag
    return True


_CASE_MAP = {
    "nominative": "nomn",
    "genitive": "gent",
    "dative": "datv",
    "accusative": "accs",
    "instrumental": "ablt",
    "prepositional": "loct",
}


def _inflect_part(part: str, case: str, marker: str, female: bool | None) -> str:
    parses = _MORPH.parse(part)
    candidates = [p for p in parses if marker in p.tag and _gender_matches(p.tag, female)]
    if not candidates:
        candidates = [p for p in parses if marker in p.tag]
    if not candidates:
        candidates = parses
    if not candidates:
        return part.lower()
    p = candidates[0]
    grammeme = _CASE_MAP.get(case, case)
    inflected = p.inflect({grammeme, "sing"})
    if inflected is None:
        inflected = p.inflect({grammeme})
    if inflected is None:
        return part.lower()
    result = inflected.word
    if part[0].isupper():
        result = result.capitalize()
    return result


def inflect(word: str, case: str, marker: str, female: bool | None = None) -> str:
    """Склоняет часть ФИО или топоним."""
    if case == "nominative":
        return word
    parts = word.split("-")
    return "-".join(_inflect_part(p, case, marker, female) for p in parts)


def luhn_complete(prefix: str, length: int, rng: random.Random) -> str:
    digits = list(prefix)
    while len(digits) < length - 1:
        digits.append(str(rng.randint(0, 9)))
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2 == 0:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    check = (10 - total % 10) % 10
    digits.append(str(check))
    return "".join(digits)


def inn12(rng: random.Random) -> str:
    digits = [str(rng.randint(0, 9)) for _ in range(10)]
    w11 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
    w12 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
    d11 = (sum(int(d) * w for d, w in zip(digits, w11, strict=True)) % 11) % 10
    d12 = (sum(int(d) * w for d, w in zip([*digits, str(d11)], w12, strict=True)) % 11) % 10
    return "".join(digits) + str(d11) + str(d12)


def inn10(rng: random.Random) -> str:
    digits = [str(rng.randint(0, 9)) for _ in range(9)]
    w = [2, 4, 10, 3, 5, 9, 4, 6, 8]
    d10 = (sum(int(d) * w for d, w in zip(digits, w, strict=True)) % 11) % 10
    return "".join(digits) + str(d10)


def snils(rng: random.Random) -> str:
    digits = [rng.randint(0, 9) for _ in range(9)]
    total = sum(d * (9 - i) for i, d in enumerate(digits))
    total %= 101
    if total == 100:
        total = 0
    return (
        f"{digits[0]}{digits[1]}{digits[2]}-{digits[3]}{digits[4]}{digits[5]}-"
        f"{digits[6]}{digits[7]}{digits[8]} {total:02d}"
    )


def person(rng: random.Random) -> dict:
    female = rng.random() < 0.5
    if female:
        return {
            "sur": rng.choice(FEMALE_SURNAMES),
            "first": rng.choice(FEMALE_NAMES),
            "patr": rng.choice(FEMALE_PATRONYMICS),
            "female": True,
        }
    return {
        "sur": rng.choice(MALE_SURNAMES),
        "first": rng.choice(MALE_NAMES),
        "patr": rng.choice(MALE_PATRONYMICS),
        "female": False,
    }


def fio_forms(p: dict, case: str = "nominative") -> dict:
    sur = inflect(p["sur"], case, "Surn", p["female"])
    first = inflect(p["first"], case, "Name", p["female"])
    patr = inflect(p["patr"], case, "Patr", p["female"])
    i_init = p["first"][0]
    o_init = p["patr"][0]
    return {
        "fio": f"{sur} {first} {patr}",
        "iof": f"{first} {patr} {sur}",
        "if": f"{first} {sur}",
        "fi": f"{sur} {first}",
        "f_io": f"{sur} {i_init}.{o_init}.",
        "io_f": f"{i_init}. {o_init}. {sur}",
        "f_io_space": f"{sur} {i_init}. {o_init}.",
    }


def date_parts(rng: random.Random, lo: int, hi: int) -> tuple[int, int, int]:
    return rng.randint(1, 28), rng.randint(1, 12), rng.randint(lo, hi)


def date_formats(d: int, m: int, y: int) -> dict:
    mm = f"{m:02d}"
    dd = f"{d:02d}"
    yy = f"{y % 100:02d}"
    yyyy = f"{y}"
    return {
        "dd.mm.yyyy": f"{dd}.{mm}.{yyyy}",
        "mm.dd.yyyy": f"{mm}.{max(d, 13):02d}.{yyyy}",
        "yyyy.dd.mm": f"{yyyy}.{max(d, 13):02d}.{mm}",
        "yyyy-mm-dd": f"{yyyy}-{mm}-{dd}",
        "dd/mm/yyyy": f"{dd}/{mm}/{yyyy}",
        "dd-mm-yyyy": f"{dd}-{mm}-{yyyy}",
        "dd.mm.yy": f"{dd}.{mm}.{yy}",
        "text": f"{d} {MONTHS_GENITIVE[m - 1]} {yyyy}",
        "text_word_day": f"{DAYS_GENITIVE[d - 1]} {MONTHS_GENITIVE[m - 1]} {yyyy}",
        "d.m.yyyy": f"{d}.{m}.{yyyy}",
    }


def passport_forms(rng: random.Random) -> list[tuple[str, list]]:
    region = f"{rng.randint(1, 99):02d}"
    year = f"{rng.randint(0, 25):02d}"
    series4 = region + year
    series2 = f"{region} {year}"
    number = f"{rng.randint(100000, 999999)}"
    return [
        ("s4_n", [(f"{series4} {number}", "PASSPORT")]),
        ("s2_s2_n", [(f"{series2} {number}", "PASSPORT")]),
        ("digits10", [(series4 + number, "PASSPORT")]),
        ("seria_nomer", ["серия ", (series4, "PASSPORT"), " номер ", (number, "PASSPORT")]),
        ("seria_no", ["серия ", (series2, "PASSPORT"), " № ", (number, "PASSPORT")]),
        ("serii_n", ["серии ", (series4, "PASSPORT"), ", номер ", (number, "PASSPORT")]),
        ("s_no_n", ["серия №", (series4, "PASSPORT"), (number, "PASSPORT")]),
    ]


def phone_forms(rng: random.Random) -> list[str]:
    code = rng.choice(["916", "903", "925", "985", "999", "977", "921", "912", "951", "495", "812"])
    a = f"{rng.randint(100, 999)}"
    b = f"{rng.randint(10, 99)}"
    c = f"{rng.randint(10, 99)}"
    return [
        f"+7 ({code}) {a}-{b}-{c}",
        f"+7{code}{a}{b}{c}",
        f"8 {code} {a} {b} {c}",
        f"8({code}){a}{b}{c}",
        f"7-{code}-{a}-{b}-{c}",
        f"+7 {code} {a}-{b}-{c}",
        f"8-{code}-{a}-{b}-{c}",
        f"+7.{code}.{a}.{b}.{c}",
        f"8{code}{a}{b}{c}",
        f"8 ({code}) {a} {b} {c}",
    ]


def card_forms(rng: random.Random) -> list[str]:
    prefix = rng.choice(["4", "51", "53", "55", "2200", "2202", "2204"])
    card16 = luhn_complete(prefix, 16, rng)
    card19 = luhn_complete("2200", 19, rng)
    return [
        f"{card16[0:4]} {card16[4:8]} {card16[8:12]} {card16[12:16]}",
        f"{card16[0:4]}-{card16[4:8]}-{card16[8:12]}-{card16[12:16]}",
        card16,
        f"{card19[0:4]} {card19[4:8]} {card19[8:12]} {card19[12:16]} {card19[16:19]}",
    ]


def address(rng: random.Random) -> list[tuple[str, list]]:
    index = str(rng.randint(101000, 692999))
    city = rng.choice(CITIES)
    street = rng.choice(STREETS)
    street_type = rng.choice(STREET_TYPES)
    house = str(rng.randint(1, 150))
    corp = str(rng.randint(1, 5))
    apt = str(rng.randint(1, 400))
    region = rng.choice(REGIONS)
    district = rng.choice(DISTRICTS)
    village = rng.choice(VILLAGES)
    return [
        (
            "full_post",
            [
                (index, "ADDRESS"),
                ", г. ",
                (city, "ADDRESS"),
                SEP_STREET,
                (street, "ADDRESS"),
                SEP_HOUSE,
                (house, "ADDRESS"),
                SEP_FLAT,
                (apt, "ADDRESS"),
            ],
        ),
        (
            "city_street_bld",
            [
                "г. ",
                (city, "ADDRESS"),
                ", ",
                street_type,
                " ",
                (street, "ADDRESS"),
                SEP_HOUSE,
                (house, "ADDRESS"),
                ", корп. ",
                (corp, "ADDRESS"),
                SEP_FLAT,
                (apt, "ADDRESS"),
            ],
        ),
        (
            "region_village",
            [
                (region, "ADDRESS"),
                " обл., ",
                (district, "ADDRESS"),
                " р-н, д. ",
                (village, "ADDRESS"),
                SEP_STREET,
                (street, "ADDRESS"),
                SEP_HOUSE,
                (house, "ADDRESS"),
            ],
        ),
        (
            "compact_dash",
            [
                (city, "ADDRESS"),
                SEP_STREET,
                (street, "ADDRESS"),
                SEP_HOUSE,
                (house, "ADDRESS"),
                "-",
                (apt, "ADDRESS"),
            ],
        ),
        (
            "words_full",
            [
                "город ",
                (city, "ADDRESS"),
                ", улица ",
                (street, "ADDRESS"),
                ", дом ",
                (house, "ADDRESS"),
                ", квартира ",
                (apt, "ADDRESS"),
            ],
        ),
        (
            "country_first",
            [
                "Россия, ",
                (index, "ADDRESS"),
                ", г. ",
                (city, "ADDRESS"),
                ", ",
                street_type,
                " ",
                (street, "ADDRESS"),
                SEP_HOUSE,
                (house, "ADDRESS"),
                SEP_FLAT,
                (apt, "ADDRESS"),
            ],
        ),
    ]
