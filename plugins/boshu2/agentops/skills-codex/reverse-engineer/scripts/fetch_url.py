#!/usr/bin/env python3
from __future__ import annotations

import sys
import urllib.parse
import urllib.request
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: fetch_url.py <url> <out_path>", file=sys.stderr)
        return 2
    url = sys.argv[1]
    out_path = Path(sys.argv[2])
    out_path.parent.mkdir(parents=True, exist_ok=True)

    parsed = urllib.parse.urlparse(url)
    if parsed.scheme in ("file", ""):
        src = Path(parsed.path if parsed.scheme == "file" else url)
        out_path.write_bytes(src.read_bytes())
        return 0

    req = urllib.request.Request(url, headers={"User-Agent": "reverse-engineer/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        out_path.write_bytes(resp.read())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

