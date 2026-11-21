#!/usr/bin/env python3
"""Extract the single JSON PRD handoff block from a review report."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


JSON_FENCE = re.compile(r"```json\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)


def extract(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    blocks = JSON_FENCE.findall(text)
    if len(blocks) != 1:
        raise ValueError(f"expected exactly one JSON handoff block, found {len(blocks)}")
    value = json.loads(blocks[0])
    if not isinstance(value, dict):
        raise ValueError("PRD handoff must be a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    try:
        value = extract(args.report)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
