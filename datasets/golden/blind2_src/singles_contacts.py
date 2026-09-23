"""Одиночные примеры: адрес, email, телефон."""

from __future__ import annotations

from common import NBSP, Gen, P, make


def A(v: str) -> P:
    return P(v, "ADDRESS")


def address(g: Gen) -> list[dict]:
    c = "ADDRESS"
    return [
        make(c, "classic", "г. ", A("Москва"), ", ул. ", A("Тверская"), ", д. ", A("7"), ", кв. ", A("15")),
        make(c, "index_str", "Адрес регистрации: ", A("125009"), ", г. ", A("Москва"), ", ", A("Тверская"),
             " ул., д. ", A("12"), ", стр. ", A("2"), ", кв. ", A("45")),
        make(c, "no_trigger", "Живу на ", A("Ленинском"), " проспекте ", A("32"), ", квартира ", A("118"),
             ", код домофона не работает."),
        make(c, "oblast_mkr", A("Московская"), " обл., г. ", A("Химки"), ", мкр. ", A("Сходня"), ", ул. ",
             A("Мичурина"), ", д. ", A("5"), ", корп. ", A("2"), ", кв. ", A("8")),
        make(c, "zelenograd", "г. ", A("Зеленоград"), ", корп. ", A("1824"), ", кв. ", A("312")),
        make(c, "spb_lines", A("Санкт-Петербург"), ", ", A("В.О."), ", ", A("7-я"), " линия, д. ", A("34"),
             ", лит. ", A("А"), ", кв. ", A("9")),
        make(c, "snt", "СНТ «", A("Рассвет"), "», уч. ", A("112"), ", ", A("Раменский"), " р-н, ",
             A("Московская"), " обл."),
        make(c, "derevnya", "д. ", A("Малые Вяземы"), ", ул. ", A("Садовая"), ", д. ", A("3")),
        make(c, "khutor", "проживает: х. ", A("Садки"), ", ", A("Ростовская"), " обл."),
        make(c, "stanitsa", "ст-ца ", A("Ленинградская"), ", ", A("Краснодарский"), " край, ул. ", A("Красная"),
             ", ", A("45")),
        make(c, "naberezhnaya", "наб. реки ", A("Фонтанки"), ", д. ", A("90"), ", кв. ", A("3")),
        make(c, "prospekt_dash", "пр-т ", A("Мира"), ", ", A("102"), "-", A("15")),
        make(c, "germany_latin", "Wohnadresse: ", A("Invalidenstraße"), " ", A("117"), ", ", A("10115"), " ",
             A("Berlin"), ", ", A("Germany")),
        make(c, "kazakhstan", A("Казахстан"), ", г. ", A("Алматы"), ", пр. ", A("Абая"), ", ", A("150/230"),
             ", кв. ", A("12")),
        make(c, "lowercase_no_punct", "проживаю по адресу ", A("москва"), " ул ", A("профсоюзная"), " ",
             A("56"), " кв ", A("7")),
        make(c, "upper", "АДРЕС: ", A("620014"), ", ", A("СВЕРДЛОВСКАЯ"), " ОБЛ., Г. ", A("ЕКАТЕРИНБУРГ"),
             ", УЛ. ", A("МАЛЫШЕВА"), ", Д. ", A("51"), ", КВ. ", A("204")),
        make(c, "republic", "Респ. ", A("Татарстан"), ", г. ", A("Казань"), ", ул. ", A("Баумана"), ", д. ",
             A("19")),
        make(c, "street_with_date", "ул. ", A("8 Марта"), ", д. ", A("1"), ", кв. ", A("64"), ", г. ",
             A("Екатеринбург")),
        make(c, "pereulok", "пер. ", A("Большой Козихинский"), ", д. ", A("22"), ", стр. ", A("1")),
        make(c, "novosib_short", A("Новосибирск"), ", ", A("Красный"), " пр-кт, ", A("25"), "-", A("4")),
        make(c, "mkrn_letter", "мкр-н ", A("Северный"), ", ", A("14А"), "-", A("56")),
        make(c, "nbsp", f"г.{NBSP}", A("Самара"), f", ул.{NBSP}", A("Ленинградская"), f", д.{NBSP}", A("12")),
        make(c, "minsk", "адрес: ", A("Минск"), ", ул. ", A("Сурганова"), " ", A("37/2"), " - ", A("88")),
        make(c, "murino_korpus", A("Ленинградская"), " обл., ", A("Всеволожский"), " р-н, пос. ", A("Мурино"),
             ", ", A("Воронцовский"), " б-р, ", A("5к1")),
        make(c, "delivery_sentence", "Привезите, пожалуйста, карту на ", A("Профсоюзную"), " ", A("12"),
             ", я буду дома после семи."),
        make(c, "rural_selo", "с. ", A("Верхний Услон"), ", ул. ", A("Чехова"), ", д. ", A("4"), ", ",
             "Республика ", A("Татарстан")),
        make(c, "usa", "Mailing address: ", A("350"), " ", A("Fifth Avenue"), ", Apt ", A("21B"), ", ",
             A("New York"), ", ", A("NY"), " ", A("10118"), ", ", A("USA")),
    ]


def email(g: Gen) -> list[dict]:
    c = "EMAIL"
    return [
        make(c, "bare", P("ivan.petrov84@mail.ru", c)),
        make(c, "label", "E-mail: ", P("kim_soyeon1990@gmail.com", c)),
        make(c, "sentence_end", "Выписку отправьте на ", P("a.smirnova@yandex.ru", c), "."),
        make(c, "plus_tag", "почта ", P("olga.v+bank@outlook.com", c)),
        make(c, "upper", "ЭЛ. ПОЧТА: ", P("SERGEEV.PAVEL@BK.RU", c)),
        make(c, "angle_brackets", "От: ", P("Нгуен Ван", "PERSON"), " <", P("nguyen.van.nam@inbox.ru", c), ">"),
        make(c, "cyrillic_domain", "мой адрес ", P("иван@почта.рф", c), ", пишите туда"),
        make(c, "obfuscated", "почта: ", P("d.korolev[at]rambler.ru", c)),
        make(c, "corp_personal", "рабочая почта сотрудника ", P("t.khabibullin@romashka-trade.ru", c)),
        make(c, "mailto", "ссылка mailto:", P("zarina.dz@list.ru", c), " в подписи"),
        make(c, "subdomain", "контакт клиента: ", P("m.ali_2001@student.msu.ru", c)),
    ]


def phone(g: Gen) -> list[dict]:
    c = "PHONE"
    out = []
    for variant, pre, style, post in (
        ("std", "Телефон: ", "std", ""),
        ("eight", "тел. ", "eight", ""),
        ("plain", "мой номер ", "plain", ", звоните после 18"),
        ("plus", "моб.: ", "plus", ""),
        ("spaces", "номер телефона ", "spaces", ""),
        ("dashes", "контактный телефон ", "dashes", ""),
        ("seven", "тел ", "seven", ""),
        ("nbsp", "Тел.: ", "nbsp", ""),
        ("dots", "позвоните мне ", "dots", ""),
        ("bare", "", "std", ""),
    ):
        out.append(make(c, variant, pre, P(g.phone(style), c), post))
    out += [
        make(c, "belarus", "номер в Минске ", P("+375 29 123-45-67", c)),
        make(c, "uzbek", "тел. родственника в Ташкенте: ", P("+998 90 123 45 67", c)),
        make(c, "kyrgyz", "WhatsApp: ", P("+996 555 123 456", c)),
        make(c, "korea", "корейский номер ", P("+82 10-1234-5678", c)),
        make(c, "home_landline", "домашний телефон ", P("8 (495) 612-34-17", c)),
        make(c, "no_country", "сотовый ", P("916 482-15-90", c)),
        make(c, "whatsapp_sentence", "напишите в вотсап на ", P("89037771122", c), ", так быстрее"),
        make(c, "en_dash", "т. ", P("+7 921 555–12–34", c)),
    ]
    return out
