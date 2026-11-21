#!/usr/bin/env python3
"""Совместимый безопасный запуск общей авторизации Метрики."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> None:
    if any(item in {"--code", "--token", "--client-id", "--client-secret"} for item in sys.argv[1:]):
        raise SystemExit("Код и учётные данные нельзя передавать в командной строке")
    root = Path(__file__).resolve().parents[3]
    launcher = root / "scripts" / "start_yandex_user_auth.py"
    os.execv(sys.executable, [sys.executable, str(launcher), "--service", "metrika", *sys.argv[1:]])


if __name__ == "__main__":
    main()
