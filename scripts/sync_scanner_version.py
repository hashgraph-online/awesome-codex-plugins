#!/usr/bin/env python3
"""Sync the HOL plugin scanner version and wheel SHA256 in contributing.md.

Fetches the latest published ``plugin-scanner`` release from PyPI and updates
``contributing.md`` so that the pip install commands and the expected wheel
SHA256 always reflect the current release.

Usage:
    python3 scripts/sync_scanner_version.py [--check]

Exit codes:
    0 — file was already up to date (or updated in-place with --check off)
    0 — --check mode and file would change (prints "DRIFT" to stdout)
    1 — network or parse error
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTRIBUTING_MD = REPO_ROOT / "CONTRIBUTING.md"
PYPI_JSON_URL = "https://pypi.org/pypi/plugin-scanner/json"
USER_AGENT = "awesome-codex-plugins-scanner-sync"
REQUEST_TIMEOUT_SECONDS = 30

# Matches: plugin-scanner==2.0.972  (inside quotes or bare)
VERSION_PATTERN = re.compile(r'(plugin-scanner==)(\d+\.\d+\.\d+)')

# Matches: Expected reviewed wheel SHA256: `<hash>`
SHA256_PATTERN = re.compile(
    r'(Expected reviewed wheel SHA256:\s*`)([0-9a-f]{64})(`)'
)


def fetch_latest_release() -> tuple[str, str]:
    """Return ``(version, sha256)`` for the latest plugin-scanner wheel on PyPI."""
    req = urllib.request.Request(PYPI_JSON_URL)
    req.add_header("User-Agent", USER_AGENT)
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
        data = json.loads(resp.read())

    version = data["info"]["version"]
    release_files = data["releases"].get(version, [])

    wheel = next(
        (f for f in release_files if f["filename"].endswith(".whl")),
        None,
    )
    if wheel is None:
        raise RuntimeError(f"No wheel found for plugin-scanner=={version}")

    sha256 = wheel["digests"]["sha256"]
    if not sha256 or len(sha256) != 64:
        raise RuntimeError(f"Invalid SHA256 for plugin-scanner=={version}")

    return version, sha256


def update_contributing(version: str, sha256: str) -> bool:
    """Update contributing.md in-place. Returns True if content changed."""
    content = CONTRIBUTING_MD.read_text(encoding="utf-8")

    new_version = f"plugin-scanner=={version}"
    updated = VERSION_PATTERN.sub(
        lambda m: f"{m.group(1)}{version}", content
    )

    updated = SHA256_PATTERN.sub(
        lambda m: f"{m.group(1)}{sha256}{m.group(3)}", updated
    )

    if updated == content:
        return False

    CONTRIBUTING_MD.write_text(updated, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync plugin-scanner version in contributing.md"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only report drift; do not write changes.",
    )
    args = parser.parse_args()

    try:
        version, sha256 = fetch_latest_release()
    except Exception as exc:
        print(f"ERROR: failed to fetch latest release: {exc}", file=sys.stderr)
        return 1

    if args.check:
        # Read-only drift check
        content = CONTRIBUTING_MD.read_text(encoding="utf-8")
        current_version_match = VERSION_PATTERN.search(content)
        current_sha_match = SHA256_PATTERN.search(content)
        if current_version_match and current_sha_match:
            current_version = current_version_match.group(2)
            current_sha = current_sha_match.group(2)
            if current_version != version or current_sha != sha256:
                print("DRIFT")
                print(f"  current: {current_version} / {current_sha[:16]}…")
                print(f"  latest:  {version} / {sha256[:16]}…")
            else:
                print("OK")
        else:
            print("DRIFT")
            print("  could not find version or SHA256 in contributing.md")
        return 0

    changed = update_contributing(version, sha256)
    if changed:
        print(f"Updated contributing.md → plugin-scanner=={version}")
        print(f"  SHA256: {sha256}")
    else:
        print(f"Already up to date: plugin-scanner=={version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
