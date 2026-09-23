#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p load/results
docker compose up -d --wait api >/dev/null
docker compose --profile load run --rm --no-deps k6 >"load/results/last_run.txt" 2>&1 || true
docker compose logs api --since 10m 2>/dev/null | grep -c '"level":"error"' | sed 's/^/api errors: /'
uv run --no-project python - <<'PY'
import json
m = json.load(open("load/results/summary.json"))["metrics"]
g = lambda k: m.get(k, {})
d = g("http_req_duration")
print(f"rps={g('http_reqs').get('rate', 0):.0f} p50={d.get('med', 0):.1f} p95={d.get('p(95)', 0):.1f} "
      f"p99={d.get('p(99)', 0):.1f} max={d.get('max', 0):.0f} ms failed={g('http_req_failed').get('value', 0):.4f} "
      f"roundtrip_errors={g('roundtrip_errors').get('count', 0)} dropped={g('dropped_iterations').get('count', 0)}")
PY
