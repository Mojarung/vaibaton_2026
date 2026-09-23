"""Разрешение пересечений, комбо-правила, слияние соседей и режим одиночного значения."""

from __future__ import annotations

from bisect import bisect_left, bisect_right, insort

import regex as re

from .gazetteers import Gazetteers, Morph, first_like, is_patronymic, surname_like
from .textutil import Token, same_record
from .types import DetectionOptions, Span
from .validators import date_any, inn, luhn, snils

# Числовая дата целиком: 1-4 цифры, разделитель, 1-2 цифры, разделитель, 2-4 цифры.
NUMERIC_DATE_RE = re.compile(r"\d{1,4}[./-]\d{1,2}[./-]\d{2,4}", re.VERSION1)

# Текстовая дата: 1-2 цифры, месяц, четыре цифры и необязательно «г», «года» или «г.».
TEXT_DATE_RE = re.compile(
    r"\d{1,2}\s+(?:январ|феврал|март|апрел|май|мая|июн|июл|август|сентябр|октябр|ноябр|декабр)"
    r"\w*\.?\s+\d{4}\s*(?:г\.?|года)?",
    re.IGNORECASE | re.VERSION1,
)

CONTAINER_MIN_CONFIDENCE = 0.85
CONTAINER_PRIORITY_SLACK = 40


def _has_partner(
    text: str, span: Span, required_types: list, window: int, spans: list[Span]
) -> bool:
    """Есть ли рядом спан нужного типа в пределах окна и той же записи."""
    for other in spans:
        if other is span or other.type not in required_types:
            continue
        if abs(other.start - span.start) <= window and same_record(text, span.start, other.start):
            return True
    return False


def apply_combo_rules(text: str, spans: list[Span], options: DetectionOptions) -> list[Span]:
    """Комбо-правила политики: PIN и CVV маскируются только рядом с картой."""
    rules = getattr(options, "combo_rules", None)
    if not rules:
        return spans
    result: list[Span] = []
    for span in spans:
        rule = next((r for r in rules if r[0] == span.type), None)
        if rule is None:
            result.append(span)
            continue
        _, required_types, window = rule
        if _has_partner(text, span, required_types, window, spans):
            result.append(span)
    return result


def drop_contained(spans: list[Span]) -> list[Span]:
    """Выкидывает короткие спаны внутри длинных надёжных."""
    if len(spans) < 2:
        return spans
    ordered = sorted(spans, key=lambda s: (s.start, -s.end))
    result: list[Span] = []
    for i, span in enumerate(ordered):
        dropped = False
        for j in range(max(0, i - 50), min(len(ordered), i + 50)):
            if j == i:
                continue
            other = ordered[j]
            if (
                other.start <= span.start
                and other.end >= span.end
                and other.end - other.start > span.end - span.start
                and other.confidence >= CONTAINER_MIN_CONFIDENCE
                and other.priority >= span.priority - CONTAINER_PRIORITY_SLACK
            ):
                dropped = True
                break
        if not dropped:
            result.append(span)
    return result


def resolve_overlaps(spans: list[Span]) -> list[Span]:
    """Жадно принимает непересекающиеся спаны по приоритету, длине, уверенности."""
    if not spans:
        return []
    ordered = sorted(
        drop_contained(spans),
        key=lambda s: (-s.priority, -(s.end - s.start), -s.confidence, s.start),
    )
    accepted: list[Span] = []
    starts: list[int] = []
    ends: list[int] = []
    for span in ordered:
        i = bisect_right(ends, span.start)
        j = bisect_left(starts, span.end)
        if i == j:
            accepted.append(span)
            insort(starts, span.start)
            insort(ends, span.end)
    return sorted(accepted, key=lambda s: s.start)


def merge_adjacent(text: str, spans: list[Span]) -> list[Span]:
    """Склеивает соседние спаны одного типа и подтипа."""
    if not spans:
        return []
    result: list[Span] = [spans[0]]
    for span in spans[1:]:
        prev = result[-1]
        if prev.type == span.type and prev.subtype == span.subtype:
            gap = text[prev.end : span.start]
            if 0 <= len(gap) <= 2 and all(c in " \t" for c in gap):
                result[-1] = Span(
                    start=prev.start,
                    end=span.end,
                    type=prev.type,
                    confidence=max(prev.confidence, span.confidence),
                    priority=max(prev.priority, span.priority),
                    rule=prev.rule,
                    subtype=prev.subtype,
                )
                continue
        result.append(span)
    return result


def single_value(
    text: str, tokens: list[Token], options: DetectionOptions, gaz: Gazetteers, morph: Morph | None
) -> Span | None:
    """Весь payload это одно значение без контекста, угадываем тип по форме."""
    if not text or len(tokens) > 6:
        return None
    value = text.strip()
    if not value:
        return None
    kind = _guess_kind(value, tokens, gaz, morph)
    if kind is None or kind not in options.entity_types:
        return None
    start = text.find(value)
    return Span(
        start=start,
        end=start + len(value),
        type=kind,
        confidence=0.7,
        priority=10,
        rule="single_value",
    )


def _looks_like_card(digits: str, _value: str) -> bool:
    return 13 <= len(digits) <= 19 and luhn(digits)


def _looks_like_cvv(digits: str, _value: str) -> bool:
    return len(digits) == 3


def _looks_like_pin(digits: str, value: str) -> bool:
    return 4 <= len(digits) <= 6 and "-" not in value and "." not in value


def _looks_like_department_code(digits: str, value: str) -> bool:
    return len(digits) == 6 and "-" in value


def _looks_like_inn(digits: str, _value: str) -> bool:
    return len(digits) in (10, 12) and inn(digits)


def _looks_like_snils(digits: str, _value: str) -> bool:
    return len(digits) == 11 and snils(digits)


def _looks_like_phone(digits: str, value: str) -> bool:
    return len(digits) in (10, 11) and value.lstrip("+").startswith(("7", "8", "9"))


def _looks_like_passport(digits: str, _value: str) -> bool:
    return len(digits) == 10


def _looks_like_numeric_date(_digits: str, value: str) -> bool:
    return NUMERIC_DATE_RE.fullmatch(value.strip()) and date_any(value.strip())


# Упорядоченные проверки числового значения без слов; порядок важен.
_NUMERIC_CHECKS: list[tuple[callable, str]] = [
    (_looks_like_card, "BANK_CARD"),
    (_looks_like_cvv, "CVV"),
    (_looks_like_pin, "PIN"),
    (_looks_like_department_code, "DEPARTMENT_CODE"),
    (_looks_like_inn, "INN"),
    (_looks_like_snils, "SNILS"),
    (_looks_like_phone, "PHONE"),
    (_looks_like_passport, "PASSPORT"),
    (_looks_like_numeric_date, "BIRTH_DATE"),
]


def _is_ascii_pair(words: list[str]) -> bool:
    return len(words) >= 2 and all(w.isascii() and w.isalpha() for w in words)


def _looks_like_cardholder(words: list[str], gaz: Gazetteers) -> bool:
    return any(gaz.is_latin_first(w) for w in words)


def _looks_like_person(
    words: list[str], has_digits: bool, gaz: Gazetteers, morph: Morph | None
) -> bool:
    return (
        not has_digits
        and len(words) <= 3
        and all(
            first_like(w, gaz, morph) >= 0.5
            or surname_like(w, gaz, morph) >= 0.6
            or is_patronymic(w, morph)
            for w in words
        )
    )


def _looks_like_text_date(value: str) -> bool:
    return bool(TEXT_DATE_RE.fullmatch(value.strip()))


def _looks_like_address(words: list[str], morph: Morph | None) -> bool:
    if morph is None or len(words) > 2:
        return False
    geox_scores = [morph.geox(w) for w in words]
    return any(g >= 0.5 for g in geox_scores) and all(
        g >= 0.5 or w[0].isupper() for g, w in zip(geox_scores, words, strict=True)
    )


def _guess_numeric(digits: str, value: str) -> str | None:
    return next((kind for check, kind in _NUMERIC_CHECKS if check(digits, value)), None)


def _guess_kind(
    value: str, tokens: list[Token], gaz: Gazetteers, morph: Morph | None
) -> str | None:
    words = [t.text for t in tokens if t.is_word]
    digits = "".join(c for c in value if c.isdigit())
    has_digits = any(c.isdigit() for c in value)
    if has_digits and not words:
        return _guess_numeric(digits, value)
    if not words:
        return None
    if _is_ascii_pair(words):
        return "CARDHOLDER" if _looks_like_cardholder(words, gaz) else None
    if gaz.is_country(value):
        return "CITIZENSHIP"
    if _looks_like_person(words, has_digits, gaz, morph):
        return "PERSON"
    if _looks_like_text_date(value):
        return "BIRTH_DATE"
    if _looks_like_address(words, morph):
        return "ADDRESS"
    return None
