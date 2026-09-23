"""Замер стоимости детекции по этапам на смеси размеров, как в нагрузке.

Запуск: python -m tools.bench_detect [--n 2000] [--profile]
"""

from __future__ import annotations

import argparse
import cProfile
import io
import pstats
import random
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import orjson  # noqa: E402

from pii_guard.core.engine import Detector  # noqa: E402
from pii_guard.core.types import DetectionOptions  # noqa: E402


def corpus() -> list[str]:
    texts: list[str] = []
    for name in ("blind.jsonl", "generated.jsonl"):
        p = ROOT / "datasets" / "golden" / name
        if p.exists():
            for raw_line in p.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if line:
                    texts.append(orjson.loads(line)["text"])
    return texts


def sample(texts: list[str], rng: random.Random) -> str:
    r = rng.random()
    if r < 0.85:
        return texts[rng.randrange(len(texts))]
    if r < 0.98:
        return "\n".join(texts[rng.randrange(len(texts))] for _ in range(8))
    return "\n".join(texts[rng.randrange(len(texts))] for _ in range(60))


def run(detector: Detector, texts: list[str], rng: random.Random, n: int):
    times: list[float] = []
    stages_total: dict[str, float] = {}
    for _ in range(n):
        text = sample(texts, rng)
        t0 = time.perf_counter()
        result = detector.detect(text, DetectionOptions())
        times.append((time.perf_counter() - t0) * 1000)
        for stage, ms in result.stages_ms.items():
            stages_total[stage] = stages_total.get(stage, 0.0) + ms
    return times, stages_total


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=2000)
    parser.add_argument("--profile", action="store_true")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    texts = corpus()
    detector = Detector(ROOT / "config")
    rng = random.Random(1)
    for _ in range(200):
        detector.detect(sample(texts, rng), DetectionOptions())

    if args.profile:
        pr = cProfile.Profile()
        pr.enable()
        times, stages_total = run(detector, texts, rng, args.n)
        pr.disable()
        s = io.StringIO()
        pstats.Stats(pr, stream=s).sort_stats("cumulative").print_stats(25)
        print(s.getvalue())
    else:
        times, stages_total = run(detector, texts, rng, args.n)

    total = sum(times)
    mean = total / len(times)
    median = statistics.median(times)
    p99 = sorted(times)[int(len(times) * 0.99) - 1]
    print(f"n={args.n} total={total:.0f}ms mean={mean:.2f} median={median:.2f} p99={p99:.2f}")
    for stage, ms in sorted(stages_total.items(), key=lambda x: -x[1]):
        print(f"  {stage}: {ms:.0f}ms ({ms / total * 100:.1f}%)")


if __name__ == "__main__":
    main()
