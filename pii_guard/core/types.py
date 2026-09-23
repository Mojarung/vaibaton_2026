"""Типы сущностей и найденные спаны.

Список типов открыт: YAML-правило может объявить новый тип.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Имя типа: (метка ru, метка en).
BASE_TYPES: dict[str, tuple[str, str]] = {
    "PERSON": ("ФИО", "PERSON"),
    "BIRTH_DATE": ("ДАТА_РОЖДЕНИЯ", "BIRTH_DATE"),
    "BIRTH_PLACE": ("МЕСТО_РОЖДЕНИЯ", "BIRTH_PLACE"),
    "PASSPORT": ("ПАСПОРТ", "PASSPORT"),
    "CITIZENSHIP": ("ГРАЖДАНСТВО", "CITIZENSHIP"),
    "PASSPORT_AUTHORITY": ("ОРГАН_ВЫДАЧИ", "PASSPORT_AUTHORITY"),
    "DEPARTMENT_CODE": ("КОД_ПОДРАЗДЕЛЕНИЯ", "DEPARTMENT_CODE"),
    "PASSPORT_DATE": ("ДАТА_ВЫДАЧИ", "PASSPORT_DATE"),
    "DRIVER_LICENSE": ("ВОДИТЕЛЬСКОЕ_УДОСТОВЕРЕНИЕ", "DRIVER_LICENSE"),
    "ADDRESS": ("АДРЕС", "ADDRESS"),
    "EMAIL": ("EMAIL", "EMAIL"),
    "PHONE": ("ТЕЛЕФОН", "PHONE"),
    "INN": ("ИНН", "INN"),
    "BANK_CARD": ("НОМЕР_КАРТЫ", "BANK_CARD"),
    "CVV": ("CVV", "CVV"),
    "PIN": ("ПИН_КОД", "PIN"),
    "CARDHOLDER": ("ДЕРЖАТЕЛЬ_КАРТЫ", "CARDHOLDER"),
    "SNILS": ("СНИЛС", "SNILS"),
    "FOREIGN_DOCUMENT": ("ДОКУМЕНТ", "ID_DOCUMENT"),
}

# Подтипы адреса: маскируется значение компонента, служебное слово остаётся.
ADDRESS_SUBTYPES: dict[str, tuple[str, str]] = {
    "COUNTRY": ("СТРАНА", "COUNTRY"),
    "POSTCODE": ("ИНДЕКС", "POSTCODE"),
    "REGION": ("РЕГИОН", "REGION"),
    "DISTRICT": ("РАЙОН", "DISTRICT"),
    "CITY": ("ГОРОД", "CITY"),
    "STREET": ("УЛИЦА", "STREET"),
    "HOUSE": ("ДОМ", "HOUSE"),
    "BUILDING": ("КОРПУС", "BUILDING"),
    "APARTMENT": ("КВАРТИРА", "APARTMENT"),
}

# Служебный тип: сбой детектора, скрыт весь текст.
FAILSAFE = "FAILSAFE"

_UPPER_SNAKE = re.compile(r"^[A-Z][A-Z0-9_]*$")


@dataclass(frozen=True, slots=True)
class Span:
    """Найденный фрагмент текста."""

    start: int
    end: int
    type: str
    confidence: float
    priority: int
    rule: str
    subtype: str | None = None

    @property
    def length(self) -> int:
        return self.end - self.start


class TypeRegistry:
    """Реестр типов ПДн с метками."""

    def __init__(self) -> None:
        self._labels: dict[str, tuple[str, str]] = dict(BASE_TYPES)

    def register(self, name: str, label_ru: str | None, label_en: str | None) -> None:
        if not _UPPER_SNAKE.match(name):
            raise ValueError("Имя типа должно быть в UPPER_SNAKE_CASE")
        self._labels[name] = (label_ru or name, label_en or name)

    def known(self, name: str) -> bool:
        return name in self._labels

    def names(self) -> list[str]:
        return sorted(self._labels)

    def label(self, span_type: str, subtype: str | None = None, lang: str = "ru") -> str:
        if span_type == FAILSAFE:
            return "СКРЫТО" if lang == "ru" else "REDACTED"
        if subtype in ADDRESS_SUBTYPES:
            return ADDRESS_SUBTYPES[subtype][0 if lang == "ru" else 1]
        labels = self._labels.get(span_type)
        if labels is None:
            return span_type
        return labels[0 if lang == "ru" else 1]


@dataclass(slots=True)
class DetectionOptions:
    """Параметры детекции из политики системы-потребителя."""

    entity_types: frozenset[str] = field(default_factory=lambda: frozenset(BASE_TYPES))
    contextual: bool = True
    single_value_mode: bool = True
    bare_date_policy: str = "birth_like"
    combo_rules: tuple = ()
