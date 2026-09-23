"""Комплексные тексты, часть B: JSON, логи, CSV, таблицы, XML, промпты к LLM, смешанные языки."""

from __future__ import annotations

from common import Gen, N, P, fmt_date, make
from complex_a import ADDRS, AUTHORITIES, CITIES
from names import PEOPLE, email_of, full, holder, initials

C = "COMPLEX"
DOMAINS = ("mail.ru", "gmail.com", "yandex.ru", "bk.ru", "outlook.com", "inbox.ru")


def _two(g: Gen):
    p1 = g.pick(PEOPLE)
    p2 = g.pick(PEOPLE)
    while p2 == p1:
        p2 = g.pick(PEOPLE)
    return p1, p2


def json_record(g: Gen, v: int) -> dict:
    p = g.pick(PEOPLE)
    return make(
        C, "json",
        '{"request_id": "', N("a7f3-11c9-0042"), '", "client": {"full_name": "', P(full(p), "PERSON"),
        '", "birth_date": "', P(fmt_date(*g.date(), "iso"), "BIRTH_DATE"),
        '", "passport": "', P("".join(g.passport()), "PASSPORT"),
        '", "phone": "', P(g.phone("plus"), "PHONE"),
        '", "email": "', P(email_of(p, g.pick(DOMAINS), v), "EMAIL"),
        '"}, "amount": 150000, "created_at": "', N("2026-09-21T10:15:00Z"), '"}',
    )


def log_line(g: Gen, v: int) -> dict:
    p = g.pick(PEOPLE)
    return make(
        C, "log",
        N("2026-09-21 12:03:44,118"), " INFO  [payment-svc] user_id=48213 fio='", P(full(p), "PERSON"),
        "' phone=", P(g.phone("plus")[1:], "PHONE"), " card=", P(g.card(), "BANK_CARD"),
        " status=DECLINED reason=", N("ERR_LIMIT_05"),
    )


def csv_rows(g: Gen, v: int) -> dict:
    p1, p2 = _two(g)
    return make(
        C, "csv",
        "fio;birth_date;phone;snils\n",
        P(full(p1), "PERSON"), ";", P(fmt_date(*g.date()), "BIRTH_DATE"), ";", P(g.phone("plain"), "PHONE"), ";",
        P(g.snils_fmt("std"), "SNILS"), "\n",
        P(full(p2), "PERSON"), ";", P(fmt_date(*g.date()), "BIRTH_DATE"), ";", P(g.phone("std"), "PHONE"), ";",
        P(g.snils_fmt("plain"), "SNILS"),
    )


def llm_prompt(g: Gen, v: int) -> dict:
    p = g.pick(PEOPLE)
    return make(
        C, "llm_prompt",
        "Ты - ассистент банка. Составь вежливое письмо клиенту ", P(full(p), "PERSON"), " (", P(email_of(p, g.pick(DOMAINS), v), "EMAIL"),
        ") о просрочке по договору ", N("№ 0012-КР/2026"), " от ", N("05.02.2026"),
        ". Упомяни, что платёж можно внести на карту ", P(g.card_fmt(" "), "BANK_CARD"),
        " или по телефону ", N("8 800 200-00-00"), ". Не используй канцелярит.",
    )


def md_table(g: Gen, v: int) -> dict:
    p1, p2 = _two(g)
    return make(
        C, "md_table",
        "| ФИО | Телефон | Email |\n|---|---|---|\n| ", P(full(p1), "PERSON"), " | ", P(g.phone("eight"), "PHONE"),
        " | ", P(email_of(p1, g.pick(DOMAINS), v), "EMAIL"), " |\n| ", P(initials(p2), "PERSON"), " | ",
        P(g.phone("dashes"), "PHONE"), " | ", P(email_of(p2, g.pick(DOMAINS), v + 1), "EMAIL"), " |",
    )


def xml_record(g: Gen, v: int) -> dict:
    p = g.pick(PEOPLE)
    return make(
        C, "xml",
        "<client><name>", P(full(p), "PERSON"), "</name><inn>", P(g.inn12(), "INN"), "</inn><snils>",
        P(g.snils_fmt("dash"), "SNILS"), "</snils><branch>", N("0341"), "</branch></client>",
    )


def email_header(g: Gen, v: int) -> dict:
    p = g.pick(PEOPLE)
    return make(
        C, "email_header",
        "From: ", P(full(p, "if"), "PERSON"), " <", P(email_of(p, g.pick(DOMAINS), v), "EMAIL"), ">\nTo: ",
        N("support@alfabank.ru"), "\nDate: ", N("Mon, 21 Sep 2026 09:12:03 +0300"),
        "\nSubject: не приходит СМС\n\nДобрый день, номер ", P(g.phone("eight"), "PHONE"), " привязан к карте, но коды не приходят.",
    )


def mixed_en(g: Gen, v: int) -> dict:
    p = g.pick(PEOPLE)
    s, n = g.passport()
    return make(
        C, "mixed_en",
        "Client: ", P(holder(p).title(), "PERSON"), ", DOB ", P(fmt_date(*g.date(), "iso"), "BIRTH_DATE"),
        ", phone ", P(g.phone("std"), "PHONE"), ", RF passport ", P(f"{s} {n}", "PASSPORT"),
        ", place of birth ", P(g.pick(("Moscow", "Tashkent", "Kazan", "Bishkek")), "BIRTH_PLACE"),
        ". KYC status: pending since ", N("2026-09-01"), ".",
    )


def beneficiary(g: Gen, v: int) -> dict:
    p = g.pick(PEOPLE)
    return make(
        C, "beneficiary",
        "Выгодоприобретатель по вкладу: ", P(full(p), "PERSON"), ", ИНН ", P(g.inn12(), "INN"), ", СНИЛС ",
        P(g.snils_fmt("std"), "SNILS"), ", место рождения - г. ", P(g.pick(CITIES), "BIRTH_PLACE"),
        ". Вклад «", N("Альфа-Вклад"), "» открыт ", N("10.06.2026"), ".",
    )


def car_loan(g: Gen, v: int) -> dict:
    p = g.pick(PEOPLE)
    r = g.pick(("77", "50", "99"))
    return make(
        C, "car_loan",
        "Автокредит. Заёмщик ", P(full(p), "PERSON"), ", водительское удостоверение ",
        P(f"{r}{g.num(2)} {g.num(6)}", "DRIVER_LICENSE"), ", стаж с 2012 г. Автомобиль ", N("Kia Rio"),
        ", VIN ", N("Z94CB41AAER123456"), ". Контакт: ", P(g.phone("std"), "PHONE"), ".",
    )


def name_change(g: Gen, v: int) -> dict:
    p = g.pick([x for x in PEOPLE if x[3] == "f"])
    sur, name, patr, _ = p
    old = g.pick(("Иванова", "Ким", "Абрамян", "Петренко", "Хасанова"))
    return make(
        C, "name_change",
        "Клиентка сменила фамилию. Прежние данные: ", P(f"{old} {name} {patr}".strip(), "PERSON"),
        ". Новые: ", P(full(p), "PERSON"), ", новый паспорт ", P(" ".join(g.passport()), "PASSPORT"),
        ", выдан ", P(fmt_date(*g.date(2020, 2025)), "PASSPORT_DATE"), ", код ", P(g.dept(), "DEPARTMENT_CODE"), ".",
    )


def yaml_record(g: Gen, v: int) -> dict:
    p = g.pick(PEOPLE)
    return make(
        C, "yaml",
        "client:\n  name: ", P(full(p), "PERSON"), "\n  cardholder: ", P(holder(p), "CARDHOLDER"),
        "\n  card: ", P(g.card(), "BANK_CARD"), "\n  cvv: ", P(g.num(3), "CVV"), "\n  pin: ", P(g.num(4), "PIN"),
        "\n  limit: ", N("300000"),
    )


def helpdesk(g: Gen, v: int) -> dict:
    p = g.pick(PEOPLE)
    return make(
        C, "helpdesk",
        "Тикет ", N("SD-2026-18842"), ". Сотрудник ", P(initials(p, before=True), "PERSON"),
        " сообщает: клиент не может войти в приложение. Звонок поступил на ", N("8 800 100-00-00"),
        " с номера ", P(g.phone("seven"), "PHONE"), ". Адрес клиента: ", *g.pick(ADDRS), ".",
    )


def child_account(g: Gen, v: int) -> dict:
    parent = g.pick([x for x in PEOPLE if x[2]])
    child_name = g.pick(("Тимур", "Давид", "Марк") if parent[3] == "m" else ("Милана", "Алиса", "Амина"))
    return make(
        C, "child_account",
        "Законный представитель ", P(full(parent), "PERSON"), " открывает детскую карту на имя ",
        P(f"{parent[0]} {child_name}", "PERSON"), ", ", P(fmt_date(*g.date(2012, 2019)), "BIRTH_DATE"),
        " г.р., свидетельство о рождении ", P(g.pick(("II-МЮ", "III-АГ", "I-ВЛ")), "FOREIGN_DOCUMENT"),
        " № ", P(g.num(6), "FOREIGN_DOCUMENT"), ".",
    )


def zagran_travel(g: Gen, v: int) -> dict:
    p = g.pick(PEOPLE)
    return make(
        C, "zagran_travel",
        "Для страховки путешественника: ", P(holder(p), "PERSON"), ", загранпаспорт ",
        P(f"{g.pick(('75', '76', '77'))} {g.num(7)}", "FOREIGN_DOCUMENT"), ", дата рождения ",
        P(fmt_date(*g.date()), "BIRTH_DATE"), ", гражданство ", P("RUS", "CITIZENSHIP"),
        ". Поездка с ", N("10.10.2026"), " по ", N("24.10.2026"), ".",
    )


def authority_letter(g: Gen, v: int) -> dict:
    p = g.pick(PEOPLE)
    s, n = g.passport()
    return make(
        C, "passport_block",
        "Паспорт гражданина РФ: ", P(f"{s} {n}", "PASSPORT"), ", выдан ", P(g.pick(AUTHORITIES), "PASSPORT_AUTHORITY"),
        ", дата выдачи ", P(fmt_date(*g.date(2008, 2024), "words"), "PASSPORT_DATE"), " г., к/п ",
        P(g.dept(), "DEPARTMENT_CODE"), ". Владелец: ", P(full(p), "PERSON"), ".",
    )


BUILDERS_B = (json_record, log_line, csv_rows, llm_prompt, md_table, xml_record, email_header, mixed_en,
              beneficiary, car_loan, name_change, yaml_record, helpdesk, child_account, zagran_travel,
              authority_letter)
