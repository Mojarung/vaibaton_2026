"""Исходные ПДн не попадают ни в логи, ни в метрики."""

from __future__ import annotations

from pii_guard.quality.golden import parse_example
from tools.gen_golden import generate


def test_no_leaks(client, capfd):
    examples = [parse_example(raw) for raw in generate(seed=3, rounds=2)]
    golden_values = set()
    for i, ex in enumerate(examples):
        for span in ex.pii:
            v = ex.text[span.start : span.end]
            if len(v) >= 5:
                golden_values.add(v)
        r = client.post("/process", json={"payload": ex.text, "payload_id": f"leak-{i}"})
        assert r.status_code == 200
        masked = r.json()["result"]
        r = client.post("/process", json={"payload": masked, "payload_id": f"leak-{i}"})
        assert r.status_code == 200

    last = examples[-1]
    r = client.post(
        "/v1/chat/completions",
        json={"model": "demo", "messages": [{"role": "user", "content": last.text}]},
    )
    assert r.status_code == 200

    r = client.get("/metrics")
    metrics_text = r.text

    captured = capfd.readouterr()
    logs = captured.out
    assert "request.done" in logs
    assert "entities" in logs

    leaked = [v for v in golden_values if v in logs or v in metrics_text]
    assert not leaked, f"Утечки: {leaked[:5]}"
