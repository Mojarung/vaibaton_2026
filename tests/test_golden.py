"""Качество детекции: пороги, ниже которых сдавать нельзя."""

from __future__ import annotations

from pathlib import Path

import pytest

from pii_guard.core.types import DetectionOptions
from pii_guard.quality.golden import Example, load, parse_example
from pii_guard.quality.metrics import Report
from tools.gen_golden import generate

ROOT = Path(__file__).resolve().parent.parent
BLIND = ROOT / "datasets" / "golden" / "blind.jsonl"


def run_report(detector, examples) -> Report:
    report = Report()
    options = DetectionOptions()
    for raw in examples:
        ex = raw if isinstance(raw, Example) else parse_example(raw)
        spans = detector.detect(ex.text, options).spans
        report.add(ex, [(s.start, s.end) for s in spans])
    return report


@pytest.fixture(scope="module")
def report(detector):
    return run_report(detector, generate(seed=11, rounds=15))


def test_generated_quality(report):
    s = report.summary()
    assert s["char_recall"] >= 0.995, s
    assert s["span_similarity"] >= 0.99, s
    assert s["trap_false_positive_rate"] <= 0.02, s


def test_per_type_coverage(report):
    weak = [row for row in report.per_type() if row["recall_full"] < 0.95]
    assert not weak, f"Слабые типы: {weak}"


@pytest.mark.skipif(not BLIND.exists(), reason="нет слепого набора")
def test_blind(detector):
    examples = load(BLIND)
    report = run_report(detector, examples)
    s = report.summary()
    assert s["char_recall"] >= 0.97, s
    assert s["span_similarity"] >= 0.98, s
    assert s["trap_false_positive_rate"] <= 0.02, s


JURY_SAMPLES = [
    ("Клиент Иванов Иван Иванович, паспорт серия 4509 номер 123456", ["Иванов", "4509", "123456"]),
    ("ФИО: ИВАНОВ ИВАН ИВАНОВИЧ", ["ИВАНОВ", "ИВАНОВИЧ"]),
    ("дата рождения 03.15.1990", ["03.15.1990"]),
    ("родился пятнадцатого марта 1990 года", ["пятнадцатого марта 1990"]),
    ("PIN 4829, карта 5536 8989 9530 3715, CVV 123", ["4829", "5536", "123"]),
]


@pytest.mark.parametrize("text,hidden", JURY_SAMPLES)
def test_jury_mask(detector, text, hidden):
    spans = detector.detect(text, DetectionOptions()).spans
    masked = list(text)
    for s in spans:
        for i in range(s.start, s.end):
            masked[i] = "#"
    masked = "".join(masked)
    for h in hidden:
        assert h not in masked, f"значение {h!r} осталось в маске"


TRAPS = [
    "Поэт Александр Пушкин написал «Евгений Онегин»",
    "Отделение банка на Тверской, дом 1 в Москве",
    "Горячая линия 8 800 100-00-00",
    "Встреча 22.09.2026 и договор № 1234567890",
    "ПАО «Альфа-Банк» с ИНН 7728168971 и адресом на Каланчевской, 27",
    "Код ошибки 500-012",
    "Флагманский офис банка на Невском проспекте",
    "Адрес поддержки support@bank.example",
    "Собор Василия Блаженного на Красной площади",
]


@pytest.mark.parametrize("text", TRAPS)
def test_traps(detector, text):
    spans = detector.detect(text, DetectionOptions()).spans
    assert spans == [], f"ловушка замаскирована: {spans}"


def test_no_label_skip(detector):
    text = "карта 2202 2012 3456 7890, CVV 123, PIN 4321"
    spans = detector.detect(text, DetectionOptions()).spans
    assert len(spans) == 3, spans
    by_type = {s.type: text[s.start : s.end] for s in spans}
    assert by_type["BANK_CARD"] == "2202 2012 3456 7890"
    assert by_type["CVV"] == "123"
    assert by_type["PIN"] == "4321"
