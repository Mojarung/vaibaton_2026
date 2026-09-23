"""Схема политики на pydantic. Опечатка в YAML падает сразу."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

MaskMode = Literal["placeholder", "redact", "stars", "partial", "synthetic"]


class ComboRule(BaseModel):
    """Тип маскируется, только если рядом найден один из requires."""

    model_config = {"extra": "forbid"}

    type: str
    requires: list[str] = Field(min_length=1)
    window: int = Field(default=200, ge=1, le=10000)

    @field_validator("requires", mode="before")
    @classmethod
    def _coerce_requires(cls, v):
        if isinstance(v, str):
            return [v]
        return v


class SystemPolicy(BaseModel):
    """Политика одной системы-потребителя."""

    model_config = {"extra": "forbid"}

    enabled: bool = True
    description: str = ""
    api_key_env: str | None = None
    entity_types: list[str] | Literal["all"] = "all"
    exclude_types: list[str] = Field(default_factory=list)
    mask_mode: MaskMode = "placeholder"
    type_modes: dict[str, MaskMode] = Field(default_factory=dict)
    placeholder_lang: Literal["ru", "en"] = "ru"
    unmask: bool = True
    contextual: bool = True
    single_value_mode: bool = True
    bare_date_policy: Literal["never", "birth_like", "always"] = "birth_like"
    combo_rules: list[ComboRule] = Field(default_factory=list)
    ttl_seconds: int = Field(default=86400, ge=60, le=7 * 24 * 3600)
    llm_proxy: bool = True

    @field_validator("api_key_env")
    @classmethod
    def _check_env_name(cls, v: str | None) -> str | None:
        if v is None:
            return None
        cleaned = v.replace("_", "")
        if not cleaned.isalnum():
            raise ValueError("api_key_env должен быть именем переменной окружения")
        return v


class SystemsFile(BaseModel):
    """Корневая схема systems.yaml."""

    model_config = {"extra": "forbid"}

    default_system: str = "default"
    defaults: dict = Field(default_factory=dict)
    systems: dict[str, dict] = Field(default_factory=dict)
