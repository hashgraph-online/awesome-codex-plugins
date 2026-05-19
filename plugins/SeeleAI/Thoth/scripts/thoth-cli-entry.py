#!/usr/bin/env python3
"""Thin Python entrypoint for the canonical Thoth CLI."""

from thoth.surface.cli import main as cli_main


if __name__ == "__main__":
    raise SystemExit(cli_main())
