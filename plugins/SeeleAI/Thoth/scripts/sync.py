#!/usr/bin/env python3
"""Wrapper for the canonical Thoth sync service."""

from __future__ import annotations

import json
from pathlib import Path

from thoth.init.service import sync_project_layer


def main() -> int:
    result = sync_project_layer(Path.cwd())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
