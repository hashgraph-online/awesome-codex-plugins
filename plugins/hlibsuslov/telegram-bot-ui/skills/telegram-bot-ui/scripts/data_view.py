#!/usr/bin/env python3
"""Render a data view as ready Telegram messages, split by the limits (references/data-views.md).

Input: a JSON spec (file or "-" for stdin) with "view" and its fields:
  table        {"title", "header": [...], "rows": [[...]], "right": [col...], "summary"?, "footer"?,
                "mode": "rich" | "html"}   rich (default) = sendRichMessage blocks (32768 chars, 500
                                           blocks, 20 columns); html = the fallback: regular messages
                                           with a <pre> grid (4096)
  leaderboard  {"entries": [[name, score]...], "me"?, "top"?, "unit"?}
  progress     {"done", "total", "width"?, "style": "blocks" | "bar" | "dots"}
  kpi          {"items": [{"label", "value", "current"?, "previous"?}]}
Common: "lang" (en, ru, uk: number format and "continued"), "limit" (override the part limit).

Output: every part with its length, or --json: {"parts": [...], "lengths": [...]} where a part is
HTML text (send with parse_mode HTML, the keyboard on the last part) or a list of Rich blocks.

  py -3 scripts/data_view.py report.json
  py -3 scripts/data_view.py report.json --json > parts.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples", "python"))
from tgkit import dataview  # noqa: E402
from tgkit.text import utf16_len  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass


def render(spec: dict) -> list:
    view, lang = spec.get("view"), spec.get("lang", "en")
    if view == "table":
        kw = {"lang": lang}
        if "limit" in spec:
            kw["limit"] = int(spec["limit"])
        if spec.get("mode", "rich") == "rich":
            return dataview.rich_table_parts(spec["title"], spec["header"], spec["rows"], summary=spec.get("summary", ""),
                                             footer=spec.get("footer", ""), numeric=frozenset(spec.get("right", [])), **kw)
        return dataview.table_parts(spec["title"], spec["header"], spec["rows"], right=frozenset(spec.get("right", [])),
                                    summary=spec.get("summary", ""), footer=spec.get("footer", ""), **kw)
    if view == "leaderboard":
        return [dataview.leaderboard([tuple(e) for e in spec["entries"]], me=spec.get("me"), top=int(spec.get("top", 10)),
                                     unit=spec.get("unit", ""), lang=lang)]
    if view == "progress":
        return [dataview.progress(spec["done"], spec["total"], width=int(spec.get("width", 10)),
                                  style=spec.get("style", "blocks"))]
    if view == "kpi":
        return [dataview.kpi_lines(spec["items"], lang)]
    raise ValueError(f"view is one of table, leaderboard, progress, kpi (got {view!r})")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("spec", help="JSON spec file, or - for stdin")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        spec = json.load(sys.stdin if args.spec == "-" else open(args.spec, encoding="utf-8"))
        parts = render(spec)
    except (OSError, ValueError, KeyError, TypeError) as err:
        print(f"data_view: {err}", file=sys.stderr)
        return 2
    lengths = [utf16_len(p) if isinstance(p, str) else len(json.dumps(p, ensure_ascii=False)) for p in parts]
    if args.json:
        print(json.dumps({"parts": parts, "lengths": lengths}, ensure_ascii=False, indent=1))
        return 0
    for i, (p, n) in enumerate(zip(parts, lengths)):
        print(f"--- part {i + 1}/{len(parts)} ({n} {'UTF-16 units' if isinstance(p, str) else 'JSON chars'})")
        print(p if isinstance(p, str) else json.dumps(p, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
