#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
from typing import Optional


class CalibreDBError(RuntimeError):
    pass


def summarize_process_error(stderr: str, stdout: str, returncode: int) -> str:
    output = stderr.strip() or stdout.strip()
    if not output:
        return f"exit code {returncode}"

    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if any(line.startswith("Traceback ") for line in lines):
        return lines[-1]

    return output


def run_calibredb(library: str, search: Optional[str], limit: Optional[int], fields: str) -> list[dict]:
    cmd = [
        "calibredb",
        "list",
        "--with-library",
        library,
        "--fields",
        fields,
        "--for-machine",
    ]
    if search:
        cmd += ["--search", search]
    if limit is not None:
        cmd += ["--limit", str(limit)]

    try:
        result = subprocess.run(cmd, capture_output=True, check=True, text=True)
    except FileNotFoundError as exc:
        raise CalibreDBError("calibredb executable was not found on PATH") from exc
    except subprocess.CalledProcessError as exc:
        detail = summarize_process_error(exc.stderr, exc.stdout, exc.returncode)
        raise CalibreDBError(f"calibredb list failed: {detail}") from exc

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        excerpt = result.stdout.strip()[:500] or "<empty output>"
        raise CalibreDBError(f"calibredb returned invalid JSON: {exc}; output: {excerpt}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="List Calibre books as JSON via calibredb list --for-machine")
    parser.add_argument(
        "--library",
        default=os.environ.get("CALIBRE_LIBRARY"),
        help="Calibre library path or content-server URL. Defaults to CALIBRE_LIBRARY.",
    )
    parser.add_argument("--search", default=None, help="Calibre search expression")
    parser.add_argument("--limit", type=int, default=None, help="Max rows")
    parser.add_argument(
        "--fields",
        default="id,title,authors,tags,formats,pubdate",
        help="Comma-separated field names for calibredb list",
    )

    args = parser.parse_args()
    if not args.library:
        parser.error("provide --library or set CALIBRE_LIBRARY")

    try:
        rows = run_calibredb(args.library, args.search, args.limit, args.fields)
    except CalibreDBError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    json.dump(rows, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
