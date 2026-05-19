#!/usr/bin/env python3
"""Measure tracked Thoth source lines with an explicit hard-metric/dashboard split."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import defaultdict
from pathlib import Path


EXCLUDED_PARTS = {
    ".git",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".pytest_cache",
}

TEXT_EXTENSIONS = {
    ".py",
    ".md",
    ".json",
    ".jsonl",
    ".yaml",
    ".yml",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".vue",
    ".css",
    ".html",
    ".svg",
}


def tracked_files(repo_root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    paths: list[Path] = []
    for line in result.stdout.splitlines():
        rel = line.strip()
        if not rel:
            continue
        path = repo_root / rel
        if any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        if path.is_file():
            paths.append(path)
    return paths


def count_lines(path: Path) -> int:
    try:
        return sum(1 for _ in path.open("r", encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return 0


def classify(relpath: str) -> tuple[str, str]:
    if relpath.startswith("templates/dashboard/frontend/"):
        return ("dashboard_frontend", "dashboard_frontend")
    if relpath.startswith("templates/dashboard/backend/"):
        return ("hard_metric", "dashboard_backend")
    if relpath.startswith("thoth/"):
        return ("hard_metric", "thoth")
    if relpath.startswith("tests/"):
        return ("hard_metric", "tests")
    if relpath.startswith("commands/"):
        return ("hard_metric", "commands")
    if relpath.startswith("plugins/thoth/skills/thoth/"):
        return ("hard_metric", "codex_skill")
    if relpath.startswith("scripts/"):
        return ("hard_metric", "scripts")
    return ("other_tracked", relpath.split("/", 1)[0])


def measure(repo_root: Path) -> dict:
    totals = defaultdict(int)
    buckets = defaultdict(int)
    files: list[dict[str, object]] = []
    for path in tracked_files(repo_root):
        rel = str(path.relative_to(repo_root))
        lines = count_lines(path)
        scope, bucket = classify(rel)
        totals["all_tracked_text"] += lines
        totals[scope] += lines
        buckets[bucket] += lines
        files.append({"path": rel, "lines": lines, "scope": scope, "bucket": bucket})
    files.sort(key=lambda item: int(item["lines"]), reverse=True)
    return {
        "repo_root": str(repo_root),
        "totals": dict(sorted(totals.items())),
        "buckets": dict(sorted(buckets.items())),
        "top_files": files[:40],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Measure tracked Thoth source lines.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true", help="Print JSON only.")
    args = parser.parse_args(argv)

    payload = measure(args.repo_root.resolve())
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("Tracked Source Line Ledger")
    print(f"repo_root: {payload['repo_root']}")
    print("")
    print("Totals:")
    for key, value in payload["totals"].items():
        print(f"  {key:24} {value:6d}")
    print("")
    print("Buckets:")
    for key, value in payload["buckets"].items():
        print(f"  {key:24} {value:6d}")
    print("")
    print("Top files:")
    for row in payload["top_files"]:
        print(f"  {row['lines']:6d}  {row['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
