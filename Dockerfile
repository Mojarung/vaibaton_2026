# syntax=docker/dockerfile:1.7
FROM ghcr.io/astral-sh/uv:0.12.17 AS uv

FROM python:3.14.7-slim-trixie AS build
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev --no-install-project --extra server
COPY pii_guard ./pii_guard
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev --extra server

FROM python:3.14.7-slim-trixie
RUN useradd --create-home --uid 10001 app
WORKDIR /app
COPY --from=build --chown=app:app /app /app
COPY --chown=app:app config ./config
COPY --chown=app:app docker/entrypoint.sh /entrypoint.sh
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 PROMETHEUS_MULTIPROC_DIR=/tmp/prom WORKERS=4 PORT=8080
USER app
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --start-period=20s CMD python -c "import urllib.request,os;urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/health/live',timeout=2)"
ENTRYPOINT ["/bin/sh", "/entrypoint.sh"]
