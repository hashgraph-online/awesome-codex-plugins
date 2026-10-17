#!/usr/bin/env python3
"""Create a compact repository snapshot to reduce broad exploratory reads."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess

IGNORE = {
    ".git", "node_modules", ".next", "dist", "build", "coverage", ".venv",
    "venv", "vendor", "target", ".cache", "__pycache__", ".turbo", ".idea"
}
MANIFESTS = {
    "package.json", "pyproject.toml", "go.mod", "Cargo.toml", "pom.xml",
    "build.gradle", "build.gradle.kts", "requirements.txt", "Gemfile", "composer.json"
}


def git_root() -> Path:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True, stderr=subprocess.DEVNULL
        ).strip()
        return Path(out)
    except Exception:
        return Path.cwd()


def git_lines(args: list[str]) -> list[str]:
    try:
        out = subprocess.check_output(["git", *args], text=True, stderr=subprocess.DEVNULL)
        return [line for line in out.splitlines() if line.strip()]
    except Exception:
        return []


def walk(root: Path, max_depth: int, max_entries: int) -> list[str]:
    rows: list[str] = []
    root_depth = len(root.parts)
    for current, dirs, files in os.walk(root):
        p = Path(current)
        depth = len(p.parts) - root_depth
        dirs[:] = sorted(d for d in dirs if d not in IGNORE and not d.startswith(".cache"))
        if depth >= max_depth:
            dirs[:] = []
        rel = p.relative_to(root)
        if rel != Path("."):
            rows.append(f"DIR  {rel}/")
        for name in sorted(files):
            if len(rows) >= max_entries:
                return rows
            if name.endswith((".map", ".min.js", ".min.css")):
                continue
            fp = p / name
            relf = fp.relative_to(root)
            marker = " *manifest*" if name in MANIFESTS else ""
            try:
                size = fp.stat().st_size
            except OSError:
                size = 0
            if size > 1_000_000 and not marker:
                rows.append(f"FILE {relf} ({size // 1024} KiB, large)")
            else:
                rows.append(f"FILE {relf}{marker}")
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--compact", action="store_true")
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument("--max-entries", type=int, default=120)
    args = ap.parse_args()

    root = git_root()
    print(f"ROOT: {root}")
    branch = git_lines(["branch", "--show-current"])
    if branch:
        print(f"BRANCH: {branch[0]}")

    status = git_lines(["status", "--short"])
    if status:
        print("\nCHANGES:")
        for line in status[:40]:
            print(f"  {line}")
        if len(status) > 40:
            print(f"  ... +{len(status)-40} more")

    print("\nPROJECT MAP:")
    entries = walk(root, 2 if args.compact else args.depth, 80 if args.compact else args.max_entries)
    for row in entries:
        print(f"  {row}")
    if len(entries) >= (80 if args.compact else args.max_entries):
        print("  ... truncated; use targeted search instead of increasing scope unless necessary")


if __name__ == "__main__":
    main()
