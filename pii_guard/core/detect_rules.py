"""Применение YAML-правил к тексту.

Правила компилируются в CompiledRule (см. rules.py). Здесь происходит тримминг
границ значения, прогон валидаторов, негативного и обязательного контекста и
проверок по словарям.
"""

from __future__ import annotations

from .gazetteers import Gazetteers, Morph
from .rules import PATTERN_TIMEOUT, CompiledRule
from .types import DetectionOptions, Span

TRIM_CHARS = " \t,.;:()«»\"'"

# Маркеры границ значения в строке контекста.
VALUE_START = "\x02"
VALUE_END = "\x03"


def trim(text: str, start: int, end: int) -> tuple[int, int]:
    """Сдвигает границы внутрь, пока на краях символы из TRIM_CHARS."""
    while start < end and text[start] in TRIM_CHARS:
        start += 1
    while end > start and text[end - 1] in TRIM_CHARS:
        end -= 1
    return start, end


def _bare_date_allowed(rule: CompiledRule, options: DetectionOptions) -> tuple[bool, bool]:
    """Применять ли правило и пропускать ли валидатор birth_like."""
    if getattr(rule, "policy", None) != "bare_date":
        return (True, False)
    bare = getattr(options, "bare_date_policy", None)
    if bare == "never":
        return (False, False)
    return (True, bare == "always")


def _check_countries_shrink(
    words: list[str], start: int, _end: int, gaz: Gazetteers, morph: Morph | None
) -> tuple[int, int] | None:
    for n in range(min(3, len(words)), 0, -1):
        cand = " ".join(words[:n])
        if gaz.is_country(cand):
            return (start, start + len(cand))
        if morph is not None:
            norm = " ".join(morph.normal_form(w) for w in words[:n])
            if gaz.is_country(norm):
                return (start, start + len(cand))
    return None


def _check_latin_first_any(
    words: list[str], start: int, end: int, gaz: Gazetteers, _morph: Morph | None
) -> tuple[int, int] | None:
    return (start, end) if any(gaz.is_latin_first(w) for w in words) else None


def _check_geox(
    words: list[str], start: int, end: int, _gaz: Gazetteers, morph: Morph | None
) -> tuple[int, int] | None:
    if morph is None:
        return (start, end)
    for w in words:
        if morph.geox(w) >= 0.3:
            return (start, end)
    return None


def _check_no_verbs(
    words: list[str], start: int, end: int, _gaz: Gazetteers, morph: Morph | None
) -> tuple[int, int] | None:
    if morph is None:
        return (start, end)
    if len(words) > 4:
        return None
    first_four = {"VERB", "INFN", "PRTF", "GRND"}
    all_seven = {"VERB", "INFN", "PRTF", "GRND", "ADJS", "PREP", "CONJ"}
    for i, w in enumerate(words):
        pos = morph.pos(w)
        if pos is None or pos == "UNKN":
            continue
        if i == 0:
            if pos in first_four:
                return None
        elif pos in all_seven:
            return None
    return (start, end)


# Диспетчер проверок по словарю: имя проверки -> функция.
_GAZETTEER_CHECKS: dict[str, callable] = {
    "countries_shrink": _check_countries_shrink,
    "latin_first_any": _check_latin_first_any,
    "geox": _check_geox,
    "no_verbs": _check_no_verbs,
}


def _gazetteer_ok(
    check: str, text: str, start: int, end: int, gaz: Gazetteers, morph: Morph | None
) -> tuple[int, int] | None:
    """Проверка по словарю; возвращает скорректированные границы или None."""
    value = text[start:end]
    words = value.split()
    fn = _GAZETTEER_CHECKS.get(check)
    if fn is None:
        return (start, end)
    return fn(words, start, end, gaz, morph)


def _negative_hit(rule: CompiledRule, text: str, start: int, end: int) -> bool:
    left = text[max(0, start - rule.negative_window) : start]
    right = text[end : end + rule.negative_after]
    ctx = left + VALUE_START + text[start:end] + VALUE_END + right
    return any(pat.search(ctx) for pat in rule.negatives)


def _required_missing(rule: CompiledRule, text: str, start: int, end: int) -> bool:
    left = text[max(0, start - rule.required_window) : start]
    right = text[end : end + (rule.required_window // 2)]
    ctx = left + VALUE_START + text[start:end] + VALUE_END + right
    return all(not pat.search(ctx) for pat in rule.required)


def _candidate(
    rule: CompiledRule,
    text: str,
    start: int,
    end: int,
    validators: list,
    gaz: Gazetteers,
    morph: Morph | None,
) -> Span | None:
    start, end = trim(text, start, end)
    if start >= end:
        return None
    value = text[start:end]
    for v in validators:
        if not v(value):
            return None
    if rule.negatives and _negative_hit(rule, text, start, end):
        return None
    if rule.required and _required_missing(rule, text, start, end):
        return None
    if rule.gazetteer_check:
        res = _gazetteer_ok(rule.gazetteer_check, text, start, end, gaz, morph)
        if res is None:
            return None
        start, end = res
    return Span(
        start=start,
        end=end,
        type=rule.type,
        confidence=rule.confidence,
        priority=rule.priority,
        rule=rule.id,
        subtype=rule.subtype,
    )


def _apply_rule(
    rule: CompiledRule,
    text: str,
    validators: list,
    gaz: Gazetteers,
    morph: Morph | None,
) -> list[Span]:
    """Прогоняет одно правило по всем совпадениям и группам."""
    spans: list[Span] = []
    for m in rule.pattern.finditer(text, timeout=PATTERN_TIMEOUT):
        for group in rule.groups:
            for s, e in m.spans(group):
                if s < 0:
                    continue
                cand = _candidate(rule, text, s, e, validators, gaz, morph)
                if cand is not None:
                    spans.append(cand)
    return spans


def _rule_validators(rule: CompiledRule, options: DetectionOptions) -> list | None:
    """Валидаторы правила с учётом политики bare_date; None — правило не применять."""
    enabled, skip_birth = _bare_date_allowed(rule, options)
    if not enabled:
        return None
    validators = rule.validators
    if skip_birth:
        validators = [v for v in validators if getattr(v, "__name__", "") != "birth_like"]
    return validators


def apply_rules(
    text: str,
    rules: list[CompiledRule],
    options: DetectionOptions,
    gaz: Gazetteers,
    morph: Morph | None,
) -> list[Span]:
    """Применяет все правила к тексту и возвращает найденные спаны."""
    text_lower = text.lower()
    digit_count = sum(1 for c in text if c.isdigit())
    spans: list[Span] = []
    for rule in rules:
        if rule.type not in options.entity_types:
            continue
        if rule.applicable and not rule.applicable(text_lower, digit_count, text):
            continue
        validators = _rule_validators(rule, options)
        if validators is None:
            continue
        spans.extend(_apply_rule(rule, text, validators, gaz, morph))
    return spans
