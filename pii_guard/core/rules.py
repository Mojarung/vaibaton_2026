"""Правила из YAML: новый тип ПДн это новый файл в config/rules без правки кода.

Правила валидируются pydantic-моделями, макросы раскрываются, паттерны
компилируются модулем regex с таймаутом на поиск.
"""

from __future__ import annotations

import re as std_re
from dataclasses import dataclass
from pathlib import Path

import regex as re
import yaml
from pydantic import BaseModel, Field, field_validator

from .types import TypeRegistry
from .validators import VALIDATORS

FLAGS = re.IGNORECASE | re.VERSION1
# Таймаут на паттерн, защита от катастрофического бэктрекинга.
PATTERN_TIMEOUT = 0.25

GAZETTEER_CHECKS = {"countries_shrink", "latin_first_any", "geox", "no_verbs"}

_MACRO_RE = std_re.compile(r"\{([A-Z0-9_]+)\}")


class RuleSpec(BaseModel):
    """Одно правило из YAML."""

    model_config = {"extra": "forbid"}

    id: str = Field(min_length=1, max_length=64)
    pattern: str = Field(min_length=1)
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    priority: int = Field(default=50, ge=0, le=200)
    validators: list[str] = Field(default_factory=list)
    negative_context: list[str] = Field(default_factory=list)
    negative_window: int = Field(default=60, ge=0, le=500)
    subtype: str | None = None
    groups: list[str] | None = None
    policy: str | None = None
    gazetteer_check: str | None = None
    requires_any: list[str] = Field(default_factory=list)
    requires_regex: str | None = None
    min_digits: int = Field(default=0, ge=0, le=64)
    negative_after: int = Field(default=20, ge=0, le=200)
    required_context: list[str] = Field(default_factory=list)
    required_window: int = Field(default=60, ge=0, le=500)

    @field_validator("gazetteer_check")
    @classmethod
    def _check_gazetteer(cls, v: str | None) -> str | None:
        if v is not None and v not in GAZETTEER_CHECKS:
            raise ValueError(f"Неизвестная проверка по словарю: {v}")
        return v

    @field_validator("validators")
    @classmethod
    def _check_validators(cls, v: list[str]) -> list[str]:
        unknown = [name for name in v if name not in VALIDATORS]
        if unknown:
            raise ValueError(f"Неизвестные валидаторы: {', '.join(unknown)}")
        return v


class RuleFile(BaseModel):
    """Файл правил одного типа."""

    model_config = {"extra": "forbid"}

    type: str = Field(pattern=r"^[A-Z][A-Z0-9_]*$")
    label_ru: str | None = None
    label_en: str | None = None
    enabled: bool = True
    rules: list[RuleSpec] = Field(default_factory=list)


@dataclass(frozen=True, slots=True)
class CompiledRule:
    """Скомпилированное правило, готовое к применению."""

    id: str
    type: str
    pattern: re.Pattern
    confidence: float
    priority: int
    validators: tuple
    negatives: tuple
    negative_window: int
    subtype: str | None
    groups: tuple
    policy: str | None
    gazetteer_check: str | None
    requires_any: tuple
    requires_regex: re.Pattern | None
    min_digits: int
    negative_after: int
    required: tuple
    required_window: int

    def applicable(self, low: str, digits: int, text: str) -> bool:
        """Префильтр: правило не запускается, если текст не подходит."""
        if digits < self.min_digits:
            return False
        if self.requires_any and not any(s in low for s in self.requires_any):
            return False
        return not (self.requires_regex is not None and not self.requires_regex.search(text))


def load_macros(path: str | Path) -> dict[str, str]:
    """Читает макросы из _macros.yaml."""
    p = Path(path)
    if not p.is_file():
        return {}
    with open(p, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    result: dict[str, str] = {}
    for key, value in data.items():
        if not isinstance(value, str):
            raise TypeError(f"Макрос {key} должен быть строкой")
        result[key] = value
    return result


def expand(pattern: str, macros: dict[str, str]) -> str:
    """Подставляет вместо {ИМЯ} значение, повторяя до пяти проходов."""
    result = pattern
    for _ in range(5):
        new = _MACRO_RE.sub(lambda m: macros.get(m.group(1), m.group(0)), result)
        if new == result:
            break
        result = new
    return result


def compile_rule(spec: RuleSpec, rule_type: str, macros: dict[str, str]) -> CompiledRule:
    """Компилирует раскрытый паттерн и контексты правила."""
    pattern = re.compile(expand(spec.pattern, macros), FLAGS)
    group_names = set(pattern.groupindex)

    if spec.groups:
        groups = tuple(spec.groups)
    else:
        groups = tuple(sorted(g for g in group_names if g.startswith("v")))
    if not groups:
        raise ValueError(f"Правило {spec.id}: нет групп для маскирования (имена v, v1, v2 ...)")
    missing = [g for g in groups if g not in group_names]
    if missing:
        raise ValueError(f"Правило {spec.id}: группы {', '.join(missing)} нет в паттерне")

    negatives = tuple(re.compile(expand(p, macros), FLAGS) for p in spec.negative_context)
    required = tuple(re.compile(expand(p, macros), FLAGS) for p in spec.required_context)
    requires_regex = re.compile(spec.requires_regex, re.VERSION1) if spec.requires_regex else None
    requires_any = tuple(s.lower() for s in spec.requires_any)

    validators = tuple(VALIDATORS[name] for name in spec.validators)

    return CompiledRule(
        id=spec.id,
        type=rule_type,
        pattern=pattern,
        confidence=spec.confidence,
        priority=spec.priority,
        validators=validators,
        negatives=negatives,
        negative_window=spec.negative_window,
        subtype=spec.subtype,
        groups=groups,
        policy=spec.policy,
        gazetteer_check=spec.gazetteer_check,
        requires_any=requires_any,
        requires_regex=requires_regex,
        min_digits=spec.min_digits,
        negative_after=spec.negative_after,
        required=required,
        required_window=spec.required_window,
    )


def load_rules(rules_dir: str | Path, registry: TypeRegistry) -> list[CompiledRule]:
    """Загружает и компилирует все правила из каталога."""
    d = Path(rules_dir)
    macros = load_macros(d / "_macros.yaml")
    compiled: list[CompiledRule] = []
    seen_ids: dict[str, str] = {}
    for path in sorted(d.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        file = RuleFile.model_validate(data)
        if not file.enabled:
            continue
        registry.register(file.type, file.label_ru, file.label_en)
        for spec in file.rules:
            if spec.id in seen_ids:
                raise ValueError(f"Дублирующиеся id правил: {', '.join(sorted(seen_ids))}")
            seen_ids[spec.id] = file.type
            compiled.append(compile_rule(spec, file.type, macros))
    return compiled
