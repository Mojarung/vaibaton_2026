#!/bin/sh
set -eu
rm -rf "${PROMETHEUS_MULTIPROC_DIR:?}" && mkdir -p "$PROMETHEUS_MULTIPROC_DIR"

exec granian pii_guard.api.app:app \
  --interface asgi \
  --host 0.0.0.0 \
  --port "${PORT:-8080}" \
  --workers "${WORKERS:-4}" \
  --runtime-mode "${RUNTIME_MODE:-mt}" \
  --loop uvloop \
  --http 1 \
  --backlog "${BACKLOG:-2048}" \
  --backpressure "${BACKPRESSURE:-256}" \
  --no-ws \
  --respawn-failed-workers \
  --no-access-log \
  --log-level warning
