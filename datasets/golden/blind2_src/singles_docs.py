"""Одиночные примеры: паспорт РФ, кем выдан, код подразделения, дата выдачи, ВУ, иные документы."""

from __future__ import annotations

from common import NBSP, Gen, P, fmt_date, make


def passport(g: Gen) -> list[dict]:
    c = "PASSPORT"
    out = []
    s, n = g.passport()
    out.append(make(c, "bare", P(f"{s} {n}", c)))
    s, n = g.passport()
    out.append(make(c, "seria_nomer", "паспорт серия ", P(s, c), " номер ", P(n, c)))
    s, n = g.passport()
    out.append(make(c, "split_series", "паспорт ", P(f"{s[:2]} {s[2:]} {n}", c)))
    s, n = g.passport()
    out.append(make(c, "colon_no", "серия: ", P(s, c), ", №: ", P(n, c)))
    s, n = g.passport()
    out.append(make(c, "rf_no", "паспорт РФ № ", P(f"{s} {n}", c)))
    s, n = g.passport()
    out.append(make(c, "hyphen", "Паспорт: ", P(f"{s}-{n}", c)))
    s, n = g.passport()
    out.append(make(c, "glued", "пасп. ", P(f"{s}{n}", c)))
    s, n = g.passport()
    out.append(make(c, "split_seria_nomer", "серия ", P(f"{s[:2]} {s[2:]}", c), " номер ", P(n, c)))
    s, n = g.passport()
    out.append(make(c, "no_sign", "паспорт ", P(s, c), " № ", P(n, c), " предъявлен"))
    s, n = g.passport()
    out.append(make(c, "nbsp", "паспортные данные: ", P(f"{s}{NBSP}{n}", c)))
    s, n = g.passport()
    out.append(make(c, "upper_genitive", "ПАСПОРТ СЕРИИ ", P(s, c), " НОМЕР ", P(n, c)))
    s, n = g.passport()
    out.append(make(c, "rf_split", "паспорт гражданина РФ ", P(f"{s[:2]} {s[2:]}", c), " №", P(n, c)))
    s, n = g.passport()
    out.append(make(c, "latin", "passport ", P(f"{s} {n}", c), " (Russian Federation)"))
    s, n = g.passport()
    out.append(make(c, "slash", "серия/номер: ", P(f"{s}/{n}", c)))
    s, n = g.passport()
    out.append(make(c, "sentence", "Клиент предъявил паспорт ", P(f"{s} {n}", c), ", данные сверены."))
    return out


def passport_authority(g: Gen) -> list[dict]:
    c = "PASSPORT_AUTHORITY"
    return [
        make(c, "gu_mvd", "Выдан: ", P("ГУ МВД России по г. Москве", c)),
        make(c, "ufms_long", "кем выдан: ",
             P("Отделом УФМС России по Республике Татарстан в Вахитовском районе г. Казани", c)),
        make(c, "ovd", "паспорт выдан ", P("ОВД района Марьино г. Москвы", c)),
        make(c, "tp_ufms", "Паспорт выдан ",
             P("ТП № 2 ОУФМС России по Санкт-Петербургу и Ленинградской обл. в Приморском р-не", c)),
        make(c, "ovm", "выдан ", P("отделением по вопросам миграции ОМВД России по Центральному району г. Новосибирска", c)),
        make(c, "upper", "ВЫДАН ", P("МВД ПО РЕСПУБЛИКЕ БАШКОРТОСТАН", c)),
        make(c, "uvd_abbr", "выд. ", P("УВД Ленинского р-на г. Самары", c)),
        make(c, "rovd", "паспорт выдан ", P("2 отделом милиции Кировского РУВД г. Екатеринбурга", c), " в 2004 г."),
        make(c, "umvd_oblast", "Орган, выдавший документ: ", P("УМВД России по Калужской области", c)),
    ]


def department_code(g: Gen) -> list[dict]:
    c = "DEPARTMENT_CODE"
    out = []
    for variant, pre, fmt, post in (
        ("label", "код подразделения ", "{a}-{b}", ""),
        ("abbr", "к/п: ", "{a}-{b}", ""),
        ("space", "код подр. ", "{a} {b}", ""),
        ("no_space", "Код подразделения:", "{a}-{b}", ""),
        ("en_dash", "подразделение ", "{a}–{b}", ""),
        ("kp", "КП ", "{a}-{b}", ", дата выдачи не указана"),
        ("sentence", "В паспорте указан код подразделения ", "{a}-{b}", "."),
        ("upper", "КОД ПОДРАЗДЕЛЕНИЯ ", "{a}-{b}", ""),
        ("glued", "код подразд. ", "{a}{b}", ""),
    ):
        a, b = g.dept().split("-")
        out.append(make(c, variant, pre, P(fmt.format(a=a, b=b), c), post))
    return out


def passport_date(g: Gen) -> list[dict]:
    c = "PASSPORT_DATE"
    out = []
    for variant, pre, style, post in (
        ("label", "дата выдачи ", "dot", ""),
        ("vydan", "паспорт выдан ", "dot", ""),
        ("words", "Дата выдачи паспорта: ", "words", " г."),
        ("iso", "когда выдан: ", "iso", ""),
        ("slash", "выдан ", "slash", ", срок не истёк"),
        ("english", "date of issue ", "dot", ""),
        ("abbr", "д/в ", "dot", ""),
        ("goda", "паспорт получен ", "dot", " года"),
    ):
        d, m, y = g.date(2005, 2025)
        out.append(make(c, variant, pre, P(fmt_date(d, m, y, style), c), post))
    return out


def driver_license(g: Gen) -> list[dict]:
    c = "DRIVER_LICENSE"
    out = []
    for variant, pre, fmt, post in (
        ("vu", "ВУ ", "{r} {s} {n}", ""),
        ("full", "водительское удостоверение ", "{r}{s} {n}", ""),
        ("prava", "права № ", "{r}{s} {n}", ", категория B"),
        ("glued", "номер ВУ: ", "{r}{s}{n}", ""),
        ("english", "driver license ", "{r} {s} {n}", ""),
        ("upper", "ВОДИТЕЛЬСКОЕ УДОСТОВЕРЕНИЕ ", "{r}{s} {n}", ""),
        ("udost_voditelya", "удостоверение водителя ", "{r} {s} {n}", " действительно до 2031 г."),
        ("nbsp", "в/у ", "{r}{NB}{s}{NB}{n}", ""),
    ):
        r, s, n = g.pick(("77", "50", "99", "78", "16", "66")), g.num(2), g.num(6)
        out.append(make(c, variant, pre, P(fmt.format(r=r, s=s, n=n, NB=NBSP), c), post))
    out.append(make(c, "old_letters", "в/у ", P("77 АВ 123984", c), " (старого образца)"))
    out.append(make(c, "seria_no", "водит. удост. серии ", P("66 23", c), " № ", P("456789", c)))
    return out


def foreign_document(g: Gen) -> list[dict]:
    c = "FOREIGN_DOCUMENT"
    return [
        make(c, "zagran", "загранпаспорт ", P(f"75 {g.num(7)}", c)),
        make(c, "zagran_full", "заграничный паспорт № ", P(f"72{g.num(7)}", c), ", действителен до 2030 г."),
        make(c, "uzb_passport", "паспорт гражданина ", P("Узбекистана", "CITIZENSHIP"), " ", P(f"FA{g.num(7)}", c)),
        make(c, "vnzh_split", "ВНЖ ", P("82", c), " № ", P(g.num(7), c)),
        make(c, "vnzh_full", "вид на жительство серии ", P("83", c), " номер ", P(f"0{g.num(6)}", c)),
        make(c, "rvp", "разрешение на временное проживание № ", P(g.num(6, False), c), " действует"),
        make(c, "military", "военный билет ", P(f"АН {g.num(7)}", c)),
        make(c, "birth_cert", "свидетельство о рождении ", P("IV-МЮ", c), " № ", P(g.num(6), c)),
        make(c, "kz_id", "удостоверение личности РК № ", P(f"0{g.num(8)}", c)),
        make(c, "seaman", "паспорт моряка ", P(f"МК {g.num(7)}", c)),
        make(c, "chinese", "Passport No. ", P(f"E{g.num(8)}", c), " (People's Republic of China)"),
        make(c, "german", "Reisepass Nr. ", P("C4J9R2K71", c)),
        make(c, "refugee", "удостоверение беженца ", P(f"ББ {g.num(6)}", c)),
        make(c, "officer", "удостоверение личности офицера ", P(f"ГО {g.num(6)}", c)),
        make(c, "foreign_passport_kg", "паспорт гражданина ", P("Кыргызстана", "CITIZENSHIP"), " ", P(f"AC{g.num(7)}", c)),
        make(c, "tj_passport", "паспорт гражданина Республики ", P("Таджикистан", "CITIZENSHIP"), " ", P(f"4{g.num(8)}", c), " предъявлен"),
    ]
