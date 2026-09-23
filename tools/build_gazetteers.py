"""Сборка больших словарей имён и фамилий из пакета natasha.

Берёт data/dict/first.txt и data/dict/last.txt из установленного пакета natasha,
сжимает их gzip (уровень 9, mtime=0) и пишет в config/gazetteers.

Запуск (natasha нужна только здесь, в зависимости проекта её нет):

    uv run --no-project --with natasha==1.6.0 python tools/build_gazetteers.py
"""

from __future__ import annotations

import gzip
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "config" / "gazetteers"

SOURCES = {
    "first_names.txt.gz": "first.txt",
    "surnames.txt.gz": "last.txt",
}


def _natasha_dict_dir() -> Path:
    spec = importlib.util.find_spec("natasha")
    if spec is None or spec.submodule_search_locations is None:
        raise SystemExit("Пакет natasha не установлен. Запусти через uv run --with natasha==1.6.0")
    pkg_dir = Path(next(iter(spec.submodule_search_locations)))
    return pkg_dir / "data" / "dict"


def build() -> None:
    dict_dir = _natasha_dict_dir()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for out_name, src_name in SOURCES.items():
        src = dict_dir / src_name
        if not src.is_file():
            raise SystemExit(f"Не найден словарь: {src}")
        out = OUT_DIR / out_name
        with src.open("rb") as f_in, gzip.GzipFile(out, "wb", compresslevel=9, mtime=0) as f_out:
            f_out.write(f_in.read())
        with gzip.open(out, "rt", encoding="utf-8") as f:
            lines = sum(1 for _ in f)
        print(f"{out} ({lines} строк)")


if __name__ == "__main__":
    build()
