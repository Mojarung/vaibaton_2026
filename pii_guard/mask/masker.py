"""Маскировщик и сессия маски."""

from __future__ import annotations

import random
import secrets
from collections import Counter
from dataclasses import dataclass

from ..core.types import Span, TypeRegistry
from .synthetic import synthesize


@dataclass(slots=True)
class Entry:
    """Один замаскированный фрагмент."""

    start: int
    end: int
    token: str
    original: str
    type: str
    subtype: str | None
    source_start: int = 0
    source_end: int = 0


@dataclass(slots=True)
class MaskResult:
    """Результат маскирования."""

    text: str
    entries: list[Entry]
    counts: Counter


def _partial_email(value: str) -> str | None:
    """Частичная маска email: первая буква локальной части, остальное звёзды."""
    local, _, domain = value.partition("@")
    if not local:
        return None
    head = local[0]
    stars = "*" * max(1, len(local) - 1)
    return f"{head}{stars}@{domain}"


def _partial_card(value: str) -> str | None:
    """Частичная маска карты: первые и последние четыре цифры."""
    d = "".join(c for c in value if c.isdigit())
    if len(d) < 13:
        return None
    return f"{d[:4]}{'*' * (len(d) - 8)}{d[-4:]}"


def _partial_generic(value: str) -> str:
    """Маска по умолчанию: все буквы и цифры заменяются звёздами."""
    return "".join("*" if c.isalnum() else c for c in value)


class Masker:
    """Держит реестр типов и отдаёт сессии маски."""

    def __init__(self, registry: TypeRegistry) -> None:
        self.registry = registry

    def session(self, mode: str, type_modes: dict | None = None, lang: str = "ru") -> MaskSession:
        return MaskSession(self.registry, mode, type_modes or {}, lang)


class MaskSession:
    """Состояние на один запрос или диалог: одинаковое значение — один токен."""

    def __init__(self, registry: TypeRegistry, mode: str, type_modes: dict, lang: str) -> None:
        self.registry = registry
        self.mode = mode
        self.type_modes = type_modes
        self.lang = lang
        self.assigned: dict[tuple[str, str], str] = {}
        self.used: set[str] = set()
        self.counts: Counter = Counter()
        self.token_map: dict[str, str] = {}
        self.rng = random.Random(secrets.randbits(64))

    def _mode_for(self, span_type: str) -> str:
        return self.type_modes.get(span_type, self.mode)

    def _label(self, span: Span) -> str:
        return self.registry.label(span.type, span.subtype, self.lang)

    def _token(self, span: Span, label: str, value: str, text: str) -> str:
        mode = self._mode_for(span.type)
        key = (label, value)
        if key in self.assigned:
            return self.assigned[key]
        token = self._build_token(span, label, value, text, mode)
        if mode in ("placeholder", "synthetic") or token.startswith("["):
            self.assigned[key] = token
            self.used.add(token)
            self.token_map[token] = value
        return token

    def _build_token(self, span: Span, label: str, value: str, text: str, mode: str) -> str:
        if mode == "redact":
            return f"[{label}]"
        if mode == "stars":
            return "".join("*" if c.isalnum() else c for c in value)
        if mode == "partial":
            return self._partial(span, value)
        if mode == "synthetic":
            for _ in range(20):
                cand = synthesize(span.type, span.subtype, value, self.rng)
                if cand != value and cand not in self.used and cand not in text:
                    return cand
        return self._placeholder(label, text)

    def _partial(self, span: Span, value: str) -> str:
        if span.type == "EMAIL":
            res = _partial_email(value)
            if res is not None:
                return res
        alnum = sum(1 for c in value if c.isalnum())
        if alnum <= 4:
            return _partial_generic(value)
        if span.type == "BANK_CARD":
            res = _partial_card(value)
            if res is not None:
                return res
        return _partial_generic(value)

    def _placeholder(self, label: str, text: str) -> str:
        n = self.counts[label]
        while True:
            n += 1
            cand = f"[{label}_{n}]"
            if cand not in text and cand not in self.used:
                self.counts[label] = n
                return cand

    def mask(self, text: str, spans: list[Span]) -> MaskResult:
        out: list[str] = []
        entries: list[Entry] = []
        counts: Counter = Counter()
        pos = 0
        result_len = 0
        for span in spans:
            if span.start > pos:
                chunk = text[pos : span.start]
                out.append(chunk)
                result_len += len(chunk)
            value = text[span.start : span.end]
            label = self._label(span)
            token = self._token(span, label, value, text)
            out.append(token)
            entries.append(
                Entry(
                    start=result_len,
                    end=result_len + len(token),
                    token=token,
                    original=value,
                    type=span.type,
                    subtype=span.subtype,
                    source_start=span.start,
                    source_end=span.end,
                )
            )
            result_len += len(token)
            counts[span.type] += 1
            pos = span.end
        if pos < len(text):
            chunk = text[pos:]
            out.append(chunk)
            result_len += len(chunk)
        return MaskResult(text="".join(out), entries=entries, counts=counts)
