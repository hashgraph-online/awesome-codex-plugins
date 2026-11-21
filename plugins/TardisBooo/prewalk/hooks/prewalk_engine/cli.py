"""Tiny inspection CLI for humans debugging a state file by hand.

Usage::

    python -m prewalk_engine status|disarm|clear <store_file> <session_id>

Hook adapters never call this — it exists for the moments when a state file
needs to be inspected outside any host.
"""

from __future__ import annotations

import sys

from .operations import describe, disarm
from .store import clear_state


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) >= 3 and arguments[0] in ("status", "disarm", "clear"):
        command, store, session_id = arguments[0], arguments[1], arguments[2]
        if command == "status":
            print(describe(store, session_id))
        elif command == "disarm":
            print(disarm(store, session_id))
        else:
            clear_state(store, session_id)
            print("cleared")
        return 0
    print("usage: python -m prewalk_engine status|disarm|clear <store_file> <session_id>", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
