"""Общие фикстуры тестов."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from pii_guard.api.app import create_app
from pii_guard.core.engine import Detector
from pii_guard.settings import Settings

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config"

KEYS = {
    "KEY_CRM": "crm-test-key",
    "KEY_SUPPORT": "support-test-key",
    "ADMIN_KEY": "admin-test-key",
}


@pytest.fixture(scope="session")
def detector():
    return Detector(CONFIG)


@pytest.fixture()
def config_copy(tmp_path):
    dest = tmp_path / "config"
    shutil.copytree(CONFIG, dest)
    return dest


@pytest.fixture()
def client(config_copy, monkeypatch):
    for name, value in KEYS.items():
        monkeypatch.setenv(name, value)
    settings = Settings(
        config_dir=config_copy,
        redis_url="",
        admin_key=KEYS["ADMIN_KEY"],
        llm_base_url="",
        log_level="INFO",
    )
    app = create_app(settings)
    with TestClient(app) as c:
        yield c
