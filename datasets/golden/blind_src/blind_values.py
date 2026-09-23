"""Детерминированные синтетические значения с корректными контрольными суммами.

Все значения случайные (seed фиксирован), к реальным людям отношения не имеют.
"""

import random

_rng = random.Random(20260922)

W10 = [2, 4, 10, 3, 5, 9, 4, 6, 8]
W11 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
W12 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]


def _digits(n: int) -> str:
    return "".join(str(_rng.randrange(10)) for _ in range(n))


def _weighted(digits: str, weights: list[int]) -> str:
    return str(sum(int(d) * w for d, w in zip(digits, weights)) % 11 % 10)


def make_inn10(p9: str) -> str:
    return p9 + _weighted(p9, W10)


def make_inn12(p10: str) -> str:
    p11 = p10 + _weighted(p10, W11)
    return p11 + _weighted(p11, W12)


def is_valid_inn(s: str) -> bool:
    d = "".join(ch for ch in s if ch.isdigit())
    if len(d) == 10:
        return make_inn10(d[:9]) == d
    if len(d) == 12:
        return make_inn12(d[:10]) == d
    return False


def snils_check(p9: str) -> str:
    s = sum(int(d) * (9 - i) for i, d in enumerate(p9))
    if s < 100:
        c = s
    elif s in (100, 101):
        c = 0
    else:
        c = s % 101
        if c == 100:
            c = 0
    return f"{c:02d}"


def is_valid_snils(s: str) -> bool:
    d = "".join(ch for ch in s if ch.isdigit())
    return len(d) == 11 and snils_check(d[:9]) == d[9:]


def luhn_digit(body: str) -> str:
    total = 0
    for i, ch in enumerate(reversed(body)):
        n = int(ch)
        if i % 2 == 0:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return str((10 - total % 10) % 10)


def is_luhn(s: str) -> bool:
    d = "".join(ch for ch in s if ch.isdigit())
    return len(d) >= 12 and luhn_digit(d[:-1]) == d[-1]


def _card(prefix: str, length: int) -> str:
    body = prefix + _digits(length - len(prefix) - 1)
    return body + luhn_digit(body)


# --- ИНН ---------------------------------------------------------------
_REG12 = ["77", "50", "78", "16", "66", "23", "54", "63", "52", "61",
          "02", "74", "36", "59", "24", "03", "31", "40", "69", "71"]
I12 = [make_inn12(r + _digits(8)) for r in _REG12]
_REG10 = ["77", "50", "78", "16", "66", "23", "54", "63", "52", "61"]
I10 = [make_inn10(r + _digits(7)) for r in _REG10]


def _break_last(s: str) -> str:
    return s[:-1] + str((int(s[-1]) + 3) % 10)


I12_BAD = [_break_last(make_inn12("50" + _digits(8)))]

# --- СНИЛС -------------------------------------------------------------
SN = []
while len(SN) < 20:
    p = _digits(9)
    if int(p) > 1001998:
        SN.append(p + snils_check(p))
_p_bad = _digits(9)
SN_BAD = [_p_bad + f"{(int(snils_check(_p_bad)) + 7) % 100:02d}"]


def snf(s: str) -> str:
    """123-456-789 01"""
    return f"{s[:3]}-{s[3:6]}-{s[6:9]} {s[9:]}"


def sns(s: str) -> str:
    """123 456 789 01"""
    return f"{s[:3]} {s[3:6]} {s[6:9]} {s[9:]}"


def snd(s: str) -> str:
    """123-456-789-01"""
    return f"{s[:3]}-{s[3:6]}-{s[6:9]}-{s[9:]}"


# --- Карты -------------------------------------------------------------
VISA = [_card("4" + str(_rng.choice([2, 5, 7, 8])), 16) for _ in range(10)]
MC = [_card("5" + str(_rng.choice([1, 3, 4, 5])), 16) for _ in range(8)]
MIR16 = [_card("220" + str(_rng.randrange(5)), 16) for _ in range(12)]
MIR19 = [_card("2200", 19) for _ in range(4)]
AMEX = [_card("37", 15) for _ in range(3)]
UP = [_card("62", 16) for _ in range(2)]
_valid_for_bad = _card("41", 16)
BAD_CARD = [_valid_for_bad[:-1] + str((int(_valid_for_bad[-1]) + 1) % 10)]


def sp(card: str) -> str:
    """Группы по 4 (16 и 19 цифр) через пробел."""
    return " ".join(card[i:i + 4] for i in range(0, len(card), 4))


def dash(card: str) -> str:
    return "-".join(card[i:i + 4] for i in range(0, len(card), 4))


def amex(card: str) -> str:
    """4-6-5"""
    return f"{card[:4]} {card[4:10]} {card[10:]}"


if __name__ == "__main__":
    print("I12", I12)
    print("I10", I10)
    print("I12_BAD", I12_BAD, [is_valid_inn(x) for x in I12_BAD])
    print("SN", [snf(x) for x in SN])
    print("SN_BAD", SN_BAD, is_valid_snils(SN_BAD[0]))
    for name, lst in [("VISA", VISA), ("MC", MC), ("MIR16", MIR16), ("MIR19", MIR19),
                      ("AMEX", AMEX), ("UP", UP), ("BAD", BAD_CARD)]:
        print(name, [(c, is_luhn(c)) for c in lst])
    assert all(is_valid_inn(x) for x in I12 + I10)
    assert all(is_valid_snils(x) for x in SN)
    assert all(is_luhn(c) for c in VISA + MC + MIR16 + MIR19 + AMEX + UP)
    assert not any(is_luhn(c) for c in BAD_CARD)
    assert not is_valid_snils(SN_BAD[0])
    assert not any(is_valid_inn(x) for x in I12_BAD)
