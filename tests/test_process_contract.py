"""Контракт автопроверки и управление системами."""

from __future__ import annotations

from pathlib import Path

from .conftest import KEYS

PROCESS_URL = "/process"
MASK_URL = "/v1/mask"
EMAIL = "ivan@mail.ru"
SURNAME = "Иванов"
NEWBOT_URL = "/admin/systems/newbot"
BASE = "Клиент Иванов Иван Иванович, паспорт серия 4509 номер 123456, тел. +7 (916) 123-45-67, email ivan@mail.ru"
FILLER = " Обычный текст обращения без персональных данных, который просто занимает место."


def process(client, payload, payload_id, system=None, key=None):
    headers = {}
    if system:
        headers["X-System-Id"] = system
    if key:
        headers["X-Api-Key"] = key
    return client.post(
        PROCESS_URL, json={"payload": payload, "payload_id": payload_id}, headers=headers
    )


def test_mask_then_unmask(client):
    r = process(client, BASE, "p1")
    assert r.status_code == 200
    masked = r.json()["result"]
    for v in (SURNAME, "4509", "123456", "916", EMAIL):
        assert v not in masked, f"{v} остался в маске"
    r = process(client, masked, "p1")
    assert r.status_code == 200
    assert r.json()["result"] == BASE


def test_idempotent(client):
    r1 = process(client, BASE, "p2")
    r2 = process(client, BASE, "p2")
    assert r1.json()["result"] == r2.json()["result"]
    masked = r1.json()["result"]
    r3 = process(client, masked, "p2")
    assert r3.json()["result"] == BASE
    r4 = process(client, masked, "p2")
    assert r4.json()["result"] == BASE


def test_big_text(client):
    block = BASE + FILLER
    big = (block * ((360_000 // len(block)) + 1))[:360_000]
    r = process(client, big, "big1")
    assert r.status_code == 200
    masked = r.json()["result"]
    assert SURNAME not in masked
    assert EMAIL not in masked
    r = process(client, masked, "big1")
    assert r.status_code == 200
    assert r.json()["result"] == big


def test_single_values(client):
    for i, value in enumerate(["4829", "Петров Пётр Петрович", "без данных", ""]):
        r = process(client, value, f"sv{i}")
        assert r.status_code == 200
        masked = r.json()["result"]
        r = process(client, masked, f"sv{i}")
        assert r.json()["result"] == value
    r = process(client, "4829", "sv-new")
    assert r.json()["result"] != "4829"


def test_invalid_requests(client):
    r = client.post(PROCESS_URL, content="{broken", headers={"Content-Type": "application/json"})
    assert r.status_code == 400
    r = client.post(PROCESS_URL, json={"payload": 4509123456, "payload_id": "x"})
    assert r.status_code == 422
    assert "4509123456" not in r.text
    r = client.post(PROCESS_URL, json={"payload": "текст"})
    assert r.status_code == 422


def test_system_policies(client):
    r = client.post(
        MASK_URL,
        json={"text": BASE},
        headers={"X-System-Id": "crm", "X-Api-Key": "wrong"},
    )
    assert r.status_code == 401
    r = client.post(MASK_URL, json={"text": BASE}, headers={"X-System-Id": "analytics"})
    assert r.status_code == 403
    r = client.post(
        MASK_URL,
        json={"text": BASE},
        headers={"X-System-Id": "crm", "X-Api-Key": KEYS["KEY_CRM"]},
    )
    assert r.status_code == 200
    data = r.json()
    assert SURNAME not in data["masked"]
    assert "[" not in data["masked"]
    r = client.post(
        "/v1/unmask",
        json={"text": data["masked"], "session_id": data["session_id"]},
        headers={"X-System-Id": "crm", "X-Api-Key": KEYS["KEY_CRM"]},
    )
    assert r.json()["text"] == BASE


def test_combo_rule(client):
    headers = {"X-System-Id": "support_bot", "X-Api-Key": KEYS["KEY_SUPPORT"]}
    r = client.post(MASK_URL, json={"text": "PIN 1234"}, headers=headers)
    assert r.json()["masked"] == "PIN 1234"
    text = "карта 5536 8989 9530 3715, PIN 1234"
    r = client.post(MASK_URL, json={"text": text}, headers=headers)
    masked = r.json()["masked"]
    assert "5536" not in masked
    assert "1234" not in masked
    r = client.post(
        "/v1/unmask",
        json={"text": masked, "session_id": r.json()["session_id"]},
        headers=headers,
    )
    assert r.status_code == 403


def test_admin_systems(client):
    r = client.get("/admin/systems")
    assert r.status_code == 403
    admin = {"X-Admin-Key": KEYS["ADMIN_KEY"]}
    r = client.put(
        NEWBOT_URL,
        json={"entity_types": ["PHONE", "EMAIL"], "mask_mode": "redact"},
        headers=admin,
    )
    assert r.status_code == 200
    assert r.json()["types"] == ["EMAIL", "PHONE"]
    r = client.post(
        MASK_URL,
        json={"text": BASE},
        headers={"X-System-Id": "newbot"},
    )
    masked = r.json()["masked"]
    assert SURNAME in masked
    assert EMAIL not in masked
    assert "[EMAIL]" in masked
    r = client.put(
        NEWBOT_URL,
        json={"entity_types": ["BOGUS_TYPE"]},
        headers=admin,
    )
    assert r.status_code == 422
    r = client.delete(NEWBOT_URL, headers=admin)
    assert r.status_code == 204


def test_new_type_from_yaml(client, config_copy):
    rules_dir = Path(config_copy) / "rules"
    yaml_text = (
        "type: OMS_POLICY\n"
        "label_ru: ПОЛИС_ОМС\n"
        "label_en: OMS_POLICY\n"
        "rules:\n"
        "  - id: oms_ctx\n"
        "    confidence: 0.99\n"
        "    priority: 130\n"
        "    pattern: \\bполис\\w*\\s+омс{SEP}(?P<v>\\d{16}){END}\n"
        "    requires_any:\n"
        "      - полис\n"
    )
    text = "Полис ОМС 7755443322110099, клиент Иванов Иван Иванович"
    r = client.post(MASK_URL, json={"text": text})
    assert "7755443322110099" in r.json()["masked"]
    (rules_dir / "oms_policy.yaml").write_text(yaml_text, encoding="utf-8")
    r = client.post("/admin/reload", headers={"X-Admin-Key": KEYS["ADMIN_KEY"]})
    assert r.status_code == 200
    r = client.post(MASK_URL, json={"text": text})
    assert r.json()["masked"] == "Полис ОМС [ПОЛИС_ОМС_1], клиент [ФИО_1]"
    r = client.get("/v1/types")
    assert any(t["id"] == "OMS_POLICY" for t in r.json()["types"])


def test_llm_proxy(client):
    r = client.post(
        "/v1/chat/completions",
        json={"model": "demo", "messages": [{"role": "user", "content": BASE}]},
        headers={"X-Pii-Debug": "1"},
    )
    assert r.status_code == 200
    data = r.json()
    sent = " ".join(m["content"] for m in data["pii_guard"]["sent_to_llm"])
    for v in (SURNAME, "4509", "123456", EMAIL):
        assert v not in sent, f"{v} ушёл в модель"
    content = data["choices"][0]["message"]["content"]
    assert "Иванов Иван Иванович" in content
