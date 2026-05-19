#!/usr/bin/env python3
"""Wrapper for canonical host hook handling."""

from __future__ import annotations

import argparse
from pathlib import Path

from thoth.surface.hooks import run_host_hook


def main() -> int:
    parser = argparse.ArgumentParser(description="Thoth session hook")
    parser.add_argument("--host", required=True, choices=("claude", "codex"))
    parser.add_argument("--event", required=True, choices=("start", "end", "stop"))
    args = parser.parse_args()
    result = run_host_hook(host=args.host, event=args.event, project_root=Path.cwd())
    if result.stdout:
        print(result.stdout, end="")
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
