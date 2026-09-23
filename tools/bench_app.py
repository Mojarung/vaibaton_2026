"""Профилирует приложение без сети: ASGI-вызовы напрямую, без HTTP-клиента.

Запуск: python -m tools.bench_app [--n 3000] [--redis ""] [--profile]
"""

from __future__ import annotations

import argparse
import asyncio
import cProfile
import io
import pstats
import random
import secrets
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import orjson  # noqa: E402

from pii_guard.api.app import create_app  # noqa: E402
from pii_guard.settings import Settings  # noqa: E402
from tools.bench_detect import corpus, sample  # noqa: E402


async def call_process(app, payload: str, payload_id: str) -> dict:
    body = orjson.dumps({"payload": payload, "payload_id": payload_id})
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/process",
        "headers": [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode()),
        ],
        "query_string": b"",
        "server": ("test", 80),
        "client": ("test", 123),
        "scheme": "http",
        "root_path": "",
        "app": app,
    }
    received = False

    def receive():
        nonlocal received
        if not received:
            received = True
            return asyncio.sleep(0, {"type": "http.request", "body": body, "more_body": False})
        return asyncio.sleep(0, {"type": "http.disconnect"})

    chunks: list[bytes] = []

    def send(message):
        if message["type"] == "http.response.body":
            chunks.append(message.get("body", b""))
        return asyncio.sleep(0)

    await app(scope, receive, send)
    return orjson.loads(b"".join(chunks))


async def run(app, texts: list[str], rng: random.Random, n: int) -> float:
    t0 = time.process_time()
    for i in range(n):
        payload = sample(texts, rng)
        pid = f"bench-{secrets.token_hex(4)}-{i}"
        r1 = await call_process(app, payload, pid)
        masked = r1["result"]
        r2 = await call_process(app, masked, pid)
        assert r2["result"] == payload
    return time.process_time() - t0


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=3000)
    parser.add_argument("--redis", default="")
    parser.add_argument("--profile", action="store_true")
    args = parser.parse_args()

    settings = Settings(redis_url=args.redis, log_level="INFO")
    app = create_app(settings)
    texts = corpus()
    rng = random.Random(3)

    async with app.router.lifespan_context(app):
        for i in range(200):
            payload = sample(texts, rng)
            await call_process(app, payload, f"bench-warm-{i}")

        if args.profile:
            pr = cProfile.Profile()
            pr.enable()
            elapsed = await run(app, texts, rng, args.n)
            pr.disable()
            s = io.StringIO()
            pstats.Stats(pr, stream=s).sort_stats("tottime").print_stats(30)
            print(s.getvalue())
        else:
            elapsed = await run(app, texts, rng, args.n)

    per_req = elapsed / args.n * 1000
    print(
        f"requests={args.n} time={elapsed:.2f}s cpu_ms_per_req={per_req:.3f}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
