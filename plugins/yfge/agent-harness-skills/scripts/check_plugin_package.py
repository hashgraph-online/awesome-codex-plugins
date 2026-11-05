#!/usr/bin/env python3
"""Validate an unpacked plugin, optionally against its source checkout."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

from check_profile_consistency import check_repository
from validate_plugin_metadata import validate_metadata


PACKAGE_DIRECTORIES = (
    ".codex-plugin", ".claude-plugin", ".cursor-plugin", ".opencode",
    "assets", "docs", "references", "scripts", "skills", "templates",
)
PACKAGE_FILES = (
    ".codexignore",
    "AGENTS.md", "INDEX.md", "GEMINI.md", "README.md", "README.zh-CN.md",
    "LICENSE", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "SECURITY.md",
    "package.json", "package-lock.json", "gemini-extension.json",
)
RESOURCE_RE = re.compile(r"`((?:\.\./)*references/[\w./-]+\.(?:md|json))`")
SCRIPT_RE = re.compile(r"\b((?:scripts/|\.opencode/)[\w./-]+\.(?:py|mjs|js))\b")


def package_files(root: Path) -> list[Path]:
    """List distributable resources, ignoring generated Python caches."""
    files = [root / name for name in PACKAGE_FILES if (root / name).is_file()]
    for name in PACKAGE_DIRECTORIES:
        directory = root / name
        if directory.is_dir():
            files.extend(
                path for path in directory.rglob("*")
                if path.is_file() and "__pycache__" not in path.parts
                and path.suffix != ".pyc"
            )
    return sorted(files)


def check_package(root: Path, source: Path | None = None) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    if source is not None and not (source / ".codex-plugin/plugin.json").is_file():
        errors.append(f"invalid source checkout: {source}")
    for name in PACKAGE_FILES:
        if not (root / name).is_file():
            errors.append(f"missing package file: {name}")
    for name in PACKAGE_DIRECTORIES:
        if not (root / name).is_dir():
            errors.append(f"missing package directory: {name}")

    # Reject escaping resources before validators read manifest-declared files.
    for path in package_files(root):
        if not path.resolve().is_relative_to(root):
            errors.append(f"resource escapes package: {path.relative_to(root)}")
    if errors:
        return errors

    errors.extend(f"{issue.path.relative_to(root)}: {issue.message}"
                  for issue in validate_metadata(root))
    errors.extend(f"{issue.path.relative_to(root)}: {issue.message}"
                  for issue in check_repository(root))

    # Skill references use both document-relative and plugin-root paths.
    for path in sorted((root / "skills").rglob("*.md")):
        for reference in RESOURCE_RE.findall(path.read_text(encoding="utf-8")):
            candidates = [(path.parent / reference).resolve()]
            if not reference.startswith("../"):
                candidates.append((root / reference).resolve())
            if not any(candidate.is_relative_to(root) and candidate.is_file()
                       for candidate in candidates):
                errors.append(f"{path.relative_to(root)}: missing resource {reference}")

    for script in sorted(set(SCRIPT_RE.findall((root / "package.json").read_text()))):
        if not (root / script).is_file():
            errors.append(f"package.json advertises missing script: {script}")

    if source is not None:
        for expected in package_files(source.resolve()):
            relative = expected.relative_to(source.resolve())
            actual = root / relative
            if not actual.is_file():
                errors.append(f"missing source resource: {relative}")
            elif actual.read_bytes() != expected.read_bytes():
                errors.append(f"source resource differs: {relative}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path,
                        default=Path(__file__).resolve().parents[1],
                        help="Unpacked or installed plugin root.")
    parser.add_argument("--source", type=Path,
                        help="Check every distributable source file is preserved byte-for-byte.")
    args = parser.parse_args()
    errors = check_package(args.root, args.source)
    if errors:
        print("Plugin package check FAILED:", file=sys.stderr)
        for error in errors:
            print(f"  error: {error}", file=sys.stderr)
        return 1
    print("Plugin package check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
