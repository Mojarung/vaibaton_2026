"""Токенизация и окна контекста. Смещения всегда по исходной строке."""

from __future__ import annotations

from dataclasses import dataclass

import regex as re

# Слово (буква, дальше буквы, а апостроф или дефис только если за ними снова
# буква), либо последовательность цифр, либо одиночный непробельный символ.
TOKEN_RE = re.compile(
    r"[\p{L}](?:[\p{L}'’\-](?=[\p{L}])|[\p{L}])*|\d+|[^\s]",
    re.VERSION1,
)

# Граница записи: перевод строки и точка с запятой.
RECORD_BREAK = "\n;"


@dataclass(frozen=True, slots=True)
class Token:
    """Токен с границами в исходной строке."""

    start: int
    end: int
    text: str

    @property
    def is_word(self) -> bool:
        return bool(self.text) and self.text[0].isalpha()

    @property
    def is_number(self) -> bool:
        return bool(self.text) and self.text.isdigit()

    @property
    def is_capitalized(self) -> bool:
        return bool(self.text) and self.text[0].isupper()

    @property
    def is_upper(self) -> bool:
        return len(self.text) > 1 and self.text.isupper()

    @property
    def is_latin(self) -> bool:
        return all(ord(c) < 128 for c in self.text)

    @property
    def lower(self) -> str:
        return self.text.lower()


def tokenize(text: str) -> list[Token]:
    return [Token(m.start(), m.end(), m.group()) for m in TOKEN_RE.finditer(text)]


def window_before(text: str, start: int, radius: int) -> str:
    """Контекст слева, не пересекающий границу записи."""
    lo = max(0, start - radius)
    cut = text.rfind("\n", lo, start)
    if cut == -1:
        cut = text.rfind(";", lo, start)
    if cut != -1:
        lo = cut + 1
    return text[lo:start]


def window_after(text: str, start: int, radius: int) -> str:
    """Контекст справа, обрезанный по первой границе записи."""
    hi = min(len(text), start + radius)
    cut = text.find("\n", start, hi)
    if cut == -1:
        cut = text.find(";", start, hi)
    if cut != -1:
        hi = cut
    return text[start:hi]


def same_record(text: str, a: int, b: int) -> bool:
    """Истина, если между позициями нет границы записи."""
    lo, hi = (a, b) if a <= b else (b, a)
    return "\n" not in text[lo:hi] and ";" not in text[lo:hi]


def normalize_yo(text: str) -> str:
    return text.replace("ё", "е").replace("Ё", "Е")
