"""Public CLI module for Thoth."""

from thoth.surface.cli import build_cli_parser, main

__all__ = ["build_cli_parser", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
