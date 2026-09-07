#!/usr/bin/env python3
"""Проверить тот же пакет минус-фраз без сетевой записи."""

from __future__ import annotations

import argparse
from pathlib import Path

from check_access_paths import sanitize_error
from direct_write_gate import prepare


def main() -> int:
    parser = argparse.ArgumentParser(description="Проверить пакет минус-фраз без записи")
    parser.add_argument("--pack", required=True)
    parser.add_argument("--pack-sha256", required=True)
    args = parser.parse_args()
    try:
        prepared = prepare(Path(args.pack), Path(args.pack_sha256), apply=False)
    except Exception as exc:
        print(f"Пакет отклонён: {sanitize_error(exc)}")
        return 1
    print(f"Пакет {prepared.pack['run_id']} проверен; сетевых вызовов не было")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
