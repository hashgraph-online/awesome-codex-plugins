#!/usr/bin/env python3
"""Wrapper for the canonical Thoth extend command."""

from __future__ import annotations

import argparse
from pathlib import Path

from thoth.surface.handlers import handle_command


class _Args:
    command = "extend"

    def __init__(self, changed: list[str]) -> None:
        self.changed = changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Thoth extend")
    parser.add_argument("--changed", nargs="*", default=[])
    args = parser.parse_args()
    return handle_command(_Args(list(args.changed)), parser, project_root=Path.cwd())


if __name__ == "__main__":
    raise SystemExit(main())
