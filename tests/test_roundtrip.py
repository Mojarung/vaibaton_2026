"""Демаскирование: восстановленный текст обязан совпасть с исходным посимвольно."""

from __future__ import annotations

import pytest

from pii_guard.core.types import DetectionOptions
from pii_guard.mask.masker import Masker
from pii_guard.mask.restore import restore_positional, restore_tokens
from pii_guard.quality.golden import parse_example
from tools.gen_golden import generate

MODES = ["placeholder", "redact", "stars", "partial", "synthetic"]


def texts():
    special = [
        "a@example.ru; b@example.ru; a@example.ru",
        "[ФИО_1] и ****, а потом Иванов Иван Иванович",
        "😀 Иванов Иван Иванович, CVV 123, CVV 456, PIN 7890",
        "",
    ]
    return [parse_example(raw).text for raw in generate(seed=5, rounds=3)] + special


@pytest.mark.parametrize("mode", MODES)
def test_roundtrip_modes(detector, mode):
    for text in texts():
        spans = detector.detect(text, DetectionOptions()).spans
        session = Masker(detector.registry).session(mode)
        mr = session.mask(text, spans)
        restored = restore_positional(mr.text, [(e.start, e.end, e.original) for e in mr.entries])
        assert restored == text


@pytest.mark.parametrize("mode", ["placeholder", "synthetic"])
def test_restore_tokens(detector, mode):
    text = "Клиент Иванов Иван Иванович, тел. +7 916 123-45-67, email ivan@mail.ru"
    spans = detector.detect(text, DetectionOptions()).spans
    session = Masker(detector.registry).session(mode)
    session.mask(text, spans)
    tokens = list(session.token_map.keys())
    assert len(tokens) == 3
    answer = f"Связались: {tokens[2]}. Клиент {tokens[0]} подтвердил телефон {tokens[1]}."
    restored, count = restore_tokens(answer, session.token_map)
    assert count == 3
    for v in ("Иванов Иван Иванович", "+7 916 123-45-67", "ivan@mail.ru"):
        assert v in restored


def test_same_value_same_token(detector):
    text = "a@example.ru и a@example.ru, а b@example.ru"
    spans = detector.detect(text, DetectionOptions()).spans
    session = Masker(detector.registry).session("placeholder")
    mr = session.mask(text, spans)
    tokens = [e.token for e in mr.entries]
    assert tokens[0] == tokens[1]
    assert tokens[0] != tokens[2]

    text2 = "[EMAIL_1] и a@example.ru"
    spans2 = detector.detect(text2, DetectionOptions()).spans
    session2 = Masker(detector.registry).session("placeholder")
    mr2 = session2.mask(text2, spans2)
    assert "[EMAIL_1]" in mr2.text
    assert "[EMAIL_2]" in mr2.text


def test_no_golden_in_mask(detector):
    for raw in generate(seed=9, rounds=2):
        ex = parse_example(raw)
        spans = detector.detect(ex.text, DetectionOptions()).spans
        session = Masker(detector.registry).session("placeholder")
        mr = session.mask(ex.text, spans)
        for span in ex.pii:
            v = ex.text[span.start : span.end]
            if len(v) >= 4:
                assert v not in mr.text, f"{v} остался в маске"
