"""Восстановление исходного текста из маски."""

from __future__ import annotations

import regex as re


def restore_positional(masked: str, entries: list[tuple[int, int, str]]) -> str:
    """Собирает строку обратно по позициям в координатах маски."""
    if not entries:
        return masked
    out: list[str] = []
    pos = 0
    for start, end, original in entries:
        if start > pos:
            out.append(masked[pos:start])
        out.append(original)
        pos = end
    if pos < len(masked):
        out.append(masked[pos:])
    return "".join(out)


def restore_tokens(text: str, token_map: dict[str, str]) -> tuple[str, int]:
    """Заменяет токены на оригиналы. Возвращает (текст, число замен)."""
    if not token_map:
        return text, 0
    tokens = sorted(token_map, key=len, reverse=True)
    pattern = re.compile("|".join(re.escape(t) for t in tokens), re.VERSION1)
    count = 0

    def _sub(m: re.Match) -> str:
        nonlocal count
        count += 1
        return token_map[m.group()]

    return pattern.sub(_sub, text), count
