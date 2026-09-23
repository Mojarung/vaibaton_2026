"""Детекция ФИО по словарям, морфологии и структуре.

Любой регистр и падеж, инициалы, латиница. Собирает ФИО из соседних слов,
подавляет публичных персон и адресные сокращения.
"""

from __future__ import annotations

from types import SimpleNamespace

import regex as re

from .gazetteers import HONORIFICS, Gazetteers, Morph, first_like, is_patronymic, surname_like
from .textutil import Token, normalize_yo
from .types import DetectionOptions, Span

# Слово длиной от двух букв (буквы и дефис, слева не буква, не дефис и не точка),
# пробелы, инициалы «буква точка, необязательный пробел, необязательно ещё буква
# точка» с отрицанием буквы справа; и обратный порядок: инициалы, потом фамилия.
INITIALS_RE = re.compile(
    r"(?<![\p{L}\-.])(?P<l>\p{L}[\p{L}\-]{1,})\s+(?P<i>\p{L}\.\s?(?:\p{L}\.)?)(?![\p{L}])"
    r"|(?<![\p{L}\-.])(?P<i2>\p{L}\.\s?(?:\p{L}\.)?\s?)(?P<l2>\p{L}[\p{L}\-]{1,})(?![\p{L}])",
    re.VERSION1,
)

# Внутри кавычек конец предложения (точка, воскл. или вопр. знак с пробелом)
# или две запятые с пробелами — это цитата письма клиента, а не название.
TITLE_BREAK_RE = re.compile(r"[.!?][ \t]|,[ \t]*,", re.VERSION1)

# Пробелы, заглавная и точка, за которой не буква.
TRAILING_INITIAL_RE = re.compile(r"[ \t]+[\p{Lu}]\.(?!\p{L})", re.VERSION1)

# Пробелы и одно из кызы, оглы, оглу, угли, улы, уулу, заде без буквы после.
PATRONYMIC_TAIL_RE = re.compile(
    r"[ \t]+(?:кызы|оглы|оглу|угли|улы|уулу|заде)(?!\p{L})", re.IGNORECASE | re.VERSION1
)

# Имя + кызы/оглы/... (иностранное отчество): «Азер кызы», «Гусейн оглы».
FOREIGN_PATRONYMIC_RE = re.compile(
    r"[ \t]+[\p{Lu}][\p{L}\-]{1,40}[ \t]+(?:кызы|оглы|оглу|угли|улы|уулу|заде)(?!\p{L})",
    re.VERSION1,
)

# Сокращения и слова адреса в конце строки: слово сразу после них топоним,
# а не человек: «ул. Тверской», «г. Орёл», «им. Гагарина».
ADDRESS_PREFIX_RE = re.compile(
    r"(?:ул\.?|улица|пр\.?|просп\.?|пер\.?|переулок|б-р|бульвар|ш\.?|шоссе|"
    r"наб\.?|набережная|пл\.?|площадь|им\.?|имени|г\.?|гор\.?|город|дер\.?|"
    r"пос\.?|ст\.?|метро|станция\w*)[ \t]*$",
    re.IGNORECASE | re.VERSION1,
)

MAX_GAP = 3
TRIGGER_WINDOW = 40
PUBLIC_WINDOW = 80
TITLE_QUOTE_WINDOW = 80
PERSONAL_AFTER_WINDOW = 15
ADDRESS_ABBREVIATIONS = {"г", "д", "с", "п", "х", "к"}


def _last_end(pattern: re.Pattern | None, text: str) -> int:
    """Конец последнего совпадения или -1."""
    if pattern is None:
        return -1
    matches = list(pattern.finditer(text))
    if not matches:
        return -1
    return matches[-1].end()


def _address_abbreviation(initials: str) -> bool:
    """Истина, если в инициалах ровно одна буква и она из адресных сокращений."""
    letters = [c for c in initials if c.isalpha()]
    return len(letters) == 1 and letters[0].lower() in ADDRESS_ABBREVIATIONS


def _in_title_quotes(text: str, start: int, end: int) -> bool:
    """Стоит ли спан внутри «ёлочек» (название книги, фильма, организации)."""
    left_start = max(0, start - TITLE_QUOTE_WINDOW)
    left = text[left_start:start]
    right = text[end : end + TITLE_QUOTE_WINDOW]
    lq = left.rfind("«")
    if lq == -1:
        return False
    if "»" in left[lq:]:
        return False
    rq = right.find("»")
    if rq == -1:
        return False
    if "«" in right[:rq]:
        return False
    inside = text[left_start + lq : end + rq]
    return not TITLE_BREAK_RE.search(inside)


class PersonDetector:
    """Собирает ФИО из соседних слов, инициалов и латинских имён."""

    def __init__(self, gaz: Gazetteers, morph: Morph | None):
        self.gaz = gaz
        self.morph = morph
        self.person_triggers = gaz.person_triggers
        self.personal_markers = gaz.personal_markers
        self.public_markers = gaz.public_markers
        self.card_context = gaz.card_context
        self.public_figures = gaz.public_figures

    def _features(self, token: Token) -> tuple[float, float, bool, bool, bool]:
        """Оценка имени, фамилии, отчество ли, с заглавной ли, латиница ли."""
        text = token.text
        latin = self._is_latin(text)
        if latin:
            return (0.0, 0.0, False, self._capitalized(text), True)
        name = first_like(text, self.gaz, self.morph)
        surname = surname_like(text, self.gaz, self.morph)
        patr = is_patronymic(text, self.morph)
        cap = self._capitalized(text)
        return (name, surname, patr, cap, False)

    def _surname_slot(self, word: str, score: float, capitalized: bool) -> bool:
        """Годится ли слово на место фамилии рядом с именем и отчеством."""
        if score >= 0.5:
            return True
        if word.lower() in HONORIFICS:
            return False
        if not capitalized or self.morph is None:
            return capitalized
        pos = self.morph.pos(word)
        if pos in ("ADJF", "ADJS"):
            return True
        if pos in (None, "", "UNKN") or pos == "NOUN":
            return not self.morph.is_common(word)
        return False

    def _adjacent(self, text: str, left: int, right: int, newline: bool) -> bool:
        gap = text[left:right]
        if not (1 <= len(gap) <= MAX_GAP):
            return False
        allowed = " \t\n" if newline else " \t"
        return all(c in allowed for c in gap)

    def _group(self, text: str, words: list, i: int, newline: bool) -> list:
        result = [words[i]]
        j = i
        while len(result) < 3 and j + 1 < len(words):
            nxt = words[j + 1]
            if not self._adjacent(text, words[j][0].end, nxt[0].start, newline):
                break
            result.append(nxt)
            j += 1
        return result

    def _triggered(self, text: str, start: int) -> bool:
        left = text[max(0, start - TRIGGER_WINDOW) : start]
        return bool(self.person_triggers and self.person_triggers.search(left))

    def _public_marker_context(self, text: str, start: int, end: int) -> bool | None:
        """Маркеры публичности/персональности вокруг спана; None — неопределённо."""
        left = text[max(0, start - PUBLIC_WINDOW) : start]
        right = text[end : end + PERSONAL_AFTER_WINDOW]
        personal_left = _last_end(self.personal_markers, left)
        public_left = _last_end(self.public_markers, left)
        personal_right = self.personal_markers and self.personal_markers.search(right)
        if personal_right:
            return False
        if public_left > personal_left:
            return True
        if personal_left >= 0:
            return False
        return None

    def _public(self, text: str, start: int, end: int, words: list) -> bool:
        """Публичная ли это персона."""
        if _in_title_quotes(text, start, end):
            return True
        marker = self._public_marker_context(text, start, end)
        if marker is not None:
            return marker
        if len(words) == 1:
            return False
        joined = normalize_yo(" ".join(w[0].text for w in words).lower())
        if joined in self.public_figures:
            return True
        norm = " ".join(self._normal_form(w[0].text) for w in words)
        if norm in self.public_figures:
            return True
        first = words[0][0].text
        if self.public_markers and self.public_markers.fullmatch(first):
            for w in words[1:]:
                if self._public_surname(w[0].text):
                    return True
        return False

    def _public_surname(self, word: str) -> bool:
        if word in self.public_figures:
            return True
        return self._normal_form(word) in self.public_figures

    def _normal_form(self, word: str) -> str:
        if self.morph is None:
            return word
        return self.morph.normal_form(word)

    def _is_common(self, word: str) -> bool:
        if self.morph is None:
            return False
        return self.morph.is_common(word)

    def detect(self, text: str, tokens: list[Token], options: DetectionOptions) -> list[Span]:
        if "PERSON" not in options.entity_types and "CARDHOLDER" not in options.entity_types:
            return []
        words = [(tok, self._features(tok)) for tok in tokens if tok.is_word and len(tok.text) >= 2]
        spans: list[Span] = []
        i = 0
        while i < len(words):
            res = self._match_at(text, words, i, options)
            if res is not None:
                span, count = res
                spans.append(span)
                i += count
            else:
                i += 1
        spans.extend(self._initials(text, options))
        return spans

    def _match_at(self, text: str, words: list, i: int, options: DetectionOptions):
        group = self._group(text, words, i, False)
        if not group:
            return None
        if group[0][1][4]:
            latin_group = []
            for w in group:
                if w[1][4]:
                    latin_group.append(w)
                else:
                    break
            return self._latin(text, latin_group, options)
        if any(w[1][4] for w in group[1:]):
            return None
        res = self._match_cyrillic(text, group, options)
        if res is not None:
            return res
        if len(group) < 3:
            group_nl = self._group(text, words, i, True)
            if len(group_nl) == 3:
                return self._match_full(text, group_nl, options)
        return None

    def _emit(
        self, text: str, group: list, count: int, confidence: float, options: DetectionOptions
    ):
        start = group[0][0].start
        end = group[count - 1][0].end
        left = text[max(0, start - 20) : start]
        if ADDRESS_PREFIX_RE.search(left):
            return None
        if options.contextual and self._public(text, start, end, group[:count]):
            return None
        m = PATRONYMIC_TAIL_RE.match(text, end)
        if m:
            end = m.end()
        else:
            m = FOREIGN_PATRONYMIC_RE.match(text, end)
            if m:
                end = m.end()
        span = Span(
            start=start,
            end=end,
            type="PERSON",
            confidence=confidence,
            priority=100,
            rule="person_structure",
        )
        return (span, count)

    def _match_full(self, text: str, group: list, options: DetectionOptions):
        if len(group) != 3:
            return None
        w0, w1, w2 = group
        f0, f1, f2 = w0[1], w1[1], w2[1]
        if f1[0] >= 0.5 and f2[2] and self._surname_slot(w0[0].text, f0[1], f0[3]):
            conf = 0.98 if f0[1] >= 0.8 else 0.93
            return self._emit(text, group, 3, conf, options)
        if f0[0] >= 0.5 and f1[2] and self._surname_slot(w2[0].text, f2[1], f2[3]):
            conf = 0.98 if f2[1] >= 0.8 else 0.93
            return self._emit(text, group, 3, conf, options)
        return None

    def _match_cyrillic(self, text: str, group: list, options: DetectionOptions):
        if len(group) == 3:
            res = self._match_full(text, group, options)
            if res is not None:
                return res
            if self._public(text, group[0][0].start, group[2][0].end, group):
                return None
        if len(group) >= 2:
            res = self._match_pair(text, group, options)
            if res is not None:
                return res
        return self._match_single(text, [group[0]], options)

    def _match_name_patronymic(self, text: str, group: list, options: DetectionOptions):
        """Имя + отчество: «Иван Иванович»."""
        w0, w1 = group[0], group[1]
        end = w1[0].end
        count = 2
        m = TRAILING_INITIAL_RE.match(text, end)
        if m:
            end = m.end()
            count = 3 if len(group) >= 3 else 2
        span = Span(
            start=w0[0].start,
            end=end,
            type="PERSON",
            confidence=0.95,
            priority=100,
            rule="person_structure",
        )
        if options.contextual and self._public(text, span.start, span.end, group[:count]):
            return None
        return (span, count)

    def _match_surname_name(
        self, text: str, group: list, options: DetectionOptions, ok: bool, weak: bool, f0, f1
    ):
        """Фамилия + имя по триггеру или сильным оценкам."""
        if not ok or not (
            (f0[1] >= 0.6 and f1[0] >= 0.8) or (f0[1] >= 0.8 and f1[0] >= 0.5) or weak
        ):
            return None
        conf = 0.92 if f0[1] >= 0.8 else 0.85
        res = self._emit(text, group, 2, conf, options)
        if res is not None:
            return self._extend_foreign(group, res)
        return None

    def _match_name_surname(
        self, text: str, group: list, options: DetectionOptions, ok: bool, f0, f1
    ):
        """Имя + фамилия."""
        if not ok or not ((f0[0] >= 0.8 and f1[1] >= 0.6) or (f0[0] >= 0.5 and f1[1] >= 0.8)):
            return None
        conf = 0.92 if f1[1] >= 0.8 else 0.85
        return self._emit(text, group, 2, conf, options)

    def _match_pair(self, text: str, group: list, options: DetectionOptions):
        w0, w1 = group[0], group[1]
        f0, f1 = w0[1], w1[1]
        if f0[0] >= 0.5 and f1[2]:
            return self._match_name_patronymic(text, group, options)
        triggered = self._triggered(text, w0[0].start)
        strong = (f0[0] == 1.0 and f1[1] >= 0.8) or (f0[1] >= 0.8 and f1[0] == 1.0)
        ok = (f0[3] and f1[3]) or triggered or strong
        weak = triggered and f0[1] >= 0.5 and f1[0] >= 0.8
        res = self._match_surname_name(text, group, options, ok, weak, f0, f1)
        if res is not None:
            return res
        return self._match_name_surname(text, group, options, ok, f0, f1)

    def _extend_foreign(self, group: list, res):
        span, count = res
        if len(group) >= 3:
            w0, w2 = group[0], group[2]
            f0, f2 = w0[1], w2[1]
            if w0[0].text.lower() in self.gaz.foreign_surnames and f2[0] >= 0.5 and f0[3] == f2[3]:
                span = Span(
                    start=span.start,
                    end=w2[0].end,
                    type=span.type,
                    confidence=span.confidence,
                    priority=span.priority,
                    rule=span.rule,
                    subtype=span.subtype,
                )
                count = 3
        return (span, count)

    def _match_single(self, text: str, group: list, options: DetectionOptions):
        w0 = group[0]
        f0 = w0[1]
        name, surname, patr, cap, latin = f0
        if latin or not cap:
            return None
        if not self._triggered(text, w0[0].start):
            return None
        if name >= 0.8 or (surname >= 0.8 and not self._is_common(w0[0].text)) or patr:
            return self._emit(text, group, 1, 0.85, options)
        return None

    def _card_context(self, text: str, start: int, end: int) -> bool:
        """Есть ли контекст карты слева или справа от спана."""
        left = text[max(0, start - 120) : start]
        right = text[end : end + 40]
        return bool(
            self.card_context
            and (self.card_context.search(left) or self.card_context.search(right))
        )

    def _latin_plausible(self, text: str, group: list, count: int, start: int) -> bool:
        """Годится ли латинская пара без контекста карты."""
        has_surname = any(self._latin_surname(w[0].text) for w in group[:count])
        return has_surname or self._triggered(text, start)

    def _latin(self, text: str, group: list, options: DetectionOptions):
        if len(group) < 2:
            return None
        w0, w1 = group[0], group[1]
        f0, f1 = w0[1], w1[1]
        if not (f0[3] and f1[3]):
            return None
        if not (self._latin_name(w0[0].text) or self._latin_name(w1[0].text)):
            return None
        count = 2
        if len(group) >= 3 and group[2][1][3]:
            count = 3
        start = w0[0].start
        end = group[count - 1][0].end
        card = self._card_context(text, start, end)
        if not card and not self._latin_plausible(text, group, count, start):
            return None
        span_type = "CARDHOLDER" if card else "PERSON"
        if span_type not in options.entity_types:
            return None
        span = Span(
            start=start, end=end, type=span_type, confidence=0.85, priority=95, rule="person_latin"
        )
        return (span, count)

    def _latin_name(self, word: str) -> bool:
        return word.lower() in self.gaz.latin_first_names

    def _latin_surname(self, word: str) -> bool:
        return self.gaz.is_latin_surname(word)

    def _initials_plausible(self, text: str, start: int, score: float, common: bool) -> bool:
        """Годится ли фамилия по оценке и триггеру."""
        if score < 0.6:
            return self._triggered(text, start) and not common
        return not (common and score < 0.8)

    def _initials_candidate(self, text: str, m, options: DetectionOptions) -> Span | None:
        """Проверяет одно совпадение инициалов; возвращает спан или None."""
        surname = m.group("l") or m.group("l2")
        initials = m.group("i") or m.group("i2")
        if surname is None or initials is None:
            return None
        start = m.start()
        end = m.end()
        while end > start and text[end - 1] in " \t":
            end -= 1
        if _address_abbreviation(initials):
            return None
        if len(surname) == 2 and surname.lower() not in self.gaz.foreign_surnames:
            return None
        score = surname_like(surname, self.gaz, self.morph)
        common = self._is_common(surname)
        if not self._initials_plausible(text, start, score, common):
            return None
        if options.contextual and self._public(
            text, start, end, [(SimpleNamespace(text=surname),)]
        ):
            return None
        return Span(
            start=start,
            end=end,
            type="PERSON",
            confidence=0.9,
            priority=100,
            rule="person_initials",
        )

    def _initials(self, text: str, options: DetectionOptions) -> list[Span]:
        if "PERSON" not in options.entity_types:
            return []
        spans: list[Span] = []
        for m in INITIALS_RE.finditer(text, overlapped=True, timeout=0.25):
            cand = self._initials_candidate(text, m, options)
            if cand is not None:
                spans.append(cand)
        return spans

    @staticmethod
    def _capitalized(word: str) -> bool:
        return bool(word) and (word[0].isupper() or word.isupper())

    @staticmethod
    def _is_latin(word: str) -> bool:
        return bool(word) and all("a" <= c.lower() <= "z" for c in word)
