#!/usr/bin/env python3
"""Normalize Wordstat region outputs by enriching regionId with names from the regions tree."""

from __future__ import annotations

import argparse
import csv
import glob
import json
from pathlib import Path
from typing import Any


def walk_tree(nodes: list[dict[str, Any]], lookup: dict[int, str]) -> None:
    for node in nodes:
        value = node.get("value") or node.get("regionId") or node.get("id")
        label = node.get("label") or node.get("name") or node.get("regionName")
        if value is not None and label:
            lookup[int(value)] = label
        children = node.get("children") or node.get("regions") or node.get("items") or []
        if isinstance(children, list):
            walk_tree(children, lookup)


def load_lookup(tree_path: Path) -> dict[int, str]:
    raw = json.load(tree_path.open("r", encoding="utf-8"))
    lookup: dict[int, str] = {}
    if isinstance(raw, list):
        walk_tree(raw, lookup)
    elif isinstance(raw, dict):
        walk_tree([raw], lookup)
    return lookup


def normalize_regions(source_dir: Path, lookup: dict[int, str], output_path: Path) -> int:
    rows: list[dict[str, str]] = []
    for source in sorted(glob.glob(str(source_dir / "*.json"))):
        source_path = Path(source)
        if source_path.name.startswith("_") or "regions_tree" in source_path.name:
            continue
        payload = json.load(source_path.open("r", encoding="utf-8"))
        if isinstance(payload, list):
            payload = payload[0] if payload else {}
        if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
            payload = payload["data"]
        if not isinstance(payload, dict):
            continue
        phrase = payload.get("requestPhrase", "")
        for item in payload.get("regions", []):
            region_id = int(item["regionId"])
            rows.append(
                {
                    "request_phrase": phrase,
                    "region_id": str(region_id),
                    "region_name": lookup.get(region_id, f"ID:{region_id}"),
                    "count": str(item.get("count", "")),
                    "share": str(item.get("share", "")),
                    "affinity_index": str(item.get("affinityIndex", "")),
                    "source_file": str(source_path),
                }
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "request_phrase",
                "region_id",
                "region_name",
                "count",
                "share",
                "affinity_index",
                "source_file",
            ],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--regions-dir", required=True)
    parser.add_argument("--regions-tree", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    lookup = load_lookup(Path(args.regions_tree).expanduser().resolve())
    total = normalize_regions(
        Path(args.regions_dir).expanduser().resolve(),
        lookup,
        Path(args.output).expanduser().resolve(),
    )
    print(f"rows={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
