"""Оценка детекции на золотых датасетах с политикой выбранной системы.

Запуск: uv run python -m tools.eval путь [путь ...] [--system default]
[--show 30] [--report reports/eval.json]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pii_guard.core.engine import Detector  # noqa: E402
from pii_guard.policy.registry import SystemRegistry  # noqa: E402
from pii_guard.quality.golden import load  # noqa: E402
from pii_guard.quality.metrics import Report  # noqa: E402


def mark(text: str, spans: list[tuple[int, int]]) -> str:
    """Показывает предсказание, обрамляя спаны скобками ⟦ ⟧."""
    out: list[str] = []
    pos = 0
    for s, e in sorted(spans):
        if s > pos:
            out.append(text[pos:s])
        out.append("⟦" + text[s:e] + "⟧")
        pos = e
    out.append(text[pos:])
    return "".join(out)


def evaluate(paths: list[Path], system_id: str):
    """Прогоняет детектор по датасетам и возвращает отчёт, ошибки и время."""
    detector = Detector(ROOT / "config")
    systems = SystemRegistry(ROOT / "config" / "systems.yaml", set(detector.registry.names()))
    options = systems.get(system_id).options
    report = Report()
    rows = []
    t0 = time.perf_counter()
    for path in paths:
        for ex in load(path):
            before = len(report.failures)
            spans = detector.detect(ex.text, options).spans
            predicted = [(s.start, s.end) for s in spans]
            report.add(ex, predicted)
            if len(report.failures) > before:
                rows.append((ex, spans, report.failures[-1]))
    elapsed = (time.perf_counter() - t0) * 1000
    return report, rows, elapsed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--system", default="default")
    parser.add_argument("--show", type=int, default=30)
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    report, rows, elapsed = evaluate(args.paths, args.system)
    s = report.summary()

    print("Сводка")
    for k, v in s.items():
        print(f"  {k}: {v}")
    print(f"  ms_per_example: {elapsed / max(1, s['examples']):.3f}")
    print()

    print("По типам")
    for row in report.per_type():
        print(
            f"  {row['type']}: {row['full']}/{row['entities']} "
            f"partial={row['partial']} recall_full={row['recall_full']:.3f}"
        )
    print()

    print("По категориям")
    for cat, v in report.per_category().items():
        print(f"  {cat}: {v['examples']} similarity={v['similarity']:.3f}")
    print()

    print(f"Ошибки (первые {args.show})")
    for ex, spans, err in rows[: args.show]:
        print(f"  {ex.id} [{ex.category}] {ex.variant}: {err}")
        print(f"    text: {ex.text!r}")
        print(f"    pred: {mark(ex.text, [(s.start, s.end) for s in spans])}")
        gold = ", ".join(f"{span.type}:{ex.text[span.start : span.end]}" for span in ex.pii)
        print(f"    gold: {gold}")

    report_path = args.report or (
        ROOT / "reports" / f"eval-{'-'.join(p.stem for p in args.paths)}.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "summary": s,
        "per_type": report.per_type(),
        "per_category": report.per_category(),
        "failures": report.failures,
    }
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
