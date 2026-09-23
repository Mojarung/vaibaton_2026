"""structlog в JSON через orjson."""

from __future__ import annotations

import logging
import sys

import orjson
import structlog

# Ключи, которые никогда не должны попасть в лог: значения ПДн.
FORBIDDEN_KEYS = {"payload", "text", "original", "masked", "result", "content", "messages"}


class _RedactProcessor:
    """Заменяет значения запрещённых ключей на <redacted>."""

    def __call__(self, _logger, _method_name, event_dict):
        for key in FORBIDDEN_KEYS:
            if key in event_dict:
                event_dict[key] = "<redacted>"
        return event_dict


class _StdoutWriter:
    """Пишет байты в sys.stdout.buffer, поток берётся заново при каждой записи."""

    def __call__(self, _logger, _method_name, event_dict):
        line = orjson.dumps(event_dict, option=orjson.OPT_NON_STR_KEYS)
        sys.stdout.buffer.write(line + b"\n")
        sys.stdout.buffer.flush()
        raise structlog.DropEvent


def configure_logging(level: str, app_name: str) -> None:
    """Настраивает стандартный logging и цепочку процессоров structlog."""
    logging.basicConfig(stream=sys.stdout, level=level.upper())
    for noisy in ("httpx", "httpcore", "watchfiles", "uvicorn.access", "granian.access"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _RedactProcessor(),
            structlog.processors.format_exc_info,
            _StdoutWriter(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level.upper()),
        cache_logger_on_first_use=True,
    )
    structlog.contextvars.bind_contextvars(service=app_name)
