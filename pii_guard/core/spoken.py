"""Расшифровки звонков: числа словами превращаются в цифры.

Строит ещё один вид текста, где серия из MIN_WORDS и больше числительных
заменена цифрами. Каждая цифра помнит границы исходного слова, поэтому спан,
найденный по цифрам, возвращается на слова.
"""

from __future__ import annotations

import regex as re

UNITS = {
    "ноль": 0,
    "нуль": 0,
    "один": 1,
    "одна": 1,
    "одно": 1,
    "два": 2,
    "две": 2,
    "три": 3,
    "четыре": 4,
    "пять": 5,
    "шесть": 6,
    "семь": 7,
    "восемь": 8,
    "девять": 9,
}
TEENS = {
    "десять": 10,
    "одиннадцать": 11,
    "двенадцать": 12,
    "тринадцать": 13,
    "четырнадцать": 14,
    "пятнадцать": 15,
    "шестнадцать": 16,
    "семнадцать": 17,
    "восемнадцать": 18,
    "девятнадцать": 19,
}
TENS = {
    "двадцать": 20,
    "тридцать": 30,
    "сорок": 40,
    "пятьдесят": 50,
    "шестьдесят": 60,
    "семьдесят": 70,
    "восемьдесят": 80,
    "девяносто": 90,
}
HUNDREDS = {
    "сто": 100,
    "двести": 200,
    "триста": 300,
    "четыреста": 400,
    "пятьсот": 500,
    "шестьсот": 600,
    "семьсот": 700,
    "восемьсот": 800,
    "девятьсот": 900,
}
VALUES: dict[str, int] = {}
VALUES.update(UNITS)
VALUES.update(TEENS)
VALUES.update(TENS)
VALUES.update(HUNDREDS)

MIN_WORDS = 4

# Слова из букв или одиночный дефис или запятая.
WORD_RE = re.compile(r"[\p{L}]+|-|,", re.VERSION1)

# Быстрый префильтр без учёта регистра.
HINT = re.compile(
    r"\b(?:ноль|нуль|один|одна|одно|два|две|три|четыре|пять|шесть|семь|восемь|"
    r"девять|двадцать|сорок|сто)\b",
    re.IGNORECASE | re.VERSION1,
)


def _place(word: str) -> float:
    if word in HUNDREDS:
        return 3
    if word in TENS or word in TEENS:
        return 2
    return 1


def _last_place(word: str) -> float:
    if word in HUNDREDS:
        return 3
    if word in TENS:
        return 2
    if word in TEENS:
        return 1.5
    return 1


def _finalize(cur: list) -> tuple[int, int, str, bool]:
    start, end, value, count, _ = cur
    return (start, end, str(value), count == 1 and value < 10)


def _groups(words: list[tuple[int, int, str]]) -> list[tuple[int, int, str, bool]]:
    """Собирает группы-числа: (начало, конец, строка цифр, одна_ли_это_цифра)."""
    groups: list[tuple[int, int, str, bool]] = []
    cur: list | None = None
    for start, end, word in words:
        if cur is None:
            cur = [start, end, VALUES[word], 1, word]
            continue
        last_word = cur[4]
        if (
            _place(word) < _last_place(last_word)
            and last_word not in TEENS
            and not (word in TENS and last_word in TENS)
        ):
            cur[1] = end
            cur[2] += VALUES[word]
            cur[3] += 1
            cur[4] = word
        else:
            groups.append(_finalize(cur))
            cur = [start, end, VALUES[word], 1, word]
    if cur is not None:
        groups.append(_finalize(cur))
    return groups


def _collect_series(text: str) -> list[list[tuple[int, int, str]]]:
    """Собирает серии числительных: список списков (начало, конец, слово)."""
    series: list[list[tuple[int, int, str]]] = []
    current: list[tuple[int, int, str]] = []
    for m in WORD_RE.finditer(text):
        w = m.group()
        if w in VALUES:
            current.append((m.start(), m.end(), w))
        elif w in ("-", ","):
            if current:
                continue
        else:
            if len(current) >= MIN_WORDS:
                series.append(current)
            current = []
    if len(current) >= MIN_WORDS:
        series.append(current)
    return series


def _emit_series(
    text: str,
    ser: list[tuple[int, int, str]],
    out: list[str],
    starts: list[int],
    ends: list[int],
    pos: int,
) -> int:
    """Добавляет одну серию числительных в выход и таблицы смещений."""
    s_start = ser[0][0]
    for i in range(pos, s_start):
        out.append(text[i])
        starts.append(i)
        ends.append(i + 1)
    groups = _groups(ser)
    for gi, (g_start, g_end, digits, is_single) in enumerate(groups):
        if gi > 0:
            prev_single = groups[gi - 1][3]
            if not (prev_single and is_single):
                out.append(" ")
                starts.append(g_start)
                ends.append(g_start)
        for ch in digits:
            out.append(ch)
            starts.append(g_start)
            ends.append(g_end)
    return ser[-1][1]


def spoken(text: str) -> tuple[str, list[int], list[int]] | None:
    """Возвращает текст с цифрами и таблицу смещений, или None."""
    if not HINT.search(text):
        return None
    series = _collect_series(text)
    if not series:
        return None

    out: list[str] = []
    starts: list[int] = []
    ends: list[int] = []
    pos = 0
    for ser in series:
        pos = _emit_series(text, ser, out, starts, ends, pos)
    for i in range(pos, len(text)):
        out.append(text[i])
        starts.append(i)
        ends.append(i + 1)
    return "".join(out), starts, ends
