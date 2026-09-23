"""Детекция цепочек адреса и места рождения после триггера.

Подавляет адреса организаций. Работает по токенам после триггера адреса или
места рождения, собирая компоненты адреса (город, улица, дом, квартира и т.д.)
в один спан.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import regex as re
import yaml

from .gazetteers import Gazetteers, Morph
from .textutil import Token, normalize_yo, window_after
from .types import DetectionOptions, Span

# Служебные слова в нижнем регистре, с падежными формами.
CITY_WORDS = {
    "г",
    "гор",
    "город",
    "городе",
    "города",
    "с",
    "село",
    "селе",
    "ст-ца",
    "г-к",
    "д",
    "дер",
    "деревня",
    "деревне",
    "пос",
    "посёлок",
    "поселок",
    "посёлке",
    "поселке",
    "п",
    "пгт",
    "ст",
    "станица",
    "станице",
    "аул",
    "хутор",
    "рп",
    "снт",
}
STREET_WORDS = {
    "ул",
    "улица",
    "улице",
    "улицы",
    "пр-т",
    "пр",
    "просп",
    "проспект",
    "проспекте",
    "пер",
    "переулок",
    "переулке",
    "б-р",
    "бульвар",
    "бульваре",
    "ш",
    "шоссе",
    "наб",
    "набережная",
    "набережной",
    "пл",
    "площадь",
    "площади",
    "пр-д",
    "проезд",
    "проезде",
    "тупик",
    "аллея",
    "аллее",
    "линия",
    "мкр",
    "микрорайон",
    "кв-л",
    "квартал",
}
REGION_WORDS = {
    "обл",
    "область",
    "области",
    "край",
    "края",
    "крае",
    "респ",
    "республика",
    "республики",
    "ао",
    "округ",
    "округа",
    "округе",
}
DISTRICT_WORDS = {"р-н", "район", "района", "районе"}
HOUSE_WORDS = {"д", "дом", "дома", "доме"}
BUILDING_WORDS = {"корп", "корпус", "к", "стр", "строение", "лит", "литера", "подъезд"}
APARTMENT_WORDS = {
    "кв",
    "квартира",
    "квартире",
    "оф",
    "офис",
    "пом",
    "помещение",
    "комн",
    "комната",
    "эт",
    "этаж",
}
PREPOSITIONS = {
    "по",
    "в",
    "на",
    "у",
    "около",
    "возле",
    "рядом",
    "с",
    "напротив",
    "от",
    "до",
    "и",
    "во",
    "о",
    "из",
}

# Падежные формы типов тоже служебные, как и начальные формы из address.yaml.
SERVICE_FORMS = (
    CITY_WORDS
    | STREET_WORDS
    | REGION_WORDS
    | DISTRICT_WORDS
    | HOUSE_WORDS
    | BUILDING_WORDS
    | APARTMENT_WORDS
    | {"реки", "река", "канала", "уч", "участок"}
)

YEAR_WORDS = {"год", "года", "году", "г", "гг", "лет", "годы"}

# После этих слов следующее слово считается значением даже в нижнем регистре.
VALUE_AFTER = CITY_WORDS | STREET_WORDS | REGION_WORDS | DISTRICT_WORDS | {"страна"}

MAX_CHAIN_TOKENS = 18
CHAIN_WINDOW = 220
CHAIN_PRIORITY = {"ADDRESS": 100, "BIRTH_PLACE": 125}
ORG_AFTER_WINDOW = 50

# Слитный адрес без разделителей: [индекс]город+улица+дом+квартира.
# Например «362618КурскПолевая51248» или «КурскПолевая514248».
COMPACT_ADDR_RE = re.compile(
    r"(?<![\p{L}\d])(?:(?P<idx>\d{6}))?(?P<city>[А-ЯЁ][а-яё]+)"
    r"(?P<street>[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)*)(?P<num>\d+)(?![\p{L}\d])",
    re.VERSION1,
)


def _compile(patterns: list[str]) -> re.Pattern | None:
    """Склеивает список шаблонов в одно выражение через альтернативу."""
    if not patterns:
        return None
    return re.compile("|".join(f"(?:{p})" for p in patterns), re.IGNORECASE | re.VERSION1)


@dataclass(slots=True)
class _ChainState:
    """Состояние разбора цепочки адреса."""

    kind: str
    allow_numbers: bool
    spans: list[Span] = field(default_factory=list)
    last_service: str | None = None
    last_kind: str | None = None
    prev_low: str | None = None
    expect_value: bool = False
    last_end: int = -1

    def add(self, tok: Token, subtype: str) -> None:
        self.spans.append(
            Span(
                start=tok.start,
                end=tok.end,
                type=self.kind,
                confidence=0.85,
                priority=CHAIN_PRIORITY[self.kind],
                rule="address_chain",
                subtype=subtype,
            )
        )
        self.last_kind = subtype
        self.expect_value = False
        self.last_end = tok.end


class AddressDetector:
    """Собирает цепочки адреса и места рождения после триггера."""

    def __init__(self, config_path: str, gaz: Gazetteers, morph: Morph | None):
        self.gaz = gaz
        self.morph = morph
        try:
            with open(config_path, encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
        except OSError:
            cfg = {}
        self.address_triggers = _compile(cfg.get("address_triggers") or [])
        self.birthplace_triggers = _compile(cfg.get("birthplace_triggers") or [])
        self.service_words = {normalize_yo(w.lower()) for w in (cfg.get("service_words") or [])}
        self.stop_words = {normalize_yo(w.lower()) for w in (cfg.get("stop_words") or [])}
        self.org_markers = self.gaz.org_markers
        self.personal_markers = self.gaz.personal_markers
        self.public_markers = self.gaz.public_markers
        self.countries = self.gaz.countries

    def _geox(self, word: str) -> bool:
        """Истина, если есть морфология и четвёртая оценка тегов (Geox) >= 0.3."""
        if self.morph is None:
            return False
        tags = self.morph.tags(word)
        if not tags or len(tags) < 4:
            return False
        return tags[3] >= 0.3

    def _public_context(self, text: str, pos: int) -> bool:
        """Публичный ли контекст слева от позиции (для «Поэт Пушкин родился в Москве»)."""
        left = text[max(0, pos - 80) : pos]
        if self.personal_markers and self.personal_markers.search(left):
            return False
        return bool(self.public_markers and self.public_markers.search(left))

    def detect(self, text: str, tokens: list[Token], options: DetectionOptions) -> list[Span]:
        spans: list[Span] = []
        if "ADDRESS" in options.entity_types and self.address_triggers:
            for m in self.address_triggers.finditer(text, timeout=0.25):
                spans.extend(self._chain(text, tokens, m.end(), "ADDRESS", True))
        if "BIRTH_PLACE" in options.entity_types and self.birthplace_triggers:
            for m in self.birthplace_triggers.finditer(text, timeout=0.25):
                if options.contextual and self._public_context(text, m.start()):
                    continue
                spans.extend(self._chain(text, tokens, m.end(), "BIRTH_PLACE", False))
        spans.extend(self.detect_compact(text, options))
        return spans

    def detect_compact(self, text: str, options: DetectionOptions) -> list[Span]:
        """Детектирует слитные адреса без разделителей и триггера.

        Голые формы генератора склеивают компоненты вплотную:
        «362618КурскПолевая51248» (индекс+город+улица+дом+кв) и
        «КурскПолевая514248» (город+улица+дом+корп+кв). Город проверяем по
        морфологии (Geox), чтобы не ловить случайные «СловоСлово123».
        """
        if "ADDRESS" not in options.entity_types:
            return []
        spans: list[Span] = []
        for m in COMPACT_ADDR_RE.finditer(text, timeout=0.25):
            if not self._geox(m.group("city")):
                continue
            spans.append(
                Span(
                    start=m.start(),
                    end=m.end(),
                    type="ADDRESS",
                    confidence=0.85,
                    priority=CHAIN_PRIORITY["ADDRESS"],
                    rule="address_compact",
                    subtype="CITY",
                )
            )
        return spans

    def _chain(
        self, text: str, tokens: list[Token], pos: int, kind: str, allow_numbers: bool
    ) -> list[Span]:
        boundary = pos + len(window_after(text, pos, CHAIN_WINDOW))
        state = _ChainState(kind=kind, allow_numbers=allow_numbers)
        window_tokens = [t for t in tokens if t.start >= pos and t.end <= boundary][
            :MAX_CHAIN_TOKENS
        ]
        for i, tok in enumerate(window_tokens):
            next_tok = window_tokens[i + 1] if i + 1 < len(window_tokens) else None
            next_low = normalize_yo(next_tok.lower) if next_tok else None
            joined = state.last_end >= 0 and text[state.last_end : tok.start].strip(" \t") == ""
            if not self._step(state, tok, next_low, joined):
                break
        return state.spans

    def _word_subtype_for(
        self, state: _ChainState, text: str, next_low: str | None, joined: bool
    ) -> str | None:
        """Подтип обычного слова; None — цепочку не продолжать."""
        reversed_form = (
            next_low in STREET_WORDS or next_low in REGION_WORDS or next_low in DISTRICT_WORDS
        )
        continues = joined and state.last_kind in ("STREET", "CITY", "REGION")
        if continues:
            return state.last_kind
        if (
            self._is_capitalized(text)
            or text.isupper()
            or self._geox(text)
            or reversed_form
            or state.expect_value
        ):
            subtype = self._word_subtype(state.last_service, next_low, state.kind, self._geox(text))
            if subtype is None and state.last_kind == "CITY" and state.kind == "ADDRESS":
                return "STREET"
            return subtype
        return None

    def _word(self, state: _ChainState, tok: Token, next_low: str | None, joined: bool) -> bool:
        """Обрабатывает обычное слово в цепочке адреса."""
        text = tok.text
        low = tok.lower
        if low in self.service_words or low in PREPOSITIONS or low in SERVICE_FORMS:
            state.last_service = low
            state.prev_low = low
            if low in VALUE_AFTER:
                state.expect_value = True
            return True
        if state.kind == "ADDRESS" and low in self.countries:
            state.add(tok, "COUNTRY")
            state.prev_low = low
            return True
        subtype = self._word_subtype_for(state, text, next_low, joined)
        if subtype is None:
            # Строчное неопознанное слово: цепочка продолжается, только пока
            # ещё ничего не замаскировано.
            return not state.spans
        state.add(tok, subtype)
        state.prev_low = low
        return True

    def _step(self, state: _ChainState, tok: Token, next_low: str | None, joined: bool) -> bool:
        text = tok.text
        if not tok.is_word and not tok.is_number:
            return self._punct(state, text)
        low = tok.lower
        if low in self.stop_words and state.spans:
            return False
        if self.org_markers and self.org_markers.fullmatch(text):
            return False
        if tok.is_number:
            if next_low in YEAR_WORDS:
                return False
            return self._number(state, tok)
        return self._word(state, tok, next_low, joined)

    def _punct(self, state: _ChainState, char: str) -> bool:
        if char in (";", "\n"):
            return False
        if char == "." and state.spans and state.prev_low not in self.service_words:
            return False
        if state.allow_numbers and state.last_kind in ("HOUSE", "BUILDING"):
            if char == "/":
                state.last_service = "к"
            elif char in ("-", "—", "–"):
                state.last_service = "кв"
        return True

    def _number(self, state: _ChainState, tok: Token) -> bool:
        low = tok.lower
        if not state.allow_numbers:
            state.prev_low = low
            return True
        if (
            state.expect_value
            and state.last_service in STREET_WORDS
            and state.last_kind != "STREET"
        ):
            state.add(tok, "STREET")
            state.last_service = None
            return True
        subtype = self._number_subtype(low, state.last_service, state.last_kind, bool(state.spans))
        if subtype is None:
            return not state.spans
        state.add(tok, subtype)
        state.last_service = None
        return True

    def _number_subtype(
        self, low: str, last_service: str | None, last_kind: str | None, masked: bool
    ) -> str | None:
        if last_service in HOUSE_WORDS:
            return "HOUSE"
        if last_service in BUILDING_WORDS:
            return "BUILDING"
        if last_service in APARTMENT_WORDS:
            return "APARTMENT"
        if (
            last_service == "индекс"
            or (len(low) == 6 and not masked)
            or (len(low) == 6 and last_kind == "COUNTRY")
        ):
            return "POSTCODE"
        if len(low) <= 4 and last_kind in ("STREET", "CITY"):
            return "HOUSE"
        if len(low) <= 4 and last_kind in ("HOUSE", "BUILDING"):
            return "APARTMENT"
        return None

    def _word_subtype(
        self, last_service: str | None, next_low: str | None, kind: str, geox: bool
    ) -> str | None:
        if kind == "BIRTH_PLACE":
            return "CITY"
        if last_service in CITY_WORDS:
            return "CITY"
        if last_service in STREET_WORDS or next_low in STREET_WORDS:
            return "STREET"
        if last_service in REGION_WORDS or next_low in REGION_WORDS:
            return "REGION"
        if last_service in DISTRICT_WORDS or next_low in DISTRICT_WORDS:
            return "DISTRICT"
        if last_service == "страна":
            return "COUNTRY"
        if geox:
            return "CITY"
        return None

    @staticmethod
    def _is_capitalized(word: str) -> bool:
        return bool(word) and word[0].isupper()

    def suppress_org(self, text: str, spans: list[Span], options: DetectionOptions) -> list[Span]:
        """Убирает адреса организаций."""
        if not options.contextual or not self.org_markers:
            return spans
        result: list[Span] = []
        for span in spans:
            if span.type != "ADDRESS":
                result.append(span)
                continue
            left = text[max(0, span.start - 90) : span.start]
            org = self.org_markers.search(left)
            if org:
                after_org = left[org.end() :]
                if not self.personal_markers.search(after_org):
                    continue
            if self._org_after(text, span):
                continue
            result.append(span)
        return result

    def _org_after(self, text: str, span: Span) -> bool:
        after = text[span.end : span.end + ORG_AFTER_WINDOW]
        dot = after.find(". ")
        if dot != -1:
            after = after[:dot]
        if self.org_markers.search(after):
            left = text[max(0, span.start - 90) : span.start]
            return not self.personal_markers.search(left)
        return False
