#!/usr/bin/env python3
"""Check an HTML widget before sendWidget (Bot API 10.4). Offline, no token.

Errors: > 32768 UTF-8 bytes; > 4096 bytes after zlib level 9 (counted exactly
like the server, per the Widgets guide); NUL; chat_data / public_data > 1024
UTF-8 bytes; secrets in code or public state; a context that production does
not offer (groups, inline, forwards are test-server only on 2026-11-12).
Warnings: no caption; browser features a widget doesn't have (network, form
controls, external resources, vh, scrolling, dialogs, keyboard/touch events…).

The runtime warnings are pattern-based (a heuristic, not a parser): a clean
report does not prove the widget renders - test it in Telegram clients.

--strict adds scripts/widget_lint.py (the gallery's checks: working budget 3800, theme-only
colours, time band, visible request outcomes, state events, drag claims, reduced motion, ...)
and fails on its warnings too. --json prints one machine-readable report per file.

Usage:
  python scripts/validate_widget.py widget.html [more.html ...] [--caption TEXT] [--chat-data JSON]
         [--public-data JSON] [--context private|group|supergroup|inline|forward]
         [--environment production|test] [--strict] [--json]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples", "python"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tgkit.widgets import check_widget  # noqa: E402
import widget_lint  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass


def validate(path: str, a) -> dict:
    with open(path, encoding="utf-8") as fh:
        html = fh.read()
    rep = check_widget(html, caption=a.caption, chat_data=a.chat_data, public_data=a.public_data,
                       context=a.context, environment=a.environment)
    errors, warnings = list(rep.errors), list(rep.warnings)
    if a.strict:
        lint = widget_lint.lint(html, caption=a.caption, compressed=rep.compressed_bytes)
        errors += lint.errors + lint.warnings
        errors += [f"[runtime] {w}" for w in warnings if "caption" not in w]
        warnings = [w for w in warnings if "caption" in w]
    return {"file": path, "ok": not errors, "raw_bytes": rep.raw_bytes,
            "compressed_bytes": rep.compressed_bytes, "errors": errors, "warnings": warnings}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="+")
    ap.add_argument("--caption")
    ap.add_argument("--chat-data")
    ap.add_argument("--public-data")
    ap.add_argument("--context", default="private")
    ap.add_argument("--environment", default="production", choices=("production", "test"))
    ap.add_argument("--strict", action="store_true", help="also run widget_lint and fail on its warnings")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    reports = [validate(f, a) for f in a.file]
    for r in reports:
        if a.json:
            print(json.dumps(r, ensure_ascii=False))
            continue
        if len(reports) > 1:
            print(f"== {r['file']}")
        for w in r["warnings"]:
            print(f"WARN: {w}")
        for e in r["errors"]:
            print(f"FAIL: {e}")
        print(f"\nsize: {r['raw_bytes']} bytes raw, {r['compressed_bytes']} bytes zlib-9 "
              f"(limits 32768 / 4096). {'INVALID' if r['errors'] else 'OK'}.")
    return 0 if all(r["ok"] for r in reports) else 1


if __name__ == "__main__":
    sys.exit(main())
