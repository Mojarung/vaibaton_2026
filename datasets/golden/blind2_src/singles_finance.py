"""Одиночные примеры: ИНН, карта, CVV, PIN, держатель карты, СНИЛС."""

from __future__ import annotations

from common import NBSP, Gen, P, make


def inn(g: Gen) -> list[dict]:
    c = "INN"
    i1, i2, i3, i4, i5, i6, i7, i8, i9 = (g.inn12() for _ in range(9))
    return [
        make(c, "label", "ИНН ", P(i1, c)),
        make(c, "spaced", "ИНН: ", P(f"{i2[:4]} {i2[4:8]} {i2[8:]}", c)),
        make(c, "fl", "инн физ. лица ", P(i3, c)),
        make(c, "sentence", "Мой ИНН - ", P(i4, c), ", проверьте, пожалуйста, налоговый вычет."),
        make(c, "ip", "ИНН индивидуального предпринимателя ", P(i5, c)),
        make(c, "latin", "TIN: ", P(i6, c)),
        make(c, "bare", P(i7, c)),
        make(c, "nbsp", f"ИНН{NBSP}", P(i8, c), " (налоговый резидент РФ)"),
        make(c, "lower_colon", "инн:", P(i9, c)),
    ]


def bank_card(g: Gen) -> list[dict]:
    c = "BANK_CARD"
    mir19 = g.card("2202", 19)
    amex = g.card("37", 15)
    return [
        make(c, "spaces", "Номер карты: ", P(g.card_fmt(" "), c)),
        make(c, "glued", "переведи на карту ", P(g.card(), c), " до вечера"),
        make(c, "dashes", "карта ", P(g.card_fmt("-"), c)),
        make(c, "nbsp", "карта клиента ", P(g.card_fmt(NBSP), c)),
        make(c, "mir19", "карта Мир ", P(f"{mir19[:4]} {mir19[4:8]} {mir19[8:12]} {mir19[12:16]} {mir19[16:]}", c)),
        make(c, "amex", "Amex ", P(f"{amex[:4]} {amex[4:10]} {amex[10:]}", c)),
        make(c, "bare", P(g.card_fmt(" "), c)),
        make(c, "card_en", "card number ", P(g.card(), c), ", exp 11/28"),
        make(c, "sentence_end", "Деньги поступили на карту ", P(g.card_fmt(" "), c), "."),
        make(c, "double_space", "№ карты ", P(g.card_fmt("  "), c)),
        make(c, "upper_ctx", "НОМЕР КАРТЫ ПОЛУЧАТЕЛЯ: ", P(g.card(), c)),
        make(c, "lost_card", "потерял карту ", P(g.card_fmt(" "), c), ", заблокируйте срочно"),
    ]


def cvv(g: Gen) -> list[dict]:
    c = "CVV"
    return [
        make(c, "label", "CVV ", P(g.num(3, False), c)),
        make(c, "cvc2", "CVC2: ", P(g.num(3, False), c)),
        make(c, "descr", "код на обороте карты ", P(g.num(3), c)),
        make(c, "slash", "cvv/cvc ", P(g.num(3), c)),
        make(c, "sentence", "три цифры на обратной стороне: ", P(g.num(3), c)),
        make(c, "dash", "CVV2 - ", P(g.num(3), c)),
        make(c, "cvc_lower", "свк ", P(g.num(3), c), ", срок 09/27"),
    ]


def pin(g: Gen) -> list[dict]:
    c = "PIN"
    return [
        make(c, "pin_kod", "пин-код ", P(g.num(4, False), c)),
        make(c, "upper", "ПИН: ", P(g.num(4, False), c)),
        make(c, "from_card", "пин от карты ", P(g.num(4), c), ", не забудь"),
        make(c, "latin", "PIN-код ", P(g.num(4), c)),
        make(c, "my_pin", "мой пин ", P(g.num(4), c), " не подходит в банкомате"),
        make(c, "pin_en", "PIN: ", P(g.num(4), c)),
        make(c, "new_pin", "Установите новый PIN ", P(g.num(4), c), " для карты"),
    ]


def cardholder(g: Gen) -> list[dict]:
    c = "CARDHOLDER"
    return [
        make(c, "label", "Держатель карты: ", P("IVAN PETROV", c)),
        make(c, "english", "Cardholder: ", P("ANNA SMIRNOVA", c)),
        make(c, "name_on_card", "имя на карте: ", P("ALEKSEY IVANOV", c)),
        make(c, "owner", "владелец карты ", P("MARIA KIM", c)),
        make(c, "upper_label", "CARDHOLDER NAME: ", P("DMITRII SOKOLOV", c)),
        make(c, "embossed", P(g.card_fmt(" "), "BANK_CARD"), "\n12/29\n", P("ELENA KUZNETSOVA", c)),
        make(c, "nguyen", "На карте написано ", P("NGUYEN VAN THANH", c), ", как в загранпаспорте."),
        make(c, "mixed_case", "держатель: ", P("Olga Belousova", c)),
    ]


def snils(g: Gen) -> list[dict]:
    c = "SNILS"
    return [
        make(c, "std", "СНИЛС ", P(g.snils_fmt("std"), c)),
        make(c, "dash", "СНИЛС: ", P(g.snils_fmt("dash"), c)),
        make(c, "space", "снилс ", P(g.snils_fmt("space"), c)),
        make(c, "plain", "СНИЛС ", P(g.snils_fmt("plain"), c)),
        make(c, "insurance", "страховой номер индивидуального лицевого счёта ", P(g.snils_fmt("std"), c)),
        make(c, "certificate", "Страховое свидетельство № ", P(g.snils_fmt("std"), c)),
        make(c, "sentence", "Для оформления пенсии укажите СНИЛС ", P(g.snils_fmt("std"), c), " в заявлении."),
        make(c, "bare", P(g.snils_fmt("std"), c)),
        make(c, "nbsp", "СНИЛС ", P(g.snils_fmt("std").replace(" ", NBSP), c)),
    ]
