"""Словари имён, фамилий, стран, публичных персон и морфология.

Словари читаются из config/gazetteers, контекстные маркеры из context.yaml.
Morph — тонкая обёртка над pymorphy3 с кэшами.
"""

from __future__ import annotations

import gzip
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import regex as re
import yaml

# Окончание отчества в конце слова.
PATRONYMIC_RE = re.compile(
    r"(?:(?:ович|евич|ьич|ич|овна|евна|ична|инична|ьевна|ьевич)(?:а|у|ем|ом|ой|е|ы|и)?"
    r"|(?:овн|евн|ичн|иничн|ьевн)(?:ой|ою|у|е|ы)?)$",
    re.IGNORECASE | re.VERSION1,
)

# Типичные фамильные окончания в конце слова.
SURNAME_SUFFIX_RE = re.compile(
    r"(?:ов|ев|ёв|ин|ын|ский|ская|цкий|цкая|ко|енко|ук|юк|чук|дзе|швили|ян|янц|"
    r"ова|ева|ёва|ина|ына|ого|ому|ым|ой|ую|их|ых|ские|ских|ским|ей)$",
    re.IGNORECASE | re.VERSION1,
)

# Базовая транслитерация по буквам.
TRANSLIT = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "kh",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "shch",
    "ъ": "",
    "ь": "",
    "ы": "y",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}

# ICAO Doc 9303: так пишут загранпаспорта РФ с 2013 года.
TRANSLIT_ICAO = dict(TRANSLIT)
TRANSLIT_ICAO.update({"й": "i", "я": "ia", "ю": "iu", "ъ": "ie"})

# Привычная английская запись.
TRANSLIT_EN = dict(TRANSLIT)
TRANSLIT_EN.update({"й": "y", "я": "ya", "ю": "yu", "х": "h", "ий": "y"})

# Фамильные окончания латинских слов.
LATIN_SURNAME_RE = re.compile(
    r"(?:ov|ev|yov|in|yn|sky|skiy|skii|skaya|skaia|tsky|enko|ko|uk|yuk|chuk|"
    r"dze|shvili|yan|ian|ova|eva|ina|yna|ovich|evich|ich)$",
    re.IGNORECASE | re.VERSION1,
)

# Части речи, которые не бывают именем или фамилией.
NON_NAME_POS = {
    "VERB",
    "INFN",
    "ADVB",
    "PRTF",
    "PRTS",
    "GRND",
    "PREP",
    "CONJ",
    "PRCL",
    "INTJ",
    "NPRO",
    "NUMR",
    "PRED",
}

# Обращения, которые в спан ФИО не входят.
HONORIFICS = {
    "уважаемый",
    "уважаемая",
    "уважаемые",
    "уважаемого",
    "уважаемой",
    "уважаемому",
    "дорогой",
    "дорогая",
    "дорогие",
    "милый",
    "милая",
    "любимый",
    "любимая",
    "господин",
    "госпожа",
    "товарищ",
    "мистер",
    "миссис",
}


def translit(word: str) -> str:
    """Транслитерация по базовой таблице в нижнем регистре."""
    return "".join(TRANSLIT.get(c, c) for c in word.lower())


def translit_variants(word: str) -> set[str]:
    """Все варианты транслитерации слова (ASCII)."""
    w = word.lower().replace("ьи", "и").replace("ье", "е")
    variants: set[str] = set()
    for table in (TRANSLIT, TRANSLIT_ICAO, TRANSLIT_EN):
        base = w.replace("ий", "y") if "ий" in table else w
        out = "".join(table.get(c, c) for c in base)
        if out.isascii():
            variants.add(out)
    extra: set[str] = set()
    for v in variants:
        if "ks" in v:
            extra.add(v.replace("ks", "x"))
    variants |= extra
    return variants


def _read_words(path: str | Path) -> frozenset[str]:
    """Словарь: одно слово в строке, после # комментарий."""
    p = Path(path)
    if not p.is_file():
        gz = Path(str(p) + ".gz")
        if not gz.is_file():
            return frozenset()
        with gzip.open(gz, "rt", encoding="utf-8") as f:
            lines = list(f)
    else:
        with open(p, encoding="utf-8") as f:
            lines = list(f)
    words: set[str] = set()
    for line in lines:
        word = line.split("#", 1)[0].strip().lower().replace("ё", "е")
        if len(word) >= 2:
            words.add(word)
    return frozenset(words)


def _compile_list(patterns: list[str]) -> re.Pattern | None:
    if not patterns:
        return None
    return re.compile("|".join(f"(?:{p})" for p in patterns), re.IGNORECASE | re.VERSION1)


@dataclass(slots=True)
class Gazetteers:
    """Словари и скомпилированные контекстные маркеры."""

    first_names: frozenset[str]
    maybe_first_names: frozenset[str]
    surnames: frozenset[str]
    latin_first_names: frozenset[str]
    countries: frozenset[str]
    public_figures: frozenset[str]
    public_markers: re.Pattern | None
    personal_markers: re.Pattern | None
    org_markers: re.Pattern | None
    person_triggers: re.Pattern | None
    card_context: re.Pattern | None
    sentence_start_words: frozenset[str] = field(default_factory=frozenset)
    foreign_surnames: frozenset[str] = field(default_factory=frozenset)
    foreign_first: frozenset[str] = field(default_factory=frozenset)

    @classmethod
    def load(cls, gazetteers_dir: str | Path, context_path: str | Path) -> Gazetteers:
        d = Path(gazetteers_dir)
        first_names = _read_words(d / "first_names.txt") | _read_words(d / "first_names_extra.txt")
        surnames = _read_words(d / "surnames.txt") | _read_words(d / "surnames_extra.txt")
        latin_first = set(_read_words(d / "latin_first_names.txt"))
        for name in first_names:
            latin_first |= translit_variants(name)
        countries = _read_words(d / "countries.txt")
        public_figures = _read_words(d / "public_figures.txt")
        maybe_first = _read_words(d / "maybe_first_names.txt")
        foreign_surnames = _read_words(d / "foreign_surnames.txt")
        foreign_first = _read_words(d / "foreign_first_names.txt")
        with open(context_path, encoding="utf-8") as f:
            ctx = yaml.safe_load(f) or {}
        return cls(
            first_names=frozenset(first_names),
            maybe_first_names=frozenset(maybe_first),
            surnames=frozenset(surnames),
            latin_first_names=frozenset(latin_first),
            countries=frozenset(countries),
            public_figures=frozenset(public_figures),
            public_markers=_compile_list(ctx.get("public_person_markers") or []),
            personal_markers=_compile_list(ctx.get("personal_markers") or []),
            org_markers=_compile_list(ctx.get("org_markers") or []),
            person_triggers=_compile_list(ctx.get("person_triggers") or []),
            card_context=_compile_list(ctx.get("card_context") or []),
            foreign_surnames=frozenset(foreign_surnames),
            foreign_first=frozenset(foreign_first),
        )

    def is_foreign_surname(self, word: str) -> bool:
        if not word:
            return False
        if not (word[0].isupper() or len(word) >= 3):
            return False
        return word.lower().replace("ё", "е") in self.foreign_surnames

    def is_foreign_first(self, word: str) -> bool:
        if not word:
            return False
        if not (word[0].isupper() or len(word) >= 3):
            return False
        return word.lower().replace("ё", "е") in self.foreign_first

    def is_first(self, word: str) -> bool:
        return word.lower().replace("ё", "е") in self.first_names

    def is_maybe_first(self, word: str) -> bool:
        return word.lower().replace("ё", "е") in self.maybe_first_names

    def is_surname(self, word: str) -> bool:
        return len(word) >= 3 and word.lower().replace("ё", "е") in self.surnames

    def is_latin_first(self, word: str) -> bool:
        return word.lower().replace("ё", "е") in self.latin_first_names

    @staticmethod
    def is_latin_surname(word: str) -> bool:
        return len(word) >= 4 and bool(LATIN_SURNAME_RE.search(word))

    def is_public_figure(self, phrase: str) -> bool:
        low = phrase.lower().replace("ё", "е")
        if low in self.public_figures:
            return True
        return any(w in self.public_figures for w in low.split())

    def is_country(self, phrase: str) -> bool:
        low = phrase.lower().replace("ё", "е").strip(" .,")
        return low in self.countries


class Morph:
    """Тонкая обёртка над pymorphy3.MorphAnalyzer с кэшами."""

    def __init__(self) -> None:
        import pymorphy3  # noqa: PLC0415 — ленивая загрузка тяжёлой морфологии

        self._analyzer = pymorphy3.MorphAnalyzer()

    @lru_cache(maxsize=200_000)  # noqa: B019
    def tags(self, word: str) -> tuple[float, float, float, float, str]:
        """Суммы score разборов с тегами Name, Surn, Patr, Geox и POS лучшего."""
        parses = self._analyzer.parse(word)
        name = surn = patr = geox = 0.0
        best = None
        best_score = -1.0
        for p in parses:
            score = p.score
            if score > best_score:
                best_score = score
                best = p
            tag = p.tag
            if "Name" in tag:
                name += score
            if "Surn" in tag:
                surn += score
            if "Patr" in tag:
                patr += score
            if "Geox" in tag:
                geox += score
        pos = str(best.tag.POS) if best is not None else ""
        return (round(name, 3), round(surn, 3), round(patr, 3), round(geox, 3), pos)

    @lru_cache(maxsize=100_000)  # noqa: B019
    def name_lemmas(self, word: str) -> frozenset[str]:
        lemmas: set[str] = set()
        for p in self._analyzer.parse(word):
            if "Name" in p.tag:
                lemmas.add(p.normal_form)
        return frozenset(lemmas)

    @lru_cache(maxsize=200_000)  # noqa: B019
    def is_common(self, word: str) -> bool:
        low = word.lower()
        if not self._analyzer.word_is_known(low):
            return False
        name, surn, patr, geox, _ = self.tags(word)
        return (name + surn + patr + geox) < 0.05

    @lru_cache(maxsize=200_000)  # noqa: B019
    def normal_form(self, word: str) -> str:
        parses = self._analyzer.parse(word)
        if not parses:
            return word.lower()
        return parses[0].normal_form

    def pos(self, word: str) -> str:
        return self.tags(word)[4]

    def geox(self, word: str) -> float:
        return self.tags(word)[3]


def _pos_blocks(word: str, morph: Morph | None) -> bool:
    """Истина для обращения, а при морфологии для части речи из NON_NAME_POS."""
    if word.lower() in HONORIFICS:
        return True
    if morph is None:
        return False
    pos = morph.pos(word)
    if pos in NON_NAME_POS:
        name, surn, patr, _, _ = morph.tags(word)
        return max(name, surn, patr) < 0.3
    return False


def is_patronymic(word: str, morph: Morph | None) -> bool:
    if len(word) < 5:
        return False
    if PATRONYMIC_RE.search(word):
        return True
    if morph is None:
        return False
    return morph.tags(word)[2] >= 0.5


def _surname_morph(word: str, gaz: Gazetteers, morph: Morph | None) -> float | None:
    """Оценка фамилии по морфологии; None — морфология не решает."""
    if morph is None:
        return None
    name, surn, _, geox, _ = morph.tags(word)
    if surn >= 0.3:
        return max(0.8, surn)
    if surn >= 0.2:
        return 0.7
    if geox >= 0.5 and name < 0.5:
        return 0.3 if gaz.is_surname(word) else 0.0
    if gaz.is_surname(word) and morph.is_common(word):
        return 0.5
    return None


def surname_like(word: str, gaz: Gazetteers, morph: Morph | None) -> float:
    """Оценка 0..1, насколько слово похоже на фамилию."""
    if gaz.is_foreign_surname(word):
        return 0.8
    if _pos_blocks(word, morph):
        return 0.0
    morph_score = _surname_morph(word, gaz, morph)
    if morph_score is not None:
        return morph_score
    if gaz.is_surname(word):
        return 1.0
    if len(word) >= 4 and SURNAME_SUFFIX_RE.search(word):
        return 0.6
    return 0.0


def _first_dictionary(word: str, morph: Morph | None) -> float:
    """Оценка словарного имени; 1.0, если морфология не противоречит."""
    if morph is not None:
        name, _, _, _, pos = morph.tags(word)
        if name < 0.35 and pos == "NOUN":
            return 0.5
    return 1.0


def _first_morph(word: str, gaz: Gazetteers, morph: Morph | None) -> float | None:
    """Оценка имени по морфологии; None — морфология не решает."""
    if morph is None:
        return None
    name, _, _, _, _ = morph.tags(word)
    if name >= 0.5:
        return 0.8
    for lemma in morph.name_lemmas(word):
        if lemma in gaz.first_names:
            return 0.7
    return None


def first_like(word: str, gaz: Gazetteers, morph: Morph | None) -> float:
    """Оценка 0..1, насколько слово похоже на имя."""
    if gaz.is_foreign_first(word) and not gaz.is_first(word):
        return 0.7
    if _pos_blocks(word, morph):
        return 0.0
    if gaz.is_first(word):
        return _first_dictionary(word, morph)
    morph_score = _first_morph(word, gaz, morph)
    if morph_score is not None:
        return morph_score
    if gaz.is_maybe_first(word):
        return 0.5
    return 0.0
