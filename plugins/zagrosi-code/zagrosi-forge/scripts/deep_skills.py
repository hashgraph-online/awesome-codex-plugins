#!/usr/bin/env python3
"""Backward-compatible wrapper for the renamed Zagrosi helper CLI."""

from zagrosi_skills import main


if __name__ == "__main__":
    raise SystemExit(main())
