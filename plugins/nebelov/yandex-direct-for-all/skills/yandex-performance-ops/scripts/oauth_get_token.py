#!/usr/bin/env python3
"""Compatibility launcher for the shared-app PKCE authorization flow."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> None:
    launcher = Path(__file__).resolve().parents[3] / "scripts" / "start_yandex_user_auth.py"
    os.execv(sys.executable, [sys.executable, str(launcher), *sys.argv[1:]])


if __name__ == "__main__":
    main()
