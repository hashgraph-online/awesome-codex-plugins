#!/usr/bin/env python3
"""Migrate a Suede intake manifest from schema 0.1.0 to 0.2.0.

The migration is evidence-preserving and non-destructive: it writes a sibling
file by default, never upgrades confirmation state, never fills shares, and
records a digest of the source manifest in the new chain of custody.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from create_transfer_package import build_manifest
from validate_transfer_package import (
    check_assets,
    check_list_shaped_sections,
    check_missing_information,
    check_nested_shape,
    check_published_json_schema,
    check_risk_flags,
    check_top_level_shape,
    check_v2_interoperability,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Migrate a suede-intake.json manifest from 0.1.0 to 0.2.0 without "
            "modifying the source or upgrading any rights fact."
        )
    )
    parser.add_argument("input", help="Path to a schema 0.1.0 suede-intake.json file.")
    parser.add_argument(
        "--output",
        help="Output JSON path. Defaults to suede-intake.v0.2.json beside the input.",
    )
    parser.add_argument("--force", action="store_true", help="Replace the output file if it exists.")
    return parser.parse_args()


def read_manifest(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Input is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("Input manifest must contain a JSON object.")
    if data.get("schema_version") != "0.1.0":
        raise ValueError("Input schema_version must be 0.1.0; no migration was performed.")
    return data, hashlib.sha256(raw).hexdigest()


def migrate(data: dict[str, Any], source_path: Path, source_digest: str) -> dict[str, Any]:
    project = data.get("project") if isinstance(data.get("project"), dict) else {}
    creator = data.get("creator") if isinstance(data.get("creator"), dict) else {}
    rights = data.get("rights") if isinstance(data.get("rights"), dict) else {}
    provenance = data.get("provenance") if isinstance(data.get("provenance"), dict) else {}
    optimization = data.get("optimization") if isinstance(data.get("optimization"), dict) else {}
    metadata: dict[str, Any] = {
        "project": project,
        "creator": creator,
        "rights": rights,
        "provenance": provenance,
        "suede": {
            "requested_services": optimization.get("requested_services", []),
            "optimization_notes": optimization.get("notes", ""),
        },
    }
    title = str(project.get("title", "unknown"))
    artist = str(project.get("artist_name", creator.get("name", "unknown")))
    assets = data.get("assets") if isinstance(data.get("assets"), list) else []
    migrated = build_manifest(
        source_path.parent,
        title,
        artist,
        assets,
        include_absolute_paths=False,
        metadata=metadata,
        metadata_source=f"migration:{source_path.name}",
    )
    migrated["missing_information"] = (
        data.get("missing_information")
        if isinstance(data.get("missing_information"), list)
        else migrated["missing_information"]
    )
    migrated["risk_flags"] = (
        data.get("risk_flags") if isinstance(data.get("risk_flags"), list) else migrated["risk_flags"]
    )
    if isinstance(provenance.get("source_root"), str):
        migrated["provenance"]["source_root"] = provenance["source_root"]
    if isinstance(provenance.get("metadata_source"), str):
        migrated["provenance"]["metadata_source"] = provenance["metadata_source"]
    if isinstance(provenance.get("creation_notes"), str):
        migrated["provenance"]["creation_notes"] = provenance["creation_notes"]
    if isinstance(provenance.get("registry_status"), str):
        migrated["provenance"]["registry_status"] = provenance["registry_status"]
    legacy_chain = provenance.get("chain_of_custody")
    migrated["provenance"]["chain_of_custody"] = (
        list(legacy_chain) if isinstance(legacy_chain, list) else []
    )
    migrated["provenance"]["chain_of_custody"].append(
        {
            "date": migrated["generated_at"][:10],
            "event": "Schema 0.1.0 manifest migrated to 0.2.0 without changing the source.",
            "actor": "suede-rights-passport",
            "evidence": f"sha256:{source_digest}",
        },
    )
    return migrated


def validate_migrated(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors += check_top_level_shape(data, strict_current=True)
    errors += check_nested_shape(data)
    errors += check_list_shaped_sections(data)
    errors += check_assets(data)
    errors += check_missing_information(data)
    errors += check_risk_flags(data)
    errors += check_published_json_schema(data)
    errors += check_v2_interoperability(data)
    return errors


def main() -> int:
    args = parse_args()
    source_path = Path(args.input).expanduser().resolve()
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else source_path.with_name("suede-intake.v0.2.json")
    )
    if not source_path.is_file():
        print(f"Input manifest not found: {source_path}", file=sys.stderr)
        return 2
    if output_path == source_path:
        print("Refusing in-place migration; choose a separate --output path.", file=sys.stderr)
        return 2
    if output_path.exists() and not args.force:
        print(f"Refusing to overwrite existing output: {output_path}", file=sys.stderr)
        return 2
    try:
        data, digest = read_manifest(source_path)
        migrated = migrate(data, source_path, digest)
    except (OSError, ValueError) as exc:
        print(f"Migration failed: {exc}", file=sys.stderr)
        return 1
    errors = validate_migrated(migrated)
    if errors:
        print("Migration produced an invalid 0.2.0 manifest:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(migrated, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"Migrated schema 0.1.0 -> 0.2.0: {output_path}")
    print(f"Source preserved: {source_path}")
    print(f"Source manifest digest: sha256:{digest}")
    print("Review normalized records and privacy rules before external exchange.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
