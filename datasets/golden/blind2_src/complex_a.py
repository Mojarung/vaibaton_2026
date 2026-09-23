"""Комплексные тексты, часть A: анкеты, диалоги, письма, SMS, OCR."""

from __future__ import annotations

from common import Gen, N, P, fmt_date, make
from names import PEOPLE, full, holder, initials

C = "COMPLEX"


def A(v: str) -> P:
    return P(v, "ADDRESS")


ADDRS = (
    ("г. ", A("Москва"), ", ул. ", A("Профсоюзная"), ", д. ", A("56"), ", кв. ", A("7")),
    (A("196240"), ", г. ", A("Санкт-Петербург"), ", ", A("Пулковское"), " ш., д. ", A("9"), ", корп. ", A("3"),
     ", кв. ", A("41")),
    (A("Московская"), " обл., г. ", A("Балашиха"), ", мкр. ", A("Железнодорожный"), ", ул. ", A("Маяковского"),
     ", д. ", A("14"), ", кв. ", A("88")),
    ("г. ", A("Казань"), ", пр-т ", A("Победы"), ", д. ", A("100"), ", кв. ", A("256")),
    (A("Краснодарский"), " край, ст-ца ", A("Динская"), ", ул. ", A("Красная"), ", ", A("112")),
    ("г. ", A("Новосибирск"), ", ул. ", A("Кирова"), ", ", A("27"), "-", A("15")),
    ("г. ", A("Зеленоград"), ", корп. ", A("1106"), ", кв. ", A("54")),
    ("Республика ", A("Дагестан"), ", г. ", A("Махачкала"), ", ул. ", A("Гагарина"), ", д. ", A("37"), ", кв. ", A("5")),
    (A("Тверская"), " обл., д. ", A("Горки"), ", ", A("12")),
    ("г. ", A("Екатеринбург"), ", ул. ", A("Малышева"), ", д. ", A("36"), ", кв. ", A("12")),
)

AUTHORITIES = (
    "ГУ МВД России по г. Москве",
    "ОУФМС России по Санкт-Петербургу и Ленинградской обл. в Кировском р-не",
    "МВД по Республике Татарстан",
    "ГУ МВД России по Новосибирской области",
    "отделом УФМС России по Краснодарскому краю в Динском районе",
)
CITIES = ("Москва", "Ташкент", "Бишкек", "Ереван", "Алматы", "Владивосток", "Ханой", "Казань", "Тбилиси", "Душанбе")


def _person(g: Gen):
    return g.pick(PEOPLE)


def _bd(g: Gen, style: str = "dot") -> str:
    return fmt_date(*g.date(), style)


def anketa(g: Gen, v: int) -> dict:
    p, (s, n), addr = _person(g), g.passport(), g.pick(ADDRS)
    return make(
        C, "anketa",
        "АНКЕТА КЛИЕНТА\nФамилия, имя, отчество: ", P(full(p), "PERSON"),
        "\nДата рождения: ", P(_bd(g), "BIRTH_DATE"),
        "\nМесто рождения: г. ", P(g.pick(CITIES), "BIRTH_PLACE"),
        "\nГражданство: ", P("РФ", "CITIZENSHIP"),
        "\nПаспорт: серия ", P(s, "PASSPORT"), " № ", P(n, "PASSPORT"),
        ", выдан ", P(g.pick(AUTHORITIES), "PASSPORT_AUTHORITY"), " ", P(fmt_date(*g.date(2010, 2024)), "PASSPORT_DATE"),
        ", код подразделения ", P(g.dept(), "DEPARTMENT_CODE"),
        "\nАдрес регистрации: ", *addr,
        "\nТелефон: ", P(g.phone("std"), "PHONE"),
        "\nИНН: ", P(g.inn12(), "INN"), "   СНИЛС: ", P(g.snils_fmt("std"), "SNILS"),
        "\nДата заполнения: ", N("21.09.2026"),
    )


def operator_dialog(g: Gen, v: int) -> dict:
    p = _person(g)
    return make(
        C, "operator_dialog",
        "Оператор: Альфа-Банк, здравствуйте. Как к вам обращаться?\nКлиент: ", P(full(p, "if"), "PERSON"),
        ".\nОператор: Назовите, пожалуйста, дату рождения.\nКлиент: ", P(_bd(g, "words"), "BIRTH_DATE"),
        ".\nОператор: И последние цифры паспорта... хорошо, полностью, пожалуйста.\nКлиент: ",
        P(" ".join(g.passport()), "PASSPORT"),
        ".\nОператор: Спасибо. Если связь прервётся, перезвоните на ", N("8 800 200-00-00"), ".",
    )


def email_letter(g: Gen, v: int) -> dict:
    p = _person(g)
    return make(
        C, "email_letter",
        "Тема: блокировка карты\n\nЗдравствуйте!\nМеня зовут ", P(full(p), "PERSON"),
        ". Вчера у меня пропала карта ", P(g.card_fmt(" "), "BANK_CARD"),
        ", прошу её заблокировать и перевыпустить. Новую карту доставьте, пожалуйста, по адресу: ",
        *g.pick(ADDRS), ".\nОбращение № ", N("CRM-771245"), " от ", N("20.09.2026"), " так и не решено.\n\nС уважением,\n",
        P(initials(p), "PERSON"), "\nтел. ", P(g.phone("eight"), "PHONE"),
    )


def sms(g: Gen, v: int) -> dict:
    p = _person(g)
    return make(
        C, "sms",
        "скинь 1500 на карту ", P(g.card(), "BANK_CARD"), " это ", P(full(p, "if"), "PERSON"),
        ", новая моя. пин кстати ", P(g.num(4), "PIN"), " если что снимешь сам",
    )


def ocr_passport(g: Gen, v: int) -> dict:
    p, (s, n) = _person(g), g.passport()
    sur, name, patr, sex = p
    return make(
        C, "ocr_passport",
        "РОССИЙСКАЯ ФЕДЕРАЦИЯ\nПаспорт выдан\n", P(g.pick(AUTHORITIES).upper(), "PASSPORT_AUTHORITY"),
        "\nДата выдачи ", P(fmt_date(*g.date(2008, 2024)), "PASSPORT_DATE"), "  Код подразделения ",
        P(g.dept(), "DEPARTMENT_CODE"),
        "\n", P(f"{s[:2]} {s[2:]}", "PASSPORT"), " ", P(n, "PASSPORT"),
        "\nФамилия ", P(sur.upper(), "PERSON"), "\nИмя ", P(name.upper(), "PERSON"),
        *(("\nОтчество ", P(patr.upper(), "PERSON")) if patr else ()),
        "\nПол ", "МУЖ." if sex == "m" else "ЖЕН.", " Дата рождения ", P(_bd(g), "BIRTH_DATE"),
        "\nМесто рождения ГОР. ", P(g.pick(CITIES).upper(), "BIRTH_PLACE"),
    )


def card_details(g: Gen, v: int) -> dict:
    p = _person(g)
    return make(
        C, "card_details",
        "Реквизиты для оплаты брони:\nНомер карты: ", P(g.card_fmt(" "), "BANK_CARD"),
        "\nСрок действия: 08/29\nCVV: ", P(g.num(3), "CVV"),
        "\nИмя держателя: ", P(holder(p), "CARDHOLDER"),
        "\nБронь № ", N("HT-55821"), " на ", N("03.11.2026"),
    )


def transfer(g: Gen, v: int) -> dict:
    p1, p2 = _person(g), _person(g)
    while p2 == p1:
        p2 = _person(g)
    return make(
        C, "transfer",
        "Перевод по номеру телефона ", P(g.phone("plus"), "PHONE"), ". Отправитель: ", P(initials(p1), "PERSON"),
        ". Получатель: ", P(full(p2, "fi"), "PERSON"), ", карта ", P(g.card_fmt(" "), "BANK_CARD"),
        ". Сумма: ", N("25 000,00"), " руб. Комиссия 0 руб.",
    )


def foreign_client(g: Gen, v: int) -> dict:
    p = _person(g)
    country, gen_country, prefix = g.pick((
        ("Узбекистан", "Республики Узбекистан", "FA"), ("Кыргызстан", "Кыргызской Республики", "AC"),
        ("Таджикистан", "Республики Таджикистан", "40"), ("Вьетнам", "СРВ", "C"),
    ))
    return make(
        C, "foreign_client",
        "Клиент: ", P(full(p), "PERSON"), ", гражданство - ", P(country, "CITIZENSHIP"),
        ". Паспорт иностранного гражданина ", P(f"{prefix}{g.num(7)}", "FOREIGN_DOCUMENT"),
        ", РВП № ", P(g.num(6), "FOREIGN_DOCUMENT"), ". Адрес пребывания: ", *g.pick(ADDRS),
        ". Документы проверены сотрудником ", N("ДО «Тверской»"), ".",
    )


def complaint(g: Gen, v: int) -> dict:
    p = _person(g)
    return make(
        C, "complaint",
        "Жалоба. Я, ", P(full(p), "PERSON"), ", ", P(_bd(g), "BIRTH_DATE"),
        " г.р., ", N("15.09.2026"), " обратился в отделение на ", N("ул. Каланчёвской, 27"),
        ", но мне отказали в выдаче наличных. Прошу разобраться. Ответ направить на ",
        P(f"{g.pick(('kseniya', 'olga', 'd.lebedeva', 'madina'))}{g.num(2)}@yandex.ru", "EMAIL"), ".",
    )


def chat_lower(g: Gen, v: int) -> dict:
    p = _person(g)
    return make(
        C, "chat_lower",
        "привет это ", P(full(p, "if").lower(), "PERSON"), " мой номер ", P(g.phone("plain"), "PHONE"),
        " пин ", P(g.num(4), "PIN"), " не подходит уже третий раз(( карта ", P(g.card(), "BANK_CARD"),
    )


def courier(g: Gen, v: int) -> dict:
    p = _person(g)
    return make(
        C, "courier",
        "Задание курьеру ", N("№ 55-0192"), ": доставить карту клиенту ", P(full(p), "PERSON"),
        " по адресу ", *g.pick(ADDRS), ". Звонить за час: ", P(g.phone("spaces"), "PHONE"),
        ". При вручении сверить паспорт ", P(" ".join(g.passport()), "PASSPORT"), ".",
    )


def doverennost(g: Gen, v: int) -> dict:
    p1, p2 = _person(g), _person(g)
    while p2 == p1:
        p2 = _person(g)
    s1, n1 = g.passport()
    s2, n2 = g.passport()
    return make(
        C, "doverennost",
        "ДОВЕРЕННОСТЬ\nг. Москва, ", N("первое октября две тысячи двадцать шестого года"),
        "\nЯ, ", P(full(p1), "PERSON"), ", паспорт ", P(s1, "PASSPORT"), " ", P(n1, "PASSPORT"),
        " выдан ", P(g.pick(AUTHORITIES), "PASSPORT_AUTHORITY"),
        ", доверяю ", P(full(p2), "PERSON"), ", паспорт серии ", P(s2, "PASSPORT"), " номер ", P(n2, "PASSPORT"),
        ", получать денежные средства с моего счёта в ", N("АО «Альфа-Банк»"), ".",
    )


def ocr_noisy(g: Gen, v: int) -> dict:
    p = _person(g)
    sur, name, patr, _ = p
    snils = g.snils_fmt("std")
    return make(
        C, "ocr_noisy",
        "СТРАХОВОЕ СВИДЕТЕЛЬСТВО\n| ", P(snils, "SNILS"), " |\nФ.И.О. ", P(sur, "PERSON"), "\n", P(f"{name} {patr}".strip(), "PERSON"),
        "\nДата и место рождения ", P(_bd(g), "BIRTH_DATE"), " гор. ", P(g.pick(CITIES), "BIRTH_PLACE"),
        "\nДата регистрации ", N("14.02.2003"),
    )


def voice_transcript(g: Gen, v: int) -> dict:
    p = _person(g)
    return make(
        C, "voice_transcript",
        "клиент да меня зовут ", P(full(p).lower(), "PERSON"), " дата рождения ",
        P(fmt_date(*g.date(), "words"), "BIRTH_DATE"), " паспорт ", P(" ".join(g.passport()), "PASSPORT"),
        " оператор спасибо ожидайте",
    )


BUILDERS_A = (anketa, operator_dialog, email_letter, sms, ocr_passport, card_details, transfer,
              foreign_client, complaint, chat_lower, courier, doverennost, ocr_noisy, voice_transcript)
