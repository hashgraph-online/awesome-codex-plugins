"""Public selftest module for Thoth."""

from thoth.observe.selftest.runner import main, run_selftest

__all__ = ["main", "run_selftest"]


if __name__ == "__main__":
    raise SystemExit(main())
