"""Настройки процесса. Политики систем живут в config/systems.yaml."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_PREFIX_RE = re.compile(r"^[a-z][a-z0-9_]{0,30}$")


class Settings(BaseSettings):
    """Настройки процесса из переменных окружения и .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Контур"
    metrics_prefix: str = Field(default="pii", max_length=31)
    config_dir: Path = Path("config")
    redis_url: str = ""
    vault_key: SecretStr = SecretStr("")
    store_prefix: str = "pii"
    admin_key: SecretStr = SecretStr("")
    llm_base_url: str = ""
    llm_api_key: SecretStr = SecretStr("")
    llm_model: str = "deepseek-ai/DeepSeek-V4-Flash-0731"
    llm_timeout_seconds: float = 90.0
    llm_verify_tls: bool = True
    max_concurrent: int = Field(default=256, ge=1)
    max_body_bytes: int = Field(default=4 * 1024 * 1024, ge=1024)
    max_text_chars: int = Field(default=1_000_000, ge=1000)
    log_level: str = "INFO"

    @field_validator("metrics_prefix")
    @classmethod
    def _check_prefix(cls, v: str) -> str:
        if not _PREFIX_RE.match(v):
            raise ValueError("metrics_prefix должен начинаться с латинской буквы")
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
