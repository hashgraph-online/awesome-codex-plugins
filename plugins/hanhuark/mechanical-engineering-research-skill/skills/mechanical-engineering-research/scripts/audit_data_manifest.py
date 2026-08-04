#!/usr/bin/env python3
"""Validate a research-data provenance and rights CSV manifest."""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from pathlib import Path
from urllib.parse import urlparse


REQUIRED_COLUMNS = {
    "artifact_id",
    "path_or_url",
    "evidence_class",
    "source_id",
    "version",
    "units",
    "schema_or_format",
    "transformation",
    "license",
    "redistribution",
    "checksum",
}


def is_url(value: str) -> bool:
    return urlparse(value).scheme in {"http", "https", "doi"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", help="CSV manifest to validate")
    parser.add_argument("--base", help="base directory for relative local paths")
    parser.add_argument("--verify-checksums", action="store_true")
    args = parser.parse_args()

    manifest = Path(args.manifest).resolve()
    if not manifest.is_file():
        print(f"ERROR: manifest not found: {manifest}", file=sys.stderr)
        return 2
    base = Path(args.base).resolve() if args.base else manifest.parent

    errors: list[str] = []
    warnings: list[str] = []
    with manifest.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing_columns = sorted(REQUIRED_COLUMNS - columns)
        if missing_columns:
            errors.append(f"missing columns: {', '.join(missing_columns)}")
        rows = list(reader)

    seen: set[str] = set()
    for number, row in enumerate(rows, start=2):
        artifact_id = (row.get("artifact_id") or "").strip()
        if not artifact_id:
            errors.append(f"row {number}: empty artifact_id")
        elif artifact_id in seen:
            errors.append(f"row {number}: duplicate artifact_id {artifact_id}")
        seen.add(artifact_id)

        for column in REQUIRED_COLUMNS - {"checksum"}:
            if not (row.get(column) or "").strip():
                errors.append(f"row {number}: empty {column}")

        location = (row.get("path_or_url") or "").strip()
        local_path: Path | None = None
        if location and not is_url(location):
            local_path = (base / location).resolve()
            if not local_path.is_file():
                errors.append(f"row {number}: local artifact not found: {local_path}")

        checksum = (row.get("checksum") or "").strip().lower()
        if not checksum:
            warnings.append(f"row {number}: checksum not recorded")
        elif checksum.startswith("sha256:"):
            checksum = checksum.split(":", 1)[1]
        if checksum and not re_full_sha256(checksum):
            errors.append(f"row {number}: checksum is not a SHA-256 digest")
        elif args.verify_checksums and checksum and local_path and local_path.is_file():
            actual = sha256(local_path)
            if actual != checksum:
                errors.append(f"row {number}: checksum mismatch for {local_path}")

    print(f"Rows: {len(rows)}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    return 1 if errors else 0


def re_full_sha256(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdef" for char in value)


if __name__ == "__main__":
    raise SystemExit(main())
