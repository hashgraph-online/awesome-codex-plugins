"""Shared helpers for the runnable recipes (offline by default)."""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))          # examples/
sys.path.insert(0, os.path.dirname(HERE))              # examples/python

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

from tgkit.transport import FakeTransport  # noqa: E402


def fixture(name: str) -> dict:
    with open(os.path.join(ROOT, "fixtures", name), encoding="utf-8") as fh:
        return json.load(fh)


def widget_html(name: str) -> str:
    with open(os.path.join(ROOT, "widgets", name), encoding="utf-8") as fh:
        return fh.read()


def _short(v, depth=0):
    if isinstance(v, str):
        return v if len(v) <= 60 else v[:57] + "…"
    if isinstance(v, list):
        return [_short(x, depth + 1) for x in v[:4]] + (["…"] if len(v) > 4 else [])
    if isinstance(v, dict):
        return {k: _short(x, depth + 1) for k, x in v.items()}
    return v


def dump(transport: FakeTransport, title: str) -> None:
    print(f"\n== {title} ==")
    for i, (method, params) in enumerate(transport.calls, 1):
        print(f"{i:2}. {method} {json.dumps(_short(params), ensure_ascii=False)}")


def check(cond: bool, message: str) -> None:
    if not cond:
        raise AssertionError(message)
    print(f"   ✓ {message}")
